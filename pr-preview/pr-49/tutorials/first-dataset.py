# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
#     "pandas",
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../../", editable = true }
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Your First Dataset

    This tutorial will guide you through creating and working with your first
    Kirin dataset. By the end, you'll understand the core concepts of datasets,
    commits, and how to work with versioned files.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What You'll Learn

    - How to create a dataset
    - How to add files to a dataset
    - How to view commit history
    - How to access files from different commits
    - How to update your dataset with new files
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prerequisites

    - Python 3.13 or higher
    - Kirin installed (see [Installation Guide](../getting-started/installation.md))
    """)
    return


@app.cell
def _():
    import tempfile
    from pathlib import Path

    from kirin import Catalog

    # Create a temporary directory for our tutorial
    # In production, you might use: Catalog(root_dir="s3://my-bucket/data")
    temp_dir = Path(tempfile.mkdtemp(prefix="kirin_tutorial_"))
    catalog = Catalog(root_dir=temp_dir)

    # Create a new dataset
    my_dataset = catalog.create_dataset(
        "my_first_dataset", description="My first Kirin dataset for learning"
    )
    my_dataset
    return Path, my_dataset, temp_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Understanding Datasets

    A **dataset** in Kirin is a collection of versioned files. Think of it
    like a Git repository, but specifically designed for data files. Each
    dataset has:

    - A **name** that identifies it
    - A **linear commit history** that tracks changes over time
    - **Files** that are stored using content-addressed storage

    **Tip**: When you display a dataset in a notebook cell (like `my_dataset`
    above), Kirin shows an interactive HTML view with a "Copy Code to Access"
    button for each file. The copied code uses "dataset" by default, but you
    can customize it by setting `my_dataset._repr_variable_name = "my_dataset"`.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Preparing Your First Files

    Before we can commit files, let's create some sample data files to work with.
    """)
    return


@app.cell
def _(temp_dir):
    # Create a directory for our data files
    data_dir = temp_dir / "sample_data"
    data_dir.mkdir(exist_ok=True)

    # Create a simple CSV file
    csv_file = data_dir / "data.csv"
    csv_file.write_text("""name,age,city
    Alice,28,New York
    Bob,35,San Francisco
    Carol,42,Chicago
    """)

    # Create a JSON configuration file
    config_file = data_dir / "config.json"
    config_file.write_text("""{
    "version": "1.0",
    "description": "Sample dataset configuration",
    "columns": ["name", "age", "city"]
    }
    """)

    print("✅ Created files:")
    print(f"   - {csv_file.name}")
    print(f"   - {config_file.name}")
    return config_file, csv_file, data_dir


@app.cell
def _(config_file, csv_file, my_dataset):
    # Commit files to the dataset
    my_dataset.commit(
        message="Initial commit: Add sample data and configuration",
        add_files=[str(csv_file), str(config_file)],
    )

    # Display the current commit with rich HTML
    my_dataset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Making Your First Commit

    Now let's add these files to our dataset. This creates your first commit.

    **What just happened?**

    - Kirin calculated content hashes for each file
    - Files were stored in content-addressed storage
    - A commit was created that references these files
    - The commit was added to the dataset's linear history
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Viewing Your Commit History

    Let's see what we've created. You should see your first commit listed
    with the files you added.
    """)
    return


@app.cell
def _(dataset):
    # Display the dataset which shows files in the current commit
    dataset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Accessing Files from a Commit

    Now let's access the files from the current commit.
    """)
    return


@app.cell
def _(Path, dataset):
    # Access files as local paths
    with dataset.local_files() as local_files:
        # Files are lazily downloaded when accessed
        csv_path = local_files["data.csv"]
        config_path = local_files["config.json"]

        # Now you can use standard Python file operations
        print("📂 Local file paths:")
        print(f"   CSV: {csv_path}")
        print(f"   Config: {config_path}")

        # Read file content
        csv_content = Path(csv_path).read_text()
        print("\n📝 CSV content:")
        print(csv_content)

        # Or use with data science libraries
        import pandas as pd

        df = pd.read_csv(csv_path)
        print("\n📊 DataFrame:")
        print(f"   Shape: {df.shape}")
        print(df)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Step 6: Working with Files Locally

    The recommended way to work with files is using the `local_files()`
    context manager. This downloads files on-demand and cleans them up
    automatically.

    **Key points:**

    - Files are only downloaded when you access them (lazy loading)
    - Files are automatically cleaned up when you exit the context manager
    - You can use standard Python libraries (pandas, polars, etc.) with the
      local paths
    """)
    return


@app.cell
def _(data_dir, dataset):
    from datetime import datetime

    # Create a new file
    results_file = data_dir / "results.txt"
    results_file.write_text("""Analysis Results
    ================
    Total records: 3
    Average age: 35.0
    Cities: New York, San Francisco, Chicago
    """)

    # Commit the new file
    commit_msg = (
        f"Add analysis results - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    dataset.commit(
        message=commit_msg,
        add_files=[str(results_file)],
    )

    # Display the current commit with rich HTML
    dataset.current_commit
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Step 7: Adding More Files

    Let's add another file to see how the commit history grows.
    """)
    return


