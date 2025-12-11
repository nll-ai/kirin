# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
#     "pandas",
#     "marimo>=0.17.0",
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
    dataset = catalog.create_dataset(
        "my_first_dataset", description="My first Kirin dataset for learning"
    )

    print(f"✅ Created dataset: {dataset.name}")
    print(f"   Dataset root: {dataset.root_dir}")
    return Path, dataset, temp_dir


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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Preparing Your First Files

    Before we can commit files, let's create some sample data files to work with.
    """)
    return


@app.cell
def _(config_file, csv_file, dataset):
    # Commit files to the dataset
    commit_hash = dataset.commit(
        message="Initial commit: Add sample data and configuration",
        add_files=[str(csv_file), str(config_file)],
    )

    print(f"✅ Created commit: {commit_hash}")
    print(f"   Short hash: {commit_hash[:8]}")
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


@app.cell
def _(dataset):
    # Get the commit history
    history = dataset.history()

    print(f"📊 Total commits: {len(history)}")
    print("\nCommit history:")
    for current_commit in history:
        print(f"  {current_commit.short_hash}: {current_commit.message}")
        print(f"    Files: {current_commit.list_files()}")
        print(f"    Date: {current_commit.timestamp}")
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
    # List files in the current commit
    files = dataset.files
    print(f"📁 Files in current commit: {list(files.keys())}")

    # Get information about a specific file
    file_obj = dataset.get_file("data.csv")
    if file_obj:
        print("\n📄 File details:")
        print(f"   Name: {file_obj.name}")
        print(f"   Size: {file_obj.size} bytes")
        print(f"   Hash: {file_obj.hash[:16]}...")
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


@app.cell(hide_code=True)
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
    new_commit_hash = dataset.commit(
        message=commit_msg,
        add_files=[str(results_file)],
    )

    print(f"✅ Created new commit: {new_commit_hash[:8]}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7: Adding More Files

    Let's add another file to see how the commit history grows.
    """)
    return


@app.cell
def _(dataset):
    # Get updated history
    updated_history = dataset.history()

    print(f"📊 Total commits: {len(updated_history)}")
    print("\nFull commit history:")
    for i, history_commit in enumerate(updated_history, 1):
        print(f"{i}. {history_commit.short_hash}: {history_commit.message}")
        print(f"   Files: {', '.join(history_commit.list_files())}")
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
    print(f"🔍 First commit: {first_commit.short_hash}")

    # Checkout the first commit
    dataset.checkout(first_commit.hash)

    # See what files are available
    print(f"\n📁 Files in first commit: {list(dataset.files.keys())}")

    # Checkout the latest commit
    dataset.checkout()  # No argument = latest commit
    print(f"\n📁 Files in latest commit: {list(dataset.files.keys())}")
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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 10: Understanding Content-Addressed Storage

    One of Kirin's key features is content-addressed storage. This means:

    - Files are stored by their content hash, not by filename
    - Identical files are automatically deduplicated
    - File integrity is guaranteed by the hash

    Even though the files have different names, they have the same content
    hash, so Kirin stores them only once!
    """)
    return


@app.cell
def _(dataset):
    # Remove a file
    dataset.commit(message="Remove duplicate file", remove_files=["data_copy.csv"])

    # Verify the file is gone
    print("✅ Removed file")
    print(f"   Files after removal: {list(dataset.files.keys())}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 11: Removing Files

    You can also remove files from a dataset.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 12: Combining Operations

    You can add and remove files in the same commit.
    """)
    return


@app.cell
def _(data_dir, dataset):
    # Create a new file
    updated_config = data_dir / "config_v2.json"
    updated_config.write_text("""{
    "version": "2.0",
    "description": "Updated configuration",
    "columns": ["name", "age", "city", "country"]
    }
    """)

    # Update dataset: add new file, remove old one
    update_commit = dataset.commit(
        message="Update configuration to v2",
        add_files=[str(updated_config)],
        remove_files=["config.json"],
    )

    print("✅ Updated dataset")
    print(f"   Commit: {update_commit[:8]}")
    print(f"   Files after update: {list(dataset.files.keys())}")
    return


@app.cell(hide_code=True)
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
