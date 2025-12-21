"""Tests for Kirin widgets."""

from pathlib import Path

from kirin.widgets import CatalogWidget, CommitWidget, DatasetWidget, FileListWidget


def test_dataset_widget_creation():
    """Test DatasetWidget can be created with data."""
    data = {
        "name": "test_dataset",
        "description": "Test description",
        "commit_count": 1,
        "total_size": "1.5 KB",
        "current_commit": {
            "hash": "abc12345",
            "message": "Initial commit",
            "timestamp": "2024-01-01 12:00:00",
        },
        "files": [
            {
                "name": "test.txt",
                "size": "100 B",
                "icon_html": "<svg>...</svg>",
            }
        ],
        "history": [
            {
                "hash": "abc12345",
                "message": "Initial commit",
                "timestamp": "2024-01-01 12:00:00",
                "file_count": 1,
                "size": "100 B",
            }
        ],
        "has_commit": True,
    }

    widget = DatasetWidget(data=data)
    html = widget._repr_html_()

    assert isinstance(html, str)
    assert "test_dataset" in html
    assert "kirin-dataset-view" in html or "data-anywidget-id" in html


def test_commit_widget_creation():
    """Test CommitWidget can be created with data."""
    data = {
        "hash": "abc12345",
        "message": "Test commit",
        "timestamp": "2024-01-01 12:00:00",
        "parent_hash": "def67890",
        "file_count": 2,
        "size": "2.5 KB",
        "files": [
            {
                "name": "file1.txt",
                "size": "1 KB",
                "icon_html": "<svg>...</svg>",
            },
            {
                "name": "file2.txt",
                "size": "1.5 KB",
                "icon_html": "<svg>...</svg>",
            },
        ],
    }

    widget = CommitWidget(data=data)
    html = widget._repr_html_()

    assert isinstance(html, str)
    assert "abc12345" in html
    assert "kirin-commit-view" in html or "data-anywidget-id" in html


def test_catalog_widget_creation():
    """Test CatalogWidget can be created with data."""
    data = {
        "root_dir": "/tmp/test",
        "dataset_count": 2,
        "datasets": [
            {
                "name": "dataset1",
                "description": "First dataset",
                "commit": {
                    "hash": "abc12345",
                    "message": "Initial commit",
                    "file_count": 1,
                    "size": "100 B",
                },
            },
            {
                "name": "dataset2",
                "description": None,
                "commit": None,
            },
        ],
        "total_size": "200 B",
    }

    widget = CatalogWidget(data=data)
    html = widget._repr_html_()

    assert isinstance(html, str)
    assert "dataset1" in html
    assert "kirin-catalog-view" in html or "data-anywidget-id" in html


def test_file_list_widget_creation():
    """Test FileListWidget can be created with data."""
    widget = FileListWidget(
        files=[
            {
                "name": "test.txt",
                "size": "100 B",
                "icon_html": "<svg>...</svg>",
            }
        ],
        dataset_name="test_dataset",
        expanded_files=[],
    )

    # FileListWidget is used internally by other widgets, not directly
    # Just verify it can be instantiated
    assert widget.files[0]["name"] == "test.txt"
    assert widget.dataset_name == "test_dataset"


def test_widget_assets_exist():
    """Test that widget asset files exist."""
    assets_dir = Path(__file__).parent.parent / "kirin" / "widgets" / "assets"

    assert (assets_dir / "shared.css").exists()
    assert (assets_dir / "ui_utils.js").exists()
    assert (assets_dir / "dataset.js").exists()
    assert (assets_dir / "commit.js").exists()
    assert (assets_dir / "catalog.js").exists()
    assert (assets_dir / "file_list.js").exists()


def test_widget_traitlet_sync():
    """Test that traitlets sync correctly."""
    widget = DatasetWidget(
        data={"name": "test", "commit_count": 0, "has_commit": False}
    )

    # Test that we can set expanded_files
    widget.expanded_files = ["0", "1"]
    assert widget.expanded_files == ["0", "1"]

    # Test that data can be updated
    widget.data = {"name": "updated", "commit_count": 1, "has_commit": True}
    assert widget.data["name"] == "updated"


