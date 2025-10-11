# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin==0.0.1",
#     "anthropic==0.69.0",
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
    # Kirin Capabilities Showcase - Linear data versioning, content-addressed storage
    from pathlib import Path

    import marimo as mo
    import polars as pl

    from kirin import Dataset
    return Dataset, Path, mo, pl


@app.cell
def _(Dataset, Path):
    # Create a new dataset to demonstrate Kirin's capabilities
    # Use a persistent directory instead of temporary one
    demo_dir = Path("/tmp/kirin_demo")
    demo_dir.mkdir(exist_ok=True)

    # Create sample data files
    data_dir = demo_dir / "data"
    data_dir.mkdir(exist_ok=True)

    # Create sample CSV data
    csv_file = data_dir / "sales_data.csv"
    csv_file.write_text("""product,price,quantity,date
    Widget A,29.99,100,2024-01-15
    Widget B,19.99,150,2024-01-16
    Widget C,39.99,75,2024-01-17
    Widget A,29.99,120,2024-01-18
    Widget B,19.99,200,2024-01-19""")

    # Create sample text data
    text_file = data_dir / "notes.txt"
    text_file.write_text("""Project Notes:
    - Widget A is our best seller
    - Widget B has high volume but lower margin
    - Widget C is premium but lower volume
    - Consider price optimization for Q2""")

    # Create dataset and commit files
    ds = Dataset(
        root_dir=str(demo_dir),
        name="sales_analysis",
        description="Sales data analysis project",
    )

    # Initial commit
    commit1 = ds.commit(
        message="Initial commit: Add sales data and notes",
        add_files=[csv_file, text_file],
    )

    # Create updated data for second commit
    updated_csv = data_dir / "sales_data_v2.csv"
    updated_csv.write_text("""product,price,quantity,date
    Widget A,29.99,100,2024-01-15
    Widget B,19.99,150,2024-01-16
    Widget C,39.99,75,2024-01-17
    Widget A,29.99,120,2024-01-18
    Widget B,19.99,200,2024-01-19
    Widget D,49.99,50,2024-01-20
    Widget A,29.99,80,2024-01-21""")

    # Second commit
    commit2 = ds.commit(
        message="Add new product Widget D and additional sales",
        add_files=[updated_csv],
    )

    # Third commit - remove old file
    commit3 = ds.commit(
        message="Remove old sales data file", remove_files=["sales_data.csv"]
    )
    return (ds,)


@app.cell
def _(ds):
    # Display dataset information
    info = ds.get_info()
    return (info,)


@app.cell
def _(ds, info, mo):
    str_dataset_info = ""
    str_dataset_info += "**Dataset Information:**\n"
    str_dataset_info += f"- **Name**: {info['name']}\n"
    str_dataset_info += f"- **Description**: {info['description']}\n"
    str_dataset_info += f"- **Current Commit**: {info['current_commit'][:8] if info['current_commit'] else 'None'}\n"
    str_dataset_info += f"- **Total Commits**: {info['commit_count']}\n"
    str_dataset_info += f"- **Files in Current Commit**: {len(ds.files)}\n"

    mo.md(str_dataset_info)
    return


@app.cell
def _(ds):
    # Show commit history
    commit_history = ds.history(limit=5)
    return (commit_history,)


@app.cell
def _(commit_history, mo):
    str_commit_history = ""

    str_commit_history += "**Commit History (Linear):\n**"

    for _i, _commit in enumerate(commit_history):
        str_commit_history += f"""
    **{_i + 1}. {_commit.short_hash}** - {_commit.message}
    - **Timestamp**: {_commit.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
    - **Files**: {_commit.get_file_count()}
    - **Size**: {_commit.get_total_size():,} bytes
    """

    mo.md(str_commit_history)
    return


@app.cell
def _(commit_history, mo):
    str_commit_details = ""
    for i, commit in enumerate(commit_history):
        str_commit_details += f"""
    **{i + 1}. {commit.short_hash}** - {commit.message}
    - **Timestamp**: {commit.timestamp.strftime("%Y-%m-%d %H:%M:%S")}
    - **Files**: {commit.get_file_count()}
    - **Size**: {commit.get_total_size():,} bytes
    """

    mo.md(str_commit_details)
    return


