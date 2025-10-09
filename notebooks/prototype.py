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

__generated_with = "0.16.4"
app = marimo.App(width="medium")


@app.cell
def _():
    # Kirin Capabilities Showcase - Linear data versioning, content-addressed storage
    import marimo as mo
    import polars as pl
    import os
    import tempfile
    from pathlib import Path

    return Path, mo, pl, tempfile


@app.cell
def _():
    # Import Kirin
    import kirin
    from kirin import Dataset, File, Commit

    return (Dataset, File, Commit)


@app.cell
def _(Dataset, Path, tempfile):
    # Create a new dataset to demonstrate Kirin's capabilities
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample data files
        data_dir = Path(temp_dir) / "data"
        data_dir.mkdir()
        
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
        ds = Dataset(root_dir=temp_dir, name="sales_analysis", description="Sales data analysis project")
        
        # Initial commit
        commit1 = ds.commit(
            message="Initial commit: Add sales data and notes",
            add_files=[csv_file, text_file]
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
            add_files=[updated_csv]
        )
        
        # Third commit - remove old file
        commit3 = ds.commit(
            message="Remove old sales data file",
            remove_files=["sales_data.csv"]
        )
        
        return ds, commit1, commit2, commit3


@app.cell
def _(ds, mo):
    # Display dataset information
    info = ds.get_info()
    mo.md(f"""
    **Dataset Information:**
    - **Name**: {info['name']}
    - **Description**: {info['description']}
    - **Current Commit**: {info['current_commit'][:8] if info['current_commit'] else 'None'}
    - **Total Commits**: {info['commit_count']}
    - **Files in Current Commit**: {len(ds.files)}
    """)


@app.cell
def _(ds, mo):
    # Show commit history
    history = ds.history(limit=5)
    mo.md("""
    **Commit History (Linear):**
    """)
    
    for i, commit in enumerate(history):
        mo.md(f"""
        **{i+1}. {commit.short_hash}** - {commit.message}
        - **Timestamp**: {commit.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
        - **Files**: {commit.get_file_count()}
        - **Size**: {commit.get_total_size():,} bytes
        """)


@app.cell
def _(ds, pl, mo):
    # Demonstrate file access and data processing
    mo.md("""
    **Data Processing with Current Commit:**
    """)
    
    # Access files using context manager
    with ds.local_files() as local_files:
        if "sales_data_v2.csv" in local_files:
            df = pl.read_csv(local_files["sales_data_v2.csv"])
            
            # Show data summary
            mo.md("**Sales Data Summary:**")
            summary = df.group_by("product").agg([
                pl.col("quantity").sum().alias("total_quantity"),
                pl.col("price").first().alias("price"),
                (pl.col("quantity") * pl.col("price")).sum().alias("total_revenue")
            ]).sort("total_revenue", descending=True)
            
            summary
        else:
            mo.md("No CSV file found in current commit")


@app.cell
def _(ds, mo):
    # Demonstrate file operations
    mo.md("""
    **File Operations:**
    """)
    
    # List files in current commit
    files = ds.list_files()
    mo.md(f"**Files in current commit**: {', '.join(files)}")
    
    # Access individual files
    if "notes.txt" in files:
        notes_content = ds.read_file("notes.txt", mode="r")
        mo.md("**Notes content:**")
        mo.md(f"```\n{notes_content}\n```")


@app.cell
def _(ds, mo):
    # Demonstrate checkout functionality
    mo.md("""
    **Checkout Previous Commit:**
    """)
    
    # Get commit history
    history = ds.history(limit=3)
    if len(history) > 1:
        # Checkout previous commit
        previous_commit = history[1]  # Second most recent
        ds.checkout(previous_commit.hash)
        
        mo.md(f"**Checked out commit**: {previous_commit.short_hash}")
        mo.md(f"**Files in this commit**: {', '.join(ds.list_files())}")
        
        # Show that we can still access files
        if "notes.txt" in ds.list_files():
            notes_content = ds.read_file("notes.txt", mode="r")
            mo.md("**Notes from previous commit:**")
            mo.md(f"```\n{notes_content}\n```")


@app.cell
def _(mo):
    # Key benefits and architecture overview
    mo.md("""
    **Kirin's Key Benefits:**

    ## 🎯 **Simplified Data Versioning**
    - **Linear History**: Simple, Git-like commits without branching complexity
    - **Content-Addressed Storage**: Files stored by content hash for integrity
    - **Backend Agnostic**: Works with local filesystem, S3, GCS, Azure, etc.

    ## 🚀 **Ergonomic Python API**
    ```python
    # Create dataset
    ds = Dataset(root_dir="/path/to/data", name="my_dataset")
    
    # Commit changes
    commit_hash = ds.commit(message="Add new data", add_files=["data.csv"])
    
    # Access files
    with ds.local_files() as files:
        df = pl.read_csv(files["data.csv"])
    
    # Checkout specific version
    ds.checkout(commit_hash)
    
    # Get history
    history = ds.history(limit=10)
    ```

    ## 🔧 **Content-Addressed Storage**
    - Files stored at `root_dir/data/{hash[:2]}/{hash[2:]}`
    - Automatic deduplication
    - Data integrity through hashing
    - Efficient storage for repeated content

    ## 📊 **Perfect for Data Science**
    - Works with any library expecting local files
    - Context managers for automatic cleanup
    - Exception-safe file handling
    - Cloud-native data workflows
    """)


@app.cell
def _(mo):
    # Architecture diagram
    mo.md("""
    **Kirin Architecture:**

    ```
    Dataset (Linear History)
    ├── Commit 1 (Initial)
    │   ├── File A (content-hashed)
    │   └── File B (content-hashed)
    ├── Commit 2 (Add File C)
    │   ├── File A (same hash, reused)
    │   ├── File B (same hash, reused)
    │   └── File C (new content-hash)
    └── Commit 3 (Remove File B)
        ├── File A (same hash, reused)
        └── File C (same hash, reused)
    ```

    **Storage Layout:**
    ```
    root_dir/
    ├── data/
    │   ├── ab/  # hash[:2]
    │   │   └── cdef1234...  # hash[2:]
    │   └── ef/
    │       └── 567890ab...
    └── datasets/
        └── my_dataset/
            └── commits.json  # Linear commit history
    ```
    """)


if __name__ == "__main__":
    app.run()
