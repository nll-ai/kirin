"""Custom model code for gitdata."""

import fsspec
from typing import Optional

from loguru import logger

from .local_state import LocalStateManager
from .utils import strip_protocol


class BranchManager:
    """Manages branches for a dataset using distributed local state.

    This class now uses local state management (like git's .git/HEAD and
    .git/refs/heads/) while keeping actual files and commit data on remote
    storage. This follows git's distributed model where each local copy
    maintains its own state.
    """

    def __init__(
        self,
        dataset_dir: str,
        fs: fsspec.AbstractFileSystem,
        dataset_name: str,
        local_state_dir: Optional[str] = None,
        remote_url: Optional[str] = None,
    ):
        self.dataset_dir = dataset_dir
        self.fs = fs
        self.dataset_name = dataset_name

        # Initialize local state manager with remote URL for unique state directories
        self.local_state = LocalStateManager(dataset_name, local_state_dir, remote_url)

        # Remote paths for reference (but we don't store state there anymore)
        self.remote_refs_dir = f"{dataset_dir}/refs/heads"
        self.remote_head_file = f"{dataset_dir}/HEAD"

        # Ensure remote refs directory exists (for backward compatibility)
        self.fs.makedirs(strip_protocol(self.remote_refs_dir), exist_ok=True)

        # Sync local state with remote state if remote has branches
        self._sync_with_remote_if_needed()

    def _sync_with_remote_if_needed(self):
        """Sync local state with remote state if remote has branches but local doesn't."""
        try:
            # Check if remote has branches
            remote_branches = self._get_remote_branches()
            local_branches = self.local_state.list_branches()

            # If remote has branches but local doesn't, sync from remote
            if remote_branches and not local_branches:
                logger.info(
                    f"Syncing local state with remote branches: {remote_branches}"
                )
                self._sync_from_remote(remote_branches)
        except Exception as e:
            logger.warning(f"Failed to sync with remote state: {e}")

    def _get_remote_branches(self) -> list[str]:
        """Get branches from remote storage."""
        try:
            files = self.fs.glob(f"{strip_protocol(self.remote_refs_dir)}/*")
            return [f.split("/")[-1] for f in files if not f.endswith("/")]
        except Exception:
            return []

    def _get_remote_branch_commit(self, branch_name: str) -> Optional[str]:
        """Get commit hash for a branch from remote storage."""
        try:
            branch_file = f"{self.remote_refs_dir}/{branch_name}"
            with self.fs.open(strip_protocol(branch_file), "r") as f:
                return f.read().strip()
        except Exception:
            return None

    def _get_remote_head(self) -> Optional[str]:
        """Get HEAD from remote storage."""
        try:
            with self.fs.open(strip_protocol(self.remote_head_file), "r") as f:
                content = f.read().strip()
                if content.startswith("ref: refs/heads/"):
                    return content.split("/")[-1]
                return None
        except Exception:
            return None

    def _sync_from_remote(self, remote_branches: list[str]):
        """Sync local state from remote branches."""
        for branch_name in remote_branches:
            commit_hash = self._get_remote_branch_commit(branch_name)
            if commit_hash:
                self.local_state.set_branch_commit(branch_name, commit_hash)
                logger.info(f"Synced branch '{branch_name}' to {commit_hash[:8]}")

        # Set current branch from remote HEAD
        remote_head = self._get_remote_head()
        if remote_head and remote_head in remote_branches:
            self.local_state.set_current_branch(remote_head)
            logger.info(f"Set current branch to '{remote_head}' from remote")

    def create_branch(self, name: str, commit_hash: str) -> str:
        """Create a new branch pointing to the specified commit.

        Args:
            name: Name of the branch to create
            commit_hash: Commit hash the branch should point to

        Returns:
            The commit hash the branch was created with

        Raises:
            ValueError: If branch already exists or name is invalid
        """
        return self.local_state.create_branch(name, commit_hash)

    def get_branch_commit(self, name: str) -> str:
        """Get the commit hash that a branch points to.

        Args:
            name: Name of the branch

        Returns:
            The commit hash the branch points to

        Raises:
            ValueError: If branch doesn't exist
        """
        commit_hash = self.local_state.get_branch_commit(name)
        if commit_hash is None:
            raise ValueError(f"Branch '{name}' does not exist")
        return commit_hash

    def update_branch(self, name: str, commit_hash: str):
        """Update a branch to point to a new commit.

        Args:
            name: Name of the branch to update
            commit_hash: New commit hash to point to

        Raises:
            ValueError: If branch doesn't exist
        """
        if not self.local_state.branch_exists(name):
            raise ValueError(f"Branch '{name}' does not exist")
        self.local_state.set_branch_commit(name, commit_hash)

    def delete_branch(self, name: str):
        """Delete a branch.

        Args:
            name: Name of the branch to delete

        Raises:
            ValueError: If trying to delete main branch or branch doesn't exist
        """
        if name == "main":
            raise ValueError("Cannot delete the main branch")

        self.local_state.delete_branch(name)

    def list_branches(self) -> list[str]:
        """List all branch names.

        Returns:
            List of branch names
        """
        return list(self.local_state.list_branches())

    def get_current_branch(self) -> str:
        """Get the name of the current branch.

        Returns:
            Name of the current branch (defaults to 'main' if HEAD doesn't exist)
        """
        return self.local_state.get_current_branch()

    def set_current_branch(self, name: str):
        """Set the current branch.

        Args:
            name: Name of the branch to set as current

        Raises:
            ValueError: If branch doesn't exist
        """
        if not self.local_state.branch_exists(name):
            raise ValueError(f"Branch '{name}' does not exist")
        self.local_state.set_current_branch(name)

    def get_current_commit(self) -> str:
        """Get the commit hash of the current branch.

        Returns:
            Commit hash of the current branch
        """
        commit_hash = self.local_state.get_current_commit()
        if commit_hash is None:
            raise ValueError("No current commit found")
        return commit_hash

    def update_current_branch(self, commit_hash: str):
        """Update the current branch to point to a new commit.

        Args:
            commit_hash: New commit hash to point to
        """
        current_branch = self.get_current_branch()
        self.update_branch(current_branch, commit_hash)