def test_dataset_widget_with_file_preview(temp_dir):
    """Test DatasetWidget includes file content for preview."""
    from kirin import Dataset

    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create test files
    csv_file = temp_dir / "data.csv"
    csv_file.write_text("name,age,city\nAlice,28,New York\nBob,35,San Francisco")

    json_file = temp_dir / "config.json"
    json_file.write_text('{"version": "1.0", "description": "Test config"}')

    txt_file = temp_dir / "readme.txt"
    txt_file.write_text("This is a test file")

    # Commit files
    dataset.commit(message="Add test files", add_files=[csv_file, json_file, txt_file])

    # Get widget data
    widget_data = dataset._get_widget_data()

    # Check that files have content for preview
    csv_file_data = next(f for f in widget_data["files"] if f["name"] == "data.csv")
    assert csv_file_data["is_text"] is True
    assert csv_file_data["content"] is not None
    assert "Alice" in csv_file_data["content"]

    json_file_data = next(f for f in widget_data["files"] if f["name"] == "config.json")
    assert json_file_data["is_text"] is True
    assert json_file_data["content"] is not None
    assert "version" in json_file_data["content"]

    txt_file_data = next(f for f in widget_data["files"] if f["name"] == "readme.txt")
    assert txt_file_data["is_text"] is True
    assert txt_file_data["content"] is not None
    assert "test file" in txt_file_data["content"]


def test_commit_widget_with_file_preview(temp_dir):
    """Test CommitWidget includes file content for preview."""
    from kirin import Dataset

    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create test CSV file
    csv_file = temp_dir / "data.csv"
    csv_file.write_text("name,age\nAlice,28\nBob,35")

    # Commit file
    commit_hash = dataset.commit(message="Add CSV", add_files=[csv_file])
    commit = dataset.get_commit(commit_hash)

    # Get widget data
    widget_data = commit._get_widget_data()

    # Check that file has content for preview
    csv_file_data = next(f for f in widget_data["files"] if f["name"] == "data.csv")
    assert csv_file_data["is_text"] is True
    assert csv_file_data["content"] is not None
    assert "Alice" in csv_file_data["content"]


def test_widget_preview_csv_rendering():
    """Test that CSV files are rendered as tables in widget HTML."""
    data = {
        "name": "test_dataset",
        "description": "Test",
        "commit_count": 1,
        "total_size": "100 B",
        "current_commit": {"hash": "abc123", "message": "Test"},
        "files": [
            {
                "name": "data.csv",
                "size": "50 B",
                "icon_html": "<svg></svg>",
                "is_text": True,
                "content": "name,age\nAlice,28\nBob,35",
            }
        ],
        "history": [],
        "has_commit": True,
    }

    widget = DatasetWidget(data=data)
    html = widget._generate_static_html(data)

    # Check that CSV table structure is present
    assert "<table>" in html
    assert "<thead>" in html
    assert "<th>name</th>" in html or "name" in html
    assert "Alice" in html


def test_widget_preview_json_rendering():
    """Test that JSON files are rendered with json class."""
    data = {
        "name": "test_dataset",
        "description": "Test",
        "commit_count": 1,
        "total_size": "100 B",
        "current_commit": {"hash": "abc123", "message": "Test"},
        "files": [
            {
                "name": "config.json",
                "size": "50 B",
                "icon_html": "<svg></svg>",
                "is_text": True,
                "content": '{"version": "1.0"}',
            }
        ],
        "history": [],
        "has_commit": True,
    }

    widget = DatasetWidget(data=data)
    html = widget._generate_static_html(data)

    # Check that JSON preview is present
    assert 'class="json"' in html or 'code class="json"' in html
    assert "version" in html


def test_widget_large_file_no_preview(temp_dir):
    """Test that large files (>100KB) don't have content loaded."""
    from kirin import Dataset

    dataset = Dataset(root_dir=temp_dir, name="test_dataset")

    # Create a large file (>100KB)
    large_file = temp_dir / "large.txt"
    large_content = "x" * (101 * 1024)  # 101 KB
    large_file.write_text(large_content)

    # Commit file
    dataset.commit(message="Add large file", add_files=[large_file])

    # Get widget data
    widget_data = dataset._get_widget_data()

    # Check that large file doesn't have content
    large_file_data = next(f for f in widget_data["files"] if f["name"] == "large.txt")
    assert large_file_data.get("content") is None
    assert large_file_data.get("is_text") is False


def test_widget_template_rendering():
    """Test that Jinja2 templates render correctly."""
    data = {
        "name": "test_dataset",
        "description": "Test description",
        "commit_count": 1,
        "total_size": "1 KB",
        "current_commit": {"hash": "abc123", "message": "Test commit"},
        "files": [],
        "history": [],
        "has_commit": True,
    }

    widget = DatasetWidget(data=data)
    html = widget._generate_static_html(data)

    # Check that template rendered correctly
    assert "test_dataset" in html
    assert "Test description" in html
    assert "Test commit" in html
    assert "<style>" in html  # CSS should be included
