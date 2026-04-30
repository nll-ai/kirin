# /// script
# requires-python = "==3.13"
# dependencies = [
#     "kirin==0.0.15",
#     "marimo>=0.17.0",
#     "matplotlib==3.10.9",
#     "numpy==2.4.4",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Plot Source Linking Demo

    This notebook demonstrates automatic source linking for plot commits in Kirin.

    We will:
    1. initialize a local dataset root
    2. create and commit a plot object
    3. verify source metadata is attached automatically to the committed plot file
    4. validate source content can be retrieved from content-addressed storage
    """)
    return


@app.cell
def _():
    from pathlib import Path
    import tempfile

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np

    from kirin import Dataset

    return Dataset, Path, mo, np, plt, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1) Initialize dataset

    Use an ephemeral local path and avoid hardcoded temp directories.
    """)
    return


@app.cell
def _(Dataset, Path, tempfile):
    dataset_root = Path(tempfile.mkdtemp(prefix="kirin_plot_source_demo_"))
    dataset = Dataset(root_dir=str(dataset_root), name="plot_source_linking_demo")

    dataset
    return (dataset,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2) Create a plot artifact
    """)
    return


@app.cell
def _(np, plt):
    np.random.seed(42)
    point_count = 100
    x_values = np.random.normal(loc=0, scale=1, size=point_count)
    y_values = np.random.gamma(shape=2, scale=2, size=point_count)

    fig, axis = plt.subplots(figsize=(8, 6))
    axis.scatter(x_values, y_values, s=50, alpha=0.6)
    axis.set_xlabel("X values (Gaussian)")
    axis.set_ylabel("Y values (Gamma)")
    axis.set_title("Bivariate Scatter Plot: Gaussian × Gamma")
    axis.grid(True, alpha=0.3)

    fig
    return (fig,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3) Commit plot with idempotent guard

    The commit call should auto-detect source context and attach source metadata to
    plot files.
    """)
    return


@app.cell
def _(dataset, fig):
    plot_commit_hash = dataset.commit(
        message="Commit scatter plot with automatic source linking",
        add_files=[fig],
        skip_if_no_changes=True,
    )

    plot_commit_hash
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4) Verify automatic source metadata on committed plot file
    """)
    return


@app.cell
def _(dataset):
    plot_filenames = sorted(name for name in dataset.files if name.endswith(".svg"))
    plot_filename = plot_filenames[0] if plot_filenames else None
    plot_file = dataset.get_file(plot_filename) if plot_filename else None
    plot_metadata = plot_file.metadata if plot_file else {}

    plot_file
    return plot_filename, plot_metadata


@app.cell
def _(dataset, mo, plot_filename, plot_metadata):
    source_file = plot_metadata.get("source_file") if plot_metadata else None
    source_hash = plot_metadata.get("source_hash") if plot_metadata else None

    source_linking_is_present = bool(source_file and source_hash)
    source_blob_exists = (
        dataset.storage.exists(source_hash, source_file)
        if source_linking_is_present
        else False
    )

    mo.md(
        f"""
    ### Source linking status

    - Plot filename: `{plot_filename}`
    - Source metadata present: **{source_linking_is_present}**
    - Source file: `{source_file}`
    - Source hash: `{source_hash[:8] if source_hash else None}`
    - Source blob exists in storage: **{source_blob_exists}**
    """
    )
    return source_file, source_hash, source_linking_is_present


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5) Preview source file snippet from storage
    """)
    return


@app.cell
def _(dataset, mo, source_file, source_hash, source_linking_is_present):
    if source_linking_is_present:
        source_content = dataset.storage.retrieve(source_hash, source_file).decode("utf-8")
        source_preview = "\n".join(source_content.splitlines()[:30])
        preview_output = mo.md(f"""```python
    {source_preview}
    ```""")
    else:
        preview_output = mo.md("No source metadata found on plot file.")

    preview_output
    return


if __name__ == "__main__":
    app.run()
