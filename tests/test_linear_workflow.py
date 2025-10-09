"""Tests for end-to-end linear workflow."""

import tempfile
from pathlib import Path

import pytest

from kirin.dataset import Dataset


def test_basic_workflow(temp_dir):
    """Test basic dataset workflow."""
    # Create dataset
    dataset = Dataset(
        root_dir=temp_dir, name="test_dataset", description="Test dataset"
    )

    # Initially empty
    assert dataset.is_empty()
    assert dataset.current_commit is None
    assert dataset.list_files() == []

    # Create initial commit
    test_file = Path(temp_dir) / "data.txt"
    test_file.write_text("Hello, World!")

    commit_hash = dataset.commit("Initial commit", add_files=[test_file])

    # Check state after commit
    assert not dataset.is_empty()
    assert dataset.current_commit is not None
    assert dataset.current_commit.hash == commit_hash
    assert dataset.has_file("data.txt")
    assert dataset.list_files() == ["data.txt"]

    # Read file content
    content = dataset.read_file("data.txt")
    assert content == "Hello, World!"


def test_multiple_commits_workflow(temp_dir):
    """Test workflow with multiple commits."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # First commit
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")

    commit1_hash = dataset.commit("Add file1", add_files=[file1])

    # Second commit
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    commit2_hash = dataset.commit("Add file2", add_files=[file2])

    # Check current state
    assert dataset.current_commit.hash == commit2_hash
    assert dataset.has_file("file1.txt")
    assert dataset.has_file("file2.txt")
    assert len(dataset.list_files()) == 2

    # Check history
    history = dataset.history()
    assert len(history) == 2
    assert history[0].hash == commit2_hash  # Newest first
    assert history[1].hash == commit1_hash


def test_file_modification_workflow(temp_dir):
    """Test workflow with file modifications."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Initial file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Version 1")

    commit1_hash = dataset.commit("Initial version", add_files=[test_file])

    # Modify file
    test_file.write_text("Version 2")

    commit2_hash = dataset.commit("Update to version 2", add_files=[test_file])

    # Check that we have the updated content
    assert dataset.read_file("test.txt") == "Version 2"

    # Checkout previous version
    dataset.checkout(commit1_hash)
    assert dataset.read_file("test.txt") == "Version 1"

    # Checkout latest version
    dataset.checkout(commit2_hash)
    assert dataset.read_file("test.txt") == "Version 2"


def test_file_removal_workflow(temp_dir):
    """Test workflow with file removal."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    dataset.commit("Add files", add_files=[file1, file2])

    # Remove one file
    dataset.commit("Remove file1", remove_files=["file1.txt"])

    # Check state
    assert not dataset.has_file("file1.txt")
    assert dataset.has_file("file2.txt")
    assert len(dataset.list_files()) == 1


def test_mixed_add_remove_workflow(temp_dir):
    """Test workflow with mixed add and remove operations."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Initial files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    dataset.commit("Add initial files", add_files=[file1, file2])

    # Mixed operation: add new file, remove existing file
    file3 = Path(temp_dir) / "file3.txt"
    file3.write_text("Content 3")

    dataset.commit(
        "Add file3, remove file1", add_files=[file3], remove_files=["file1.txt"]
    )

    # Check final state
    assert not dataset.has_file("file1.txt")
    assert dataset.has_file("file2.txt")
    assert dataset.has_file("file3.txt")
    assert len(dataset.list_files()) == 2


def test_checkout_workflow(temp_dir):
    """Test checkout workflow."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create multiple commits
    commits = []
    for i in range(3):
        test_file = Path(temp_dir) / f"file{i}.txt"
        test_file.write_text(f"Content {i}")

        commit_hash = dataset.commit(f"Add file{i}", add_files=[test_file])
        commits.append(commit_hash)

    # Checkout each commit
    for i, commit_hash in enumerate(commits):
        dataset.checkout(commit_hash)

        # Should have files up to this point
        expected_files = [f"file{j}.txt" for j in range(i + 1)]
        actual_files = dataset.list_files()

        for expected_file in expected_files:
            assert expected_file in actual_files


def test_partial_hash_checkout(temp_dir):
    """Test checkout with partial hash."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create commit
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello")

    full_hash = dataset.commit("Test commit", add_files=[test_file])

    # Checkout with partial hash
    partial_hash = full_hash[:8]
    dataset.checkout(partial_hash)

    assert dataset.current_commit.hash == full_hash
    assert dataset.has_file("test.txt")


