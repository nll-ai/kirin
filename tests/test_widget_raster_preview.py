"""Tests for raster image previews in notebook widgets."""

from pathlib import Path

from PIL import Image

from kirin.html_repr import (
    WIDGET_RASTER_IMAGE_MAX_PREVIEW_BYTES,
    is_raster_image_file,
    raster_mime_for_widget_data_uri,
    widget_raster_image_data_uri,
)


def test_is_raster_image_file_recognizes_extensions():
    """Raster helper accepts common raster types and rejects SVG."""

    assert is_raster_image_file("a.png", "application/octet-stream") is True
    assert is_raster_image_file("a.PNG", None) is True
    assert is_raster_image_file("photo.jpg", "image/jpeg") is True
    assert is_raster_image_file("x.webp", None) is True

    assert is_raster_image_file("plot.svg", "image/svg+xml") is False
    assert is_raster_image_file("plot.svg", None) is False


def test_raster_mime_for_widget_data_uri():
    """MIME inference aligns with filename and content-type."""

    assert raster_mime_for_widget_data_uri("x.png", "image/png") == "image/png"
    assert raster_mime_for_widget_data_uri("x.jpg", None) == "image/jpeg"


def test_widget_raster_image_data_uri_small_png(temp_dir):
    """Committed PNG produces a PNG data URI for widgets."""

    from kirin import Dataset

    path = Path(temp_dir) / "plot.png"
    Image.new("RGB", (12, 8), color="blue").save(path)

    ds = Dataset(root_dir=temp_dir, name="ds_raster")
    ds.commit(message="add png", add_files=[str(path)])

    data = ds._get_widget_data()
    file_entry = next(f for f in data["files"] if f["name"] == "plot.png")

    assert file_entry["is_image"] is True
    uri = file_entry["image_data_uri"]
    assert uri is not None
    assert uri.startswith("data:image/png;base64,")


def test_widget_raster_commit_has_data_uri(temp_dir):
    """Commit widget data includes raster data URI."""

    from kirin import Dataset

    path = Path(temp_dir) / "snap.gif"
    Image.new("RGB", (4, 4), color=(200, 10, 20)).save(path, format="GIF")

    ds = Dataset(root_dir=temp_dir, name="ds_gif")
    commit_hash = ds.commit(message="gif", add_files=[str(path)])
    commit = ds.get_commit(commit_hash)

    data = commit._get_widget_data()
    file_entry = next(f for f in data["files"] if f["name"] == "snap.gif")

    assert file_entry["is_image"] is True
    assert file_entry["image_data_uri"].startswith("data:image/gif;base64,")


def test_svg_remains_preview_marker_without_uri(temp_dir):
    """SVG commits stay is_image without embedded raster URI."""

    from kirin import Dataset

    svg = Path(temp_dir) / "vector.svg"
    svg.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg">'
        '<rect width="1" height="1"/></svg>'
    )

    ds = Dataset(root_dir=temp_dir, name="ds_svg")
    ds.commit(message="svg", add_files=[str(svg)])

    data = ds._get_widget_data()
    file_entry = next(f for f in data["files"] if f["name"] == "vector.svg")

    assert file_entry["is_image"] is True
    assert file_entry.get("image_data_uri") is None


def test_widget_static_html_contains_img_for_raster(temp_dir):
    """Static HTML renders an img tag when image_data_uri is set."""

    from kirin.widgets import DatasetWidget

    data_with_image = {
        "name": "x",
        "description": "",
        "commit_count": 1,
        "total_size": "1 B",
        "current_commit": {"hash": "a", "message": "m"},
        "files": [
            {
                "name": "a.png",
                "size": "100 B",
                "icon_html": "<svg>x</svg>",
                "content_type": "image/png",
                "is_image": True,
                "is_text": False,
                "image_data_uri": "data:image/png;base64,abab",
            }
        ],
        "history": [],
        "has_commit": True,
    }

    html = DatasetWidget(data=data_with_image)._generate_static_html(data_with_image)

    assert 'class="widget-raster-image"' in html
    assert "data:image/png;base64,abab" in html


def test_widget_raster_image_data_uri_rejects_oversized_file(temp_dir):
    """Embedded preview returns None when file bytes exceed caller max."""

    from kirin import Dataset

    path = Path(temp_dir) / "tiny.png"
    Image.new("RGB", (20, 20), color="green").save(path)

    ds = Dataset(root_dir=temp_dir, name="ds_cap")
    ds.commit(message="png", add_files=[str(path)])
    png_file = ds.get_file("tiny.png")

    assert png_file.size > 20
    assert widget_raster_image_data_uri(png_file, max_bytes=10) is None
    uri = widget_raster_image_data_uri(
        png_file,
        max_bytes=WIDGET_RASTER_IMAGE_MAX_PREVIEW_BYTES,
    )
    assert uri is not None and uri.startswith("data:image/png;base64,")