@app.cell
def _(ds, pl):
    # Demonstrate file access and data processing
    # Access files using context manager
    summary = None
    has_csv = False

    with ds.local_files() as local_files:
        if "sales_data_v2.csv" in local_files:
            df = pl.read_csv(local_files["sales_data_v2.csv"])

            # Show data summary
            summary = (
                df.group_by("product")
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
            has_csv = True
    summary
    return has_csv, summary


@app.cell
def _(has_csv, mo, summary):
    str_data_processing = ""
    str_data_processing += "**Data Processing with Current Commit:**\n"

    if has_csv and summary is not None:
        str_data_processing += "**Sales Data Summary:**\n"
        _disp = mo.md(str_data_processing)
        summary
    else:
        str_data_processing += "No CSV file found in current commit\n"
        _disp = mo.md(str_data_processing)
    _disp
    return


@app.cell
def _(ds):
    # Demonstrate file operations
    # List files in current commit
    files = ds.list_files()

    # Access individual files
    current_notes = None
    has_notes = False

    if "notes.txt" in files:
        current_notes = ds.read_file("notes.txt", mode="r")
        has_notes = True
    return current_notes, files, has_notes


@app.cell
def _(files, mo):
    str_file_operations = ""
    str_file_operations += "**File Operations:**\n\n"
    str_file_operations += f"**Files in current commit**: {', '.join(files)}\n"

    mo.md(str_file_operations)
    return


@app.cell
def _(current_notes, has_notes, mo):
    if has_notes and current_notes is not None:
        str_notes_content = ""
        str_notes_content += "**Notes content:**\n"
        str_notes_content += f"```\n{current_notes}\n```\n"

    mo.md(str_notes_content)
    return


@app.cell
def _(ds):
    # Demonstrate checkout functionality
    # Get commit history
    checkout_history = ds.history(limit=3)
    previous_commit = None
    previous_notes = None
    has_previous = False

    if len(checkout_history) > 1:
        # Checkout previous commit
        previous_commit = checkout_history[1]  # Second most recent
        ds.checkout(previous_commit.hash)

        # Show that we can still access files
        if "notes.txt" in ds.list_files():
            previous_notes = ds.read_file("notes.txt", mode="r")
            has_previous = True
    return has_previous, previous_commit, previous_notes


@app.cell
def _(mo):
    str_checkout_header = ""
    str_checkout_header += "**Checkout Previous Commit:**\n"

    mo.md(str_checkout_header)
    return


@app.cell
def _(ds, has_previous, mo, previous_commit, previous_notes):
    if previous_commit is not None:
        str_checkout_info = ""
        str_checkout_info += (
            f"**Checked out commit**: {previous_commit.short_hash}\n"
        )
        str_checkout_info += (
            f"**Files in this commit**: {', '.join(ds.list_files())}\n"
        )

        if has_previous and previous_notes is not None:
            str_checkout_info += "**Notes from previous commit:**\n"
            str_checkout_info += f"```\n{previous_notes}\n```\n"

        mo.md(str_checkout_info)
    return


@app.cell
def _(mo):
    # Key benefits and architecture overview
    str_benefits = ""
    str_benefits += "**Kirin's Key Benefits:**\n\n"
    str_benefits += "## 🎯 **Simplified Data Versioning**\n"
    str_benefits += "- **Linear History**: Simple, Git-like commits without branching complexity\n"
    str_benefits += "- **Content-Addressed Storage**: Files stored by content hash for integrity\n"
    str_benefits += "- **Backend Agnostic**: Works with local filesystem, S3, GCS, Azure, etc.\n\n"
    str_benefits += "## 🚀 **Ergonomic Python API**\n"
    str_benefits += "```python\n"
    str_benefits += "# Create dataset\n"
    str_benefits += 'ds = Dataset(root_dir="/path/to/data", name="my_dataset")\n\n'
    str_benefits += "# Commit changes\n"
    str_benefits += 'commit_hash = ds.commit(message="Add new data", add_files=["data.csv"])\n\n'
    str_benefits += "# Access files\n"
    str_benefits += "with ds.local_files() as files:\n"
    str_benefits += '    df = pl.read_csv(files["data.csv"])\n\n'
    str_benefits += "# Checkout specific version\n"
    str_benefits += "ds.checkout(commit_hash)\n\n"
    str_benefits += "# Get history\n"
    str_benefits += "history = ds.history(limit=10)\n"
    str_benefits += "```\n\n"
    str_benefits += "## 🔧 **Content-Addressed Storage**\n"
    str_benefits += "- Files stored at `root_dir/data/{hash[:2]}/{hash[2:]}`\n"
    str_benefits += "- Automatic deduplication\n"
    str_benefits += "- Data integrity through hashing\n"
    str_benefits += "- Efficient storage for repeated content\n\n"
    str_benefits += "## 📊 **Perfect for Data Science**\n"
    str_benefits += "- Works with any library expecting local files\n"
    str_benefits += "- Context managers for automatic cleanup\n"
    str_benefits += "- Exception-safe file handling\n"
    str_benefits += "- Cloud-native data workflows\n"

    mo.md(str_benefits)
    return


@app.cell
def _(mo):
    # Architecture diagram
    str_architecture = ""
    str_architecture += "**Kirin Architecture:**\n\n"
    str_architecture += "```\n"
    str_architecture += "Dataset (Linear History)\n"
    str_architecture += "├── Commit 1 (Initial)\n"
    str_architecture += "│   ├── File A (content-hashed)\n"
    str_architecture += "│   └── File B (content-hashed)\n"
    str_architecture += "├── Commit 2 (Add File C)\n"
    str_architecture += "│   ├── File A (same hash, reused)\n"
    str_architecture += "│   ├── File B (same hash, reused)\n"
    str_architecture += "│   └── File C (new content-hash)\n"
    str_architecture += "└── Commit 3 (Remove File B)\n"
    str_architecture += "    ├── File A (same hash, reused)\n"
    str_architecture += "    └── File C (same hash, reused)\n"
    str_architecture += "```\n\n"
    str_architecture += "**Storage Layout:**\n"
    str_architecture += "```\n"
    str_architecture += "root_dir/\n"
    str_architecture += "├── data/\n"
    str_architecture += "│   ├── ab/  # hash[:2]\n"
    str_architecture += "│   │   └── cdef1234...  # hash[2:]\n"
    str_architecture += "│   └── ef/\n"
    str_architecture += "│       └── 567890ab...\n"
    str_architecture += "└── datasets/\n"
    str_architecture += "    └── my_dataset/\n"
    str_architecture += "        └── commits.json  # Linear commit history\n"
    str_architecture += "```\n"

    mo.md(str_architecture)
    return


if __name__ == "__main__":
    app.run()
