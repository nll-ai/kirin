"""Git semantics implementation for Kirin.

This module provides proper Git DAG (Directed Acyclic Graph) handling
with configurable merge strategies, defaulting to rebase merges.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger


class MergeStrategy(Enum):
    """Available merge strategies."""

    REBASE = "rebase"  # Default: rebase incoming branch onto target
    MERGE = "merge"  # Create merge commit
    SQUASH = "squash"  # Squash all commits into one


@dataclass
class CommitNode:
    """Represents a commit in the DAG."""

    hash: str
    short_hash: str
    message: str
    file_count: int
    parents: List[str]
    children: List[str]
    branch: Optional[str] = None
    is_merge: bool = False
    is_rebase: bool = False
    timestamp: Optional[str] = None


@dataclass
class BranchInfo:
    """Information about a branch."""

    name: str
    head_commit: str
    commits: List[str]  # Commits in this branch
    is_main: bool = False


class GitDAG:
    """Manages the Git DAG structure with proper branch semantics."""

    def __init__(self, dataset, merge_strategy: MergeStrategy = MergeStrategy.REBASE):
        self.dataset = dataset
        self.merge_strategy = merge_strategy
        self.commits: Dict[str, CommitNode] = {}
        self.branches: Dict[str, BranchInfo] = {}
        self._build_dag()

    def _build_dag(self):
        """Build the complete DAG structure from all commits."""
        logger.info("Building Git DAG structure")

        # Get all commits data
        commits_data = self.dataset._get_commits_data()

        # Create commit nodes
        for commit_hash, commit_data in commits_data.items():
            parent_hash = commit_data.get("parent_hash", "")
            parent_hashes = commit_data.get("parent_hashes", [])

            # Combine single parent and multiple parents
            all_parents = (
                parent_hashes
                if parent_hashes
                else ([parent_hash] if parent_hash else [])
            )

            self.commits[commit_hash] = CommitNode(
                hash=commit_hash,
                short_hash=commit_hash[:8],
                message=commit_data.get("commit_message", ""),
                file_count=len(commit_data.get("file_hashes", [])),
                parents=all_parents,
                children=[],  # Will be populated below
                is_merge=len(parent_hashes) > 1,
                is_rebase=False,  # Will be determined by branch analysis
            )

        # Build parent-child relationships
        for commit_hash, commit_node in self.commits.items():
            for parent_hash in commit_node.parents:
                if parent_hash in self.commits:
                    self.commits[parent_hash].children.append(commit_hash)

        # Build branch information
        self._build_branch_info()

        logger.info(
            f"Built DAG with {len(self.commits)} commits and {len(self.branches)} branches"
        )

    def _build_branch_info(self):
        """Build branch information from the dataset."""
        all_branches = self.dataset.list_branches()
        main_branch = self.dataset.get_current_branch()

        for branch_name in all_branches:
            try:
                head_commit = self.dataset.get_branch_commit(branch_name)
                commits = self._get_branch_commits_smart(head_commit, branch_name)

                self.branches[branch_name] = BranchInfo(
                    name=branch_name,
                    head_commit=head_commit,
                    commits=commits,
                    is_main=(branch_name == main_branch),
                )

                # Note: We don't assign commits to branches like Git doesn't
                # Commits just exist in the DAG, and branch history is determined
                # by traversing from the branch HEAD backwards

            except Exception as e:
                logger.warning(f"Could not build branch info for {branch_name}: {e}")

    def _get_branch_commits(self, head_commit: str) -> List[str]:
        """Get all commits in a branch, following the proper Git branch history.

        This follows the linear history from the branch head to the root,
        which is the correct Git semantics for branch history.
        """
        commits = []
        visited = set()  # Prevent duplicate commits
        current = head_commit

        # Follow the linear history by following the first parent
        # This is the correct Git semantics for branch history
        while current and current in self.commits and current not in visited:
            visited.add(current)
            commits.append(current)

            # Get the commit node
            commit_node = self.commits[current]

            # Follow the first parent (main branch) for linear history
            if commit_node.parents:
                current = commit_node.parents[0]  # First parent is the main branch
            else:
                break  # No more parents

        return commits

    def _get_branch_commits_proper(self, head_commit: str) -> List[str]:
        """Get commits for a branch using proper Git reachability semantics.

        This method only returns commits that are directly reachable from the branch HEAD,
        following the first parent chain (which is the correct Git semantics for branch history).
        """
        commits = []
        current = head_commit

        # Follow the first parent chain only (this is what Git does for branch history)
        while current and current in self.commits:
            commits.append(current)

            # Get the commit node
            commit_node = self.commits[current]

            # Only follow the first parent (main branch) for linear history
            # This prevents traversing into merged branches
            if commit_node.parents:
                current = commit_node.parents[0]  # First parent only
            else:
                break  # No more parents

        return commits

    def _get_branch_commits_smart(
        self, head_commit: str, branch_name: str
    ) -> List[str]:
        """Get commits for a branch using proper Git semantics.

        This method follows the first parent chain from the branch HEAD,
        which is the correct Git semantics for branch history.
        """
        commits = []
        current = head_commit
        visited = set()

        # Follow the first parent chain (this is what Git does for branch history)
        while current and current in self.commits and current not in visited:
            visited.add(current)
            commits.append(current)

            # Get the commit node
            commit_node = self.commits[current]

            # Only follow the first parent (main branch) for linear history
            # This prevents traversing into merged branches
            if commit_node.parents:
                current = commit_node.parents[0]  # First parent only
            else:
                break  # No more parents

        return commits

    def get_branch_history(self, branch_name: str) -> List[CommitNode]:
        """Get the commit history for a specific branch."""
        if branch_name not in self.branches:
            return []

        branch_info = self.branches[branch_name]
        history = []

        # Get commits in chronological order (newest first)
        # The commits are already in the correct order from _get_branch_commits
        for commit_hash in branch_info.commits:
            if commit_hash in self.commits:
                history.append(self.commits[commit_hash])

        # No need to sort - commits are already in newest-first order
        return history

    def get_merge_commits(self) -> List[CommitNode]:
        """Get all merge commits in the DAG."""
        return [commit for commit in self.commits.values() if commit.is_merge]

    def get_rebase_commits(self) -> List[CommitNode]:
        """Get all rebase commits in the DAG."""
        return [commit for commit in self.commits.values() if commit.is_rebase]

    def get_commit_ancestors(self, commit_hash: str) -> Set[str]:
        """Get all ancestors of a commit."""
        ancestors = set()
        visited = set()

        def traverse(current_hash: str):
            if current_hash in visited or current_hash not in self.commits:
                return

            visited.add(current_hash)

            for parent_hash in self.commits[current_hash].parents:
                ancestors.add(parent_hash)
                traverse(parent_hash)

        traverse(commit_hash)
        return ancestors

    def get_commit_descendants(self, commit_hash: str) -> Set[str]:
        """Get all descendants of a commit."""
        descendants = set()
        visited = set()

        def traverse(current_hash: str):
            if current_hash in visited or current_hash not in self.commits:
                return

            visited.add(current_hash)

            for child_hash in self.commits[current_hash].children:
                descendants.add(child_hash)
                traverse(child_hash)

        traverse(commit_hash)
        return descendants

    def find_merge_base(self, commit1: str, commit2: str) -> Optional[str]:
        """Find the merge base (common ancestor) of two commits."""
        ancestors1 = self.get_commit_ancestors(commit1)
        ancestors2 = self.get_commit_ancestors(commit2)

        common_ancestors = ancestors1.intersection(ancestors2)

        if not common_ancestors:
            return None

        # Find the most recent common ancestor
        # (This is a simplified implementation)
        for commit_hash in common_ancestors:
            if commit_hash in self.commits:
                return commit_hash

        return None

    def get_branch_divergence(
        self, branch1: str, branch2: str
    ) -> Tuple[List[str], List[str]]:
        """Get commits that are in branch1 but not in branch2, and vice versa."""
        if branch1 not in self.branches or branch2 not in self.branches:
            return [], []

        commits1 = set(self.branches[branch1].commits)
        commits2 = set(self.branches[branch2].commits)

        only_in_branch1 = list(commits1 - commits2)
        only_in_branch2 = list(commits2 - commits1)

        return only_in_branch1, only_in_branch2

    def visualize_dag(self) -> str:
        """Create a text visualization of the DAG structure."""
        lines = []
        lines.append("Git DAG Structure:")
        lines.append("=" * 50)

        for branch_name, branch_info in self.branches.items():
            lines.append(
                f"\nBranch: {branch_name} {'(main)' if branch_info.is_main else ''}"
            )
            lines.append("-" * 30)

            history = self.get_branch_history(branch_name)
            for commit in history[:10]:  # Show first 10 commits
                merge_indicator = " (merge)" if commit.is_merge else ""
                rebase_indicator = " (rebase)" if commit.is_rebase else ""
                lines.append(
                    f"  {commit.short_hash}: {commit.message}{merge_indicator}{rebase_indicator}"
                )

        return "\n".join(lines)


def get_branch_aware_commits(dataset, branch_name: Optional[str] = None) -> List[Dict]:
    """Get commits for a specific branch, preserving Git semantics.

    Args:
        dataset: The dataset to get commits from
        branch_name: Specific branch to get commits for. If None, uses current branch.

    Returns:
        List of commit dictionaries with proper Git semantics
    """
    if branch_name is None:
        branch_name = dataset.get_current_branch()

    # Create DAG instance
    dag = GitDAG(dataset)

    # Get branch history starting from the branch's latest commit
    # This shows the proper branch history, not the checked-out commit history
    history = dag.get_branch_history(branch_name)

    # Convert to the format expected by the web UI
    commits = []
    for commit in history:
        commits.append(
            {
                "hash": commit.hash,
                "short_hash": commit.short_hash,
                "message": commit.message,
                "file_count": commit.file_count,
                "parent_hash": commit.parents[0] if commit.parents else "",
                "parent_hashes": commit.parents,
                "is_merge": commit.is_merge,
                "is_rebase": commit.is_rebase,
                "branch": commit.branch,
            }
        )

    return commits


def get_all_branches_commits(dataset) -> Dict[str, List[Dict]]:
    """Get commits for all branches, preserving Git semantics.

    Returns:
        Dictionary mapping branch names to their commit lists
    """
    dag = GitDAG(dataset)
    result = {}

    for branch_name in dataset.list_branches():
        result[branch_name] = get_branch_aware_commits(dataset, branch_name)

    return result


def analyze_merge_strategy(dataset, source_branch: str, target_branch: str) -> Dict:
    """Analyze what merge strategy would be used for merging branches.

    Returns:
        Dictionary with merge analysis information
    """
    dag = GitDAG(dataset)

    if source_branch not in dag.branches or target_branch not in dag.branches:
        return {"error": "Branch not found"}

    # Get divergence information
    only_in_source, only_in_target = dag.get_branch_divergence(
        source_branch, target_branch
    )

    # Find merge base
    source_head = dag.branches[source_branch].head_commit
    target_head = dag.branches[target_branch].head_commit
    merge_base = dag.find_merge_base(source_head, target_head)

    return {
        "source_branch": source_branch,
        "target_branch": target_branch,
        "source_commits": len(only_in_source),
        "target_commits": len(only_in_target),
        "merge_base": merge_base[:8] if merge_base else None,
        "recommended_strategy": "rebase",  # Default to rebase
        "conflicts_possible": len(only_in_source) > 0 and len(only_in_target) > 0,
    }
