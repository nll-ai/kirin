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
Diagnostic script to checkout branches and visualize commit history.

This script helps diagnose why the Kirin UI shows duplicate initial commits
by using the dataset API directly to checkout branches and visualize the history.
"""

import sys
from pathlib import Path

from loguru import logger

# Add the parent directory to the path so we can import kirin
sys.path.insert(0, str(Path(__file__).parent.parent))

from kirin.dataset import Dataset
from kirin.git_semantics import GitDAG, get_branch_aware_commits


def print_commit_info(commits, title):
    """Print commit information in a readable format."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"Total commits: {len(commits)}")

    for i, commit in enumerate(commits):
        merge_indicator = " (merge)" if commit.get("is_merge", False) else ""
        rebase_indicator = " (rebase)" if commit.get("is_rebase", False) else ""
        branch_info = (
            f" [{commit.get('branch', 'unknown')}]" if commit.get("branch") else ""
        )

        print(
            f"{i + 1:2d}. {commit['short_hash']}{branch_info}: {commit['message']}{merge_indicator}{rebase_indicator}"
        )
        print(f"     Hash: {commit['hash']}")
        print(
            f"     Parent: {commit.get('parent_hash', 'None')[:8] if commit.get('parent_hash') else 'None'}"
        )
        print(
            f"     Parents: {[p[:8] for p in commit.get('parent_hashes', [])] if commit.get('parent_hashes') else 'None'}"
        )
        print(f"     Files: {commit.get('file_count', 0)}")
        print()


def generate_mermaid_diagram(commits, title):
    """Generate a Mermaid diagram of the commit history."""
    print(f"\n{'=' * 60}")
    print(f"Mermaid Diagram: {title}")
    print(f"{'=' * 60}")

    if not commits:
        print("No commits to visualize")
        return

    # Generate Mermaid diagram
    lines = ["graph TD"]

    # Create nodes for each commit
    for commit in commits:
        node_id = f"commit_{commit['short_hash']}"
        node_label = f"{commit['short_hash']}\\n{commit['message'][:30]}{'...' if len(commit['message']) > 30 else ''}"

        # Style merge commits differently
        if commit.get("is_merge", False):
            lines.append(f'{node_id}["{node_label}"]:::merge')
        else:
            lines.append(f'{node_id}["{node_label}"]')

    # Add connections between commits
    for commit in commits:
        if commit.get("parent_hash"):
            parent_commit = next(
                (c for c in commits if c["hash"] == commit["parent_hash"]), None
            )
            if parent_commit:
                node_id = f"commit_{commit['short_hash']}"
                parent_node_id = f"commit_{parent_commit['short_hash']}"
                lines.append(f"{node_id} --> {parent_node_id}")

    # Add styling
    lines.append("classDef merge fill:#ff9999,stroke:#ff0000,color:#000000")

    mermaid_code = "\n".join(lines)
    print(mermaid_code)
    print()


def diagnose_dataset(dataset_path, dataset_name):
    """Diagnose a dataset's commit history."""
    print(f"🔍 Diagnosing dataset: {dataset_name}")
    print(f"📁 Path: {dataset_path}")

    try:
        # Load the dataset
        dataset = Dataset(root_dir=dataset_path, dataset_name=dataset_name)

        # Get basic info
        current_branch = dataset.get_current_branch()
        current_commit = dataset.current_version_hash()
        branch_commit = dataset.get_branch_commit(current_branch)

        print(f"📊 Current branch: {current_branch}")
        print(f"📊 Current commit: {current_commit[:8]}")
        print(f"📊 Branch commit: {branch_commit[:8]}")
        print(f"📊 Are they the same? {current_commit == branch_commit}")

        # Get all branches
        branches = dataset.list_branches()
        print(f"📊 Available branches: {branches}")

        # Get commits using different methods
        print("\n🔍 Method 1: Using dataset.get_commits()")
        dataset_commits = dataset.get_commits()
        print_commit_info(dataset_commits, "Dataset.get_commits()")

        print("\n🔍 Method 2: Using get_branch_aware_commits()")
        branch_commits = get_branch_aware_commits(dataset, current_branch)
        print_commit_info(branch_commits, "get_branch_aware_commits()")

        # Generate Mermaid diagrams
        generate_mermaid_diagram(dataset_commits, "Dataset.get_commits()")
        generate_mermaid_diagram(branch_commits, "get_branch_aware_commits()")

        # Test checking out different commits
        print("\n🔍 Testing checkout functionality")
        if len(dataset_commits) > 1:
            # Try checking out the second commit
            second_commit = dataset_commits[1]
            print(f"Checking out commit: {second_commit['short_hash']}")
            dataset.checkout(second_commit["hash"])

            # Get commits after checkout
            after_checkout_commits = dataset.get_commits()
            print_commit_info(after_checkout_commits, "After checkout")
            generate_mermaid_diagram(after_checkout_commits, "After checkout")

            # Checkout back to branch
            print(f"Checking out back to branch: {current_branch}")
            dataset.checkout(branch_commit)

        # Test with GitDAG visualization
        print("\n🔍 GitDAG visualization")
        dag = GitDAG(dataset)
        dag_visualization = dag.visualize_dag()
        print("GitDAG visualization:")
        print(dag_visualization)

    except Exception as e:
        logger.error(f"Error diagnosing dataset: {e}")
        raise


def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python diagnose_commit_history.py <dataset_path> <dataset_name>")
        print(
            "Example: python diagnose_commit_history.py /tmp/kirin-test-dataset test-dataset"
        )
        sys.exit(1)

    dataset_path = sys.argv[1]
    dataset_name = sys.argv[2]

    diagnose_dataset(dataset_path, dataset_name)


if __name__ == "__main__":
    main()
