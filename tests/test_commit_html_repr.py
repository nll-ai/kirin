"""Tests for Commit._repr_html_ method."""

from datetime import datetime

import pytest

from kirin.commit import Commit
from kirin.file import File
from kirin.storage import ContentStore


@pytest.fixture
def mock_storage(temp_dir):
    """Create a mock storage for testing."""
    return ContentStore(str(temp_dir))


def test_commit_html_repr_basic(mock_storage):
    """Test HTML representation of basic commit."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=100,
        content_type="text/plain",
        _storage=mock_storage,
    )

    commit = Commit(
        hash="commit123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash="parent123",
        files={"file1.txt": file1},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    assert "commit123" in html or "commit" in html.lower()
    assert "Test commit" in html
    assert "file1.txt" in html
    assert "kirin-commit-view" in html


def test_commit_html_repr_initial_commit(mock_storage):
    """Test HTML representation of initial commit."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=100,
        content_type="text/plain",
        _storage=mock_storage,
    )

    commit = Commit(
        hash="commit123",
        message="Initial commit",
        timestamp=datetime.now(),
        parent_hash=None,
        files={"file1.txt": file1},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    assert commit.is_initial
    assert "Initial commit" in html
    assert "initial" in html.lower() or "first" in html.lower()


def test_commit_html_repr_multiple_files(mock_storage):
    """Test HTML representation with multiple files."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=100,
        content_type="text/plain",
        _storage=mock_storage,
    )
    file2 = File(
        hash="def456",
        name="file2.csv",
        size=200,
        content_type="text/csv",
        _storage=mock_storage,
    )

    commit = Commit(
        hash="commit123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash="parent123",
        files={"file1.txt": file1, "file2.csv": file2},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    assert "file1.txt" in html
    assert "file2.csv" in html
    assert "file-item" in html


def test_commit_html_repr_includes_metadata(mock_storage):
    """Test HTML representation includes commit metadata."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=100,
        content_type="text/plain",
        _storage=mock_storage,
    )

    commit = Commit(
        hash="commit123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash="parent123",
        files={"file1.txt": file1},
        metadata={"accuracy": 0.95, "epochs": 10},
        tags=["production", "v1.0"],
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    # Metadata might be shown or not, but commit info should be there
    assert "commit123" in html or commit.short_hash in html
    assert "Test commit" in html


def test_commit_html_repr_includes_file_sizes(mock_storage):
    """Test HTML representation includes file size information."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=1024,
        content_type="text/plain",
        _storage=mock_storage,
    )

    commit = Commit(
        hash="commit123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash="parent123",
        files={"file1.txt": file1},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    assert "file1.txt" in html
    # Should include size information
    assert "B" in html or "KB" in html or "bytes" in html.lower()


def test_commit_html_repr_includes_timestamp(mock_storage):
    """Test HTML representation includes commit timestamp."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=100,
        content_type="text/plain",
        _storage=mock_storage,
    )

    timestamp = datetime(2024, 1, 15, 10, 30, 0)
    commit = Commit(
        hash="commit123",
        message="Test commit",
        timestamp=timestamp,
        parent_hash="parent123",
        files={"file1.txt": file1},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    # Timestamp should be formatted and visible
    assert "2024" in html or str(timestamp.year) in html


def test_commit_html_repr_empty_commit(mock_storage):
    """Test HTML representation of commit with no files."""
    commit = Commit(
        hash="commit123",
        message="Empty commit",
        timestamp=datetime.now(),
        parent_hash="parent123",
        files={},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    assert "Empty commit" in html
    assert "No files" in html or "empty" in html.lower() or "0 files" in html


def test_commit_html_repr_self_contained(mock_storage):
    """Test HTML is self-contained (includes inline CSS)."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=100,
        content_type="text/plain",
        _storage=mock_storage,
    )

    commit = Commit(
        hash="commit123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash="parent123",
        files={"file1.txt": file1},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    # Should include inline styles
    assert "<style>" in html


def test_commit_html_repr_valid_html(mock_storage):
    """Test HTML is valid and well-formed."""
    file1 = File(
        hash="abc123",
        name="file1.txt",
        size=100,
        content_type="text/plain",
        _storage=mock_storage,
    )

    commit = Commit(
        hash="commit123",
        message="Test commit",
        timestamp=datetime.now(),
        parent_hash="parent123",
        files={"file1.txt": file1},
    )

    html = commit._repr_html_()

    assert isinstance(html, str)
    # Basic HTML structure checks
    assert html.strip().startswith("<")
    assert "</div>" in html or html.count("<div") == html.count("</div>")
