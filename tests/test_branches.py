"""Tests for branch functionality in GitData."""

import os
import tempfile
from pathlib import Path

import pytest

from kirin.dataset import Dataset
from kirin.models import BranchManager


def test_branch_manager_initialization():
    """Test that BranchManager initializes correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        # Create a mock filesystem
        import fsspec

        fs = fsspec.filesystem("file")

        branch_manager = BranchManager(dataset_dir, fs)

        # Check that refs directory was created
        assert fs.exists(f"{dataset_dir}/refs/heads")

        # Check that main branch is created by default
        assert branch_manager.get_current_branch() == "main"


def test_create_branch():
    """Test creating a new branch."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        import fsspec

        fs = fsspec.filesystem("file")
        branch_manager = BranchManager(dataset_dir, fs)

        # Create a branch
        commit_hash = "abc123def456"
        branch_manager.create_branch("feature", commit_hash)

        # Check that branch was created
        assert branch_manager.get_branch_commit("feature") == commit_hash
        assert "feature" in branch_manager.list_branches()


def test_create_branch_already_exists():
    """Test that creating a branch that already exists raises an error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        import fsspec

        fs = fsspec.filesystem("file")
        branch_manager = BranchManager(dataset_dir, fs)

        # Create a branch
        commit_hash = "abc123def456"
        branch_manager.create_branch("feature", commit_hash)

        # Try to create the same branch again
        with pytest.raises(ValueError, match="Branch 'feature' already exists"):
            branch_manager.create_branch("feature", "def456ghi789")


def test_create_main_branch():
    """Test that creating a branch named 'main' when it already exists raises an error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        import fsspec

        fs = fsspec.filesystem("file")
        branch_manager = BranchManager(dataset_dir, fs)

        # First create the main branch (this should work)
        branch_manager.create_branch("main", "abc123def456")

        # Now try to create it again (this should fail)
        with pytest.raises(ValueError, match="Cannot create a branch named 'main'"):
            branch_manager.create_branch("main", "def456ghi789")


def test_update_branch():
    """Test updating a branch to point to a new commit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        import fsspec

        fs = fsspec.filesystem("file")
        branch_manager = BranchManager(dataset_dir, fs)

        # Create a branch
        commit_hash1 = "abc123def456"
        branch_manager.create_branch("feature", commit_hash1)

        # Update the branch
        commit_hash2 = "def456ghi789"
        branch_manager.update_branch("feature", commit_hash2)

        # Check that branch was updated
        assert branch_manager.get_branch_commit("feature") == commit_hash2


def test_delete_branch():
    """Test deleting a branch."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        import fsspec

        fs = fsspec.filesystem("file")
        branch_manager = BranchManager(dataset_dir, fs)

        # Create a branch
        commit_hash = "abc123def456"
        branch_manager.create_branch("feature", commit_hash)

        # Delete the branch
        branch_manager.delete_branch("feature")

        # Check that branch was deleted
        assert "feature" not in branch_manager.list_branches()
        with pytest.raises(ValueError, match="Branch 'feature' does not exist"):
            branch_manager.get_branch_commit("feature")


def test_delete_main_branch():
    """Test that deleting the main branch raises an error."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        import fsspec

        fs = fsspec.filesystem("file")
        branch_manager = BranchManager(dataset_dir, fs)

        with pytest.raises(ValueError, match="Cannot delete the main branch"):
            branch_manager.delete_branch("main")


def test_set_current_branch():
    """Test setting the current branch."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_dir = f"{temp_dir}/test_dataset"
        os.makedirs(dataset_dir, exist_ok=True)

        import fsspec

        fs = fsspec.filesystem("file")
        branch_manager = BranchManager(dataset_dir, fs)

        # Create a branch
        commit_hash = "abc123def456"
        branch_manager.create_branch("feature", commit_hash)

        # Set current branch
        branch_manager.set_current_branch("feature")

        # Check that current branch was set
        assert branch_manager.get_current_branch() == "feature"
        assert branch_manager.get_current_commit() == commit_hash


def test_dataset_branch_operations():
    """Test branch operations through the Dataset class."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add some files and commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, world!")

        dataset.commit("Initial commit", add_files=str(test_file))

        # Create a new branch
        dataset.create_branch("feature")

        # Check that branch was created
        branches = dataset.list_branches()
        assert "feature" in branches
        assert "main" in branches

        # Switch to the feature branch
        dataset.switch_branch("feature")
        assert dataset.get_current_branch() == "feature"

        # Add a file to the feature branch
        feature_file = Path(temp_dir) / "feature.txt"
        feature_file.write_text("Feature content")

        dataset.commit("Add feature file", add_files=str(feature_file))

        # Switch back to main
        dataset.switch_branch("main")
        assert dataset.get_current_branch() == "main"

        # Check that main doesn't have the feature file
        assert "feature.txt" not in dataset.file_dict

        # Switch back to feature
        dataset.switch_branch("feature")
        assert "feature.txt" in dataset.file_dict


def test_dataset_branch_commit_history():
    """Test that commits are properly tracked per branch."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add initial file to main
        main_file = Path(temp_dir) / "main.txt"
        main_file.write_text("Main content")
        dataset.commit("Add main file", add_files=str(main_file))

        # Create feature branch
        dataset.create_branch("feature")

        # Add file to feature branch
        feature_file = Path(temp_dir) / "feature.txt"
        feature_file.write_text("Feature content")
        dataset.switch_branch("feature")
        dataset.commit("Add feature file", add_files=str(feature_file))

        # Switch back to main and add another file
        dataset.switch_branch("main")
        main_file2 = Path(temp_dir) / "main2.txt"
        main_file2.write_text("Main content 2")
        dataset.commit("Add second main file", add_files=str(main_file2))

        # Check that each branch has the correct files
        dataset.switch_branch("feature")
        assert "feature.txt" in dataset.file_dict
        assert "main2.txt" not in dataset.file_dict

        dataset.switch_branch("main")
        assert "main.txt" in dataset.file_dict
        assert "main2.txt" in dataset.file_dict
        assert "feature.txt" not in dataset.file_dict


def test_dataset_delete_branch():
    """Test deleting a branch through the Dataset class."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add some files and commit
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, world!")
        dataset.commit("Initial commit", add_files=str(test_file))

        # Create a branch
        dataset.create_branch("feature")

        # Delete the branch
        dataset.delete_branch("feature")

        # Check that branch was deleted
        branches = dataset.list_branches()
        assert "feature" not in branches
        assert "main" in branches


def test_dataset_branch_commit_updates_branch():
    """Test that committing updates the current branch."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a dataset
        dataset = Dataset(root_dir=temp_dir, dataset_name="test_dataset")

        # Add initial file
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello, world!")
        dataset.commit("Initial commit", add_files=str(test_file))

        # Get the initial commit hash
        initial_commit = dataset.current_version_hash()

        # Create a feature branch
        dataset.create_branch("feature")
        dataset.switch_branch("feature")

        # Add another file
        feature_file = Path(temp_dir) / "feature.txt"
        feature_file.write_text("Feature content")
        dataset.commit("Add feature file", add_files=str(feature_file))

        # Check that the feature branch was updated
        feature_commit = dataset.get_branch_commit("feature")
        assert feature_commit != initial_commit

        # Check that main branch still points to the original commit
        main_commit = dataset.get_branch_commit("main")
        assert main_commit == initial_commit
