"""Tests for the Dataset entity class."""

from pathlib import Path

import pytest

from kirin.dataset import Dataset


def test_dataset_creation(temp_dir):
    """Test creating a Dataset instance."""
    dataset = Dataset(
        root_dir=temp_dir, name="test_dataset", description="Test dataset"
    )

    assert dataset.name == "test_dataset"
    assert dataset.description == "Test dataset"
    assert dataset.root_dir == str(temp_dir)
    assert dataset.is_empty()
    assert dataset.current_commit is None
    assert dataset.head is None
    assert dataset.files == {}
    assert dataset.list_files() == []


def test_dataset_initial_commit(temp_dir):
    """Test creating initial commit."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create test file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    # Create initial commit
    commit_hash = dataset.commit(message="Initial commit", add_files=[test_file])

    assert not dataset.is_empty()
    assert dataset.current_commit is not None
    assert dataset.current_commit.hash == commit_hash
    assert dataset.current_commit.is_initial
    assert dataset.current_commit.message == "Initial commit"
    assert dataset.has_file("test.txt")
    assert dataset.list_files() == ["test.txt"]


def test_dataset_multiple_commits(temp_dir):
    """Test multiple commits."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # First commit
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")

    commit1_hash = dataset.commit(message="First commit", add_files=[file1])

    # Second commit
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    commit2_hash = dataset.commit(message="Second commit", add_files=[file2])

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


def test_dataset_file_removal(temp_dir):
    """Test removing files in commit."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    dataset.commit("Add files", add_files=[file1, file2])

    # Remove one file
    dataset.commit(message="Remove file1", remove_files=["file1.txt"])

    assert dataset.has_file("file2.txt")
    assert not dataset.has_file("file1.txt")
    assert len(dataset.list_files()) == 1


def test_dataset_checkout(temp_dir):
    """Test checking out specific commits."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create commits
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")

    commit1_hash = dataset.commit("First commit", add_files=[file1])

    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    commit2_hash = dataset.commit("Second commit", add_files=[file2])

    # Checkout first commit
    dataset.checkout(commit1_hash)
    assert dataset.current_commit.hash == commit1_hash
    assert dataset.has_file("file1.txt")
    assert not dataset.has_file("file2.txt")

    # Checkout second commit
    dataset.checkout(commit2_hash)
    assert dataset.current_commit.hash == commit2_hash
    assert dataset.has_file("file1.txt")
    assert dataset.has_file("file2.txt")


def test_dataset_file_operations(temp_dir):
    """Test file operations."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    dataset.commit("Add file", add_files=[test_file])

    # Test file operations
    assert dataset.has_file("test.txt")

    # Read file content
    content = dataset.read_file("test.txt")
    assert content == "Hello, World!"

    # Read file as bytes
    content_bytes = dataset.read_file("test.txt", mode="rb")
    assert content_bytes == b"Hello, World!"

    # Download file
    download_path = Path(temp_dir) / "downloaded.txt"
    downloaded = dataset.download_file("test.txt", download_path)
    assert Path(downloaded).exists()
    assert Path(downloaded).read_text() == "Hello, World!"


def test_dataset_file_not_found(temp_dir):
    """Test operations on non-existent files."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add a file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")
    dataset.commit("Add file", add_files=[test_file])

    # Test operations on non-existent file
    assert not dataset.has_file("nonexistent.txt")

    with pytest.raises(FileNotFoundError):
        dataset.read_file("nonexistent.txt")

    with pytest.raises(FileNotFoundError):
        dataset.download_file("nonexistent.txt", "output.txt")


def test_dataset_local_files_context(temp_dir):
    """Test local files context manager."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    dataset.commit("Add files", add_files=[file1, file2])

    # Use local files context
    with dataset.local_files() as local_files:
        assert len(local_files) == 2
        assert "file1.txt" in local_files
        assert "file2.txt" in local_files

        # Check that files exist and have correct content
        assert Path(local_files["file1.txt"]).read_text() == "Content 1"
        assert Path(local_files["file2.txt"]).read_text() == "Content 2"


def test_dataset_empty_local_files(temp_dir):
    """Test local files context with empty dataset."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    with dataset.local_files() as local_files:
        assert local_files == {}


