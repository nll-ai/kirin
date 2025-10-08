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
Create a comprehensive dummy dataset demonstrating Kirin's full workflow.

This script creates a dataset at /tmp/gitdata-test-dataset and demonstrates:
1. Creating a dataset with main branch
2. Writing two files over two commits
3. Branching to 'add-third' from main and adding a third file
4. Branching to 'add-fourth' from main and adding a fourth file
5. Merging 'add-third' into main with rebase
6. Merging 'add-fourth' into main with rebase
7. Adding one more commit that removes one file on a branch and merges back to main

This follows the design document's approach for demonstrating the complete
Kirin workflow as outlined in the branching and merging capabilities.
"""

import os
import shutil
import tempfile
from pathlib import Path
from loguru import logger

from kirin import Dataset


def create_test_files(temp_dir: Path, files: dict) -> None:
    """Create test files in the temporary directory."""
    for filename, content in files.items():
        file_path = temp_dir / filename
        file_path.write_text(content)
        logger.info(f"Created test file: {filename}")


def main():
    """Create a comprehensive dummy dataset demonstrating Kirin's full workflow."""

    # Set up the dataset path
    dataset_path = "/tmp/gitdata-test-dataset"

    # Clean up any existing dataset
    if os.path.exists(dataset_path):
        logger.info(f"Cleaning up existing dataset at {dataset_path}")
        shutil.rmtree(dataset_path)

    # Clean up any existing local state
    local_state_dir = Path.home() / ".gitdata" / "test-dataset"
    if local_state_dir.exists():
        logger.info(f"Cleaning up existing local state at {local_state_dir}")
        shutil.rmtree(local_state_dir)

    logger.info("🚀 Starting comprehensive Kirin workflow demonstration")
    logger.info(f"Dataset will be created at: {dataset_path}")

    # Create temporary directory for file operations
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Step 1: Create the dataset with main branch
        logger.info("📦 Step 1: Creating dataset with main branch")
        dataset = Dataset(root_dir=dataset_path, dataset_name="test-dataset")
        logger.info(f"✅ Dataset created at {dataset_path}")
        logger.info(f"Current branch: {dataset.get_current_branch()}")

        # Ensure we're on main branch
        if dataset.get_current_branch() != "main":
            dataset.switch_branch("main")
            logger.info(f"Switched to main branch: {dataset.get_current_branch()}")

        # Step 2: Write two files over two commits
        logger.info("📝 Step 2: Writing two files over two commits")

        # First commit - file1.txt
        create_test_files(
            temp_path,
            {
                "file1.txt": "This is the first file in our dataset.\nIt contains some sample data."
            },
        )
        dataset.commit(
            "Initial commit with file1", add_files=str(temp_path / "file1.txt")
        )
        logger.info("✅ First commit completed")

        # Second commit - file2.txt
        create_test_files(
            temp_path,
            {
                "file2.txt": "This is the second file in our dataset.\nIt contains additional sample data."
            },
        )
        dataset.commit("Add file2 to dataset", add_files=str(temp_path / "file2.txt"))
        logger.info("✅ Second commit completed")

        # Verify files in main branch
        files_in_main = dataset.file_dict
        logger.info(f"Files in main branch: {list(files_in_main.keys())}")

        # Step 3: Branch to 'add-third' from main and add third file
        logger.info("🌿 Step 3: Creating 'add-third' branch and adding third file")
        dataset.create_branch("add-third")
        dataset.switch_branch("add-third")
        logger.info(f"Switched to branch: {dataset.get_current_branch()}")

        create_test_files(
            temp_path,
            {
                "file3.txt": "This is the third file added on the add-third branch.\nIt demonstrates branching workflow."
            },
        )
        dataset.commit(
            "Add file3 on add-third branch", add_files=str(temp_path / "file3.txt")
        )
        logger.info("✅ Third file added on add-third branch")

        # Step 4: Branch to 'add-fourth' from main and add fourth file
        logger.info("🌿 Step 4: Creating 'add-fourth' branch and adding fourth file")
        dataset.switch_branch("main")
        dataset.create_branch("add-fourth")
        dataset.switch_branch("add-fourth")
        logger.info(f"Switched to branch: {dataset.get_current_branch()}")

        create_test_files(
            temp_path,
            {
                "file4.txt": "This is the fourth file added on the add-fourth branch.\nIt demonstrates parallel development."
            },
        )
        dataset.commit(
            "Add file4 on add-fourth branch", add_files=str(temp_path / "file4.txt")
        )
        logger.info("✅ Fourth file added on add-fourth branch")

        # Step 5: Merge 'add-third' into main with rebase
        logger.info("🔄 Step 5: Merging 'add-third' into main with rebase")
        dataset.switch_branch("main")
        merge_result_third = dataset.merge("add-third", "main", strategy="rebase")

        if merge_result_third["success"]:
            logger.info("✅ Successfully merged add-third into main with rebase")
            logger.info(f"Merge result: {merge_result_third}")
        else:
            logger.error(f"❌ Failed to merge add-third: {merge_result_third}")
            return

        # Verify files after first merge
        files_after_third = dataset.file_dict
        logger.info(
            f"Files in main after merging add-third: {list(files_after_third.keys())}"
        )

        # Step 6: Merge 'add-fourth' into main with rebase
        logger.info("🔄 Step 6: Merging 'add-fourth' into main with rebase")
        merge_result_fourth = dataset.merge("add-fourth", "main", strategy="rebase")

        if merge_result_fourth["success"]:
            logger.info("✅ Successfully merged add-fourth into main with rebase")
            logger.info(f"Merge result: {merge_result_fourth}")
        else:
            logger.error(f"❌ Failed to merge add-fourth: {merge_result_fourth}")
            return

        # Verify files after second merge
        files_after_fourth = dataset.file_dict
        logger.info(
            f"Files in main after merging add-fourth: {list(files_after_fourth.keys())}"
        )

        # Step 7: Add one more commit that removes one file on a branch and merges back
        logger.info("🗑️ Step 7: Creating cleanup branch to remove a file")
        dataset.create_branch("cleanup-remove-file1")
        dataset.switch_branch("cleanup-remove-file1")
        logger.info(f"Switched to branch: {dataset.get_current_branch()}")

        # Remove file1.txt
        dataset.commit(
            "Remove file1.txt as it's no longer needed", remove_files=["file1.txt"]
        )
        logger.info("✅ Removed file1.txt on cleanup branch")

        # Verify file removal
        files_after_removal = dataset.file_dict
        logger.info(f"Files after removal: {list(files_after_removal.keys())}")
        assert "file1.txt" not in files_after_removal, "file1.txt should be removed"

        # Merge cleanup branch back to main
        logger.info("🔄 Merging cleanup branch back to main")
        dataset.switch_branch("main")
        merge_result_cleanup = dataset.merge(
            "cleanup-remove-file1", "main", strategy="rebase"
        )

        if merge_result_cleanup["success"]:
            logger.info("✅ Successfully merged cleanup branch into main")
            logger.info(f"Merge result: {merge_result_cleanup}")
        else:
            logger.error(f"❌ Failed to merge cleanup: {merge_result_cleanup}")
            return

        # Final verification
        final_files = dataset.file_dict
        logger.info(f"Final files in main: {list(final_files.keys())}")

        # List all branches
        all_branches = dataset.list_branches()
        logger.info(f"All branches: {all_branches}")

        # Show commit history
        logger.info("📊 Final commit history:")
        commits = dataset.get_commits()
        for i, commit in enumerate(commits[:10]):  # Limit to first 10 commits
            logger.info(f"  Commit {i + 1}: {commit['message']}")
            logger.info(f"    Hash: {commit['short_hash']}...")
            logger.info(f"    Files: {commit['file_count']} files")

        logger.info("🎉 Comprehensive Kirin workflow demonstration completed!")
        logger.info(f"Dataset created at: {dataset_path}")

        # Print dataset URL and name for easy access
        dataset_url = f"file://{dataset_path}"
        dataset_name = "test-dataset"
        print(f"\n{'=' * 60}")
        print(f"DATASET INFORMATION:")
        print(f"{'=' * 60}")
        print(f"Dataset URL: {dataset_url}")
        print(f"Dataset Name: {dataset_name}")
        print(f"Web UI URL: http://localhost:8000/d/{dataset_name}?url={dataset_url}")
        print(f"{'=' * 60}\n")

        logger.info("You can now explore the dataset using the web UI or CLI")


if __name__ == "__main__":
    main()
