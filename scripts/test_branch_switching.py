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
Test branch switching and commit history correctness.
"""

import sys
from pathlib import Path
from loguru import logger

# Add the parent directory to the path so we can import kirin
sys.path.insert(0, str(Path(__file__).parent.parent))

from kirin.dataset import Dataset
from kirin.git_semantics import get_branch_aware_commits


def test_branch_switching(dataset_path, dataset_name):
    """Test branch switching and verify commit history for each branch."""
    print(f"🔍 Testing branch switching for: {dataset_name}")
    print(f"📁 Path: {dataset_path}")

    try:
        # Load the dataset
        dataset = Dataset(root_dir=dataset_path, dataset_name=dataset_name)

        # Get all branches
        branches = dataset.list_branches()
        print(f"📊 Available branches: {branches}")

        # Test each branch
        for branch in branches:
            print(f"\n{'=' * 60}")
            print(f"🔍 Testing branch: {branch}")
            print(f"{'=' * 60}")

            # Switch to the branch
            print(f"Switching to branch: {branch}")
            dataset.switch_branch(branch)

            # Verify we're on the correct branch
            current_branch = dataset.get_current_branch()
            current_commit = dataset.current_version_hash()
            branch_commit = dataset.get_branch_commit(branch)

            print(f"✅ Current branch: {current_branch}")
            print(f"✅ Current commit: {current_commit[:8]}")
            print(f"✅ Branch commit: {branch_commit[:8]}")
            print(f"✅ Branch matches: {current_branch == branch}")
            print(f"✅ Commit matches: {current_commit == branch_commit}")

            # Get commits using both methods
            print(f"\n📋 Getting commits for branch: {branch}")

            # Method 1: Dataset.get_commits()
            dataset_commits = dataset.get_commits()
            print(f"📊 Dataset.get_commits(): {len(dataset_commits)} commits")

            # Method 2: get_branch_aware_commits()
            branch_commits = get_branch_aware_commits(dataset, branch)
            print(f"📊 get_branch_aware_commits(): {len(branch_commits)} commits")

            # Verify both methods return the same number of commits
            if len(dataset_commits) != len(branch_commits):
                print(f"⚠️  WARNING: Different commit counts!")
                print(f"   Dataset method: {len(dataset_commits)}")
                print(f"   Branch-aware method: {len(branch_commits)}")
            else:
                print(f"✅ Both methods return {len(dataset_commits)} commits")

            # Display commit history
            print(f"\n📋 Commit History for {branch}:")
            print("-" * 50)

            for i, commit in enumerate(branch_commits):
                merge_indicator = " (merge)" if commit.get("is_merge", False) else ""
                rebase_indicator = " (rebase)" if commit.get("is_rebase", False) else ""
                branch_info = (
                    f" [{commit.get('branch', 'unknown')}]"
                    if commit.get("branch")
                    else ""
                )

                print(
                    f"{i + 1:2d}. {commit['short_hash']}{branch_info}: {commit['message']}{merge_indicator}{rebase_indicator}"
                )
                print(f"     Hash: {commit['hash']}")
                print(
                    f"     Parent: {commit.get('parent_hash', 'None')[:8] if commit.get('parent_hash') else 'None'}"
                )
                print(f"     Files: {commit.get('file_count', 0)}")
                print()

            # Verify commit order (newest first)
            print(f"🔍 Verifying commit order for {branch}:")
            for i in range(len(branch_commits) - 1):
                current_commit = branch_commits[i]
                next_commit = branch_commits[i + 1]

                # Check if current commit's parent is the next commit
                if current_commit.get("parent_hash") == next_commit["hash"]:
                    print(
                        f"  ✅ {current_commit['short_hash']} → {next_commit['short_hash']} (correct order)"
                    )
                else:
                    print(
                        f"  ⚠️  {current_commit['short_hash']} → {next_commit['short_hash']} (parent: {current_commit.get('parent_hash', 'None')[:8]})"
                    )

            # Check for duplicate commits
            commit_hashes = [commit["hash"] for commit in branch_commits]
            unique_hashes = set(commit_hashes)

            if len(commit_hashes) != len(unique_hashes):
                print(f"❌ DUPLICATE COMMITS FOUND!")
                duplicates = []
                seen = set()
                for hash_val in commit_hashes:
                    if hash_val in seen:
                        duplicates.append(hash_val)
                    else:
                        seen.add(hash_val)
                print(f"   Duplicate hashes: {[h[:8] for h in duplicates]}")
            else:
                print(f"✅ No duplicate commits found")

            # Check for duplicate messages
            messages = [commit["message"] for commit in branch_commits]
            message_counts = {}
            for message in messages:
                message_counts[message] = message_counts.get(message, 0) + 1

            duplicate_messages = {
                msg: count for msg, count in message_counts.items() if count > 1
            }
            if duplicate_messages:
                print(f"⚠️  Duplicate messages found:")
                for msg, count in duplicate_messages.items():
                    print(f"   '{msg}': {count} times")
            else:
                print(f"✅ No duplicate messages found")

        print(f"\n{'=' * 60}")
        print("🎉 Branch switching test completed!")
        print(f"{'=' * 60}")

    except Exception as e:
        logger.error(f"Error testing branch switching: {e}")
        raise


def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python test_branch_switching.py <dataset_path> <dataset_name>")
        print(
            "Example: python test_branch_switching.py /tmp/gitdata-test-dataset test-dataset"
        )
        sys.exit(1)

    dataset_path = sys.argv[1]
    dataset_name = sys.argv[2]

    test_branch_switching(dataset_path, dataset_name)


if __name__ == "__main__":
    main()
