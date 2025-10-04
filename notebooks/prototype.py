# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "gitdata==0.0.1",
#     "anthropic==0.69.0",
# ]
#
# [tool.uv.sources]
# gitdata = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.16.4"
app = marimo.App(width="medium")


@app.cell
def _():
    # GitData Capabilities Showcase - Lazy loading, context managers, cloud storage
    import marimo as mo
    import polars as pl
    import os
    import tempfile
    from pathlib import Path

    return Path, mo, pl, tempfile


@app.cell
def _():
    # Import GitData
    import gitdata
    from gitdata.dataset import Dataset

    return (Dataset,)


@app.cell
def _(Dataset):
    # Load dataset from Google Cloud Storage
    ds = Dataset(root_dir="gs://gitdata-test-bucket", dataset_name="dummy")
    return (ds,)


@app.cell
def _(ds):
    # Checkout specific commit
    ds.checkout("5c27f392")
    return


@app.cell
def _(ds, mo):
    # Audio file access with lazy loading - file only downloaded when accessed
    with ds.local_files() as audio_files:
        audio_file = audio_files[
            "厦门六中合唱团全新演绎《夜空中最亮的星》 [-uzuhqQIaTM].mp3"
        ]
        audio = mo.audio(src=audio_file)

    audio
    return


@app.cell
def _(Dataset, Path, pl, tempfile):
    # Data processing with Polars - demonstrates CSV handling
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample data
        csv_file = Path(temp_dir) / "sample_data.csv"
        csv_file.write_text("""name,age,city,score
    Alice,30,New York,95.5
    Bob,25,London,87.2
    Charlie,35,Paris,92.8
    Diana,28,Tokyo,89.1
    Eve,32,Berlin,94.3""")

        # Create dataset and commit file
        demo_ds = Dataset(root_dir=temp_dir, dataset_name="demo")
        demo_ds.commit(commit_message="Add sample data", add_files=[csv_file])

        # Process data with context manager
        with demo_ds.local_files() as data_files:
            df = pl.read_csv(data_files["sample_data.csv"])
            summary = (
                df.group_by("city")
                .agg(
                    [
                        pl.col("age").mean().alias("avg_age"),
                        pl.col("score").mean().alias("avg_score"),
                        pl.col("name").count().alias("count"),
                    ]
                )
                .sort("avg_score", descending=True)
            )

    summary
    return


@app.cell
def _(ds, mo):
    # Commit history visualization
    mo.mermaid(ds.commit_history_mermaid())
    return


@app.cell
def _(mo):
    # Alternative file access methods
    mo.md("""
    **File Access Patterns:**

    ```python
    # Context Manager (Recommended)
    with ds.local_files() as local_files:
        df = pl.read_csv(local_files["data.csv"])

    # Single File Download
    local_path = ds.get_local_path("data.csv")
    df = pl.read_csv(local_path)
    os.unlink(local_path)  # Manual cleanup

    # Direct Content Access
    content = ds.get_file_content("data.txt", mode="r")

    # Streaming for Large Files
    with ds.open_file("large_file.csv", mode="r") as f:
        df = pl.read_csv(f)
    ```
    """)
    return


@app.cell
def _(mo):
    # Key benefits and problem/solution comparison
    mo.md("""
    **The Problem GitData Solves:**

    ```python
    # ❌ This doesn't work with remote storage
    audio_file = ds.file_dict["audio.mp3"]  # Returns: "gs://bucket/path/audio.mp3"
    mo.audio(src=audio_file)  # Fails - not a local path!

    # ✅ GitData's solution
    with ds.local_files() as local_files:
        audio_file = local_files["audio.mp3"]  # Returns: "/tmp/local_audio.mp3"
        mo.audio(src=audio_file)  # Works perfectly!
    ```

    **Key Benefits:**
    - 🚀 **Lazy Loading**: Only download what you need
    - 🧹 **Automatic Cleanup**: No manual file management
    - 🔄 **Exception Safety**: Cleanup even on errors
    - 📁 **Cloud Native**: Works with any storage backend
    - 🎯 **Library Integration**: Works with any library expecting local paths
    - ⚡ **Performance**: Efficient bandwidth and storage usage
    """)
    return


if __name__ == "__main__":
    app.run()
