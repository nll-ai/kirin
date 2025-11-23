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
Analyze the actual commit structure to understand why we have duplicates.
"""

import sys
from pathlib import Path

from loguru import logger

# Add the parent directory to the path so we can import kirin
sys.path.insert(0, str(Path(__file__).parent.parent))

from kirin.dataset import Dataset


def analyze_commit_structure(dataset_path, dataset_name):
    """Analyze the actual commit structure in the dataset."""
    print(f"🔍 Analyzing commit structure for: {dataset_name}")
    print(f"📁 Path: {dataset_path}")

    try:
        # Load the dataset
        dataset = Dataset(root_dir=dataset_path, dataset_name=dataset_name)

        # Get all commits data
        commits_dict = dataset._get_commits_data()
        print(f"📊 Total commits in dataset: {len(commits_dict)}")

        # Analyze each commit
        print("\n🔍 Commit Analysis:")
        print("=" * 80)

        for commit_hash, commit_data in commits_dict.items():
            parent_hash = commit_data.get("parent_hash", "")
            parent_hashes = commit_data.get("parent_hashes", [])
            message = commit_data.get("commit_message", "")
            file_count = len(commit_data.get("file_hashes", []))

            print(f"Commit: {commit_hash[:8]}")
            print(f"  Message: {message}")
            print(f"  Parent: {parent_hash[:8] if parent_hash else 'None'}")
            print(
                f"  Parents: {[p[:8] for p in parent_hashes] if parent_hashes else 'None'}"
            )
            print(f"  Files: {file_count}")
            print(f"  Is merge: {len(parent_hashes) > 1}")
            print()

        # Check for duplicate messages
        print("\n🔍 Duplicate Message Analysis:")
        print("=" * 40)

        message_counts = {}
        for commit_hash, commit_data in commits_dict.items():
            message = commit_data.get("commit_message", "")
            if message not in message_counts:
                message_counts[message] = []
            message_counts[message].append(commit_hash[:8])

        for message, hashes in message_counts.items():
            if len(hashes) > 1:
                print(f"Duplicate message '{message}': {hashes}")

        # Check for duplicate file counts
        print("\n🔍 Duplicate File Count Analysis:")
        print("=" * 40)

        file_count_groups = {}
        for commit_hash, commit_data in commits_dict.items():
            file_count = len(commit_data.get("file_hashes", []))
            if file_count not in file_count_groups:
                file_count_groups[file_count] = []
            file_count_groups[file_count].append(commit_hash[:8])

        for file_count, hashes in file_count_groups.items():
            if len(hashes) > 1:
                print(f"File count {file_count}: {hashes}")

        # Analyze the branch structure
        print("\n🔍 Branch Analysis:")
        print("=" * 40)

        branches = dataset.list_branches()
        for branch in branches:
            branch_commit = dataset.get_branch_commit(branch)
            print(f"Branch '{branch}': {branch_commit[:8]}")

        # Check if commits are actually duplicated
        print("\n🔍 Commit Hash Uniqueness:")
        print("=" * 40)

        all_hashes = list(commits_dict.keys())
        unique_hashes = set(all_hashes)

        print(f"Total commits: {len(all_hashes)}")
        print(f"Unique commits: {len(unique_hashes)}")
        print(f"Are all commits unique? {len(all_hashes) == len(unique_hashes)}")

        if len(all_hashes) != len(unique_hashes):
            print("❌ DUPLICATE COMMIT HASHES FOUND!")
            # Find duplicates
            seen = set()
            duplicates = set()
            for hash_val in all_hashes:
                if hash_val in seen:
                    duplicates.add(hash_val)
                else:
                    seen.add(hash_val)
            print(f"Duplicate hashes: {[h[:8] for h in duplicates]}")

    except Exception as e:
        logger.error(f"Error analyzing dataset: {e}")
        raise


def main():
    """Main function."""
    if len(sys.argv) != 3:
        print("Usage: python analyze_commit_structure.py <dataset_path> <dataset_name>")
        print(
            "Example: python analyze_commit_structure.py /tmp/kirin-test-dataset test-dataset"
        )
        sys.exit(1)

    dataset_path = sys.argv[1]
    dataset_name = sys.argv[2]

    analyze_commit_structure(dataset_path, dataset_name)


if __name__ == "__main__":
    main()
