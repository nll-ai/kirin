"""Tests for variable name detection in HTML representations."""

from pathlib import Path

from kirin import Catalog, Dataset
from kirin.utils import detect_variable_name


def test_detect_variable_name_default():
    """Test that detect_variable_name returns default when called directly."""
    result = detect_variable_name(default="test_default")
    assert result == "test_default"


def test_dataset_html_repr_basic(temp_dir):
    """Test that Dataset HTML representation works."""
    # This test simulates what happens when a user writes:
    # my_dataset = Dataset(...)
    # my_dataset  # This calls _repr_html_()

    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Simulate the call stack by creating a frame
    def test_function():
        """Helper function to simulate notebook cell execution."""
        my_dataset = dataset
        return my_dataset._repr_html_()

    html = test_function()
    # Verify the HTML is generated correctly
    assert isinstance(html, str)
    assert "kirin-dataset-view" in html


def test_dataset_html_repr_manual_override(temp_dir):
    """Test that manual _repr_variable_name override works."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")
    dataset._repr_variable_name = "custom_name"

    # Create a test file so code snippets are generated
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("test content")
    dataset.commit(message="Test", add_files=[str(test_file)])

    html = dataset._repr_html_()

    # Check that the custom name is used in code snippets
    assert "custom_name" in html
    assert "with custom_name.local_files()" in html


def test_dataset_html_repr_default_variable_name(temp_dir):
    """Test that Dataset HTML uses default variable name in code snippets."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create a test file
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("test content")
    dataset.commit(message="Test", add_files=[str(test_file)])

    # Test in a function to simulate notebook cell
    def test_cell():
        """Helper function to simulate notebook cell execution."""
        my_dataset = dataset
        return my_dataset._repr_html_()

    html = test_cell()
    assert isinstance(html, str)
    # Should contain dataset view
    assert "kirin-dataset-view" in html
    # Should use default "dataset" variable name in code snippets
    assert "with dataset.local_files()" in html


def test_commit_html_repr_default_variable_name(temp_dir):
    """Test that Commit HTML uses default variable name in code snippets."""
    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create a test file and commit
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("test content")
    commit_hash = dataset.commit(message="Test", add_files=[str(test_file)])

    commit = dataset.get_commit(commit_hash)

    # Test in a function to simulate notebook cell
    def test_cell():
        """Helper function to simulate notebook cell execution."""
        my_commit = commit
        return my_commit._repr_html_()

    html = test_cell()
    assert isinstance(html, str)
    # Should contain commit view
    assert "kirin-commit-view" in html
    # Should contain checkout code
    assert "checkout" in html.lower()
    # Should use default "dataset" variable name
    assert "dataset.checkout" in html


def test_catalog_html_repr_manual_override(temp_dir):
    """Test that manual _repr_variable_name override works for Catalog."""
    catalog = Catalog(root_dir=temp_dir)
    catalog._repr_variable_name = "my_catalog"

    html = catalog._repr_html_()

    assert isinstance(html, str)
    assert "kirin-catalog-view" in html


def test_catalog_html_repr_basic(temp_dir):
    """Test that Catalog HTML representation works."""
    catalog = Catalog(root_dir=temp_dir)

    # Test in a function to simulate notebook cell
    def test_cell():
        """Helper function to simulate notebook cell execution."""
        my_catalog = catalog
        return my_catalog._repr_html_()

    html = test_cell()
    assert isinstance(html, str)
    assert "kirin-catalog-view" in html


def test_detect_variable_name_fallback_on_error(monkeypatch):
    """Test that detect_variable_name falls back to default on errors."""
    # Mock inspect.currentframe to return None (simulating error case)
    import inspect as inspect_module

    def mock_current_frame():
        return None

    monkeypatch.setattr(inspect_module, "currentframe", mock_current_frame)

    result = detect_variable_name(default="fallback")
    assert result == "fallback"


def test_detect_variable_name_fallback_no_source(monkeypatch):
    """Test that detect_variable_name falls back when source is unavailable."""
    import inspect as inspect_module
    import linecache as linecache_module

    # Create a mock frame that has no source
    mock_frame = type(
        "Frame",
        (),
        {
            "f_back": type(
                "Frame",
                (),
                {
                    "f_back": type(
                        "Frame",
                        (),
                        {
                            "f_code": type("Code", (), {"co_filename": "<string>"})(),
                        },
                    )(),
                },
            )(),
        },
    )()

    def mock_current_frame():
        return mock_frame

    def mock_getline(filename, lineno):
        return ""  # Empty source line

    monkeypatch.setattr(inspect_module, "currentframe", mock_current_frame)
    monkeypatch.setattr(linecache_module, "getline", mock_getline)

    result = detect_variable_name(default="fallback")
    assert result == "fallback"
