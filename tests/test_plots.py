"""Tests for the kirin.plots module."""

import matplotlib.pyplot as plt
import numpy as np
import pytest

from kirin.plots import (
    is_matplotlib_figure,
    is_plotly_figure,
    save_plot,
    serialize_plot,
)
from kirin.storage import ContentStore


def test_save_matplotlib_figure_svg(temp_dir):
    """Test saving a matplotlib figure as SVG."""
    storage = ContentStore(temp_dir)

    # Create a simple matplotlib figure
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot([1, 2, 3], [1, 4, 9])
    ax.set_title("Test Plot")

    # Save plot (filename extension will be changed to .svg)
    filename = "test_plot.png"
    content_hash, actual_filename, _, _ = save_plot(fig, filename, storage)

    # Verify hash is returned
    assert content_hash is not None
    assert len(content_hash) == 64  # SHA256 hex digest length

    # Verify file was stored with .svg extension (function changes extension)
    svg_filename = "test_plot.svg"
    assert actual_filename == svg_filename
    assert storage.exists(content_hash, svg_filename)

    # Verify content is SVG (should start with SVG header)
    content = storage.retrieve(content_hash, svg_filename)
    assert content.startswith(b"<svg") or content.startswith(b"<?xml")

    plt.close(fig)


def test_save_matplotlib_figure_webp_for_raster(temp_dir):
    """Test saving a matplotlib raster plot (defaults to SVG for now)."""
    storage = ContentStore(temp_dir)

    # Create a raster plot (image-based)
    fig, ax = plt.subplots(figsize=(6, 4))
    data = np.random.rand(10, 10)
    ax.imshow(data, cmap="viridis")

    # Save plot (will be saved as SVG by default)
    filename = "raster_plot.png"
    content_hash, actual_filename, _, _ = save_plot(fig, filename, storage)

    # Verify hash is returned
    assert content_hash is not None

    # Verify file was stored with .svg extension (function changes extension)
    svg_filename = "raster_plot.svg"
    assert actual_filename == svg_filename
    assert storage.exists(content_hash, svg_filename)

    # Verify content is stored
    content = storage.retrieve(content_hash, svg_filename)
    assert len(content) > 0

    plt.close(fig)


