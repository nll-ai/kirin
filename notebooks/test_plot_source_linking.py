# /// script
# requires-python = "==3.13"
# dependencies = [
#     "kirin",
#     "marimo>=0.17.0",
#     "matplotlib",
#     "numpy",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    """Test source detection."""

    from kirin.utils import detect_source_file

    detected = detect_source_file()
    print(f"Detected source file: {detected}")
    return


@app.cell
def _():
    """Setup imports and dataset."""

    import tempfile
    from pathlib import Path
    from kirin import Dataset
    import matplotlib.pyplot as plt
    import numpy as np
    return Dataset, np, plt, tempfile


@app.cell
def _(Dataset, tempfile):
    """Create a temporary dataset for testing."""

    temp_dir = tempfile.mkdtemp()
    dataset = Dataset(root_dir="/tmp/plots", name="test_plot_source")
    print(f"Created dataset at: {temp_dir}")
    return (dataset,)


@app.cell
def _(np, plt):
    """Create a simple plot."""

    # Generate 100 random points
    # X-axis: Gaussian (normal) distribution
    # Y-axis: Gamma distribution
    n_points = 100
    x = np.random.normal(loc=0, scale=1, size=n_points)
    y = np.random.gamma(shape=2, scale=2, size=n_points)

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(x, y, s=50, alpha=0.6)
    ax.set_xlabel("X values (Gaussian)")
    ax.set_ylabel("Y values (Gamma)")
    ax.set_title("Bivariate Scatter Plot: Gaussian × Gamma")
    ax.grid(True, alpha=0.3)
    fig
    return (fig,)


@app.cell
def _(dataset, fig):
    """Commit the plot directly."""

    commit_hash = dataset.commit(
        message="Test plot with source linking",
        add_files=[fig],  # Plot object automatically converted to SVG
    )
    print(f"✅ Plot saved! Commit hash: {commit_hash[:8]}")
    return


@app.cell
def _(dataset):
    """Check if source file was detected and linked."""

    plot_file = dataset.get_file(
        "test_plot.svg"
    )  # Note: extension changes to .svg
    if plot_file:
        print(f"Plot file: {plot_file.name}")
        print(f"Plot hash: {plot_file.hash[:8]}")

        if plot_file.metadata.get("source_file"):
            print(f"\n✅ Source file detected!")
            print(f"   Source file: {plot_file.metadata['source_file']}")
            print(f"   Source hash: {plot_file.metadata['source_hash'][:8]}")

            # Check if source file is in the commit
            source_file = dataset.get_file(plot_file.metadata["source_file"])
            if source_file:
                print(f"   ✅ Source file is stored in the commit!")
                print(f"   Source file size: {source_file.size} bytes")
            else:
                print(f"   ❌ Source file NOT found in commit")
        else:
            print(f"\n❌ No source file metadata found")
            print(f"   Metadata: {plot_file.metadata}")
    else:
        print("❌ Plot file not found")
    return (plot_file,)


@app.cell
def _(dataset):
    """List all files in the commit."""

    print("Files in commit:")
    for name, file_obj in dataset.files.items():
        print(f"  - {name} ({file_obj.size} bytes, hash: {file_obj.hash[:8]})")
    return


@app.cell
def _(dataset, plot_file):
    """Display the source file content if available."""

    if plot_file and plot_file.metadata.get("source_file"):
        source_file_obj = dataset.get_file(plot_file.metadata["source_file"])
        if source_file_obj:
            source_content = source_file_obj.read_text()
            print("Source file content (first 500 chars):")
            print("=" * 60)
            print(source_content[:500])
            print("=" * 60)
    return


if __name__ == "__main__":
    app.run()
