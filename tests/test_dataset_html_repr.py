"""Tests for Dataset._repr_html_ method."""

from pathlib import Path

from kirin.dataset import Dataset


def test_dataset_html_repr_empty_dataset(temp_dir):
    """Test HTML representation of empty dataset."""
    dataset = Dataset(root_dir=temp_dir, name="empty_dataset")
    html = dataset._repr_html_()

    assert isinstance(html, str)
    assert "empty_dataset" in html
    assert "No commits" in html or "empty" in html.lower()
    assert "kirin-dataset-view" in html


def test_dataset_html_repr_with_files(temp_dir):
    """Test HTML representation of dataset with files."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create test files
    test_file1 = Path(temp_dir) / "file1.txt"
    test_file1.write_text("Hello, World!")
    test_file2 = Path(temp_dir) / "file2.csv"
    test_file2.write_text("col1,col2\n1,2\n3,4")

    # Create commit
    dataset.commit(
        message="Initial commit", add_files=[str(test_file1), str(test_file2)]
    )

    html = dataset._repr_html_()

    assert isinstance(html, str)
    assert "test_dataset" in html
    assert "file1.txt" in html
    assert "file2.csv" in html
    assert "Initial commit" in html
    assert "kirin-dataset-view" in html
    assert "file-item" in html


def test_dataset_html_repr_with_commit_history(temp_dir):
    """Test HTML representation shows commit history."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create multiple commits
    test_file1 = Path(temp_dir) / "file1.txt"
    test_file1.write_text("Version 1")
    dataset.commit(message="First commit", add_files=[str(test_file1)])

    test_file2 = Path(temp_dir) / "file2.txt"
    test_file2.write_text("Version 2")
    dataset.commit(message="Second commit", add_files=[str(test_file2)])

    html = dataset._repr_html_()

    assert isinstance(html, str)
    assert "First commit" in html
    assert "Second commit" in html
    assert "commit-item" in html or "commit" in html.lower()


def test_dataset_html_repr_includes_metadata(temp_dir):
    """Test HTML representation includes dataset metadata."""
    dataset = Dataset(
        root_dir=temp_dir, name="test_dataset", description="Test description"
    )

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Test content")
    dataset.commit(message="Initial commit", add_files=[str(test_file)])

    html = dataset._repr_html_()

    assert isinstance(html, str)
    assert "test_dataset" in html
    assert "Test description" in html or "description" in html.lower()


def test_dataset_html_repr_includes_file_sizes(temp_dir):
    """Test HTML representation includes file size information."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Test content" * 100)  # Make it larger
    dataset.commit(message="Initial commit", add_files=[str(test_file)])

    html = dataset._repr_html_()

    assert isinstance(html, str)
    assert "test.txt" in html
    # Should include size information (bytes, KB, etc.)
    assert "B" in html or "KB" in html or "bytes" in html.lower()


def test_dataset_html_repr_includes_current_commit_info(temp_dir):
    """Test HTML representation includes current commit information."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Test content")
    commit_hash = dataset.commit(message="Initial commit", add_files=[str(test_file)])

    html = dataset._repr_html_()

    assert isinstance(html, str)
    assert commit_hash[:8] in html  # Short hash should be visible
    assert "Initial commit" in html


def test_dataset_html_repr_self_contained(temp_dir):
    """Test HTML is self-contained (includes inline CSS)."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Test content")
    dataset.commit(message="Initial commit", add_files=[str(test_file)])

    html = dataset._repr_html_()

    assert isinstance(html, str)
    # Should include inline styles
    assert "<style>" in html


def test_dataset_html_repr_valid_html(temp_dir):
    """Test HTML is valid and well-formed."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Test content")
    dataset.commit(message="Initial commit", add_files=[str(test_file)])

    html = dataset._repr_html_()

    assert isinstance(html, str)
    # Basic HTML structure checks
    assert html.strip().startswith("<")
    assert "</div>" in html or html.count("<div") == html.count("</div>")


def test_dataset_html_repr_includes_file_access_code(temp_dir):
    """Test HTML representation includes code snippets for file access."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Test content")
    dataset.commit(message="Initial commit", add_files=[str(test_file)])

    html = dataset._repr_html_()

    assert isinstance(html, str)
    # Should include code snippet showing how to access files
    assert "local_files" in html
    assert "with dataset.local_files()" in html
    assert "code-snippet" in html
