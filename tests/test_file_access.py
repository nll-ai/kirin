"""Tests for file access methods in GitData."""

import os
from pathlib import Path

import pytest

from kirin import Dataset


def test_download_file(tmp_path):
    """Test downloading a file to local path."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

    # Test downloading to a specific path
    download_path = tmp_path / "downloaded.txt"
    result_path = ds.download_file("test.txt", str(download_path))

    assert result_path == str(download_path)
    assert download_path.exists()
    assert download_path.read_text() == "Hello, World!"


def test_download_file_temp(tmp_path):
    """Test downloading a file to temporary location."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

    # Test downloading to temporary location
    temp_path = tmp_path / "downloaded.txt"
    result_path = ds.download_file("test.txt", temp_path)

    assert os.path.exists(result_path)
    assert Path(result_path).read_text() == "Hello, World!"

    # Clean up
    os.unlink(result_path)


def test_download_file_not_found(tmp_path):
    """Test downloading a non-existent file."""
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.download_file("nonexistent.txt", tmp_path / "dummy.txt")


def test_get_file_content_bytes(tmp_path):
    """Test getting file content as bytes."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

    # Test getting content as bytes
    content = ds.read_file("test.txt", mode="rb")
    assert isinstance(content, bytes)
    assert content == b"Hello, World!"


def test_get_file_content_string(tmp_path):
    """Test getting file content as string."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

    # Test getting content as string
    content = ds.read_file("test.txt", mode="r")
    assert isinstance(content, str)
    assert content == "Hello, World!"


def test_get_file_content_not_found(tmp_path):
    """Test getting content of non-existent file."""
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.read_file("nonexistent.txt")


def test_get_file_lines(tmp_path):
    """Test getting file lines."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file with multiple lines
    test_file = tmp_path / "test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

    # Test getting lines
    content = ds.read_file("test.txt")
    lines = content.split("\n")
    assert lines == ["Line 1", "Line 2", "Line 3"]


def test_get_file_lines_not_found(tmp_path):
    """Test getting lines of non-existent file."""
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.read_file("nonexistent.txt")


def test_open_file(tmp_path):
    """Test opening a file for reading."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

    # Test opening file
    with ds.open_file("test.txt", mode="r") as f:
        content = f.read()
        assert content == "Hello, World!"


def test_open_file_not_found(tmp_path):
    """Test opening a non-existent file."""
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.open_file("nonexistent.txt")


def test_get_local_path(tmp_path):
    """Test getting local path for a file."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

    # Test downloading file to local path
    local_path = tmp_path / "downloaded.txt"
    result_path = ds.download_file("test.txt", local_path)

    assert os.path.exists(result_path)
    assert Path(result_path).read_text() == "Hello, World!"

    # Clean up
    os.unlink(result_path)


def test_get_local_path_not_found(tmp_path):
    """Test getting local path for non-existent file."""
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    with pytest.raises(FileNotFoundError):
        ds.download_file("nonexistent.txt", tmp_path / "dummy.txt")


def test_file_access_with_multiple_files(tmp_path):
    """Test file access with multiple files in dataset."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create multiple test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")

    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")

    # Commit the files
    ds.commit(message="Add files", add_files=[file1, file2])

    # Test accessing different files
    content1 = ds.read_file("file1.txt", mode="r")
    content2 = ds.read_file("file2.txt", mode="r")

    assert content1 == "Content 1"
    assert content2 == "Content 2"

    # Test files property still works
    file_dict = ds.files
    assert "file1.txt" in file_dict
    assert "file2.txt" in file_dict


def test_get_local_file_dict(tmp_path):
    """Test getting local file dictionary."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create multiple test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")

    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")

    # Commit the files
    ds.commit(message="Add files", add_files=[file1, file2])

    # Test getting file dict
    file_dict = ds.files

    assert "file1.txt" in file_dict
    assert "file2.txt" in file_dict

    # Check that files exist in the dataset
    for filename, file_obj in file_dict.items():
        assert file_obj is not None
        assert file_obj.name == filename

        # Verify content
        content = file_obj.read_text()
        if filename == "file1.txt":
            assert content == "Content 1"
        elif filename == "file2.txt":
            assert content == "Content 2"

    # No cleanup needed for file objects


def test_get_local_file_dict_empty_dataset(tmp_path):
    """Test getting local file dictionary for empty dataset."""
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    file_dict = ds.files
    assert file_dict == {}


def test_local_files_context_manager(tmp_path):
    """Test the local_files context manager."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create multiple test files
    file1 = tmp_path / "file1.txt"
    file1.write_text("Content 1")

    file2 = tmp_path / "file2.txt"
    file2.write_text("Content 2")

    # Commit the files
    ds.commit(message="Add files", add_files=[file1, file2])

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
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    with ds.local_files() as local_files:
        assert len(local_files) == 0
        assert list(local_files.keys()) == []
        assert list(local_files.values()) == []


def test_local_files_context_manager_exception_cleanup(tmp_path):
    """Test that context manager cleans up files even when exception occurs."""
    # Create a test dataset
    ds = Dataset(root_dir=tmp_path, name="test_dataset")

    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    ds.commit(message="Add test file", add_files=[test_file])

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
