# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin==0.0.15",
#     "anthropic==0.69.0",
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
    # Kirin Local Storage Demo

    This notebook demonstrates Kirin workflows on local filesystem storage.

    We will:
    1. initialize a local dataset
    2. create sample files in small steps
    3. create three commits (add/add/remove)
    4. inspect history and process current files
    5. show checkout differences clearly
    """)
    return


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import polars as pl

    from kirin import Dataset

    return Dataset, Path, mo, pl


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1) Initialize local dataset

    Use a persistent local path so reruns can demonstrate idempotent commit behavior.
    """)
    return


@app.cell
def _(Dataset, Path):
    demo_dir = Path("/tmp/kirin_demo")
    demo_dir.mkdir(exist_ok=True)

    data_dir = demo_dir / "data"
    data_dir.mkdir(exist_ok=True)

    ds = Dataset(
        root_dir=str(demo_dir),
        name="sales_analysis",
        description="Sales data analysis project",
    )

    ds.name
    return data_dir, ds


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2) Create initial files

    Split file creation by file so each cell performs one logical operation.
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3) Create commits with idempotent guard

    All commit cells use `skip_if_no_changes=True` to avoid duplicate no-op commits
    when reactive cells rerun.
    """)
    return


@app.cell
def _(csv_file, ds, text_file):
    initial_commit = ds.commit(
        message="Initial commit: Add sales data and notes",
        add_files=[csv_file, text_file],
        skip_if_no_changes=True,
    )

    initial_commit
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
def _(ds, updated_csv):
    second_commit = ds.commit(
        message="Add new product Widget D and additional sales",
        add_files=[updated_csv],
        skip_if_no_changes=True,
    )

    second_commit
    return


@app.cell
def _(ds):
    third_commit = ds.commit(
        message="Remove old sales data file",
        remove_files=["sales_data.csv"],
        skip_if_no_changes=True,
    )

    third_commit
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4) Inspect dataset status and history
    """)
    return


@app.cell
def _(ds):
    info = ds.get_info()
    commit_history = ds.history(limit=5)
    return commit_history, info


@app.cell
def _(commit_history, ds, info, mo):
    history_lines = [
        f"- `{commit.short_hash}`: {commit.message}" for commit in commit_history
    ]

    mo.md(
        f"""
    ### Dataset status

    - **Name**: {info['name']}
    - **Description**: {info['description']}
    - **Current commit**: `{info['current_commit'][:8] if info['current_commit'] else 'None'}`
    - **Commit count**: {info['commit_count']}
    - **Current file count**: {len(ds.files)}

    ### Recent commits
    {chr(10).join(history_lines)}
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5) Process current committed CSV data

    Use `local_files()` to materialize files locally and run standard analysis.
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
                        (pl.col("quantity") * pl.col("price")).sum().alias("total_revenue"),
                    ]
                )
                .sort("total_revenue", descending=True)
            )

    summary
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6) Demonstrate checkout differences

    Compare current vs previous commit using file presence and file lists.
    """)
    return


@app.cell
def _(ds):
    current_files = ds.list_files()
    return (current_files,)


@app.cell
def _(commit_history, ds):
    previous_commit = commit_history[1] if len(commit_history) > 1 else None
    previous_files = []
    if previous_commit is not None:
        ds.checkout(previous_commit.hash)
        previous_files = ds.list_files()
        ds.checkout()
    return previous_commit, previous_files


@app.cell
def _(current_files, mo, previous_commit, previous_files):
    current_set = set(current_files)
    previous_set = set(previous_files)

    added_since_previous = sorted(current_set - previous_set)
    removed_since_previous = sorted(previous_set - current_set)

    sales_data_current = "sales_data.csv" in current_set
    sales_data_previous = "sales_data.csv" in previous_set

    mo.md(
        f"""
    ### Current commit files
    {', '.join(current_files) if current_files else '(none)'}

    ### Previous commit files (`{previous_commit.short_hash if previous_commit else 'N/A'}`)
    {', '.join(previous_files) if previous_files else '(none)'}

    ### Diff (current vs previous)
    - **Added in current**: {', '.join(added_since_previous) if added_since_previous else '(none)'}
    - **Removed in current**: {', '.join(removed_since_previous) if removed_since_previous else '(none)'}

    ### Concrete proof
    - `sales_data.csv` in current commit: **{sales_data_current}**
    - `sales_data.csv` in previous commit: **{sales_data_previous}**
    """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7) Architecture notes

    - Kirin uses linear commit history
    - files are stored by content hash (content-addressed)
    - dataset metadata is tracked in `datasets/<name>/commits.json`
    """)
    return


if __name__ == "__main__":
    app.run()
