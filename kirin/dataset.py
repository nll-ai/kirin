"""Dataset entity for Kirin - represents a versioned collection of files with linear history."""  # noqa: E501

import tempfile
from collections.abc import MutableMapping
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Union

import fsspec
from loguru import logger

from .commit import Commit, CommitBuilder
from .commit_store import CommitStore
from .file import File
from .storage import ContentStore
from .utils import get_filesystem, strip_protocol


class LazyLocalFiles(MutableMapping):
    """Dictionary-like object that lazily downloads files on access.

    Files are only downloaded when accessed via key lookup. Downloaded files
    are cached for fast repeated access. Iterating over keys does not trigger
    downloads.

    Args:
        files: Dictionary mapping filenames to File objects
        temp_dir: Temporary directory for downloaded files
    """

    def __init__(self, files: Dict[str, File], temp_dir: str):
        self._files = files
        self._temp_dir = temp_dir
        self._cache = {}  # filename -> local path cache

    def __getitem__(self, key: str) -> str:
        """Get local path for a file, downloading if necessary.

        Args:
            key: Filename to access

        Returns:
            Local path to the downloaded file

        Raises:
            KeyError: If file doesn't exist
        """
        # If already downloaded, return cached path
        if key in self._cache:
            return self._cache[key]

        # Download on first access
        if key not in self._files:
            raise KeyError(f"File not found: {key}")

        local_path = Path(self._temp_dir) / key
        self._files[key].download_to(local_path)
        self._cache[key] = str(local_path)
        return self._cache[key]

    def __setitem__(self, key: str, value: str) -> None:
        """Set a local path (for internal use)."""
        self._cache[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a cached file path."""
        if key in self._cache:
            del self._cache[key]

    def __iter__(self):
        """Iterate over filenames without downloading."""
        return iter(self._files)

    def __len__(self) -> int:
        """Return number of files."""
        return len(self._files)

    def __contains__(self, key: str) -> bool:
        """Check if file exists without downloading."""
        return key in self._files

    def keys(self):
        """Return filenames without downloading."""
        return self._files.keys()

    def values(self):
        """Return local paths for downloaded files only."""
        return self._cache.values()

    def items(self):
        """Return (filename, local_path) pairs for downloaded files only."""
        return self._cache.items()

    def get(self, key: str, default=None):
        """Get local path with default if not found."""
        try:
            return self[key]
        except KeyError:
            return default


class Dataset:
    """Represents a versioned collection of files with linear commit history.

    This is the main interface for working with Kirin datasets. It provides
    methods for committing changes, checking out specific versions, and
    accessing files from the current commit.

    The dataset maintains a linear commit history where each commit represents
    a snapshot of files at a point in time. You can checkout any commit to
    access files from that version, or checkout the latest commit by calling
    checkout() without arguments.

    **Important:** New commits can only be created when checked out to the
    latest commit. This ensures linear history without divergent branches.
    If you've checked out an older commit, you must first checkout() to the
    latest commit before making new commits.

    Example:
        # Create a dataset
        dataset = Dataset(root_dir="/path/to/data", name="my_dataset")

        # Commit some files
        commit_hash = dataset.commit(message="Initial commit", add_files=["file1.csv"])

        # Checkout an older commit to view files
        dataset.checkout(commit_hash)

        # Must checkout to latest before committing again
        dataset.checkout()  # Move to latest
        dataset.commit(message="New commit", add_files=["file2.csv"])

    Args:
        root_dir: Root directory for the dataset
        name: Name of the dataset
        description: Description of the dataset
        fs: Filesystem to use (auto-detected if None)
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        name: str,
        description: str = "",
        fs: Optional[fsspec.AbstractFileSystem] = None,
        # AWS/S3 authentication
        aws_profile: Optional[str] = None,
        # GCP/GCS authentication
        gcs_token: Optional[Union[str, Path]] = None,
        gcs_project: Optional[str] = None,
        # Azure authentication
        azure_account_name: Optional[str] = None,
        azure_account_key: Optional[str] = None,
        azure_connection_string: Optional[str] = None,
    ):
        self.root_dir = str(root_dir)
        self.name = name
        self.description = description
        self.fs = fs or get_filesystem(
            self.root_dir,
            aws_profile=aws_profile,
            gcs_token=gcs_token,
            gcs_project=gcs_project,
            azure_account_name=azure_account_name,
            azure_account_key=azure_account_key,
            azure_connection_string=azure_connection_string,
        )

        # Initialize storage and commit store
        self.storage = ContentStore(self.root_dir, self.fs)
        self.commit_store = CommitStore(self.root_dir, name, self.fs, self.storage)

        # Current commit (lazy loaded)
        self._current_commit: Optional[Commit] = None

        logger.info(f"Dataset '{name}' initialized at {self.root_dir}")

    @property
    def current_commit(self) -> Optional[Commit]:
        """Get the current commit.

        Returns:
            Current commit if any exist, None otherwise
        """
        if self._current_commit is None:
            self._current_commit = self.commit_store.get_latest_commit()
        return self._current_commit

    @current_commit.setter
    def current_commit(self, commit: Optional[Commit]):
        """Set the current commit.

        Args:
            commit: Commit to set as current
        """
        self._current_commit = commit

    @property
    def head(self) -> Optional[Commit]:
        """Get the latest commit (alias for current_commit)."""
        return self.current_commit

    @property
    def files(self) -> Dict[str, File]:
        """Get files from the current commit.

        Returns:
            Dictionary mapping filenames to File objects
        """
        if self.current_commit is None:
            return {}
        return self.current_commit.files

    def commit(
        self,
        message: str,
        add_files: List[Union[str, Path]] = None,
        remove_files: List[str] = None,
    ) -> str:
        """Create a new commit with changes.

        Args:
            message: Commit message
            add_files: List of files to add/update
            remove_files: List of filenames to remove

        Returns:
            Hash of the new commit

        Raises:
            ValueError: If no changes are specified or if not on latest commit
            FileNotFoundError: If a file to add doesn't exist
        """
        if not add_files and not remove_files:
            raise ValueError(
                "No changes specified - at least one of add_files or "
                "remove_files must be provided"
            )

        # Ensure we're on the latest commit before allowing new commits
        latest_commit = self.commit_store.get_latest_commit()
        if latest_commit is not None:  # Only check if commits exist
            if (
                self.current_commit is None
                or self.current_commit.hash != latest_commit.hash
            ):
                raise ValueError(
                    "Cannot commit: currently checked out to non-latest commit. "
                    "Use checkout() to move to the latest commit first."
                )

        # Start building commit from current state
        builder = CommitBuilder(self.current_commit)

        # Add files
        if add_files:
            for file_path in add_files:
                file_path = str(file_path)

                # Check if file exists
                source_fs = get_filesystem(file_path)
                if not source_fs.exists(strip_protocol(file_path)):
                    raise FileNotFoundError(f"File not found: {file_path}")

                # Store file in content store
                content_hash = self.storage.store_file(file_path)

                # Create File object
                file_size = source_fs.size(strip_protocol(file_path))
                file_obj = File(
                    hash=content_hash,
                    name=Path(file_path).name,
                    size=file_size,
                    _storage=self.storage,
                )

                # Add to commit
                builder.add_file(file_obj.name, file_obj)

        # Remove files
        if remove_files:
            for filename in remove_files:
                builder.remove_file(filename)

        # Build and save commit
        commit = builder.build(message)
        self.commit_store.save_commit(commit)
        self._current_commit = commit

        logger.info(f"Created commit {commit.short_hash}: {message}")
        return commit.hash

    def checkout(self, commit_hash: Optional[str] = None) -> None:
        """Checkout a specific commit or the latest commit.

        This method allows you to switch between different versions of your dataset.
        You can checkout a specific commit by providing its hash, or checkout the
        latest commit by calling without arguments.

        Args:
            commit_hash: Hash of the commit to checkout (can be partial hash).
                        If None or not provided, checks out the latest commit.

        Raises:
            ValueError: If commit not found or no commits exist in dataset

        Examples:
            # Checkout the latest commit
            dataset.checkout()

            # Checkout a specific commit by full hash
            dataset.checkout("abc123def456...")

            # Checkout a specific commit by partial hash
            dataset.checkout("abc123")
        """
        if commit_hash is None:
            # Checkout the latest commit
            commit = self.commit_store.get_latest_commit()
            if commit is None:
                raise ValueError("No commits found in dataset")
        else:
            # Checkout specific commit
            commit = self.commit_store.get_commit(commit_hash)
            if commit is None:
                raise ValueError(f"Commit not found: {commit_hash}")

        self.current_commit = commit
        logger.info(f"Checked out commit {commit.short_hash}: {commit.message}")

    def get_file(self, name: str) -> Optional[File]:
        """Get a file from the current commit.

        Args:
            name: Name of the file to get

        Returns:
            File object if found, None otherwise
        """
        if self.current_commit is None:
            return None
        return self.current_commit.get_file(name)

    def list_files(self) -> List[str]:
        """List files in the current commit.

        Returns:
            List of filenames
        """
        if self.current_commit is None:
            return []
        return self.current_commit.list_files()

    def has_file(self, name: str) -> bool:
        """Check if a file exists in the current commit.

        Args:
            name: Name of the file to check

        Returns:
            True if file exists, False otherwise
        """
        if self.current_commit is None:
            return False
        return self.current_commit.has_file(name)

    def read_file(self, name: str, mode: str = "r") -> Union[str, bytes]:
        """Read a file from the current commit.

        Args:
            name: Name of the file to read
            mode: Read mode ('r' for text, 'rb' for bytes)

        Returns:
            File content

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_obj = self.get_file(name)
        if file_obj is None:
            raise FileNotFoundError(f"File not found: {name}")

        return file_obj.read(mode)

    def download_file(self, name: str, target_path: Union[str, Path]) -> str:
        """Download a file from the current commit.

        Args:
            name: Name of the file to download
            target_path: Local path to save the file

        Returns:
            Path where the file was saved

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_obj = self.get_file(name)
        if file_obj is None:
            raise FileNotFoundError(f"File not found: {name}")

        return file_obj.download_to(target_path)

    def open_file(self, name: str, mode: str = "rb"):
        """Open a file from the current commit.

        Args:
            name: Name of the file to open
            mode: Open mode

        Returns:
            File-like object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_obj = self.get_file(name)
        if file_obj is None:
            raise FileNotFoundError(f"File not found: {name}")

        return file_obj.open(mode)

    @contextmanager
    def local_files(self):
        """Context manager for accessing files as local paths.

        Files are downloaded lazily on first access and cached for fast repeated
        access. Iterating over keys does not trigger downloads. Files are
        automatically cleaned up when exiting the context.

        Yields:
            LazyLocalFiles object that behaves like a dictionary mapping
            filenames to local file paths
        """
        if self.current_commit is None:
            yield {}
            return

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"kirin_{self.name}_")

        try:
            # Return lazy-loading dict-like object
            yield LazyLocalFiles(self.current_commit.files, temp_dir)

        finally:
            # Clean up all downloaded files
            import shutil

            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary directory {temp_dir}: {e}"
                )

    def history(self, limit: Optional[int] = None) -> List[Commit]:
        """Get commit history.

        Args:
            limit: Maximum number of commits to return

        Returns:
            List of commits in chronological order (newest first)
        """
        return self.commit_store.get_commit_history(limit)

    def get_commit(self, commit_hash: str) -> Optional[Commit]:
        """Get a specific commit.

        Args:
            commit_hash: Hash of the commit to get

        Returns:
            Commit if found, None otherwise
        """
        return self.commit_store.get_commit(commit_hash)

    def get_commits(self) -> List[Commit]:
        """Get all commits in the dataset.

        Returns:
            List of all commits
        """
        return self.commit_store.get_commits()

    def is_empty(self) -> bool:
        """Check if the dataset is empty (no commits).

        Returns:
            True if no commits exist, False otherwise
        """
        return self.commit_store.is_empty()

    def get_info(self) -> dict:
        """Get information about the dataset.

        Returns:
            Dictionary with dataset information
        """
        info = self.commit_store.get_dataset_info()
        info.update(
            {
                "name": self.name,
                "description": self.description,
                "root_dir": self.root_dir,
                "current_commit": self.current_commit.hash
                if self.current_commit
                else None,
            }
        )
        return info

    def cleanup_orphaned_files(self) -> int:
        """Remove files that are no longer referenced by any commit.

        Returns:
            Number of files removed
        """
        return self.commit_store.cleanup_orphaned_files()

    def to_dict(self) -> dict:
        """Convert the dataset to a dictionary representation.

        Returns:
            Dictionary with dataset properties
        """
        return {
            "name": self.name,
            "description": self.description,
            "root_dir": self.root_dir,
            "current_commit": self.current_commit.hash if self.current_commit else None,
            "commit_count": self.commit_store.get_commit_count(),
        }

    def __str__(self) -> str:
        """String representation of the dataset."""
        commit_count = self.commit_store.get_commit_count()
        current_hash = self.current_commit.short_hash if self.current_commit else "None"
        return (
            f"Dataset(name='{self.name}', commits={commit_count}, "
            f"current={current_hash})"
        )

    def __repr__(self) -> str:
        """Detailed string representation of the dataset."""
        return (
            f"Dataset(name='{self.name}', description='{self.description}', "
            f"root_dir='{self.root_dir}')"
        )
