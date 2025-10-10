# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo==0.16.5",
#     "kirin==0.0.1",
#     "loguru==0.7.3",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    """Setup Kirin and basic imports."""
    import sys
    from pathlib import Path
    from loguru import logger

    # Add the parent directory to Python path for Kirin imports
    sys.path.insert(0, str(Path.cwd().parent))

    from kirin import Dataset, File, Commit
    from kirin.catalog import Catalog
    return Catalog, logger


@app.cell
def _(logger):
    """Create a temporary directory for testing."""
    import tempfile
    import os

    # Create a temporary directory for this notebook session
    temp_dir = tempfile.mkdtemp(prefix="kirin_notebook_")
    logger.info(f"Created temporary directory: {temp_dir}")
    return os, temp_dir


@app.cell
def _(Catalog):
    catalog = Catalog(root_dir="gs://kirin-test-bucket")
    catalog.datasets()
    return (catalog,)


@app.cell
def _(catalog):
    dataset = catalog.get_dataset("test-dataset")
    dataset.list_files()
    return (dataset,)


@app.cell
def _(dataset, logger):
    """Demonstrate basic Kirin operations."""
    # Show dataset information
    logger.info(f"Dataset name: {dataset.name}")
    logger.info(f"Current commit: {dataset.current_commit}")
    logger.info(f"Files in dataset: {len(dataset.files)}")
    return


@app.cell
def _(logger, os, temp_dir):
    """Cleanup temporary directory."""
    import shutil

    # Clean up the temporary directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        logger.info(f"Cleaned up temporary directory: {temp_dir}")
    return


if __name__ == "__main__":
    app.run()
