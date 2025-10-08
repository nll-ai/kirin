"""Tests for consolidated index implementation (Zarr-inspired approach)."""

import os
import shutil
import tempfile
from pathlib import Path

import json5 as json
import pytest

from kirin import Dataset


def test_consolidated_index_data_integrity():
    """Test that consolidated index contains exactly the same data as individual JSON files.

    This is the most critical test because it ensures we don't lose any data
    when implementing the consolidated index approach.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="integrity-test")

        # Create a commit using the current method
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, World!")
        commit_hash = dataset.commit("Test commit", add_files=str(test_file))

        # Get the data from the individual JSON file (current method)
        json_file_path = f"{dataset.dataset_dir}/{commit_hash}/commit.json"
        with dataset.fs.open(json_file_path, "r") as f:
            original_data = json.load(f)

        # Get the data from the consolidated index (new method)
        index_file_path = f"{dataset.dataset_dir}/.kirin-index"
        with dataset.fs.open(index_file_path, "r") as f:
            index_data = json.load(f)

        # CRITICAL: The consolidated index must contain the same data
        assert commit_hash in index_data["commits"], "Commit must be in index"

        commit_in_index = index_data["commits"][commit_hash]

        # Verify all critical fields match exactly
        assert commit_in_index["message"] == original_data["commit_message"]
        assert commit_in_index["parent"] == original_data.get("parent_hash")
        # Timestamp is added by the index, so we just verify it exists
        assert "timestamp" in commit_in_index
        assert commit_in_index["files"] == original_data.get("file_hashes", [])

        # Verify branch reference is correct
        assert index_data["branches"]["main"] == commit_hash

        # Verify the index structure is complete
        assert "commits" in index_data
        assert "branches" in index_data
        assert "tags" in index_data


def test_consolidated_index_creation_on_commit():
    """Test that consolidated index is created and updated when commits are made.

    This test ensures that the consolidated index is automatically maintained
    as commits are created, providing the foundation for fast commit loading.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="creation-test")

        # Verify index exists with root commit
        index_file_path = f"{dataset.dataset_dir}/.kirin-index"
        assert dataset.fs.exists(index_file_path), "Index should exist with root commit"

        # Create first commit
        test_file1 = Path(temp_dir) / "file1.txt"
        test_file1.write_text("Content 1")
        commit_hash1 = dataset.commit("First commit", add_files=str(test_file1))

        # Verify index is created after first commit
        assert dataset.fs.exists(index_file_path), (
            "Index should be created after first commit"
        )

        # Verify index contains the commit
        with dataset.fs.open(index_file_path, "r") as f:
            index_data = json.load(f)

        assert commit_hash1 in index_data["commits"], "First commit should be in index"
        assert index_data["branches"]["main"] == commit_hash1, (
            "Main branch should point to first commit"
        )

        # Create second commit
        test_file2 = Path(temp_dir) / "file2.txt"
        test_file2.write_text("Content 2")
        commit_hash2 = dataset.commit("Second commit", add_files=str(test_file2))

        # Verify index is updated with second commit
        with dataset.fs.open(index_file_path, "r") as f:
            index_data = json.load(f)

        assert commit_hash1 in index_data["commits"], (
            "First commit should still be in index"
        )
        assert commit_hash2 in index_data["commits"], "Second commit should be in index"
        assert index_data["branches"]["main"] == commit_hash2, (
            "Main branch should point to second commit"
        )

        # Verify parent relationship is correct
        assert index_data["commits"][commit_hash2]["parent"] == commit_hash1, (
            "Second commit should have first commit as parent"
        )

        # Verify index structure is maintained
        assert "commits" in index_data
        assert "branches" in index_data
        assert "tags" in index_data


