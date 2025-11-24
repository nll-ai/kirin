# /// script
# requires-python = "==3.13"
# dependencies = [
#     "kirin",
#     "marimo",
#     "matplotlib",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.18.0"
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
    return Dataset, plt, tempfile


@app.cell
def _(Dataset, tempfile):
    """Create a temporary dataset for testing."""
    temp_dir = tempfile.mkdtemp()
    dataset = Dataset(root_dir=temp_dir, name="test_plot_source")
    print(f"Created dataset at: {temp_dir}")
    return (dataset,)


@app.cell
def _(plt):
    """Create a simple plot."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.plot([1, 2, 3, 4], [1, 4, 9, 16], marker='o', linestyle='-', linewidth=2)
    ax.set_xlabel('X values')
    ax.set_ylabel('Y values')
    ax.set_title('Test Plot for Source Linking')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    return (fig,)


@app.cell
def _(dataset, fig):
    """Save the plot with auto-commit."""
    commit_hash = dataset.save_plot(
        fig,
        "test_plot.png",
        auto_commit=True,
        message="Test plot with source linking"
    )
    print(f"✅ Plot saved! Commit hash: {commit_hash[:8]}")
    return


@app.cell
def _(dataset):
    """Check if source file was detected and linked."""
    plot_file = dataset.get_file("test_plot.svg")  # Note: extension changes to .svg
    if plot_file:
        print(f"Plot file: {plot_file.name}")
        print(f"Plot hash: {plot_file.hash[:8]}")

        if plot_file.metadata.get("source_file"):
            print(f"\n✅ Source file detected!")
            print(f"   Source file: {plot_file.metadata['source_file']}")
            print(f"   Source hash: {plot_file.metadata['source_hash'][:8]}")

            # Check if source file is in the commit
            source_file = dataset.get_file(plot_file.metadata['source_file'])
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
        source_file_obj = dataset.get_file(plot_file.metadata['source_file'])
        if source_file_obj:
            source_content = source_file_obj.read_text()
            print("Source file content (first 500 chars):")
            print("=" * 60)
            print(source_content[:500])
            print("=" * 60)
    return


if __name__ == "__main__":
    app.run()
