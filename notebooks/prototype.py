# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "gitdata==0.0.1",
# ]
#
# [tool.uv.sources]
# gitdata = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import polars as pl
    return (mo,)


@app.cell
def _():
    import gitdata
    return


@app.cell
def _():
    from gitdata.dataset import Dataset
    return (Dataset,)


@app.cell
def _(Dataset):
    ds = Dataset(root_dir="gs://gitdata-test-bucket", dataset_name="test")
    return (ds,)


@app.cell
def _(ds):
    ds.commit("Add another dummy", add_files=["another dummy.txt"])
    return


@app.cell
def _(ds):
    ds.commit("Add some dummy text files", add_files=["dummy.txt"])
    return


@app.cell
def _(ds):
    ds.commit("Remove some dummy text files", remove_files=["dummy.txt"])
    return


@app.cell
def _(ds, mo):
    mo.mermaid(ds.commit_history_mermaid())
    return


if __name__ == "__main__":
    app.run()
