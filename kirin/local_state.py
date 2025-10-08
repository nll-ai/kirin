"""Local state management for GitData - implements distributed state like git.

This module provides local state management for HEAD and branch references,
while keeping actual files and commit data on remote storage. This follows
git's distributed model where each local copy maintains its own state.
"""

import json
import time
from pathlib import Path
from typing import Dict, Optional, Set

from loguru import logger


class LocalStateManager:
    """Manages local state for GitData datasets.

    This class handles local storage of HEAD and branch references, similar to
    how git stores state in .git/HEAD and .git/refs/heads/. The actual files
    and commit data remain on remote storage, but the state is local.
    """

    def __init__(
        self,
        dataset_name: str,
        local_state_dir: Optional[str] = None,
        remote_url: Optional[str] = None,
    ):
        """Initialize local state manager.

        Args:
            dataset_name: Name of the dataset
            local_state_dir: Directory to store local state (defaults to ~/.kirin)
            remote_url: Remote URL for this dataset (used to create unique local state)
        """
        self.dataset_name = dataset_name

        # Default to ~/.kirin/{remote_url_hash}/{dataset_name}/ for local state
        if local_state_dir is None:
            home_dir = Path.home()
            if remote_url:
                # Create unique directory based on remote URL hash
                import hashlib

                remote_url_hash = hashlib.sha256(remote_url.encode()).hexdigest()[:16]
                self.local_state_dir = (
                    home_dir / ".kirin" / remote_url_hash / dataset_name
                )
            else:
                # Fallback to old behavior for backward compatibility
                self.local_state_dir = home_dir / ".kirin" / dataset_name
        else:
            self.local_state_dir = Path(local_state_dir)

        # Ensure local state directory exists
        self.local_state_dir.mkdir(parents=True, exist_ok=True)

        # Local state files (similar to git structure)
        self.head_file = self.local_state_dir / "HEAD"
        self.refs_dir = self.local_state_dir / "refs" / "heads"
        self.config_file = self.local_state_dir / "config.json"

        # Ensure refs directory exists
        self.refs_dir.mkdir(parents=True, exist_ok=True)

        # Initialize default state if needed
        self._initialize_default_state()

        logger.info(f"Local state manager initialized for dataset: {dataset_name}")
        logger.info(f"Local state directory: {self.local_state_dir}")

    def _initialize_default_state(self):
        """Initialize default local state if it doesn't exist."""
        # Initialize HEAD if it doesn't exist
        if not self.head_file.exists():
            self.head_file.write_text("ref: refs/heads/main")
            logger.info("Initialized local HEAD to point to main branch")

        # Initialize config if it doesn't exist
        if not self.config_file.exists():
            config = {
                "dataset_name": self.dataset_name,
                "created_at": time.time(),
                "last_sync": None,
                "remote_url": None,
            }
            self.config_file.write_text(json.dumps(config, indent=2))
            logger.info("Initialized local config file")

    def get_current_branch(self) -> str:
        """Get the current branch name.

        Returns:
            Name of the current branch (defaults to 'main')
        """
        try:
            content = self.head_file.read_text().strip()
            if content.startswith("ref: refs/heads/"):
                return content.split("/")[-1]
            else:
                # Detached HEAD state - treat as main
                return "main"
        except FileNotFoundError:
            return "main"

    def set_current_branch(self, branch_name: str):
        """Set the current branch.

        Args:
            branch_name: Name of the branch to set as current
        """
        self.head_file.write_text(f"ref: refs/heads/{branch_name}")
        logger.info(f"Set current branch to: {branch_name}")

    def get_branch_commit(self, branch_name: str) -> Optional[str]:
        """Get the commit hash for a branch.

        Args:
            branch_name: Name of the branch

        Returns:
            Commit hash or None if branch doesn't exist
        """
        branch_file = self.refs_dir / branch_name
        try:
            return branch_file.read_text().strip()
        except FileNotFoundError:
            return None

    def set_branch_commit(self, branch_name: str, commit_hash: str):
        """Set the commit hash for a branch.

        Args:
            branch_name: Name of the branch
            commit_hash: Commit hash to set
        """
        branch_file = self.refs_dir / branch_name
        branch_file.write_text(commit_hash)
        logger.info(f"Set branch {branch_name} to commit {commit_hash[:8]}")

    def create_branch(self, branch_name: str, commit_hash: str) -> str:
        """Create a new branch pointing to a commit.

        Args:
            branch_name: Name of the branch to create
            commit_hash: Commit hash the branch should point to

        Returns:
            The commit hash the branch was created with

        Raises:
            ValueError: If branch already exists
        """
        if self.branch_exists(branch_name):
            raise ValueError(f"Branch '{branch_name}' already exists")

        self.set_branch_commit(branch_name, commit_hash)
        logger.info(f"Created branch '{branch_name}' pointing to {commit_hash[:8]}")
        return commit_hash

    def delete_branch(self, branch_name: str):
        """Delete a branch.

        Args:
            branch_name: Name of the branch to delete

        Raises:
            ValueError: If branch doesn't exist or is current branch
        """
        if not self.branch_exists(branch_name):
            raise ValueError(f"Branch '{branch_name}' does not exist")

        if self.get_current_branch() == branch_name:
            raise ValueError(f"Cannot delete current branch '{branch_name}'")

        branch_file = self.refs_dir / branch_name
        branch_file.unlink()
        logger.info(f"Deleted branch '{branch_name}'")

    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists.

        Args:
            branch_name: Name of the branch

        Returns:
            True if branch exists, False otherwise
        """
        branch_file = self.refs_dir / branch_name
        return branch_file.exists()

    def list_branches(self) -> Set[str]:
        """List all branch names.

        Returns:
            Set of branch names
        """
        try:
            return {f.name for f in self.refs_dir.iterdir() if f.is_file()}
        except FileNotFoundError:
            return set()

    def get_current_commit(self) -> Optional[str]:
        """Get the current commit hash.

        Returns:
            Current commit hash or None if no current commit
        """
        current_branch = self.get_current_branch()
        return self.get_branch_commit(current_branch)

    def set_current_commit(self, commit_hash: str):
        """Set the current commit (detached HEAD state).

        Args:
            commit_hash: Commit hash to set as current
        """
        self.head_file.write_text(commit_hash)
        logger.info(f"Set current commit to {commit_hash[:8]} (detached HEAD)")

    def get_config(self) -> Dict:
        """Get local configuration.

        Returns:
            Configuration dictionary
        """
        try:
            return json.loads(self.config_file.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def set_config(self, config: Dict):
        """Set local configuration.

        Args:
            config: Configuration dictionary
        """
        self.config_file.write_text(json.dumps(config, indent=2))
        logger.info("Updated local configuration")

    def set_remote_url(self, remote_url: str):
        """Set the remote URL for this dataset.

        Args:
            remote_url: URL of the remote dataset
        """
        config = self.get_config()
        config["remote_url"] = remote_url
        config["last_sync"] = time.time()
        self.set_config(config)
        logger.info(f"Set remote URL to: {remote_url}")

    def get_remote_url(self) -> Optional[str]:
        """Get the remote URL for this dataset.

        Returns:
            Remote URL or None if not set
        """
        config = self.get_config()
        return config.get("remote_url")

    def sync_with_remote(self, remote_state_manager):
        """Sync local state with remote state.

        This is an optional operation that can be used to sync local state
        with a remote repository, similar to git fetch/pull.

        Args:
            remote_state_manager: Remote state manager to sync with
        """
        logger.info("Syncing local state with remote...")

        # Get remote branches
        remote_branches = remote_state_manager.list_branches()

        # Update local branches with remote data
        for branch_name in remote_branches:
            remote_commit = remote_state_manager.get_branch_commit(branch_name)
            if remote_commit:
                self.set_branch_commit(branch_name, remote_commit)
                logger.info(f"Synced branch '{branch_name}' to {remote_commit[:8]}")

        # Update config with sync timestamp
        config = self.get_config()
        config["last_sync"] = time.time()
        self.set_config(config)

        logger.info("Local state sync completed")

    def push_to_remote(self, remote_state_manager):
        """Push local state to remote.

        This pushes local branch state to the remote, similar to git push.

        Args:
            remote_state_manager: Remote state manager to push to
        """
        logger.info("Pushing local state to remote...")

        for branch_name in self.list_branches():
            local_commit = self.get_branch_commit(branch_name)
            if local_commit:
                remote_state_manager.set_branch_commit(branch_name, local_commit)
                logger.info(f"Pushed branch '{branch_name}' to remote")

        # Push HEAD state
        current_branch = self.get_current_branch()
        remote_state_manager.set_current_branch(current_branch)

        logger.info("Local state push completed")

    def get_state_summary(self) -> Dict:
        """Get a summary of the current local state.

        Returns:
            Dictionary with state summary
        """
        return {
            "dataset_name": self.dataset_name,
            "current_branch": self.get_current_branch(),
            "current_commit": self.get_current_commit(),
            "branches": {
                branch: self.get_branch_commit(branch)
                for branch in self.list_branches()
            },
            "remote_url": self.get_remote_url(),
            "last_sync": self.get_config().get("last_sync"),
        }
