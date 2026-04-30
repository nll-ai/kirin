# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin>=0.0.15",
#     "anthropic==0.69.0",
#     "loguru==0.7.3",
#     "gcsfs>=2024.2.0",
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
    # Kirin + Google Cloud Storage

    This notebook demonstrates a practical Kirin workflow on GCS:

    1. Create a dataset rooted at `gs://...`
    2. Create local files to commit
    3. Commit multiple snapshots
    4. Read data back through `local_files()`
    5. Inspect history and checkout behavior
    """)
    return


@app.cell
def _():
    import tempfile
    from pathlib import Path

    import marimo as mo
    import polars as pl

    from kirin import Dataset

    return Dataset, Path, mo, pl, tempfile


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1) Initialize a GCS-backed dataset

    We create a dataset at `gs://kirin-test-bucket` and a temporary local staging
    folder where we generate files before committing them.
    """)
    return


@app.cell
def _(Dataset, Path, tempfile):
    ds = Dataset("gs://kirin-test-bucket", name="test-dataset")

    temp_dir = Path(tempfile.mkdtemp())
    data_dir = temp_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir, ds


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2) Create initial local files

    Each file is created in its own small cell so the workflow stays readable and
    easy to modify.
    """)
    return


@app.cell
def _(data_dir):
    csv_file = data_dir / "sales_data.csv"
    csv_file.write_text("""product,price,quantity,date
    Widget A,29.99,100,2024-01-15
    Widget B,19.99,150,2024-01-16
    Widget C,39.99,75,2024-01-17
    Widget A,29.99,120,2024-01-18
    Widget B,19.99,200,2024-01-19""")
    return (csv_file,)


@app.cell
def _(data_dir):
    text_file = data_dir / "notes.txt"
    text_file.write_text("""Project Notes:
    - Widget A is our best seller
    - Widget B has high volume but lower margin
    - Widget C is premium but lower volume
    - Consider price optimization for Q2""")
    return (text_file,)


@app.cell
def _(data_dir):
    json_file = data_dir / "config.json"
    json_file.write_text("""{
      "project_name": "Widget Analytics",
      "version": "1.0.0",
      "settings": {
        "auto_backup": true,
        "retention_days": 30
      }
    }""")
    return (json_file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3) Commit the initial snapshot to GCS

    This writes a commit object and stores file contents in Kirin's
    content-addressed layout under the bucket.
    """)
    return


