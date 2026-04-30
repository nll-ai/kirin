# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin>=0.0.15",
#     "loguru==0.7.3",
#     "marimo>=0.23.4",
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
    # Kirin Linear Workflow Demo

    This notebook demonstrates a clean, linear Kirin workflow:

    1. initialize a dataset
    2. create and commit initial files
    3. add a new file in a second commit
    4. remove a file in a third commit
    5. inspect linear commit history

    All commits in this notebook opt in to idempotent behavior with
    `skip_if_no_changes=True` to avoid duplicate no-op commits on reruns.
    """)
    return


@app.cell
def _():
    import shutil
    import tempfile
    from pathlib import Path

    import marimo as mo

    from kirin.dataset import Dataset

    return Dataset, Path, mo, shutil, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1) Initialize dataset

    Create a local dataset root and open a dataset for the workflow.
    """)
    return


@app.cell
def _(Dataset, tempfile):
    temp_dir = tempfile.mkdtemp()
    dataset_name = "demo_linear_workflow"
    dataset = Dataset(root_dir=temp_dir, name=dataset_name)

    temp_dir
    return dataset, temp_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2) Create initial files

    Create two baseline files to version in the first commit.
    """)
    return


@app.cell
def _(Path, temp_dir):
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content of file 1")

    file1
    return (file1,)


@app.cell
def _(Path, temp_dir):
    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content of file 2")

    file2
    return (file2,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3) Initial commit

    Commit both baseline files as the first snapshot.
    """)
    return


@app.cell
def _(dataset, file1, file2):
    initial_commit = dataset.commit(
        message="Initial commit with two files",
        add_files=[str(file1), str(file2)],
        skip_if_no_changes=True,
    )

    initial_commit
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4) Add new data

    Create `file3.txt` and commit it as a second snapshot.
    """)
    return


@app.cell
def _(Path, temp_dir):
    file3 = Path(temp_dir) / "file3.txt"
    file3.write_text("Content of file 3")

    file3
    return (file3,)


@app.cell
def _(dataset, file3):
    add_commit = dataset.commit(
        message="Add file3",
        add_files=[str(file3)],
        skip_if_no_changes=True,
    )

    add_commit
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5) Remove outdated file

    Remove `file1.txt` and commit the removal as the third snapshot.
    """)
    return


@app.cell
def _(dataset):
    remove_commit = dataset.commit(
        message="Remove file1",
        remove_files=["file1.txt"],
        skip_if_no_changes=True,
    )

    remove_commit
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6) Verify linear history

    Inspect commit history and confirm expected file state in the latest commit.
    """)
    return


@app.cell
def _(dataset, mo):
    history_commits = dataset.history(limit=10)
    history_messages = [commit.message for commit in history_commits]
    current_files = sorted(dataset.files.keys())

    assert "Initial commit with two files" in history_messages
    assert "Add file3" in history_messages
    assert "Remove file1" in history_messages
    assert "file1.txt" not in current_files
    assert "file2.txt" in current_files
    assert "file3.txt" in current_files

    mo.md(
        "## Current state\n\n"
        f"- commit count: {len(history_commits)}\n"
        f"- current files: {', '.join(current_files)}"
    )
    return (history_commits,)


@app.cell
def _(history_commits, mo):
    history_lines = [
        f"- `{commit.short_hash}`: {commit.message}" for commit in history_commits
    ]

    mo.md("## Commit history\n\n" + "\n".join(history_lines))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7) Key takeaways

    - history remains linear and easy to inspect
    - each commit captures a logical unit of change
    - `skip_if_no_changes=True` prevents duplicate no-op commits during reruns
    """)
    return


@app.cell
def _(shutil, temp_dir):
    # Optional cleanup for local temp directory
    shutil.rmtree(temp_dir)
    "cleanup complete"
    return


if __name__ == "__main__":
    app.run()
