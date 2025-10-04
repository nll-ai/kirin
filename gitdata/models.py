"""Custom model code for gitdata."""

import fsspec

from .utils import strip_protocol


class BranchManager:
    """Manages branches for a dataset using Git's approach.

    Branches are stored as individual files in refs/heads/ directory,
    each containing a commit hash. The current branch is stored in HEAD file.
    This mirrors Git's internal structure exactly.
    """

    def __init__(self, dataset_dir: str, fs: fsspec.AbstractFileSystem):
        self.dataset_dir = dataset_dir
        self.fs = fs
        self.refs_dir = f"{dataset_dir}/refs/heads"
        self.head_file = f"{dataset_dir}/HEAD"

        # Ensure refs directory exists
        self.fs.makedirs(strip_protocol(self.refs_dir), exist_ok=True)

    def _get_branch_file(self, branch_name: str) -> str:
        """Get the file path for a branch reference."""
        return f"{self.refs_dir}/{branch_name}"

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
        branch_file = self._get_branch_file(name)

        if name == "main" and self.fs.exists(strip_protocol(branch_file)):
            raise ValueError(
                "Cannot create a branch named 'main' - it's the default branch"
            )

        # Check if branch already exists
        if self.fs.exists(strip_protocol(branch_file)):
            raise ValueError(f"Branch '{name}' already exists")

        # Create the branch file with the commit hash
        with self.fs.open(strip_protocol(branch_file), "w") as f:
            f.write(commit_hash)

        return commit_hash

    def get_branch_commit(self, name: str) -> str:
        """Get the commit hash that a branch points to.

        Args:
            name: Name of the branch

        Returns:
            The commit hash the branch points to

        Raises:
            ValueError: If branch doesn't exist
        """
        branch_file = self._get_branch_file(name)

        if not self.fs.exists(strip_protocol(branch_file)):
            raise ValueError(f"Branch '{name}' does not exist")

        with self.fs.open(strip_protocol(branch_file), "r") as f:
            return f.read().strip()

    def update_branch(self, name: str, commit_hash: str):
        """Update a branch to point to a new commit.

        Args:
            name: Name of the branch to update
            commit_hash: New commit hash to point to

        Raises:
            ValueError: If branch doesn't exist
        """
        branch_file = self._get_branch_file(name)

        if not self.fs.exists(strip_protocol(branch_file)):
            raise ValueError(f"Branch '{name}' does not exist")

        with self.fs.open(strip_protocol(branch_file), "w") as f:
            f.write(commit_hash)

    def delete_branch(self, name: str):
        """Delete a branch.

        Args:
            name: Name of the branch to delete

        Raises:
            ValueError: If trying to delete main branch or branch doesn't exist
        """
        if name == "main":
            raise ValueError("Cannot delete the main branch")

        branch_file = self._get_branch_file(name)

        if not self.fs.exists(strip_protocol(branch_file)):
            raise ValueError(f"Branch '{name}' does not exist")

        self.fs.rm(strip_protocol(branch_file))

    def list_branches(self) -> list[str]:
        """List all branch names.

        Returns:
            List of branch names
        """
        try:
            # List all files in the refs/heads directory
            files = self.fs.glob(f"{strip_protocol(self.refs_dir)}/*")
            return [f.split("/")[-1] for f in files if not f.endswith("/")]
        except Exception:
            return []

    def get_current_branch(self) -> str:
        """Get the name of the current branch.

        Returns:
            Name of the current branch (defaults to 'main' if HEAD doesn't exist)
        """
        try:
            with self.fs.open(strip_protocol(self.head_file), "r") as f:
                content = f.read().strip()
                # Handle both "ref: refs/heads/branch_name" and direct commit hashes
                if content.startswith("ref: refs/heads/"):
                    return content.split("/")[-1]
                else:
                    # If HEAD contains a commit hash directly, we're in detached HEAD
                    # state. For now, we'll treat this as main branch
                    return "main"
        except FileNotFoundError:
            # Default to main branch if HEAD doesn't exist
            return "main"

    def set_current_branch(self, name: str):
        """Set the current branch.

        Args:
            name: Name of the branch to set as current

        Raises:
            ValueError: If branch doesn't exist
        """
        # Verify the branch exists
        branch_file = self._get_branch_file(name)
        if not self.fs.exists(strip_protocol(branch_file)):
            raise ValueError(f"Branch '{name}' does not exist")

        # Update HEAD to point to the branch
        with self.fs.open(strip_protocol(self.head_file), "w") as f:
            f.write(f"ref: refs/heads/{name}")

    def get_current_commit(self) -> str:
        """Get the commit hash of the current branch.

        Returns:
            Commit hash of the current branch
        """
        current_branch = self.get_current_branch()
        return self.get_branch_commit(current_branch)

    def update_current_branch(self, commit_hash: str):
        """Update the current branch to point to a new commit.

        Args:
            commit_hash: New commit hash to point to
        """
        current_branch = self.get_current_branch()
        self.update_branch(current_branch, commit_hash)
