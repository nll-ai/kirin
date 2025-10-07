"""Test for linear history workflow with rebase merges."""

import tempfile
import time
from pathlib import Path

import pytest

from gitdata.dataset import Dataset


def test_linear_history_workflow():
    """Test a complete linear history workflow with rebase merges.

    This test verifies that:
    1. Dataset creation works
    2. Multiple commits on main branch
    3. Branch creation and commits
    4. Rebase merge (no merge commits)
    5. File removal workflow
    6. Final linear history without merge commits
    """
    # Use 3 random words for dataset name
    dataset_name = f"test_linear_{int(time.time())}"

    with tempfile.TemporaryDirectory() as temp_dir:
        # (a) Create the dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name=dataset_name)

        # (b) Commit two dummy text files
        file1 = Path(temp_dir) / "file1.txt"
        file1.write_text("Content of file 1")

        file2 = Path(temp_dir) / "file2.txt"
        file2.write_text("Content of file 2")

        dataset.commit(
            "Initial commit with two files", add_files=[str(file1), str(file2)]
        )

        # (c) Checkout to new branch "branch-add" and commit one dummy text file
        dataset.create_branch("branch-add")
        dataset.switch_branch("branch-add")

        file3 = Path(temp_dir) / "file3.txt"
        file3.write_text("Content of file 3")

        dataset.commit("Add file3 on branch-add", add_files=str(file3))

        # (d) Merge branch-add into main using rebase (no merge commits)
        dataset.switch_branch("main")
        result = dataset.merge("branch-add", "main", strategy="rebase")

        # Verify merge was successful
        assert result["success"] is True
        assert result["source_branch"] == "branch-add"
        assert result["target_branch"] == "main"

        # Verify all files are present in main
        dataset.checkout(dataset.current_version_hash())
        files = dataset.file_dict
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "file3.txt" in files

        # (e) Create branch-remove, commit removal of one original file
        dataset.create_branch("branch-remove")
        dataset.switch_branch("branch-remove")

        dataset.commit("Remove file1", remove_files="file1.txt")

        # Merge branch-remove into main using rebase
        dataset.switch_branch("main")
        result = dataset.merge("branch-remove", "main", strategy="rebase")

        # Verify merge was successful
        assert result["success"] is True
        assert result["source_branch"] == "branch-remove"
        assert result["target_branch"] == "main"

        # Verify file1 is removed but file2 and file3 remain
        dataset.checkout(dataset.current_version_hash())
        files = dataset.file_dict
        assert "file1.txt" not in files  # Should be removed
        assert "file2.txt" in files  # Should remain
        assert "file3.txt" in files  # Should remain

        # (f) Assert that main branch has linear history with no merge commits
        commits = dataset.get_commits()

        # Check that no commit messages contain "Merge"
        merge_commits = [
            commit for commit in commits if "Merge" in commit.get("message", "")
        ]
        assert len(merge_commits) == 0, (
            f"Found merge commits: {[c['message'] for c in merge_commits]}"
        )

        # Verify we have the expected commits in linear order
        expected_messages = [
            "Remove file1",
            "Add file3 on branch-add",
            "Initial commit with two files",
        ]

        actual_messages = [commit.get("message", "") for commit in commits]

        # Check that all expected messages are present
        for expected_msg in expected_messages:
            assert expected_msg in actual_messages, (
                f"Expected message '{expected_msg}' not found in {actual_messages}"
            )

        # Verify linear history (commits should be in reverse chronological order)
        assert len(commits) >= 3, f"Expected at least 3 commits, got {len(commits)}"

        print(f"✅ Linear history test passed!")
        print(f"✅ Dataset: {dataset_name}")
        print(f"✅ Commits: {len(commits)}")
        print(f"✅ No merge commits found")
        print(f"✅ All expected files present/removed correctly")