def test_dataset_history_limits(temp_dir):
    """Test commit history with limits."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create multiple commits
    for i in range(5):
        test_file = Path(temp_dir) / f"file{i}.txt"
        test_file.write_text(f"Content {i}")
        dataset.commit(f"Commit {i}", add_files=[test_file])

    # Test history limits
    all_history = dataset.history()
    assert len(all_history) == 5

    limited_history = dataset.history(limit=3)
    assert len(limited_history) == 3

    # History should be newest first
    assert limited_history[0].message == "Commit 4"
    assert limited_history[1].message == "Commit 3"
    assert limited_history[2].message == "Commit 2"


def test_dataset_get_commit(temp_dir):
    """Test getting specific commits."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create commits
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello")

    commit1_hash = dataset.commit("First commit", add_files=[test_file])

    test_file.write_text("Hello World")
    commit2_hash = dataset.commit("Second commit", add_files=[test_file])

    # Get specific commits
    commit1 = dataset.get_commit(commit1_hash)
    assert commit1 is not None
    assert commit1.message == "First commit"

    commit2 = dataset.get_commit(commit2_hash)
    assert commit2 is not None
    assert commit2.message == "Second commit"

    # Test partial hash
    partial_hash = commit1_hash[:8]
    commit1_partial = dataset.get_commit(partial_hash)
    assert commit1_partial is not None
    assert commit1_partial.hash == commit1_hash


def test_dataset_info(temp_dir):
    """Test dataset information."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset", description="Test")

    # Empty dataset
    info = dataset.get_info()
    assert info["name"] == "test_dataset"
    assert info["description"] == "Test"
    assert info["commit_count"] == 0
    assert info["current_commit"] is None

    # Add commit
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello")
    commit_hash = dataset.commit("Test commit", add_files=[test_file])

    info = dataset.get_info()
    assert info["commit_count"] == 1
    assert info["current_commit"] == commit_hash
    assert info["latest_commit"] == commit_hash


def test_dataset_to_dict(temp_dir):
    """Test converting dataset to dictionary."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset", description="Test")

    data = dataset.to_dict()
    expected = {
        "name": "test_dataset",
        "description": "Test",
        "root_dir": str(temp_dir),
        "current_commit": None,
        "commit_count": 0,
    }

    assert data == expected


def test_dataset_string_representations(temp_dir):
    """Test string representations of dataset."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    str_repr = str(dataset)
    assert "Dataset(name='test_dataset'" in str_repr
    assert "commits=0" in str_repr

    repr_str = repr(dataset)
    assert "Dataset(name='test_dataset'" in repr_str
    assert "description=''" in repr_str
    assert f"root_dir='{temp_dir}'" in repr_str


def test_dataset_commit_validation(temp_dir):
    """Test commit validation."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # No changes should raise error
    with pytest.raises(ValueError, match="No changes specified"):
        dataset.commit("Test commit")

    # Empty add_files and remove_files
    with pytest.raises(ValueError, match="No changes specified"):
        dataset.commit("Test commit", add_files=[], remove_files=[])


def test_dataset_checkout_nonexistent(temp_dir):
    """Test checking out non-existent commit."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    with pytest.raises(ValueError, match="Commit not found"):
        dataset.checkout("nonexistent_hash")


def test_dataset_cleanup_orphaned_files(temp_dir):
    """Test cleaning up orphaned files."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello")
    dataset.commit("Add file", add_files=[test_file])

    # Cleanup should return 0 (no orphaned files)
    removed_count = dataset.cleanup_orphaned_files()
    assert removed_count == 0