@app.cell
def _(csv_file, ds, json_file, text_file):
    initial_commit = ds.commit(
        message="Initial commit: add sales data, notes, and config",
        add_files=[csv_file, text_file, json_file],
        skip_if_no_changes=True,
    )
    initial_commit
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4) Prepare files for the next snapshot

    We add a new sales file version and a small analysis script.
    """)
    return


@app.cell
def _(data_dir):
    updated_csv = data_dir / "sales_data_v2.csv"
    updated_csv.write_text("""product,price,quantity,date
    Widget A,29.99,100,2024-01-15
    Widget B,19.99,150,2024-01-16
    Widget C,39.99,75,2024-01-17
    Widget A,29.99,120,2024-01-18
    Widget B,19.99,200,2024-01-19
    Widget D,49.99,50,2024-01-20
    Widget A,29.99,80,2024-01-21""")
    return (updated_csv,)


@app.cell
def _(data_dir):
    analysis_file = data_dir / "analysis.py"
    analysis_file.write_text("""import polars as pl

    def analyze_sales(df: pl.DataFrame) -> pl.DataFrame:
        return (
            df.group_by(\"product\")
            .agg([
                pl.col(\"quantity\").sum().alias(\"total_quantity\"),
                pl.col(\"price\").first().alias(\"price\"),
                (pl.col(\"quantity\") * pl.col(\"price\")).sum().alias(\"total_revenue\"),
            ])
            .sort(\"total_revenue\", descending=True)
        )
    """)
    return (analysis_file,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5) Add and remove files across commits

    This shows both `add_files` and `remove_files` workflows with linear history.
    """)
    return


@app.cell
def _(analysis_file, ds, updated_csv):
    second_commit = ds.commit(
        message="Add updated sales file and analysis script",
        add_files=[updated_csv, analysis_file],
        skip_if_no_changes=True,
    )
    second_commit
    return


@app.cell
def _(ds):
    third_commit = ds.commit(
        message="Remove original sales_data.csv",
        remove_files=["sales_data.csv"],
        skip_if_no_changes=True,
    )
    third_commit
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6) Inspect dataset metadata and commit history
    """)
    return


@app.cell
def _(ds):
    info = ds.get_info()
    commit_history = ds.history(limit=5)
    return commit_history, info


@app.cell(hide_code=True)
def _(commit_history, ds, info, mo):
    history_lines = [
        f"- `{commit.short_hash}`: {commit.message}" for commit in commit_history
    ]

    mo.md(
        f"""
    ### Current dataset state

    - **Name**: {info["name"]}
    - **Storage root**: `gs://kirin-test-bucket`
    - **Current commit**: `{info["current_commit"][:8] if info["current_commit"] else "None"}`
    - **Commit count**: {info["commit_count"]}
    - **Current files**: {len(ds.files)}

    ### Recent commits
    {chr(10).join(history_lines)}
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7) Read committed data through `local_files()`

    Kirin materializes files locally on demand so normal file-based tools work
    without changing your analysis code.
    """)
    return


@app.cell
def _(ds, pl):
    summary = None

    with ds.local_files() as local_files:
        if "sales_data_v2.csv" in local_files:
            dataframe = pl.read_csv(local_files["sales_data_v2.csv"])
            summary = (
                dataframe.group_by("product")
                .agg(
                    [
                        pl.col("quantity").sum().alias("total_quantity"),
                        pl.col("price").first().alias("price"),
                        (pl.col("quantity") * pl.col("price"))
                        .sum()
                        .alias("total_revenue"),
                    ]
                )
                .sort("total_revenue", descending=True)
            )

    summary
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8) Demonstrate an obvious checkout difference

    This section compares the **current commit** against the **previous commit**
    using file presence and file lists, so the change is visually obvious.
    """)
    return


@app.cell
def _(ds):
    files = ds.list_files()
    current_notes = (
        ds.read_file("notes.txt", mode="r") if "notes.txt" in files else None
    )
    current_config = (
        ds.read_file("config.json", mode="r") if "config.json" in files else None
    )
    return (files,)


@app.cell
def _(commit_history, ds):
    previous_commit = commit_history[1] if len(commit_history) > 1 else None
    previous_files = []

    if previous_commit is not None:
        ds.checkout(previous_commit.hash)
        previous_files = ds.list_files()
        ds.checkout()
    return previous_commit, previous_files


@app.cell(hide_code=True)
def _(files, mo, previous_commit, previous_files):
    current_files_set = set(files)
    previous_files_set = set(previous_files)

    added_since_previous = sorted(current_files_set - previous_files_set)
    removed_since_previous = sorted(previous_files_set - current_files_set)

    sales_data_current = "sales_data.csv" in current_files_set
    sales_data_previous = "sales_data.csv" in previous_files_set

    current_files_text = ", ".join(files) if files else "(no files)"
    previous_files_text = (
        ", ".join(previous_files) if previous_files else "(no files)"
    )
    added_text = (
        ", ".join(added_since_previous) if added_since_previous else "(none)"
    )
    removed_text = (
        ", ".join(removed_since_previous) if removed_since_previous else "(none)"
    )

    mo.md(
        f"""
    ### Current commit files
    {current_files_text}

    ### Previous commit files (`{previous_commit.short_hash if previous_commit else "N/A"}`)
    {previous_files_text}

    ### Diff (current vs previous)
    - **Added in current**: {added_text}
    - **Removed in current**: {removed_text}

    ### Concrete checkout proof
    - `sales_data.csv` in current commit: **{sales_data_current}**
    - `sales_data.csv` in previous commit: **{sales_data_previous}**

    This shows the checkout difference clearly: `sales_data.csv` exists in the
    previous commit but not in the current commit.
    """
    )
    return


if __name__ == "__main__":
    app.run()
