"""Tests for the storage layer."""

import tempfile
from pathlib import Path

import pytest

from kirin.storage import ContentStore


def test_content_store_creation(temp_dir):
    """Test creating a ContentStore instance."""
    store = ContentStore(temp_dir)

    assert store.root_dir == str(temp_dir)
    assert store.data_dir == f"{temp_dir}/data"
    assert store.fs is not None


def test_store_content(temp_dir):
    """Test storing content."""
    store = ContentStore(temp_dir)

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Verify content was stored
    assert store.exists(content_hash)
    assert store.retrieve(content_hash) == content


def test_store_file(temp_dir):
    """Test storing a file."""
    store = ContentStore(temp_dir)

    # Create test file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!")

    # Store file
    content_hash = store.store_file(test_file)

    # Verify file was stored
    assert store.exists(content_hash)
    assert store.retrieve(content_hash) == b"Hello, World!"


def test_store_duplicate_content(temp_dir):
    """Test storing duplicate content."""
    store = ContentStore(temp_dir)

    content = b"Hello, World!"

    # Store content twice
    hash1 = store.store_content(content)
    hash2 = store.store_content(content)

    # Should get same hash
    assert hash1 == hash2
    assert store.exists(hash1)
    assert store.exists(hash2)


def test_retrieve_content(temp_dir):
    """Test retrieving content."""
    store = ContentStore(temp_dir)

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Retrieve content
    retrieved = store.retrieve(content_hash)
    assert retrieved == content


def test_retrieve_nonexistent_content(temp_dir):
    """Test retrieving non-existent content."""
    store = ContentStore(temp_dir)

    with pytest.raises(FileNotFoundError):
        store.retrieve("nonexistent_hash")


def test_retrieve_to_file(temp_dir):
    """Test retrieving content to a file."""
    store = ContentStore(temp_dir)

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Retrieve to file
    target_path = Path(temp_dir) / "retrieved.txt"
    retrieved_path = store.retrieve_to_file(content_hash, target_path)

    assert Path(retrieved_path).exists()
    assert Path(retrieved_path).read_bytes() == content


def test_open_stream(temp_dir):
    """Test opening content as a stream."""
    store = ContentStore(temp_dir)

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Open as stream
    with store.open_stream(content_hash) as stream:
        assert stream.read() == content


def test_open_stream_text_mode(temp_dir):
    """Test opening content as text stream."""
    store = ContentStore(temp_dir)

    # Store text content
    content = "Hello, World!"
    content_bytes = content.encode("utf-8")
    content_hash = store.store_content(content_bytes)

    # Open as text stream
    with store.open_stream(content_hash, "r") as stream:
        assert stream.read() == content


def test_exists(temp_dir):
    """Test checking if content exists."""
    store = ContentStore(temp_dir)

    # Content doesn't exist initially
    assert not store.exists("nonexistent_hash")

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Content should exist now
    assert store.exists(content_hash)


def test_get_size(temp_dir):
    """Test getting content size."""
    store = ContentStore(temp_dir)

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Get size
    size = store.get_size(content_hash)
    assert size == len(content)


def test_get_size_nonexistent(temp_dir):
    """Test getting size of non-existent content."""
    store = ContentStore(temp_dir)

    with pytest.raises(FileNotFoundError):
        store.get_size("nonexistent_hash")


def test_list_hashes(temp_dir):
    """Test listing content hashes."""
    store = ContentStore(temp_dir)

    # Initially empty
    assert store.list_hashes() == []

    # Store multiple contents
    content1 = b"Hello"
    content2 = b"World"

    hash1 = store.store_content(content1)
    hash2 = store.store_content(content2)

    # List hashes
    hashes = store.list_hashes()
    assert len(hashes) == 2
    assert hash1 in hashes
    assert hash2 in hashes


def test_cleanup_orphaned_files(temp_dir):
    """Test cleaning up orphaned files."""
    store = ContentStore(temp_dir)

    # Store some content
    content1 = b"Hello"
    content2 = b"World"

    hash1 = store.store_content(content1)
    hash2 = store.store_content(content2)

    # Cleanup with only hash1 in use
    used_hashes = {hash1}
    removed_count = store.cleanup_orphaned_files(used_hashes)

    # Should remove hash2
    assert removed_count == 1
    assert store.exists(hash1)
    assert not store.exists(hash2)


def test_cleanup_no_orphaned_files(temp_dir):
    """Test cleanup when no files are orphaned."""
    store = ContentStore(temp_dir)

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Cleanup with all hashes in use
    used_hashes = {content_hash}
    removed_count = store.cleanup_orphaned_files(used_hashes)

    # Should remove nothing
    assert removed_count == 0
    assert store.exists(content_hash)


def test_storage_path_structure(temp_dir):
    """Test that files are stored in the correct directory structure."""
    store = ContentStore(temp_dir)

    # Store content
    content = b"Hello, World!"
    content_hash = store.store_content(content)

    # Check that file is stored at data/{hash[:2]}/{hash[2:]}
    expected_path = Path(temp_dir) / "data" / content_hash[:2] / content_hash[2:]
    assert expected_path.exists()
    assert expected_path.read_bytes() == content


def test_store_file_nonexistent(temp_dir):
    """Test storing non-existent file."""
    store = ContentStore(temp_dir)

    nonexistent_file = Path(temp_dir) / "nonexistent.txt"

    with pytest.raises(FileNotFoundError):
        store.store_file(nonexistent_file)


def test_store_file_with_different_filesystem(temp_dir):
    """Test storing file from different filesystem."""
    store = ContentStore(temp_dir)

    # Create file in a subdirectory
    subdir = Path(temp_dir) / "subdir"
    subdir.mkdir()
    test_file = subdir / "test.txt"
    test_file.write_text("Hello, World!")

    # Store file (should work with different path)
    content_hash = store.store_file(test_file)

    # Verify content
    assert store.exists(content_hash)
    assert store.retrieve(content_hash) == b"Hello, World!"