def test_local_files_context_workflow(temp_dir):
    """Test local files context manager workflow."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add multiple files
    files = []
    for i in range(3):
        test_file = Path(temp_dir) / f"file{i}.txt"
        test_file.write_text(f"Content {i}")
        files.append(test_file)

    dataset.commit("Add files", add_files=files)

    # Use local files context
    with dataset.local_files() as local_files:
        assert len(local_files) == 3

        # Check that all files exist and have correct content
        for i in range(3):
            filename = f"file{i}.txt"
            assert filename in local_files

            local_path = Path(local_files[filename])
            assert local_path.exists()
            assert local_path.read_text() == f"Content {i}"


def test_empty_dataset_workflow(temp_dir):
    """Test workflow with empty dataset."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Should be empty initially
    assert dataset.is_empty()
    assert dataset.current_commit is None
    assert dataset.list_files() == []

    # Local files context should return empty dict
    with dataset.local_files() as local_files:
        assert local_files == {}

    # History should be empty
    assert dataset.history() == []

    # Info should reflect empty state
    info = dataset.get_info()
    assert info["commit_count"] == 0
    assert info["current_commit"] is None


def test_dataset_info_workflow(temp_dir):
    """Test dataset information workflow."""
    dataset = Dataset(
        root_dir=temp_dir, name="test_dataset", description="Test dataset"
    )

    # Empty dataset info
    info = dataset.get_info()
    assert info["name"] == "test_dataset"
    assert info["description"] == "Test dataset"
    assert info["commit_count"] == 0
    assert info["current_commit"] is None

    # Add commit
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello")

    commit_hash = dataset.commit("Test commit", add_files=[test_file])

    # Updated info
    info = dataset.get_info()
    assert info["commit_count"] == 1
    assert info["current_commit"] == commit_hash
    assert info["latest_commit"] == commit_hash
    assert len(info["recent_commits"]) == 1


def test_commit_validation_workflow(temp_dir):
    """Test commit validation in workflow."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # No changes should raise error
    with pytest.raises(ValueError, match="No changes specified"):
        dataset.commit("Test commit")

    # Empty lists should raise error
    with pytest.raises(ValueError, match="No changes specified"):
        dataset.commit("Test commit", add_files=[], remove_files=[])

    # Valid commit should work
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello")

    commit_hash = dataset.commit("Valid commit", add_files=[test_file])
    assert commit_hash is not None


def test_file_operations_workflow(temp_dir):
    """Test various file operations in workflow."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    dataset.commit("Add file", add_files=[test_file])

    # Test file operations
    assert dataset.has_file("test.txt")
    assert not dataset.has_file("nonexistent.txt")

    # Read file
    content = dataset.read_file("test.txt")
    assert content == "Hello, World!"

    # Read as bytes
    content_bytes = dataset.read_file("test.txt", mode="rb")
    assert content_bytes == b"Hello, World!"

    # Download file
    download_path = Path(temp_dir) / "downloaded.txt"
    downloaded = dataset.download_file("test.txt", download_path)
    assert Path(downloaded).exists()
    assert Path(downloaded).read_text() == "Hello, World!"

    # Open file
    with dataset.open_file("test.txt", mode="r") as f:
        assert f.read() == "Hello, World!"


def test_error_handling_workflow(temp_dir):
    """Test error handling in workflow."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello")

    dataset.commit("Add file", add_files=[test_file])

    # Test error cases
    with pytest.raises(FileNotFoundError):
        dataset.read_file("nonexistent.txt")

    with pytest.raises(FileNotFoundError):
        dataset.download_file("nonexistent.txt", "output.txt")

    with pytest.raises(ValueError, match="Commit not found"):
        dataset.checkout("nonexistent_hash")