@app.cell
def _(dataset):
    # Display the dataset which shows updated commit history
    updated_history = dataset.history()
    dataset
    return (updated_history,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 8: Viewing the Updated History

    Let's see how the history has changed. Notice how the commit history is
    linear - each commit builds on the previous one.
    """)
    return


@app.cell
def _(dataset, updated_history):
    # Get the first commit
    first_commit = updated_history[-1]  # Oldest commit is last in history

    # Checkout the first commit and display it
    dataset.checkout(first_commit.hash)
    first_commit

    # Checkout the latest commit and display the dataset
    dataset.checkout()  # No argument = latest commit
    dataset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 9: Checking Out Different Commits

    You can checkout any commit to see what files were available at that point.
    """)
    return


@app.cell
def _(csv_file, data_dir, dataset):
    # Create a file with the same content as data.csv
    duplicate_file = data_dir / "data_copy.csv"
    duplicate_file.write_text(csv_file.read_text())

    # Commit the duplicate
    dataset.commit(message="Add duplicate file", add_files=[str(duplicate_file)])

    # Check the file objects
    original = dataset.get_file("data.csv")
    duplicate = dataset.get_file("data_copy.csv")

    print("🔍 Content-Addressed Storage Demo:")
    print(f"   Original file hash: {original.hash}")
    print(f"   Duplicate file hash: {duplicate.hash}")
    print(f"   Same content = Same hash: {original.hash == duplicate.hash}")
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Understanding Content-Addressed Storage

    One of Kirin's key features is content-addressed storage. This means:

    - Files are stored by their content hash, not by filename
    - Identical files are automatically deduplicated
    - File integrity is guaranteed by the hash

    Even though the files have different names, they have the same content
    hash, so Kirin stores them only once!
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 10: Removing Files

    You can also remove files from a dataset.
    """)
    return


@app.cell
def _(dataset):
    # Remove a file
    dataset.commit(message="Remove duplicate file", remove_files=["data_copy.csv"])

    # Display the dataset to see updated state
    dataset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 11: Combining Operations

    You can add and remove files in the same commit.
    """)
    return


@app.cell
def _(data_dir, dataset):
    # Create a summary report file
    summary_report = data_dir / "monthly_summary.json"
    summary_report.write_text("""{
    "period": "2024-01",
    "total_records": 3,
    "average_age": 35.0,
    "cities": ["New York", "San Francisco", "Chicago"],
    "generated_at": "2024-01-15T10:00:00Z"
    }
    """)

    # Add summary report and remove detailed processing log
    # These are different types of files: summary vs detailed logs
    dataset.commit(
        message="Add monthly summary, remove detailed processing logs",
        add_files=[str(summary_report)],
        remove_files=["results.txt"],
    )

    # Display the dataset to see updated state
    dataset
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Summary

    Congratulations! You've learned the fundamentals of working with Kirin datasets:

    - ✅ **Created a dataset** using a catalog
    - ✅ **Made commits** to track file changes
    - ✅ **Viewed commit history** to see how your dataset evolved
    - ✅ **Accessed files** from different commits
    - ✅ **Worked with files locally** using the context manager
    - ✅ **Understood content-addressed storage** and deduplication
    - ✅ **Updated datasets** by adding and removing files

    ## Key Concepts

    - **Dataset**: A collection of versioned files with linear commit history
    - **Commit**: A snapshot of files at a point in time
    - **Content-addressed storage**: Files stored by content hash for
      integrity and deduplication
    - **Linear history**: Simple, sequential commits without branching
      complexity

    ## Next Steps

    - **[Working with Commits](commits.md)** - Deep dive into commit
      operations and history
    - **[Cloud Storage Overview](cloud-storage.md)** - Learn about using
      cloud storage backends
    - **[Track Model Training Data](../how-to/track-model-data.md)** - See
      a real-world example with ML models
    """)
    return


if __name__ == "__main__":
    app.run()
