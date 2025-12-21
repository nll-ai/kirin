"""Commit entity for Kirin - represents an immutable snapshot of files."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from loguru import logger

from .file import File

if TYPE_CHECKING:
    from .storage import ContentStore


@dataclass(frozen=True)
class Commit:
    """Represents an immutable snapshot of files at a point in time.

    Commits form a linear chain where each commit has exactly one parent
    (except the first commit which has no parent). This creates a simple
    linear history without branches or merges.
    """

    hash: str
    message: str
    timestamp: datetime
    parent_hash: Optional[str]
    files: Dict[str, File] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate commit properties after initialization."""
        if not self.hash:
            raise ValueError("Commit hash cannot be empty")
        if not self.message:
            raise ValueError("Commit message cannot be empty")
        if self.timestamp is None:
            raise ValueError("Commit timestamp cannot be None")

    @property
    def short_hash(self) -> str:
        """Return the first 8 characters of the commit hash."""
        return self.hash[:8]

    @property
    def is_initial(self) -> bool:
        """Check if this is the initial commit (no parent)."""
        return self.parent_hash is None

    def get_file(self, name: str) -> Optional[File]:
        """Get a file by name from this commit.

        Args:
            name: Name of the file to get

        Returns:
            File object if found, None otherwise
        """
        return self.files.get(name)

    def list_files(self) -> List[str]:
        """List all file names in this commit.

        Returns:
            List of file names
        """
        return list(self.files.keys())

    def has_file(self, name: str) -> bool:
        """Check if a file exists in this commit.

        Args:
            name: Name of the file to check

        Returns:
            True if file exists, False otherwise
        """
        return name in self.files

    def get_file_count(self) -> int:
        """Get the number of files in this commit.

        Returns:
            Number of files
        """
        return len(self.files)

    def get_total_size(self) -> int:
        """Get the total size of all files in this commit.

        Returns:
            Total size in bytes
        """
        return sum(file.size for file in self.files.values())

    def to_dict(self) -> dict:
        """Convert the commit to a dictionary representation.

        Returns:
            Dictionary with commit properties
        """
        return {
            "hash": self.hash,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "parent_hash": self.parent_hash,
            "files": {name: file.to_dict() for name, file in self.files.items()},
            "metadata": self.metadata,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(
        cls, data: dict, storage: Optional["ContentStore"] = None
    ) -> "Commit":
        """Create a Commit from a dictionary representation.

        Args:
            data: Dictionary with commit properties
            storage: Optional storage system for files

        Returns:
            Commit instance
        """
        # Parse timestamp
        if isinstance(data["timestamp"], str):
            timestamp = datetime.fromisoformat(data["timestamp"])
        else:
            timestamp = data["timestamp"]

        # Parse files
        files = {}
        for name, file_data in data.get("files", {}).items():
            file = File.from_dict(file_data, storage)
            files[name] = file

        return cls(
            hash=data["hash"],
            message=data["message"],
            timestamp=timestamp,
            parent_hash=data.get("parent_hash"),
            files=files,
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
        )

    def __str__(self) -> str:
        """String representation of the commit."""
        file_count = len(self.files)
        message_preview = (
            f"{self.message[:50]}{'...' if len(self.message) > 50 else ''}"
        )
        return f"Commit({self.short_hash}: {message_preview}, {file_count} files)"

    def __repr__(self) -> str:
        """Detailed string representation of the commit."""
        return (
            f"Commit(hash='{self.hash}', message='{self.message}', "
            f"timestamp={self.timestamp}, parent_hash='{self.parent_hash}', "
            f"files={len(self.files)})"
        )

    def _get_widget_data(self) -> dict:
        """Get widget data dictionary for CommitWidget.

        Returns:
            Dictionary with commit data for widget rendering
        """
        from .html_repr import format_file_size, get_file_icon_html

        file_count = len(self.files)
        total_size = sum(f.size for f in self.files.values())

        # Build files list with content for preview
        files = []
        for filename, file_obj in sorted(self.files.items()):
            file_data = {
                "name": filename,
                "size": format_file_size(file_obj.size),
                "icon_html": get_file_icon_html(filename, file_obj.content_type),
                "content_type": file_obj.content_type,
            }

            # Add file content for preview (only for small text files)
            # Limit to 100KB for text files
            max_preview_size = 100 * 1024  # 100KB
            is_text_file = (
                file_obj.content_type
                and (
                    file_obj.content_type.startswith("text/")
                    or file_obj.content_type in ["application/json", "application/xml"]
                )
            ) or filename.lower().endswith((".txt", ".csv", ".json", ".md", ".py"))
            is_image = (
                file_obj.content_type
                and file_obj.content_type.startswith("image/")
                or filename.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
                )
            )

            if is_text_file and file_obj.size <= max_preview_size:
                try:
                    content = file_obj.read_text()
                    file_data["content"] = content
                    file_data["is_text"] = True
                except Exception as e:
                    logger.debug(f"Failed to read file {filename} for preview: {e}")
                    file_data["content"] = None
                    file_data["is_text"] = False
            elif is_image:
                # For images, we'll need to get the data URL or path
                # For now, mark it as an image
                file_data["is_image"] = True
                file_data["is_text"] = False
            else:
                file_data["is_text"] = False
                file_data["is_image"] = False

            files.append(file_data)

        return {
            "hash": self.short_hash,
            "message": self.message,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "parent_hash": self.parent_hash[:8] if self.parent_hash else None,
            "file_count": file_count,
            "size": format_file_size(total_size),
            "files": files,
        }

    def _repr_html_(self) -> str:
        """Generate HTML representation of the commit for notebook display.

        Returns:
            HTML string with commit information and file list
        """
        # Use widgets - let errors propagate for debugging
        from .widgets import CommitWidget

        widget = CommitWidget(data=self._get_widget_data())
        return widget._repr_html_()