def test_local_files_lazy_loading(temp_dir):
    """Test that local_files() uses lazy loading - files not downloaded on entry."""
    from unittest.mock import patch

    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    dataset.commit("Add files", add_files=[file1, file2])

    # Mock the download_to method at the class level to track downloads
    with patch("kirin.file.File.download_to") as mock_download:
        with dataset.local_files() as local_files:
            # Files should NOT be downloaded when entering context
            mock_download.assert_not_called()

            # Files should be downloaded only when accessed
            local_files["file1.txt"]
            assert mock_download.call_count == 1

            # Second access should use cache (no additional download)
            local_files["file1.txt"]
            assert mock_download.call_count == 1  # Still only called once

            # Access second file
            local_files["file2.txt"]
            assert mock_download.call_count == 2


def test_local_files_iteration_no_download(temp_dir):
    """Test that iterating over local_files does not trigger downloads."""
    from unittest.mock import patch

    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    dataset.commit("Add files", add_files=[file1, file2])

    # Mock download_to to track downloads
    with patch("kirin.file.File.download_to") as mock_download:
        with dataset.local_files() as local_files:
            # Iterating should not trigger downloads
            filenames = list(local_files)
            assert set(filenames) == {"file1.txt", "file2.txt"}
            mock_download.assert_not_called()

            # keys() should also not trigger downloads
            keys = list(local_files.keys())
            assert set(keys) == {"file1.txt", "file2.txt"}
            mock_download.assert_not_called()


def test_local_files_caching(temp_dir):
    """Test that downloaded files are cached for fast repeated access."""
    from unittest.mock import patch

    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add file
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")

    dataset.commit("Add file", add_files=[file1])

    with patch("kirin.file.File.download_to") as mock_download:
        with dataset.local_files() as local_files:
            # First access should download
            path1 = local_files["file1.txt"]
            mock_download.assert_called_once()

            # Second access should use cache (no additional download)
            path2 = local_files["file1.txt"]
            assert mock_download.call_count == 1  # Still only called once
            assert path1 == path2  # Same path returned


def test_local_files_key_error(temp_dir):
    """Test that accessing non-existent file raises KeyError."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add one file
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    dataset.commit("Add file", add_files=[file1])

    with dataset.local_files() as local_files:
        # Accessing existing file should work
        assert "file1.txt" in local_files
        path = local_files["file1.txt"]
        assert Path(path).read_text() == "Content 1"

        # Accessing non-existent file should raise KeyError
        with pytest.raises(KeyError, match="File not found: nonexistent.txt"):
            local_files["nonexistent.txt"]


def test_local_files_get_method(temp_dir):
    """Test the get() method with default values."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add file
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    dataset.commit("Add file", add_files=[file1])

    with dataset.local_files() as local_files:
        # get() with existing file should return path
        path = local_files.get("file1.txt")
        assert path is not None
        assert Path(path).read_text() == "Content 1"

        # get() with non-existent file should return default
        default_path = local_files.get("nonexistent.txt", "default")
        assert default_path == "default"

        # get() with no default should return None
        none_path = local_files.get("nonexistent.txt")
        assert none_path is None


def test_local_files_dict_behavior(temp_dir):
    """Test that LazyLocalFiles behaves like a dictionary."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Add files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content 1")
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content 2")

    dataset.commit("Add files", add_files=[file1, file2])

    with dataset.local_files() as local_files:
        # Test len()
        assert len(local_files) == 2

        # Test 'in' operator
        assert "file1.txt" in local_files
        assert "file2.txt" in local_files
        assert "nonexistent.txt" not in local_files

        # Test values() and items() for downloaded files only
        path1 = local_files["file1.txt"]  # Download first file

        # values() should only return downloaded files
        values = list(local_files.values())
        assert len(values) == 1
        assert path1 in values

        # items() should only return downloaded files
        items = list(local_files.items())
        assert len(items) == 1
        assert ("file1.txt", path1) in items
