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

    from kirin.catalog import Catalog
    return Catalog, Path


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
def _(dataset):
    dataset.commit("add scratch.py", add_files=["scratch.py"])
    dataset.files
    return


@app.cell
def _(dataset):
    dataset.history()
    return


@app.cell
def _(dataset):
    dataset.checkout("859179e6")
    return


@app.cell
def _(dataset):
    dataset.files
    return


@app.cell
def _(dataset):
    with dataset.local_files() as lf:
        print(lf.keys())
    return


@app.cell
def _(Path, dataset):
    from kirin import Dataset

    # Checkout to latest commit (HEAD)
    dataset.checkout("6e25abbe68066f92933f18eca9b99a9d21182986184da3fd2f3935bdcbe0b749")


    # Access files as local paths
    with dataset.local_files() as local_files:
        file_path = local_files["prototype.ipynb"]

        print(Path(file_path).read_text())
        # Process file at file_path
        # Note: Files are temporary and will be deleted when exiting this context
    return


if __name__ == "__main__":
    app.run()
