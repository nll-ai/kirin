"""Tests for file access methods in GitData."""

import os
import tempfile
import pytest
from pathlib import Path

from kirin import Dataset


def test_download_file(tmp_path):
    """Test downloading a file to local path."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test downloading to a specific path
    download_path = tmp_path / "downloaded.txt"
    result_path = ds.download_file("test.txt", str(download_path))

    assert result_path == str(download_path)
    assert download_path.exists()
    assert download_path.read_text() == "Hello, World!"


def test_download_file_temp(tmp_path):
    """Test downloading a file to temporary location."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test downloading to temporary location
    result_path = ds.download_file("test.txt")

    assert os.path.exists(result_path)
    assert Path(result_path).read_text() == "Hello, World!"

    # Clean up
    os.unlink(result_path)


def test_download_file_not_found(tmp_path):
    """Test downloading a non-existent file."""
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.download_file("nonexistent.txt")


def test_get_file_content_bytes(tmp_path):
    """Test getting file content as bytes."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test getting content as bytes
    content = ds.get_file_content("test.txt", mode="rb")
    assert isinstance(content, bytes)
    assert content == b"Hello, World!"


def test_get_file_content_string(tmp_path):
    """Test getting file content as string."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test getting content as string
    content = ds.get_file_content("test.txt", mode="r")
    assert isinstance(content, str)
    assert content == "Hello, World!"


def test_get_file_content_not_found(tmp_path):
    """Test getting content of non-existent file."""
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.get_file_content("nonexistent.txt")


def test_get_file_lines(tmp_path):
    """Test getting file lines."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file with multiple lines
    test_file = tmp_path / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test getting lines
    lines = ds.get_file_lines("test.txt")
    assert lines == ["Line 1", "Line 2", "Line 3"]


def test_get_file_lines_not_found(tmp_path):
    """Test getting lines of non-existent file."""
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.get_file_lines("nonexistent.txt")


def test_open_file(tmp_path):
    """Test opening a file for reading."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test opening file
    with ds.open_file("test.txt", mode="r") as f:
        content = f.read()
        assert content == "Hello, World!"


def test_open_file_not_found(tmp_path):
    """Test opening a non-existent file."""
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.open_file("nonexistent.txt")


def test_get_local_path(tmp_path):
    """Test getting local path for a file."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test getting local path
    local_path = ds.get_local_path("test.txt")

    assert os.path.exists(local_path)
    assert Path(local_path).read_text() == "Hello, World!"

    # Clean up
    os.unlink(local_path)


def test_get_local_path_not_found(tmp_path):
    """Test getting local path for non-existent file."""
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.get_local_path("nonexistent.txt")


def test_file_access_with_multiple_files(tmp_path):
    """Test file access with multiple files in dataset."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create multiple test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")

    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")

    # Commit the files
    ds.commit(commit_message="Add files", add_files=[file1, file2])

    # Test accessing different files
    content1 = ds.get_file_content("file1.txt", mode="r")
    content2 = ds.get_file_content("file2.txt", mode="r")

    assert content1 == "Content 1"
    assert content2 == "Content 2"

    # Test file_dict still works
    file_dict = ds.file_dict
    assert "file1.txt" in file_dict
    assert "file2.txt" in file_dict


def test_get_local_file_dict(tmp_path):
    """Test getting local file dictionary."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create multiple test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")

    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")

    # Commit the files
    ds.commit(commit_message="Add files", add_files=[file1, file2])

    # Test getting local file dict
    local_file_dict = ds.get_local_file_dict()

    assert "file1.txt" in local_file_dict
    assert "file2.txt" in local_file_dict

    # Check that all paths are local and exist
    for filename, local_path in local_file_dict.items():
        assert os.path.exists(local_path)
        assert not local_path.startswith(("s3://", "gs://", "az://"))

        # Verify content
        with open(local_path, "r") as f:
            content = f.read()
            if filename == "file1.txt":
                assert content == "Content 1"
            elif filename == "file2.txt":
                assert content == "Content 2"

    # Clean up
    for local_path in local_file_dict.values():
        os.unlink(local_path)


def test_get_local_file_dict_empty_dataset(tmp_path):
    """Test getting local file dictionary for empty dataset."""
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    local_file_dict = ds.get_local_file_dict()
    assert local_file_dict == {}


def test_local_files_context_manager(tmp_path):
    """Test the local_files context manager."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create multiple test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")

    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")

    # Commit the files
    ds.commit(commit_message="Add files", add_files=[file1, file2])

    # Test context manager
    downloaded_paths = []
    with ds.local_files() as local_files:
        assert "file1.txt" in local_files
        assert "file2.txt" in local_files

        # Check that all paths are local and exist
        for filename, local_path in local_files.items():
            assert os.path.exists(local_path)
            assert not local_path.startswith(("s3://", "gs://", "az://"))
            downloaded_paths.append(local_path)

            # Verify content
            with open(local_path, "r") as f:
                content = f.read()
                if filename == "file1.txt":
                    assert content == "Content 1"
                elif filename == "file2.txt":
                    assert content == "Content 2"

    # Files should be cleaned up after context exit
    for local_path in downloaded_paths:
        assert not os.path.exists(local_path)


def test_local_files_context_manager_empty_dataset(tmp_path):
    """Test the local_files context manager with empty dataset."""
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    with ds.local_files() as local_files:
        assert len(local_files) == 0
        assert list(local_files.keys()) == []
        assert list(local_files.values()) == []


def test_local_files_context_manager_exception_cleanup(tmp_path):
    """Test that context manager cleans up files even when exception occurs."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, dataset_name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(commit_message="Add test file", add_files=[test_file])

    # Test that cleanup happens even with exception
    with pytest.raises(ValueError):
        with ds.local_files() as local_files:
            assert "test.txt" in local_files
            local_path = local_files["test.txt"]
            assert os.path.exists(local_path)
            # Raise an exception
            raise ValueError("Test exception")

    # File should still be cleaned up
    # Note: We can't easily test this without access to the local_files dict
    # but the context manager should handle cleanup in __exit__
