"""Tests for the File entity class."""

import tempfile

import pytest

from kirin.file import File
from kirin.storage import ContentStore


def test_file_creation():
    """Test creating a File instance."""
    file = File(hash="abc123", name="test.txt", size=100, content_type="text/plain")

    assert file.hash == "abc123"
    assert file.name == "test.txt"
    assert file.size == 100
    assert file.content_type == "text/plain"
    assert file.path == "test.txt"


def test_file_validation():
    """Test file validation."""
    # Empty hash should raise error
    with pytest.raises(ValueError, match="File hash cannot be empty"):
        File(hash="", name="test.txt", size=100)

    # Empty name should raise error
    with pytest.raises(ValueError, match="File name cannot be empty"):
        File(hash="abc123", name="", size=100)

    # Negative size should raise error
    with pytest.raises(ValueError, match="File size cannot be negative"):
        File(hash="abc123", name="test.txt", size=-1)


def test_file_properties():
    """Test file properties."""
    file = File(hash="abc123", name="test.txt", size=100)

    assert file.path == "test.txt"
    assert file.short_hash == "abc123"[:8]


def test_file_with_storage(temp_dir):
    """Test file operations with storage."""
    # Create storage
    storage = ContentStore(temp_dir)

    # Create test content
    test_content = b"Hello, World!"
    content_hash = storage.store_content(test_content, "test.txt")

    # Create file with storage
    file = File(
        hash=content_hash, name="test.txt", size=len(test_content), _storage=storage
    )

    # Test reading content
    assert file.read_bytes() == test_content
    assert file.read_text() == "Hello, World!"
    assert file.exists()


def test_file_download(temp_dir):
    """Test downloading file to local path."""
    storage = ContentStore(temp_dir)

    # Create test content
    test_content = b"Hello, World!"
    content_hash = storage.store_content(test_content, "test.txt")

    file = File(
        hash=content_hash, name="test.txt", size=len(test_content), _storage=storage
    )

    # Download to temporary file
    with tempfile.NamedTemporaryFile() as temp_file:
        downloaded_path = file.download_to(temp_file.name)

        # Verify content
        with open(downloaded_path, "rb") as f:
            assert f.read() == test_content


def test_file_open(temp_dir):
    """Test opening file for reading."""
    storage = ContentStore(temp_dir)

    # Create test content
    test_content = b"Hello, World!"
    content_hash = storage.store_content(test_content, "test.txt")

    file = File(
        hash=content_hash, name="test.txt", size=len(test_content), _storage=storage
    )

    # Test binary mode
    with file.open("rb") as f:
        assert f.read() == test_content

    # Test text mode
    with file.open("r") as f:
        assert f.read() == "Hello, World!"


def test_file_without_storage():
    """Test file operations without storage."""
    file = File(hash="abc123", name="test.txt", size=100)

    # Operations should raise RuntimeError
    with pytest.raises(RuntimeError, match="File not associated with storage"):
        file.read_bytes()

    with pytest.raises(RuntimeError, match="File not associated with storage"):
        file.open()


def test_file_to_dict():
    """Test converting file to dictionary."""
    file = File(hash="abc123", name="test.txt", size=100, content_type="text/plain")

    data = file.to_dict()
    expected = {
        "hash": "abc123",
        "name": "test.txt",
        "size": 100,
        "content_type": "text/plain",
    }

    assert data == expected


def test_file_from_dict():
    """Test creating file from dictionary."""
    data = {
        "hash": "abc123",
        "name": "test.txt",
        "size": 100,
        "content_type": "text/plain",
    }

    file = File.from_dict(data)

    assert file.hash == "abc123"
    assert file.name == "test.txt"
    assert file.size == 100
    assert file.content_type == "text/plain"


def test_file_from_dict_with_storage(temp_dir):
    """Test creating file from dictionary with storage."""
    storage = ContentStore(temp_dir)

    data = {
        "hash": "abc123",
        "name": "test.txt",
        "size": 100,
        "content_type": "text/plain",
    }

    file = File.from_dict(data, storage)

    assert file.hash == "abc123"
    assert file.name == "test.txt"
    assert file.size == 100
    assert file.content_type == "text/plain"
    # Storage association is internal, so we can't directly test it


def test_file_string_representations():
    """Test string representations of file."""
    file = File(hash="abc123", name="test.txt", size=100)

    str_repr = str(file)
    assert "File(name='test.txt'" in str_repr
    assert "hash='abc123'" in str_repr
    assert "size=100" in str_repr

    repr_str = repr(file)
    assert "File(hash='abc123'" in repr_str
    assert "name='test.txt'" in repr_str
    assert "size=100" in repr_str
