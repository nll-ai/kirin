"""Tests for the Commit entity class."""

from datetime import datetime

import pytest

from kirin.commit import Commit, CommitBuilder
from kirin.file import File
from kirin.storage import ContentStore


def test_commit_creation():
    """Test creating a Commit instance."""
    commit = Commit(
        hash="abc123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash="def456",
    )

    assert commit.hash == "abc123"
    assert commit.message == "Test commit"
    assert commit.parent_hash == "def456"
    assert not commit.is_initial
    assert commit.short_hash == "abc123"[:8]


def test_initial_commit():
    """Test creating an initial commit."""
    commit = Commit(
        hash="abc123",
        message="Initial commit",
        timestamp=datetime.now(),
        parent_hash=None,
    )

    assert commit.is_initial
    assert commit.parent_hash is None


def test_commit_validation():
    """Test commit validation."""
    # Empty hash should raise error
    with pytest.raises(ValueError, match="Commit hash cannot be empty"):
        Commit(hash="", message="Test", timestamp=datetime.now(), parent_hash=None)

    # Empty message should raise error
    with pytest.raises(ValueError, match="Commit message cannot be empty"):
        Commit(hash="abc123", message="", timestamp=datetime.now(), parent_hash=None)

    # None timestamp should raise error
    with pytest.raises(ValueError, match="Commit timestamp cannot be None"):
        Commit(hash="abc123", message="Test", timestamp=None, parent_hash=None)


def test_commit_with_files(temp_dir):
    """Test commit with files."""
    storage = ContentStore(temp_dir)

    # Create test files
    file1 = File(hash="hash1", name="file1.txt", size=100, _storage=storage)
    file2 = File(hash="hash2", name="file2.txt", size=200, _storage=storage)

    files = {"file1.txt": file1, "file2.txt": file2}

    commit = Commit(
        hash="abc123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash=None,
        files=files,
    )

    assert commit.get_file_count() == 2
    assert commit.get_total_size() == 300
    assert commit.list_files() == ["file1.txt", "file2.txt"]
    assert commit.has_file("file1.txt")
    assert not commit.has_file("nonexistent.txt")
    assert commit.get_file("file1.txt") == file1
    assert commit.get_file("nonexistent.txt") is None


def test_commit_to_dict():
    """Test converting commit to dictionary."""
    timestamp = datetime.now()
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=timestamp, parent_hash="def456"
    )

    data = commit.to_dict()
    expected = {
        "hash": "abc123",
        "message": "Test commit",
        "timestamp": timestamp.isoformat(),
        "parent_hash": "def456",
        "files": {},
    }

    assert data == expected


def test_commit_from_dict():
    """Test creating commit from dictionary."""
    timestamp = datetime.now()
    data = {
        "hash": "abc123",
        "message": "Test commit",
        "timestamp": timestamp.isoformat(),
        "parent_hash": "def456",
        "files": {},
    }

    commit = Commit.from_dict(data)

    assert commit.hash == "abc123"
    assert commit.message == "Test commit"
    assert commit.timestamp == timestamp
    assert commit.parent_hash == "def456"


def test_commit_string_representations():
    """Test string representations of commit."""
    commit = Commit(
        hash="abc123",
        message="Test commit message",
        timestamp=datetime.now(),
        parent_hash=None,
    )

    str_repr = str(commit)
    assert "Commit(abc123:" in str_repr
    assert "Test commit message" in str_repr

    repr_str = repr(commit)
    assert "Commit(hash='abc123'" in repr_str
    assert "message='Test commit message'" in repr_str


def test_commit_builder_initial():
    """Test building initial commit."""
    builder = CommitBuilder()

    # Add a file
    file = File(hash="hash1", name="file1.txt", size=100)
    builder.add_file("file1.txt", file)

    commit = builder.build("Initial commit")

    assert commit.is_initial
    assert commit.message == "Initial commit"
    assert commit.get_file_count() == 1
    assert commit.has_file("file1.txt")


def test_commit_builder_with_parent():
    """Test building commit with parent."""
    # Create parent commit
    parent_file = File(hash="parent_hash", name="parent.txt", size=50)
    parent_commit = Commit(
        hash="parent123",
        message="Parent commit",
        timestamp=datetime.now(),
        parent_hash=None,
        files={"parent.txt": parent_file},
    )

    builder = CommitBuilder(parent_commit)

    # Add new file
    new_file = File(hash="new_hash", name="new.txt", size=75)
    builder.add_file("new.txt", new_file)

    # Remove parent file
    builder.remove_file("parent.txt")

    commit = builder.build("Child commit")

    assert not commit.is_initial
    assert commit.parent_hash == "parent123"
    assert commit.message == "Child commit"
    assert commit.get_file_count() == 1
    assert commit.has_file("new.txt")
    assert not commit.has_file("parent.txt")


def test_commit_builder_changes():
    """Test commit builder change tracking."""
    builder = CommitBuilder()

    # Add files
    file1 = File(hash="hash1", name="file1.txt", size=100)
    file2 = File(hash="hash2", name="file2.txt", size=200)

    builder.add_file("file1.txt", file1)
    builder.add_file("file2.txt", file2)
    builder.remove_file("file1.txt")  # Remove it again

    changes = builder.get_changes()

    assert set(changes["added_files"]) == {"file1.txt", "file2.txt"}
    assert changes["removed_files"] == ["file1.txt"]
    assert changes["total_files"] == 1
    assert changes["is_initial"] is True


def test_commit_builder_custom_hash():
    """Test building commit with custom hash."""
    builder = CommitBuilder()

    file = File(hash="hash1", name="file1.txt", size=100)
    builder.add_file("file1.txt", file)

    custom_hash = "custom123"
    commit = builder.build("Test commit", custom_hash)

    assert commit.hash == custom_hash


def test_commit_builder_method_chaining():
    """Test commit builder method chaining."""
    builder = CommitBuilder()

    file1 = File(hash="hash1", name="file1.txt", size=100)
    file2 = File(hash="hash2", name="file2.txt", size=200)

    # Chain method calls
    builder.add_file("file1.txt", file1).add_file("file2.txt", file2).remove_file(
        "file1.txt"
    )

    commit = builder.build("Chained commit")

    assert commit.get_file_count() == 1
    assert commit.has_file("file2.txt")
    assert not commit.has_file("file1.txt")
