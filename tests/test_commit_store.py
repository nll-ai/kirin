"""Tests for the commit store."""

import json
from datetime import datetime
from pathlib import Path

from kirin.commit import Commit
from kirin.commit_store import CommitStore
from kirin.file import File


def test_commit_store_creation(temp_dir):
    """Test creating a CommitStore instance."""
    store = CommitStore(temp_dir, "test_dataset")

    assert store.root_dir == str(temp_dir)
    assert store.dataset_name == "test_dataset"
    assert store.dataset_dir == f"{temp_dir}/datasets/test_dataset"
    assert store.commits_file == f"{temp_dir}/datasets/test_dataset/commits.json"
    assert store.is_empty()


def test_save_commit(temp_dir):
    """Test saving a commit."""
    store = CommitStore(temp_dir, "test_dataset")

    # Create a commit
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=datetime.now(), parent_hash=None
    )

    # Save commit
    store.save_commit(commit)

    # Verify commit was saved
    assert not store.is_empty()
    assert store.get_commit_count() == 1
    assert store.has_commit("abc123")


def test_get_commit(temp_dir):
    """Test getting a commit."""
    store = CommitStore(temp_dir, "test_dataset")

    # Create and save commit
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=datetime.now(), parent_hash=None
    )
    store.save_commit(commit)

    # Get commit
    retrieved = store.get_commit("abc123")
    assert retrieved is not None
    assert retrieved.hash == "abc123"
    assert retrieved.message == "Test commit"


def test_get_commit_nonexistent(temp_dir):
    """Test getting non-existent commit."""
    store = CommitStore(temp_dir, "test_dataset")

    assert store.get_commit("nonexistent") is None


def test_get_commit_partial_hash(temp_dir):
    """Test getting commit with partial hash."""
    store = CommitStore(temp_dir, "test_dataset")

    # Create and save commit
    commit = Commit(
        hash="abc123def456",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash=None,
    )
    store.save_commit(commit)

    # Get with partial hash
    retrieved = store.get_commit("abc123")
    assert retrieved is not None
    assert retrieved.hash == "abc123def456"


def test_get_latest_commit(temp_dir):
    """Test getting the latest commit."""
    store = CommitStore(temp_dir, "test_dataset")

    # Initially no commits
    assert store.get_latest_commit() is None

    # Add commits
    commit1 = Commit(
        hash="commit1",
        message="First commit",
        timestamp=datetime.now(),
        parent_hash=None,
    )
    store.save_commit(commit1)

    commit2 = Commit(
        hash="commit2",
        message="Second commit",
        timestamp=datetime.now(),
        parent_hash="commit1",
    )
    store.save_commit(commit2)

    # Latest should be commit2
    latest = store.get_latest_commit()
    assert latest is not None
    assert latest.hash == "commit2"


def test_get_commit_history(temp_dir):
    """Test getting commit history."""
    store = CommitStore(temp_dir, "test_dataset")

    # Add commits
    commit1 = Commit(
        hash="commit1",
        message="First commit",
        timestamp=datetime.now(),
        parent_hash=None,
    )
    store.save_commit(commit1)

    commit2 = Commit(
        hash="commit2",
        message="Second commit",
        timestamp=datetime.now(),
        parent_hash="commit1",
    )
    store.save_commit(commit2)

    # Get history
    history = store.get_commit_history()
    assert len(history) == 2
    assert history[0].hash == "commit2"  # Newest first
    assert history[1].hash == "commit1"


def test_get_commit_history_with_limit(temp_dir):
    """Test getting commit history with limit."""
    store = CommitStore(temp_dir, "test_dataset")

    # Add multiple commits
    for i in range(5):
        commit = Commit(
            hash=f"commit{i}",
            message=f"Commit {i}",
            timestamp=datetime.now(),
            parent_hash=f"commit{i - 1}" if i > 0 else None,
        )
        store.save_commit(commit)

    # Get limited history
    history = store.get_commit_history(limit=3)
    assert len(history) == 3
    assert history[0].hash == "commit4"  # Newest first


def test_get_commits(temp_dir):
    """Test getting all commits."""
    store = CommitStore(temp_dir, "test_dataset")

    # Add commits
    commit1 = Commit(
        hash="commit1",
        message="First commit",
        timestamp=datetime.now(),
        parent_hash=None,
    )
    store.save_commit(commit1)

    commit2 = Commit(
        hash="commit2",
        message="Second commit",
        timestamp=datetime.now(),
        parent_hash="commit1",
    )
    store.save_commit(commit2)

    # Get all commits
    commits = store.get_commits()
    assert len(commits) == 2

    # Check that both commits are present
    commit_hashes = {commit.hash for commit in commits}
    assert "commit1" in commit_hashes
    assert "commit2" in commit_hashes


