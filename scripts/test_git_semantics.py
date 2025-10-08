# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin==0.0.1",
#     "loguru==0.7.3",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

"""
Test the Git semantics to understand what should be shown.
"""

import sys
from pathlib import Path
from loguru import logger

# Add the parent directory to the path so we can import kirin
sys.path.insert(0, str(Path(__file__).parent.parent))

from kirin.dataset import Dataset
from kirin.git_semantics import GitDAG


def test_git_semantics(dataset_path, dataset_name):
    """Test the Git semantics to understand the commit structure."""
    print(f"🔍 Testing Git semantics for: {dataset_name}")
    print(f"📁 Path: {dataset_path}")

    try:
        # Load the dataset
        dataset = Dataset(root_dir=dataset_path, dataset_name=dataset_name)

        # Create DAG
        dag = GitDAG(dataset)

        # Test each branch
        branches = dataset.list_branches()
        print(f"📊 Available branches: {branches}")

        for branch in branches:
            print(f"\n🔍 Branch: {branch}")
            print("=" * 50)

            # Get branch commit
            branch_commit = dataset.get_branch_commit(branch)
            print(f"Branch HEAD: {branch_commit[:8]}")

            # Get commits using the proper method
            commits = dag._get_branch_commits_proper(branch_commit)
            print(f"Commits in branch: {len(commits)}")

            for i, commit_hash in enumerate(commits):
                if commit_hash in dag.commits:
                    commit = dag.commits[commit_hash]
                    print(f"  {i + 1}. {commit.short_hash}: {commit.message}")
                else:
                    print(f"  {i + 1}. {commit_hash[:8]}: (not in DAG)")

        # Test the main branch specifically
        print(f"\n🔍 Main branch analysis:")
        print("=" * 50)

        main_branch = dataset.get_current_branch()
        main_commit = dataset.get_branch_commit(main_branch)
        print(f"Main branch: {main_branch}")
        print(f"Main commit: {main_commit[:8]}")

        # Get the linear history
        linear_commits = dag._get_branch_commits_proper(main_commit)
        print(f"Linear history: {len(linear_commits)} commits")

        for i, commit_hash in enumerate(linear_commits):
            if commit_hash in dag.commits:
                commit = dag.commits[commit_hash]
                print(f"  {i + 1}. {commit.short_hash}: {commit.message}")

        # Check if there are any merge commits
        print(f"\n🔍 Merge commits analysis:")
        print("=" * 50)

        merge_commits = dag.get_merge_commits()
        print(f"Merge commits: {len(merge_commits)}")

        for commit in merge_commits:
            print(
                f"  {commit.short_hash}: {commit.message} (parents: {len(commit.parents)})"
            )

    except Exception as e:
        logger.error(f"Error testing Git semantics: {e}")
        raise


def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python test_git_semantics.py <dataset_path> <dataset_name>")
        print(
            "Example: python test_git_semantics.py /tmp/gitdata-test-dataset test-dataset"
        )
        sys.exit(1)

    dataset_path = sys.argv[1]
    dataset_name = sys.argv[2]

    test_git_semantics(dataset_path, dataset_name)


if __name__ == "__main__":
    main()
