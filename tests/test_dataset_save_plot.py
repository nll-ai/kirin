"""Tests for Dataset.save_plot() method."""

import tempfile

import matplotlib.pyplot as plt
import pytest

from kirin.dataset import Dataset


@pytest.fixture
def empty_dataset(tmp_path):
    """Create an empty dataset."""
    return Dataset(root_dir=tmp_path, name="test_dataset")


def test_dataset_save_plot_default_mode(empty_dataset):
    """Test Dataset.save_plot() in default mode (returns file path)."""
    # Create a simple matplotlib figure
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    # Save plot in default mode
    filename = "test_plot.png"
    plot_path = empty_dataset.save_plot(fig, filename)

    # Verify it returns a file path
    assert isinstance(plot_path, str)
    assert plot_path == filename or plot_path.endswith(".svg")

    # Verify plot was stored but not committed
    assert len(empty_dataset.files) == 0

    # Now commit explicitly
    commit_hash = empty_dataset.commit(message="Add plot", add_files=[plot_path])

    # Verify commit was created
    assert commit_hash is not None
    assert len(empty_dataset.files) > 0

    plt.close(fig)


def test_dataset_save_plot_auto_commit_mode(empty_dataset):
    """Test Dataset.save_plot() in auto-commit mode (returns commit hash)."""
    # Create a simple matplotlib figure
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    # Save plot with auto-commit
    filename = "test_plot.png"
    commit_hash = empty_dataset.save_plot(
        fig, filename, auto_commit=True, message="Add plot"
    )

    # Verify it returns a commit hash
    assert isinstance(commit_hash, str)
    assert len(commit_hash) == 64  # SHA256 hex digest length

    # Verify plot was automatically committed
    assert len(empty_dataset.files) > 0
    assert empty_dataset.current_commit is not None
    assert empty_dataset.current_commit.hash == commit_hash

    plt.close(fig)


def test_dataset_save_plot_batch_multiple_plots(empty_dataset):
    """Test saving multiple plots in one commit using default mode."""
    # Create multiple plots
    fig1, ax1 = plt.subplots()
    ax1.plot([1, 2, 3], [1, 4, 9])

    fig2, ax2 = plt.subplots()
    ax2.plot([1, 2, 3], [1, 2, 3])

    # Save plots in default mode
    plot1_path = empty_dataset.save_plot(fig1, "plot1.png")
    plot2_path = empty_dataset.save_plot(fig2, "plot2.png")

    # Verify plots are not committed yet
    assert len(empty_dataset.files) == 0

    # Commit both plots together
    commit_hash = empty_dataset.commit(
        message="Add multiple plots", add_files=[plot1_path, plot2_path]
    )

    # Verify both plots are in the commit
    assert commit_hash is not None
    assert len(empty_dataset.files) >= 2

    plt.close(fig1)
    plt.close(fig2)


def test_dataset_save_plot_with_existing_files(empty_dataset):
    """Test saving plot when dataset already has files."""
    # Add a regular file first
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
        f.write("test content")
        temp_file = f.name

    try:
        # Commit regular file
        empty_dataset.commit(message="Add file", add_files=[temp_file])

        # Create and save plot
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 4, 9])

        plot_path = empty_dataset.save_plot(fig, "plot.png")

        # Commit plot along with keeping existing files
        commit_hash = empty_dataset.commit(message="Add plot", add_files=[plot_path])

        # Verify both file and plot are in commit
        assert commit_hash is not None
        assert len(empty_dataset.files) >= 2

        plt.close(fig)
    finally:
        import os

        if os.path.exists(temp_file):
            os.unlink(temp_file)


def test_dataset_save_plot_auto_commit_with_metadata(empty_dataset):
    """Test auto-commit mode with metadata."""
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    # Save plot with auto-commit and metadata
    commit_hash = empty_dataset.save_plot(
        fig,
        "plot.png",
        auto_commit=True,
        message="Add plot",
        metadata={"plot_type": "line", "data_points": 3},
    )

    # Verify commit was created with metadata
    assert commit_hash is not None
    assert empty_dataset.current_commit is not None
    assert "plot_type" in empty_dataset.current_commit.metadata
    assert empty_dataset.current_commit.metadata["plot_type"] == "line"

    plt.close(fig)


def test_dataset_save_plot_format_detection(empty_dataset):
    """Test that format detection works in Dataset.save_plot()."""
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 4, 9])

    # Save plot (should default to SVG for matplotlib)
    plot_path = empty_dataset.save_plot(fig, "plot.png")

    # Verify the path reflects the format (SVG)
    assert plot_path.endswith(".svg") or "svg" in plot_path.lower()

    plt.close(fig)