def test_has_commit(temp_dir):
    """Test checking if commit exists."""
    store = CommitStore(temp_dir, "test_dataset")

    # Initially no commits
    assert not store.has_commit("nonexistent")

    # Add commit
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=datetime.now(), parent_hash=None
    )
    store.save_commit(commit)

    # Check existence
    assert store.has_commit("abc123")
    assert not store.has_commit("nonexistent")


def test_get_commit_count(temp_dir):
    """Test getting commit count."""
    store = CommitStore(temp_dir, "test_dataset")

    # Initially empty
    assert store.get_commit_count() == 0

    # Add commits
    for i in range(3):
        commit = Commit(
            hash=f"commit{i}",
            message=f"Commit {i}",
            timestamp=datetime.now(),
            parent_hash=f"commit{i - 1}" if i > 0 else None,
        )
        store.save_commit(commit)

    # Check count
    assert store.get_commit_count() == 3


def test_is_empty(temp_dir):
    """Test checking if store is empty."""
    store = CommitStore(temp_dir, "test_dataset")

    # Initially empty
    assert store.is_empty()

    # Add commit
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=datetime.now(), parent_hash=None
    )
    store.save_commit(commit)

    # Should not be empty
    assert not store.is_empty()


def test_cleanup_orphaned_files(temp_dir):
    """Test cleaning up orphaned files."""
    store = CommitStore(temp_dir, "test_dataset")

    # Create some files in storage
    content1 = b"Hello"
    content2 = b"World"

    hash1 = store.storage.store_content(content1)
    hash2 = store.storage.store_content(content2)

    # Create commit with only hash1
    file1 = File(hash=hash1, name="file1.txt", size=len(content1))
    commit = Commit(
        hash="commit1",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash=None,
        files={"file1.txt": file1},
    )
    store.save_commit(commit)

    # Cleanup orphaned files
    removed_count = store.cleanup_orphaned_files()

    # Should remove hash2 (not referenced by any commit)
    assert removed_count == 1
    assert store.storage.exists(hash1)
    assert not store.storage.exists(hash2)


def test_get_dataset_info(temp_dir):
    """Test getting dataset information."""
    store = CommitStore(temp_dir, "test_dataset")

    # Empty dataset - check basic properties
    assert store.dataset_name == "test_dataset"
    assert store.get_commit_count() == 0
    assert store.get_latest_commit() is None

    # Add commit
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=datetime.now(), parent_hash=None
    )
    store.save_commit(commit)

    # Dataset with commit - check basic properties
    assert store.dataset_name == "test_dataset"
    assert store.get_commit_count() == 1
    latest_commit = store.get_latest_commit()
    assert latest_commit is not None
    assert latest_commit.hash == "abc123"
    assert latest_commit.message == "Test commit"


def test_persistence(temp_dir):
    """Test that commits are persisted to disk."""
    store = CommitStore(temp_dir, "test_dataset")

    # Add commit
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=datetime.now(), parent_hash=None
    )
    store.save_commit(commit)

    # Create new store instance (should load from disk)
    new_store = CommitStore(temp_dir, "test_dataset")

    # Should have the same commit
    assert new_store.get_commit_count() == 1
    assert new_store.has_commit("abc123")

    retrieved = new_store.get_commit("abc123")
    assert retrieved is not None
    assert retrieved.message == "Test commit"


def test_json_file_structure(temp_dir):
    """Test that commits are stored in correct JSON structure."""
    store = CommitStore(temp_dir, "test_dataset")

    # Add commit
    commit = Commit(
        hash="abc123", message="Test commit", timestamp=datetime.now(), parent_hash=None
    )
    store.save_commit(commit)

    # Check JSON file structure
    commits_file = Path(temp_dir) / "datasets" / "test_dataset" / "commits.json"
    assert commits_file.exists()

    with open(commits_file) as f:
        data = json.load(f)

    assert data["dataset_name"] == "test_dataset"
    assert len(data["commits"]) == 1

    commit_data = data["commits"][0]
    assert commit_data["hash"] == "abc123"
    assert commit_data["message"] == "Test commit"
    assert commit_data["parent_hash"] is None