def test_save_plotly_figure_svg(temp_dir):
    """Test saving a plotly figure as SVG."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        pytest.skip("plotly not installed")

    # Check if kaleido is available (required for plotly image export)
    try:
        import importlib.util

        spec = importlib.util.find_spec("kaleido")
        if spec is None:
            pytest.skip("kaleido not installed (required for plotly image export)")
    except ImportError:
        pytest.skip("kaleido not installed (required for plotly image export)")

    storage = ContentStore(temp_dir)

    # Create a simple plotly figure
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 4, 9], mode="lines"))

    # Save plot (filename extension will be changed to .svg)
    filename = "plotly_plot.png"
    content_hash, actual_filename, _, _ = save_plot(fig, filename, storage)

    # Verify hash is returned
    assert content_hash is not None
    assert len(content_hash) == 64

    # Verify file was stored with .svg extension
    svg_filename = "plotly_plot.svg"
    assert actual_filename == svg_filename
    assert storage.exists(content_hash, svg_filename)

    # Verify content is SVG
    content = storage.retrieve(content_hash, svg_filename)
    assert content.startswith(b"<svg") or content.startswith(b"<?xml")


def test_save_plot_with_custom_filename(temp_dir):
    """Test saving plot with custom filename."""
    storage = ContentStore(temp_dir)

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])

    filename = "custom_name.svg"
    content_hash, actual_filename, _, _ = save_plot(fig, filename, storage)

    # Verify file was stored with custom name
    assert actual_filename == filename
    assert storage.exists(content_hash, filename)

    plt.close(fig)


def test_save_plot_returns_hash(temp_dir):
    """Test that save_plot returns a content hash."""
    storage = ContentStore(temp_dir)

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])

    filename = "test.png"
    content_hash, actual_filename, _, _ = save_plot(fig, filename, storage)

    # Verify hash format (SHA256 hex)
    assert isinstance(content_hash, str)
    assert len(content_hash) == 64
    assert all(c in "0123456789abcdef" for c in content_hash)
    assert isinstance(actual_filename, str)

    plt.close(fig)


def test_save_plot_deterministic_hash(temp_dir):
    """Test that same matplotlib plot content produces identical hashes."""

    storage = ContentStore(temp_dir)

    # Create identical plots with same data
    fig1, ax1 = plt.subplots()
    ax1.plot([1, 2, 3], [1, 4, 9])

    fig2, ax2 = plt.subplots()
    ax2.plot([1, 2, 3], [1, 4, 9])

    filename = "test.png"
    hash1, filename1, _, _ = save_plot(fig1, filename, storage)
    hash2, filename2, _, _ = save_plot(fig2, filename, storage)

    assert hash1 == hash2
    assert filename1 == filename2

    plt.close(fig1)
    plt.close(fig2)


def test_save_plot_handles_unsupported_type(temp_dir):
    """Test that save_plot handles unsupported plot types gracefully."""
    storage = ContentStore(temp_dir)

    # Try to save something that's not a plot
    with pytest.raises((ValueError, TypeError)):
        save_plot("not a plot", "test.png", storage)


def test_save_plot_format_detection_matplotlib_vector(temp_dir):
    """Test format detection for matplotlib vector plots."""
    storage = ContentStore(temp_dir)

    # Create a vector plot (line plot)
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    filename = "vector_plot.png"
    content_hash, actual_filename, _, _ = save_plot(fig, filename, storage)

    # Verify it was saved with .svg extension (format detection happens internally)
    svg_filename = "vector_plot.svg"
    assert actual_filename == svg_filename
    assert storage.exists(content_hash, svg_filename)

    plt.close(fig)


def test_is_matplotlib_figure():
    """Test is_matplotlib_figure detection function."""
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])

    assert is_matplotlib_figure(fig) is True
    assert is_matplotlib_figure("not a figure") is False
    assert is_matplotlib_figure(42) is False
    assert is_matplotlib_figure(None) is False

    plt.close(fig)


def test_is_plotly_figure():
    """Test is_plotly_figure detection function."""
    try:
        import plotly.graph_objects as go
    except ImportError:
        pytest.skip("plotly not installed")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[1, 2, 3], y=[1, 2, 3]))

    assert is_plotly_figure(fig) is True
    assert is_plotly_figure("not a figure") is False
    assert is_plotly_figure(42) is False

    # Matplotlib figure should not be detected as plotly
    mpl_fig, _ = plt.subplots()
    assert is_plotly_figure(mpl_fig) is False
    plt.close(mpl_fig)


def test_serialize_plot_matplotlib(tmp_path):
    """Test serialize_plot with matplotlib figure."""
    import fsspec

    from kirin.storage import ContentStore

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    storage = ContentStore(str(tmp_path), fsspec.filesystem("file"))

    # Serialize plot with explicit variable name
    plot_path, source_path, source_hash = serialize_plot(
        fig, variable_name="test_plot", temp_dir=tmp_path, storage=storage
    )

    # Verify file was created
    assert plot_path is not None
    import os

    assert os.path.exists(plot_path)
    assert plot_path.endswith(".svg")  # Default format is SVG

    # Verify file content is SVG
    with open(plot_path, "rb") as f:
        content = f.read()
        assert content.startswith(b"<svg") or content.startswith(b"<?xml")

    plt.close(fig)


def test_serialize_plot_format_detection(tmp_path):
    """Test that serialize_plot uses format auto-detection."""
    import fsspec

    from kirin.storage import ContentStore

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    storage = ContentStore(str(tmp_path), fsspec.filesystem("file"))

    # Serialize without format (should auto-detect SVG)
    plot_path, _, _ = serialize_plot(
        fig, variable_name="test_plot", temp_dir=tmp_path, storage=storage
    )

    assert plot_path.endswith(".svg")

    plt.close(fig)


def test_serialize_plot_without_variable_name_raises_error(tmp_path, monkeypatch):
    """Test that serialize_plot raises error if variable name cannot be detected."""
    import fsspec

    from kirin.storage import ContentStore

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    storage = ContentStore(str(tmp_path), fsspec.filesystem("file"))

    # Mock detect_plot_variable_name to return None (simulating detection failure)
    monkeypatch.setattr(
        "kirin.plots.detect_plot_variable_name", lambda x: None
    )

    # Try to serialize without variable name - should raise error
    with pytest.raises(ValueError, match="Could not detect variable name"):
        serialize_plot(fig, temp_dir=tmp_path, storage=storage)

    plt.close(fig)
