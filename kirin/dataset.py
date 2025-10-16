"""Simplified Git-based dataset using pygit2 directly."""

import shutil
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, List, Optional, Union

import pygit2
from loguru import logger

from .file import File


class Dataset:
    """Simplified Git-based dataset.

    Uses pygit2 directly without complex wrapper layers.
    Maintains the same API but with much simpler implementation.
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        name: str,
        description: str = "",
        **kwargs  # For cloud auth compatibility
    ):
        self.root_dir = str(root_dir)
        self.name = name
        self.description = description

        # Initialize Git repository (this handles everything we need)
        try:
            self.repo = pygit2.Repository(self.root_dir)
        except pygit2.GitError:
            self.repo = pygit2.init_repository(self.root_dir)
            # Set basic config
            self.repo.config['user.name'] = 'Kirin'
            self.repo.config['user.email'] = 'kirin@data.versioning'

        logger.info(f"Git dataset '{name}' ready at {self.root_dir}")

    @property
    def current_commit(self) -> Optional["Commit"]:
        """Get current commit (HEAD)."""
        try:
            git_commit = self.repo.head.peel(pygit2.Commit)
            return Commit(git_commit, self.repo)
        except (pygit2.GitError, AttributeError):
            return None

    @property
    def head(self) -> Optional["Commit"]:
        """Alias for current_commit for backward compatibility."""
        return self.current_commit

    @property
    def files(self) -> Dict[str, File]:
        """Get files from current commit."""
        if self.current_commit:
            return self.current_commit.files
        return {}

    def is_empty(self) -> bool:
        """Check if dataset has no commits."""
        return self.current_commit is None

    def get_commit(self, commit_hash: str) -> Optional["Commit"]:
        """Get a specific commit by hash (supports partial hashes)."""
        try:
            # Handle partial hashes by expanding them
            if len(commit_hash) < 40:
                # Find commits that start with this prefix
                for ref in self.repo.listall_reference_objects():
                    if hasattr(ref, 'target') and ref.target:
                        commit = self.repo.get(ref.target)
                        if commit and str(commit.id).startswith(commit_hash):
                            commit_hash = str(commit.id)
                            break

            git_commit = self.repo.get(commit_hash)
            if git_commit and git_commit.type == pygit2.GIT_OBJECT_COMMIT:
                return Commit(git_commit, self.repo)
        except (pygit2.GitError, ValueError):
            pass
        return None

    def get_info(self) -> Dict:
        """Get dataset information."""
        commit_count = len(list(self.repo.walk(self.repo.head.target))) if self.current_commit else 0
        recent_commits = []
        if self.current_commit:
            recent_commits = [{"hash": c.hash, "message": c.message} for c in self.history(limit=5)]

        return {
            "name": self.name,
            "description": self.description,
            "commit_count": commit_count,
            "current_commit": self.current_commit.hash if self.current_commit else None,
            "latest_commit": self.current_commit.hash if self.current_commit else None,
            "recent_commits": recent_commits,
        }

    def to_dict(self) -> Dict:
        """Convert dataset to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "root_dir": self.root_dir,
            "current_commit": self.current_commit.hash if self.current_commit else None,
            "commit_count": len(list(self.repo.walk(self.repo.head.target))) if self.current_commit else 0,
        }

    def cleanup_orphaned_files(self) -> int:
        """Clean up orphaned files (no-op for Git implementation)."""
        # Git handles this automatically, so this is just for compatibility
        return 0

    def __str__(self) -> str:
        """String representation of the dataset."""
        commit_count = len(list(self.repo.walk(self.repo.head.target))) if self.current_commit else 0
        return f"Dataset(name='{self.name}', commits={commit_count})"

    def __repr__(self) -> str:
        """Detailed representation of the dataset."""
        return f"Dataset(name='{self.name}', description='{self.description}', root_dir='{self.root_dir}')"

    def commit(
        self,
        message: str,
        add_files: Optional[List[Union[str, Path]]] = None,
        remove_files: Optional[List[str]] = None,
    ) -> str:
        """Create a new commit."""
        if not add_files and not remove_files:
            raise ValueError("No changes specified")

        # Start with current tree or empty tree
        if self.current_commit:
            tree_builder = self.repo.TreeBuilder(self.current_commit._git_commit.tree)
        else:
            tree_builder = self.repo.TreeBuilder()

        # Add files
        for file_path in (add_files or []):
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Validate filename to prevent Git conflicts
            filename = file_path.name
            if filename.startswith('.git'):
                raise ValueError(f"Cannot add file '{filename}': conflicts with Git metadata. Files starting with '.git' are reserved.")

            # Create blob and add to tree
            with open(file_path, "rb") as f:
                blob_id = self.repo.create_blob(f.read())
            tree_builder.insert(filename, blob_id, pygit2.GIT_FILEMODE_BLOB)

        # Remove files
        for file_name in (remove_files or []):
            try:
                # Extract just the filename from the path
                file_path = Path(file_name)
                tree_builder.remove(file_path.name)
            except KeyError:
                pass  # File not in tree, ignore

        # Create tree and commit
        tree_id = tree_builder.write()

        # Get parent commits
        parents = [self.current_commit._git_commit.id] if self.current_commit else []

        # Create commit
        signature = pygit2.Signature("Kirin", "kirin@data.versioning")
        commit_id = self.repo.create_commit(
            "HEAD",  # Update HEAD
            signature,
            signature,
            message,
            tree_id,
            parents
        )

        logger.info(f"Created commit {str(commit_id)[:8]}: {message}")
        return str(commit_id)

    def checkout(self, commit_hash: Optional[str] = None):
        """Checkout a commit."""
        if commit_hash:
            try:
                # Handle partial hashes by expanding them
                if len(commit_hash) < 40:
                    # Find commits that start with this prefix
                    for ref in self.repo.listall_reference_objects():
                        if hasattr(ref, 'target') and ref.target:
                            commit = self.repo.get(ref.target)
                            if commit and str(commit.id).startswith(commit_hash):
                                commit_hash = str(commit.id)
                                break
                    else:
                        # Try walking through commit history
                        try:
                            for commit in self.repo.walk(self.repo.head.target):
                                if str(commit.id).startswith(commit_hash):
                                    commit_hash = str(commit.id)
                                    break
                        except pygit2.GitError:
                            pass

                commit_id = pygit2.Oid(hex=commit_hash)
                # Verify commit exists
                commit = self.repo.get(commit_id)
                if not commit or commit.type != pygit2.GIT_OBJECT_COMMIT:
                    raise ValueError("Commit not found")
                self.repo.set_head(commit_id)
            except (ValueError, pygit2.GitError) as e:
                if "Commit not found" in str(e):
                    raise
                raise ValueError("Commit not found")
        # If no hash provided, already at HEAD

    def get_file(self, name: str) -> Optional[File]:
        """Get a file from current commit."""
        if not self.current_commit:
            return None
        return self.current_commit.files.get(name)

    def read_file(self, name: str, mode: str = "r") -> Union[str, bytes]:
        """Read file content.

        Args:
            name: Name of the file to read
            mode: Read mode ('r' for text, 'rb' for bytes)

        Returns:
            File content as string (mode='r') or bytes (mode='rb')
        """
        file_obj = self.get_file(name)
        if not file_obj:
            raise FileNotFoundError(f"File not found: {name}")

        if mode == "rb":
            return file_obj.read_bytes()
        elif mode == "r":
            return file_obj.read_text()
        else:
            raise ValueError(f"Unsupported mode: {mode}. Use 'r' or 'rb'")

    def list_files(self) -> List[str]:
        """List files in current commit."""
        if self.current_commit:
            return list(self.current_commit.files.keys())
        return []

    def has_file(self, name: str) -> bool:
        """Check if file exists."""
        return name in self.files

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

        Downloads all files to a temporary directory and provides a dictionary
        mapping filenames to local paths. Files are automatically cleaned up
        when exiting the context.

        Yields:
            Dictionary mapping filenames to local file paths
        """
        if self.current_commit is None:
            yield {}
            return

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"kirin_{self.name}_")
        local_files = {}

        try:
            # Download all files
            for name, file_obj in self.current_commit.files.items():
                local_path = Path(temp_dir) / name
                file_obj.download_to(local_path)
                local_files[name] = str(local_path)

            yield local_files

        finally:
            # Clean up temporary directory
            import shutil

            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary directory {temp_dir}: {e}"
                )

    def history(self, limit: Optional[int] = None) -> List["Commit"]:
        """Get commit history."""
        if not self.current_commit:
            return []

        commits = []
        for git_commit in self.repo.walk(self.current_commit._git_commit.id):
            commits.append(Commit(git_commit, self.repo))
            if limit and len(commits) >= limit:
                break
        return commits

    # Simplified branching (optional - can be added later)
    def create_branch(self, name: str):
        """Create branch."""
        if not self.current_commit:
            raise ValueError("No commits to branch from")
        ref = f"refs/heads/{name}"
        self.repo.create_reference(ref, self.current_commit._git_commit.id)

    def checkout_branch(self, name: str):
        """Checkout branch."""
        ref = f"refs/heads/{name}"
        self.repo.set_head(ref)

    def current_branch(self) -> str:
        """Get current branch name."""
        try:
            return self.repo.head.shorthand
        except pygit2.GitError:
            return "main"

    def list_branches(self) -> List[str]:
        """List all branches."""
        branches = []
        for ref_name in self.repo.references:
            if ref_name.startswith("refs/heads/"):
                branch_name = ref_name[len("refs/heads/"):]
                branches.append(branch_name)
        return sorted(branches)

    def delete_branch(self, name: str):
        """Delete a branch."""
        if name == self.current_branch():
            raise ValueError("Cannot delete the current branch")
        ref = f"refs/heads/{name}"
        self.repo.references[ref].delete()

    @contextmanager
    def file_context(self, file_name: str):
        """Context manager for temporary file access."""
        file_obj = self.get_file(file_name)
        if not file_obj:
            raise FileNotFoundError(f"File not found: {file_name}")

        with tempfile.NamedTemporaryFile(suffix=f"_{file_name}", delete=False) as tmp_file:
            tmp_file.write(file_obj.read_bytes())
            tmp_path = Path(tmp_file.name)

        try:
            yield tmp_path
        finally:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    def download_file(self, file_name: str, target_path: Union[str, Path]) -> str:
        """Download a file to local path."""
        file_obj = self.get_file(file_name)
        if not file_obj:
            raise FileNotFoundError(f"File not found: {file_name}")

        target_path = Path(target_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with open(target_path, "wb") as f:
            f.write(file_obj.read_bytes())

        logger.info(f"Downloaded '{file_name}' to {target_path}")
        return str(target_path)


class Commit:
    """Simplified commit wrapper."""

    def __init__(self, git_commit: pygit2.Commit, repo: pygit2.Repository):
        self._git_commit = git_commit
        self._repo = repo
        self._files = None

    @property
    def hash(self) -> str:
        return str(self._git_commit.id)

    @property
    def short_hash(self) -> str:
        return self.hash[:8]

    @property
    def message(self) -> str:
        return self._git_commit.message.strip()

    @property
    def timestamp(self):
        from datetime import datetime
        return datetime.fromtimestamp(self._git_commit.commit_time)

    @property
    def parent_hash(self) -> Optional[str]:
        if self._git_commit.parents:
            return str(self._git_commit.parents[0].id)
        return None

    @property
    def is_initial(self) -> bool:
        return len(self._git_commit.parents) == 0

    @property
    def files(self) -> Dict[str, File]:
        """Get files (lazy loaded)."""
        if self._files is None:
            self._files = {}
            for entry in self._git_commit.tree:
                if entry.type == pygit2.GIT_OBJECT_BLOB:
                    blob = self._repo[entry.id]
                    file_obj = File(
                        hash=str(entry.id),
                        name=entry.name,
                        size=len(blob.data),
                        content_type=self._guess_content_type(entry.name),
                        _storage=BlobStorage(self._repo),
                    )
                    self._files[entry.name] = file_obj
        return self._files

    def _guess_content_type(self, file_name: str) -> Optional[str]:
        """Guess content type from file extension."""
        import mimetypes
        content_type, _ = mimetypes.guess_type(file_name)
        return content_type

    def get_file(self, name: str) -> Optional[File]:
        return self.files.get(name)

    def list_files(self) -> List[str]:
        return list(self.files.keys())

    def has_file(self, name: str) -> bool:
        return name in self.files

    def get_file_count(self) -> int:
        return len(self.files)

    def get_total_size(self) -> int:
        return sum(file.size for file in self.files.values())

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "hash": self.hash,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "parent_hash": self.parent_hash,
            "files": {
                name: {
                    "hash": file.hash,
                    "name": file.name,
                    "size": file.size,
                    "content_type": file.content_type,
                }
                for name, file in self.files.items()
            },
        }

    def __str__(self) -> str:
        return f"GitCommit({self.short_hash}: {self.message[:50]})"

    def __repr__(self) -> str:
        return (
            f"GitCommit(hash={self.hash}, message='{self.message}', "
            f"timestamp={self.timestamp}, files={len(self.files)})"
        )


class BlobStorage:
    """Minimal storage adapter for Git blobs."""

    def __init__(self, repo: pygit2.Repository):
        self.repo = repo

    def retrieve(self, blob_hash: str) -> bytes:
        """Retrieve blob content."""
        blob_id = pygit2.Oid(hex=blob_hash)
        blob = self.repo[blob_id]
        return blob.data

    def exists(self, blob_hash: str) -> bool:
        """Check if blob exists."""
        try:
            blob_id = pygit2.Oid(hex=blob_hash)
            blob = self.repo[blob_id]
            return blob.type == pygit2.GIT_OBJECT_BLOB
        except (KeyError, ValueError):
            return False