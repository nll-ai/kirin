"""File entity for Kirin - represents a versioned file with content-addressed storage."""

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union, BinaryIO, TextIO

import fsspec
from loguru import logger

from .utils import strip_protocol


@dataclass(frozen=True)
class File:
    """Represents a versioned file with content-addressed storage.

    Files are immutable once created and are identified by their content hash.
    The actual file content is stored in the content-addressed storage system.
    """

    hash: str
    name: str
    size: int
    content_type: Optional[str] = None
    _storage: Optional["ContentStore"] = None
    _fs: Optional[fsspec.AbstractFileSystem] = None

    def __post_init__(self):
        """Validate file properties after initialization."""
        if not self.hash:
            raise ValueError("File hash cannot be empty")
        if not self.name:
            raise ValueError("File name cannot be empty")
        if self.size < 0:
            raise ValueError("File size cannot be negative")

    @property
    def path(self) -> str:
        """Return the original filename/path."""
        return self.name

    @property
    def short_hash(self) -> str:
        """Return the first 8 characters of the hash."""
        return self.hash[:8]

    def read_bytes(self) -> bytes:
        """Read the file content as bytes.

        Returns:
            The file content as bytes

        Raises:
            FileNotFoundError: If the file doesn't exist in storage
            IOError: If there's an error reading the file
        """
        if not self._storage:
            raise RuntimeError("File not associated with storage system")

        try:
            return self._storage.retrieve(self.hash)
        except Exception as e:
            logger.error(
                f"Failed to read file {self.name} (hash: {self.hash[:8]}): {e}"
            )
            raise IOError(f"Failed to read file {self.name}: {e}") from e

    def read_text(self, encoding: str = "utf-8") -> str:
        """Read the file content as text.

        Args:
            encoding: Text encoding to use (default: utf-8)

        Returns:
            The file content as a string
        """
        return self.read_bytes().decode(encoding)

    def read(self, mode: str = "rb") -> Union[bytes, str]:
        """Read the file content.

        Args:
            mode: Read mode ('rb' for bytes, 'r' for text)

        Returns:
            File content as bytes or string depending on mode
        """
        if mode == "rb":
            return self.read_bytes()
        elif mode == "r":
            return self.read_text()
        else:
            raise ValueError(f"Unsupported read mode: {mode}")

    def open(self, mode: str = "rb") -> Union[BinaryIO, TextIO]:
        """Open the file for reading.

        Args:
            mode: Open mode ('rb' for binary, 'r' for text)

        Returns:
            File-like object for reading

        Note:
            This downloads the file to a temporary location and returns
            a file handle to it. The temporary file is cleaned up when
            the handle is closed.
        """
        if not self._storage:
            raise RuntimeError("File not associated with storage system")

        # Create a temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix=f"_{self.name}")
        os.close(temp_fd)  # Close the file descriptor

        try:
            # Download the file content
            content = self.read_bytes()

            # Write to temporary file
            with open(temp_path, "wb") as f:
                f.write(content)

            # Return a file handle that will clean up the temp file
            return _TempFileHandle(temp_path, mode)

        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise IOError(f"Failed to open file {self.name}: {e}") from e

    def download_to(self, path: Union[str, Path]) -> str:
        """Download the file to a local path.

        Args:
            path: Local path to save the file

        Returns:
            The local path where the file was saved

        Raises:
            IOError: If there's an error downloading the file
        """
        if not self._storage:
            raise RuntimeError("File not associated with storage system")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            content = self.read_bytes()
            with open(path, "wb") as f:
                f.write(content)

            logger.info(f"Downloaded file {self.name} to {path}")
            return str(path)

        except Exception as e:
            logger.error(f"Failed to download file {self.name} to {path}: {e}")
            raise IOError(f"Failed to download file {self.name}: {e}") from e

    def exists(self) -> bool:
        """Check if the file exists in storage.

        Returns:
            True if the file exists in storage, False otherwise
        """
        if not self._storage:
            return False

        try:
            return self._storage.exists(self.hash)
        except Exception:
            return False

    def to_dict(self) -> dict:
        """Convert the file to a dictionary representation.

        Returns:
            Dictionary with file properties
        """
        return {
            "hash": self.hash,
            "name": self.name,
            "size": self.size,
            "content_type": self.content_type,
        }

    @classmethod
    def from_dict(cls, data: dict, storage: Optional["ContentStore"] = None) -> "File":
        """Create a File from a dictionary representation.

        Args:
            data: Dictionary with file properties
            storage: Optional storage system to associate with the file

        Returns:
            File instance
        """
        file = cls(
            hash=data["hash"],
            name=data["name"],
            size=data["size"],
            content_type=data.get("content_type"),
        )

        # Associate with storage if provided
        if storage:
            object.__setattr__(file, "_storage", storage)

        return file

    def __str__(self) -> str:
        """String representation of the file."""
        return f"File(name='{self.name}', hash='{self.hash[:8]}', size={self.size})"

    def __repr__(self) -> str:
        """Detailed string representation of the file."""
        return f"File(hash='{self.hash}', name='{self.name}', size={self.size}, content_type='{self.content_type}')"


class _TempFileHandle:
    """File handle that cleans up temporary files when closed."""

    def __init__(self, path: str, mode: str):
        self.path = path
        self.mode = mode
        self._file = None

    def __enter__(self):
        """Open the temporary file."""
        self._file = open(self.path, self.mode)
        return self._file

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the file and clean up the temporary file."""
        if self._file:
            self._file.close()

        # Clean up the temporary file
        try:
            if os.path.exists(self.path):
                os.unlink(self.path)
        except Exception as e:
            logger.warning(f"Failed to clean up temporary file {self.path}: {e}")

    def __getattr__(self, name):
        """Delegate attribute access to the underlying file."""
        if self._file is None:
            raise RuntimeError("File handle not opened")
        return getattr(self._file, name)


# Import ContentStore here to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .storage import ContentStore
