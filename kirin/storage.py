"""Content-addressed storage for Kirin files."""

from hashlib import sha256
from pathlib import Path
from typing import Optional, Union

import fsspec
from loguru import logger

from .utils import get_filesystem, strip_protocol


class ContentStore:
    """Manages content-addressed storage for files.

    Files are stored at root_dir/data/{hash[:2]}/{hash[2:]} to avoid
    filesystem limitations with large numbers of files in a single directory.
    """

    def __init__(
        self, root_dir: Union[str, Path], fs: Optional[fsspec.AbstractFileSystem] = None
    ):
        """Initialize the content store.

        Args:
            root_dir: Root directory for content storage
            fs: Filesystem to use (auto-detected from root_dir if None)
        """
        self.root_dir = str(root_dir)
        self.fs = fs or get_filesystem(self.root_dir)
        self.data_dir = f"{self.root_dir}/data"

        # Ensure data directory exists
        self.fs.makedirs(strip_protocol(self.data_dir), exist_ok=True)
        logger.info(f"Content store initialized at {self.data_dir}")

    def store_file(self, file_path: Union[str, Path]) -> str:
        """Store a file and return its content hash.

        Args:
            file_path: Path to the file to store

        Returns:
            Content hash of the stored file

        Raises:
            FileNotFoundError: If the source file doesn't exist
            IOError: If there's an error reading or storing the file
        """
        file_path = str(file_path)

        # Check if source file exists
        source_fs = get_filesystem(file_path)
        if not source_fs.exists(strip_protocol(file_path)):
            raise FileNotFoundError(f"Source file not found: {file_path}")

        # Read and hash the file content
        try:
            with source_fs.open(strip_protocol(file_path), "rb") as f:
                content = f.read()

            # Calculate content hash
            content_hash = sha256(content).hexdigest()

            # Check if file already exists in storage
            if self.exists(content_hash):
                logger.info(f"File already exists in storage: {content_hash[:8]}")
                return content_hash

            # Store the file
            self._store_content(content_hash, content)
            logger.info(f"Stored file {file_path} with hash {content_hash[:8]}")
            return content_hash

        except Exception as e:
            logger.error(f"Failed to store file {file_path}: {e}")
            raise IOError(f"Failed to store file {file_path}: {e}") from e

    def store_content(self, content: bytes) -> str:
        """Store content bytes and return the hash.

        Args:
            content: Content bytes to store

        Returns:
            Content hash of the stored content
        """
        # Calculate content hash
        content_hash = sha256(content).hexdigest()

        # Check if content already exists
        if self.exists(content_hash):
            logger.info(f"Content already exists in storage: {content_hash[:8]}")
            return content_hash

        # Store the content
        self._store_content(content_hash, content)
        logger.info(f"Stored content with hash {content_hash[:8]}")
        return content_hash

    def _store_content(self, content_hash: str, content: bytes):
        """Store content at the appropriate location.

        Args:
            content_hash: Hash of the content
            content: Content bytes to store
        """
        # Create storage path: data/{hash[:2]}/{hash[2:]}
        hash_dir = f"{self.data_dir}/{content_hash[:2]}"
        file_path = f"{hash_dir}/{content_hash[2:]}"

        # Ensure directory exists
        self.fs.makedirs(strip_protocol(hash_dir), exist_ok=True)

        # Write content
        with self.fs.open(strip_protocol(file_path), "wb") as f:
            f.write(content)

    def retrieve(self, content_hash: str) -> bytes:
        """Retrieve content by hash.

        Args:
            content_hash: Hash of the content to retrieve

        Returns:
            Content bytes

        Raises:
            FileNotFoundError: If content doesn't exist
            IOError: If there's an error reading the content
        """
        if not self.exists(content_hash):
            raise FileNotFoundError(f"Content not found: {content_hash}")

        try:
            file_path = self._get_content_path(content_hash)
            with self.fs.open(strip_protocol(file_path), "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to retrieve content {content_hash[:8]}: {e}")
            raise IOError(f"Failed to retrieve content {content_hash[:8]}: {e}") from e

    def retrieve_to_file(self, content_hash: str, target_path: Union[str, Path]) -> str:
        """Retrieve content to a local file.

        Args:
            content_hash: Hash of the content to retrieve
            target_path: Local path to save the content

        Returns:
            Path where the content was saved
        """
        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            content = self.retrieve(content_hash)
            with open(target_path, "wb") as f:
                f.write(content)

            logger.info(f"Retrieved content {content_hash[:8]} to {target_path}")
            return str(target_path)

        except Exception as e:
            logger.error(
                f"Failed to retrieve content {content_hash[:8]} to {target_path}: {e}"
            )
            raise IOError(f"Failed to retrieve content to {target_path}: {e}") from e

    def open_stream(self, content_hash: str, mode: str = "rb"):
        """Open content as a stream.

        Args:
            content_hash: Hash of the content to open
            mode: Open mode ('rb' for binary, 'r' for text)

        Returns:
            File-like object for reading the content
        """
        if not self.exists(content_hash):
            raise FileNotFoundError(f"Content not found: {content_hash}")

        file_path = self._get_content_path(content_hash)
        return self.fs.open(strip_protocol(file_path), mode)

    def exists(self, content_hash: str) -> bool:
        """Check if content exists in storage.

        Args:
            content_hash: Hash of the content to check

        Returns:
            True if content exists, False otherwise
        """
        try:
            file_path = self._get_content_path(content_hash)
            return self.fs.exists(strip_protocol(file_path))
        except Exception:
            return False

    def get_size(self, content_hash: str) -> int:
        """Get the size of stored content.

        Args:
            content_hash: Hash of the content

        Returns:
            Size of the content in bytes

        Raises:
            FileNotFoundError: If content doesn't exist
        """
        if not self.exists(content_hash):
            raise FileNotFoundError(f"Content not found: {content_hash}")

        try:
            file_path = self._get_content_path(content_hash)
            return self.fs.size(strip_protocol(file_path))
        except Exception as e:
            logger.error(f"Failed to get size for content {content_hash[:8]}: {e}")
            raise IOError(
                f"Failed to get size for content {content_hash[:8]}: {e}"
            ) from e

    def _get_content_path(self, content_hash: str) -> str:
        """Get the storage path for content.

        Args:
            content_hash: Hash of the content

        Returns:
            Storage path for the content
        """
        return f"{self.data_dir}/{content_hash[:2]}/{content_hash[2:]}"

    def list_hashes(self) -> list[str]:
        """List all content hashes in storage.

        Returns:
            List of content hashes
        """
        try:
            # Get all files in the data directory
            pattern = f"{strip_protocol(self.data_dir)}/*/*"
            files = self.fs.glob(pattern)

            # Extract hashes from file paths
            hashes = []
            for file_path in files:
                # Extract hash from path: data_dir/hash[:2]/hash[2:]
                path_parts = file_path.split("/")
                if len(path_parts) >= 2:
                    hash_prefix = path_parts[-2]
                    hash_suffix = path_parts[-1]
                    full_hash = hash_prefix + hash_suffix
                    hashes.append(full_hash)

            return hashes

        except Exception as e:
            logger.warning(f"Failed to list content hashes: {e}")
            return []

    def cleanup_orphaned_files(self, used_hashes: set[str]) -> int:
        """Remove files that are no longer referenced.

        Args:
            used_hashes: Set of content hashes that are still in use

        Returns:
            Number of files removed
        """
        try:
            all_hashes = set(self.list_hashes())
            orphaned_hashes = all_hashes - used_hashes

            removed_count = 0
            for content_hash in orphaned_hashes:
                try:
                    file_path = self._get_content_path(content_hash)
                    self.fs.rm(strip_protocol(file_path))
                    removed_count += 1
                    logger.info(f"Removed orphaned file: {content_hash[:8]}")
                except Exception as e:
                    logger.warning(
                        f"Failed to remove orphaned file {content_hash[:8]}: {e}"
                    )

            logger.info(f"Cleaned up {removed_count} orphaned files")
            return removed_count

        except Exception as e:
            logger.error(f"Failed to cleanup orphaned files: {e}")
            return 0