class CommitBuilder:
    """Builder for creating new commits.

    This class helps construct commits by tracking changes from a parent commit.

    **Rationale for Builder Pattern:**

    We use a builder pattern primarily for **encapsulation**. Commit construction
    involves non-trivial logic:
    - Generating commit hashes from content
    - Managing parent hash relationships
    - Copying and merging state (files, metadata, tags) from parent commits
    - Tracking changes for logging

    The builder encapsulates this complexity, keeping the Dataset.commit() method
    focused on file operations rather than commit construction details.

    Args:
        parent_commit: Parent commit to base changes on (None for initial commit)
    """

    def __init__(self, parent_commit: Optional[Commit] = None):
        self.parent_commit = parent_commit
        self.files = dict(parent_commit.files) if parent_commit else {}
        self.metadata = dict(parent_commit.metadata) if parent_commit else {}
        self.tags = list(parent_commit.tags) if parent_commit else []
        self.added_files = set()
        self.removed_files = set()

    def add_file(self, name: str, file: File) -> "CommitBuilder":
        """Add or update a file in the commit.

        Args:
            name: Name of the file
            file: File object to add

        Returns:
            Self for method chaining
        """
        self.files[name] = file
        self.added_files.add(name)
        return self

    def remove_file(self, name: str) -> "CommitBuilder":
        """Remove a file from the commit.

        Args:
            name: Name of the file to remove

        Returns:
            Self for method chaining
        """
        if name in self.files:
            del self.files[name]
            self.removed_files.add(name)
        return self

    def set_metadata(self, metadata: Dict[str, Any]) -> "CommitBuilder":
        """Set metadata for the commit.

        Args:
            metadata: Dictionary of metadata to store

        Returns:
            Self for method chaining
        """
        self.metadata = metadata
        return self

    def add_tags(self, tags: List[str]) -> "CommitBuilder":
        """Add tags to the commit.

        Args:
            tags: List of tags to add

        Returns:
            Self for method chaining
        """
        self.tags = tags
        return self

    def __call__(self, message: str, commit_hash: Optional[str] = None) -> Commit:
        """Build the commit (callable interface).

        Args:
            message: Commit message
            commit_hash: Optional commit hash (generated if not provided)

        Returns:
            New Commit instance
        """
        # Generate commit hash if not provided
        if commit_hash is None:
            commit_hash = self._generate_commit_hash(message)

        # Get parent hash
        parent_hash = self.parent_commit.hash if self.parent_commit else None

        # Create commit
        commit = Commit(
            hash=commit_hash,
            message=message,
            timestamp=datetime.now(),
            parent_hash=parent_hash,
            files=self.files.copy(),
            metadata=self.metadata.copy(),
            tags=self.tags.copy(),
        )

        logger.info(f"Built commit {commit_hash[:8]}: {message}")
        logger.info(f"  Added files: {list(self.added_files)}")
        logger.info(f"  Removed files: {list(self.removed_files)}")

        return commit

    def _generate_commit_hash(self, message: str) -> str:
        """Generate a commit hash based on content and message.

        Args:
            message: Commit message

        Returns:
            Generated commit hash
        """
        import hashlib

        # Create hash from file hashes, message, and timestamp
        file_hashes = sorted(file.hash for file in self.files.values())
        parent_hash = self.parent_commit.hash if self.parent_commit else ""

        # Combine all components
        content = (
            "\n".join(file_hashes)
            + "\n"
            + message
            + "\n"
            + parent_hash
            + "\n"
            + str(datetime.now())
        )

        # Generate hash
        hasher = hashlib.sha256()
        hasher.update(content.encode("utf-8"))
        return hasher.hexdigest()

    def get_changes(self) -> dict:
        """Get summary of changes in this commit.

        Returns:
            Dictionary with change summary
        """
        return {
            "added_files": list(self.added_files),
            "removed_files": list(self.removed_files),
            "total_files": len(self.files),
            "is_initial": self.parent_commit is None,
        }