def test_consolidated_index_edge_cases():
    """Test consolidated index behavior in edge cases.

    This test ensures the consolidated index handles edge cases gracefully:
    - Empty datasets
    - Corrupted index files
    - Concurrent access scenarios
    - Missing data scenarios
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test 1: Empty dataset (no commits)
        dataset = Dataset(root_dir=temp_dir, dataset_name="empty-test")

        # Index should exist with root commit
        index_file_path = f"{dataset.dataset_dir}/.kirin-index"
        assert dataset.fs.exists(index_file_path), "Index should exist with root commit"

        # Test 2: Corrupted index file recovery
        dataset2 = Dataset(root_dir=temp_dir, dataset_name="corrupted-test")

        # Create a commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, World!")
        commit_hash = dataset2.commit("Test commit", add_files=str(test_file))

        # Get the correct index file path for dataset2
        index_file_path2 = f"{dataset2.dataset_dir}/.kirin-index"

        # Manually corrupt the index file
        with dataset2.fs.open(index_file_path2, "w") as f:
            f.write("corrupted json content")

        # The system should be able to recover from corrupted index
        dataset2._rebuild_index_from_commits()

        # Verify index is restored
        assert dataset2.fs.exists(index_file_path2), (
            "Index should be restored after corruption"
        )

        # Verify the rebuilt index is valid JSON
        with dataset2.fs.open(index_file_path2, "r") as f:
            index_data = json.load(f)

        assert commit_hash in index_data["commits"], (
            "Commit should be restored in index"
        )

        # Test 3: Index with missing commit data
        # Create another commit
        test_file2 = Path(temp_dir) / "test2.txt"
        test_file2.write_text("Hello, World 2!")
        commit_hash2 = dataset2.commit("Test commit 2", add_files=str(test_file2))

        # Manually remove a commit JSON file (simulate data loss)
        json_file_path = f"{dataset2.dataset_dir}/{commit_hash}/commit.json"
        if dataset2.fs.exists(json_file_path):
            dataset2.fs.rm(json_file_path)

        # The system should handle missing commit data gracefully
        # (This will be implemented as part of the solution)
        dataset2._rebuild_index_from_commits()

        # Verify index is still consistent
        with dataset2.fs.open(index_file_path2, "r") as f:
            index_data = json.load(f)

        # Should still have the second commit
        assert commit_hash2 in index_data["commits"], (
            "Second commit should still be in index"
        )


def test_consolidated_index_integration_with_branching():
    """Test consolidated index integration with branching and merging.

    This test ensures the consolidated index works correctly with complex
    Git operations like branching, merging, and branch switching.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset = Dataset(root_dir=temp_dir, dataset_name="integration-test")

        # Create initial commit
        test_file1 = Path(temp_dir) / "file1.txt"
        test_file1.write_text("Content 1")
        commit1 = dataset.commit("Initial commit", add_files=str(test_file1))

        # Create branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Add commit to branch
        test_file2 = Path(temp_dir) / "file2.txt"
        test_file2.write_text("Content 2")
        commit2 = dataset.commit("Feature commit", add_files=str(test_file2))

        # Verify index contains both commits
        index_file_path = f"{dataset.dataset_dir}/.kirin-index"
        with dataset.fs.open(index_file_path, "r") as f:
            index_data = json.load(f)

        assert commit1 in index_data["commits"], "Initial commit should be in index"
        assert commit2 in index_data["commits"], "Feature commit should be in index"
        assert index_data["branches"]["main"] == commit1, (
            "Main branch should point to initial commit"
        )
        assert index_data["branches"]["feature"] == commit2, (
            "Feature branch should point to feature commit"
        )

        # Switch back to main
        dataset.switch_branch("main")

        # Verify index is still consistent after branch switching
        with dataset.fs.open(index_file_path, "r") as f:
            index_data = json.load(f)

        assert commit1 in index_data["commits"], (
            "Initial commit should still be in index"
        )
        assert commit2 in index_data["commits"], (
            "Feature commit should still be in index"
        )

        # Merge feature branch
        merge_result = dataset.merge("feature")

        # Verify index is updated after merge
        with dataset.fs.open(index_file_path, "r") as f:
            index_data = json.load(f)

        assert merge_result["merge_commit"] in index_data["commits"], (
            "Merge commit should be in index"
        )
        assert index_data["branches"]["main"] == merge_result["merge_commit"], (
            "Main branch should point to merge commit"
        )

        # Verify parent relationships are correct
        merge_commit_data = index_data["commits"][merge_result["merge_commit"]]
        assert commit1 in merge_commit_data.get("parents", []), (
            "Merge commit should have initial commit as parent"
        )
        assert commit2 in merge_commit_data.get("parents", []), (
            "Merge commit should have feature commit as parent"
        )
