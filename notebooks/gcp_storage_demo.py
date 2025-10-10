# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "kirin==0.0.1",
#     "anthropic==0.69.0",
#     "loguru==0.7.3",
#     "gcsfs>=2024.2.0",
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
    # Kirin GCP Storage Demo - Cloud-native data versioning with Google Cloud Storage
    import marimo as mo
    import polars as pl
    from pathlib import Path
    import tempfile
    from kirin import Dataset, File, Commit

    return Dataset, Path, mo, pl, tempfile


@app.cell
def _(Dataset, Path, tempfile):
    # Create a dataset using Google Cloud Storage
    # Initialize dataset with GCS bucket
    ds = Dataset("gs://kirin-test-bucket", name="test-dataset")

    # Create temporary local files for demonstration
    temp_dir = Path(tempfile.mkdtemp())

    # Create sample data files
    data_dir = temp_dir / "data"
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

    # Create sample JSON data
    json_file = data_dir / "config.json"
    json_file.write_text("""{
    "project_name": "Widget Analytics",
    "version": "1.0.0",
    "settings": {
        "auto_backup": true,
        "retention_days": 30
    }
    }""")
    return csv_file, data_dir, ds, json_file, text_file


@app.cell
def _(csv_file, ds, json_file, text_file):
    # Initial commit to GCS
    commit1 = ds.commit(
        message="Initial commit: Add sales data, notes, and config to GCS",
        add_files=[csv_file, text_file, json_file],
    )
    return


@app.cell
def _(data_dir):
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

    # Create additional analysis file
    analysis_file = data_dir / "analysis.py"
    analysis_file.write_text("""# Sales Analysis Script
    import polars as pl

    def analyze_sales(df):
    \"\"\"Analyze sales data and return summary.\"\"\"
    return df.group_by("product").agg([
        pl.col("quantity").sum().alias("total_quantity"),
        pl.col("price").first().alias("price"),
        (pl.col("quantity") * pl.col("price")).sum().alias("total_revenue")
    ]).sort("total_revenue", descending=True)

    if __name__ == "__main__":
    # Load and analyze data
    df = pl.read_csv("sales_data_v2.csv")
    summary = analyze_sales(df)
    print(summary)
    """)
    return analysis_file, updated_csv


@app.cell
def _(analysis_file, ds, updated_csv):
    # Second commit - add new files to GCS
    commit2 = ds.commit(
        message="Add new product Widget D and analysis script",
        add_files=[updated_csv, analysis_file],
    )
    return


@app.cell
def _(ds):
    # Third commit - remove old file
    commit3 = ds.commit(
        message="Remove old sales data file from GCS", remove_files=["sales_data.csv"]
    )
    return


@app.cell
def _(ds):
    # Display dataset information
    info = ds.get_info()
    return (info,)


@app.cell
def _(ds, info, mo):
    str_dataset_info = ""
    str_dataset_info += "**GCP Dataset Information:**\n"
    str_dataset_info += f"- **Name**: {info['name']}\n"
    str_dataset_info += f"- **Description**: {info['description']}\n"
    str_dataset_info += "- **Storage**: Google Cloud Storage (gs://kirin-test-bucket)\n"
    current_commit = info["current_commit"][:8] if info["current_commit"] else "None"
    str_dataset_info += f"- **Current Commit**: {current_commit}\n"
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
    str_commit_history = "**GCP Commit History (Linear):**\n"

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
def _(ds, pl):
    # Demonstrate file access and data processing from GCS
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
    str_data_processing += "**Data Processing with GCS Files:**\n"

    if has_csv and summary is not None:
        str_data_processing += "**Sales Data Summary (from GCS):**\n"
        _disp = mo.md(str_data_processing)
        summary
    else:
        str_data_processing += "No CSV file found in current commit\n"
        _disp = mo.md(str_data_processing)
    _disp
    return


@app.cell
def _(ds):
    # Demonstrate file operations with GCS
    # List files in current commit
    files = ds.list_files()

    # Access individual files
    current_notes = None
    current_config = None
    has_notes = False
    has_config = False

    if "notes.txt" in files:
        current_notes = ds.read_file("notes.txt", mode="r")
        has_notes = True

    if "config.json" in files:
        current_config = ds.read_file("config.json", mode="r")
        has_config = True
    return current_config, current_notes, files, has_config, has_notes


@app.cell
def _(files, mo):
    str_file_operations = ""
    str_file_operations += "**GCS File Operations:**\n\n"
    str_file_operations += f"**Files in current commit**: {', '.join(files)}\n"

    mo.md(str_file_operations)
    return


@app.cell
def _(current_config, current_notes, has_config, has_notes, mo):
    str_file_contents = ""

    if has_notes and current_notes is not None:
        str_file_contents += "**Notes content (from GCS):**\n"
        str_file_contents += f"```\n{current_notes}\n```\n\n"

    if has_config and current_config is not None:
        str_file_contents += "**Config content (from GCS):**\n"
        str_file_contents += f"```json\n{current_config}\n```\n"

    mo.md(str_file_contents)
    return


@app.cell
def _(ds):
    # Demonstrate checkout functionality with GCS
    # Get commit history
    checkout_history = ds.history(limit=3)
    previous_commit = None
    previous_notes = None
    has_previous = False

    if len(checkout_history) > 1:
        # Checkout previous commit
        previous_commit = checkout_history[1]  # Second most recent
        ds.checkout(previous_commit.hash)

        # Show that we can still access files from GCS
        if "notes.txt" in ds.list_files():
            previous_notes = ds.read_file("notes.txt", mode="r")
            has_previous = True
    return has_previous, previous_commit, previous_notes


@app.cell
def _(mo):
    str_checkout_header = ""
    str_checkout_header += "**Checkout Previous Commit (GCS):**\n"

    mo.md(str_checkout_header)
    return


@app.cell
def _(ds, has_previous, mo, previous_commit, previous_notes):
    if previous_commit is not None:
        str_checkout_info = ""
        str_checkout_info += f"**Checked out commit**: {previous_commit.short_hash}\n"
        str_checkout_info += f"**Files in this commit**: {', '.join(ds.list_files())}\n"

        if has_previous and previous_notes is not None:
            str_checkout_info += "**Notes from previous commit (GCS):**\n"
            str_checkout_info += f"```\n{previous_notes}\n```\n"

        mo.md(str_checkout_info)
    return


@app.cell
def _(mo):
    # Key benefits and GCS architecture overview
    str_benefits = ""
    str_benefits += "**Kirin with Google Cloud Storage:**\n\n"
    str_benefits += "## ☁️ **Cloud-Native Data Versioning**\n"
    str_benefits += (
        "- **GCS Integration**: Direct storage in Google Cloud Storage buckets\n"
    )
    str_benefits += (
        "- **Linear History**: Simple, Git-like commits without branching complexity\n"
    )
    str_benefits += (
        "- **Content-Addressed Storage**: Files stored by content hash for integrity\n"
    )
    str_benefits += (
        "- **Backend Agnostic**: Works with local filesystem, S3, GCS, Azure, etc.\n\n"
    )
    str_benefits += "## 🚀 **Ergonomic Python API for Cloud**\n"
    str_benefits += "```python\n"
    str_benefits += "# Create dataset with GCS\n"
    str_benefits += 'ds = Dataset("gs://my-bucket")\n\n'
    str_benefits += "# Commit changes to cloud\n"
    str_benefits += (
        'commit_hash = ds.commit(message="Add new data", add_files=["data.csv"])\n\n'
    )
    str_benefits += "# Access files from cloud\n"
    str_benefits += "with ds.local_files() as files:\n"
    str_benefits += '    df = pl.read_csv(files["data.csv"])\n\n'
    str_benefits += "# Checkout specific version from cloud\n"
    str_benefits += "ds.checkout(commit_hash)\n\n"
    str_benefits += "# Get history from cloud\n"
    str_benefits += "history = ds.history(limit=10)\n"
    str_benefits += "```\n\n"
    str_benefits += "## 🔧 **GCS Content-Addressed Storage**\n"
    str_benefits += "- Files stored at `gs://bucket/data/{hash[:2]}/{hash[2:]}`\n"
    str_benefits += "- Automatic deduplication across commits\n"
    str_benefits += "- Data integrity through hashing\n"
    str_benefits += "- Efficient storage for repeated content\n"
    str_benefits += "- Cloud-native performance\n\n"
    str_benefits += "## 📊 **Perfect for Cloud Data Science**\n"
    str_benefits += "- Works with any library expecting local files\n"
    str_benefits += "- Context managers for automatic cleanup\n"
    str_benefits += "- Exception-safe file handling\n"
    str_benefits += "- Seamless cloud-to-local workflows\n"
    str_benefits += "- No data movement for processing\n"

    mo.md(str_benefits)
    return


@app.cell
def _(mo):
    # GCS Architecture diagram
    str_architecture = ""
    str_architecture += "**Kirin GCS Architecture:**\n\n"
    str_architecture += "```\n"
    str_architecture += "GCS Bucket (gs://kirin-test-bucket)\n"
    str_architecture += "├── data/  # Content-addressed storage\n"
    str_architecture += "│   ├── ab/  # hash[:2]\n"
    str_architecture += "│   │   └── cdef1234...  # hash[2:]\n"
    str_architecture += "│   └── ef/\n"
    str_architecture += "│       └── 567890ab...\n"
    str_architecture += "└── datasets/  # Linear commit history\n"
    str_architecture += "    └── my_dataset/\n"
    str_architecture += "        └── commits.json\n"
    str_architecture += "```\n\n"
    str_architecture += "**Linear Commit History in GCS:**\n"
    str_architecture += "```\n"
    str_architecture += "Commit 1 (Initial) → GCS\n"
    str_architecture += "├── File A (content-hashed in GCS)\n"
    str_architecture += "└── File B (content-hashed in GCS)\n"
    str_architecture += "    ↓\n"
    str_architecture += "Commit 2 (Add File C) → GCS\n"
    str_architecture += "├── File A (same hash, reused)\n"
    str_architecture += "├── File B (same hash, reused)\n"
    str_architecture += "└── File C (new content-hash in GCS)\n"
    str_architecture += "    ↓\n"
    str_architecture += "Commit 3 (Remove File B) → GCS\n"
    str_architecture += "├── File A (same hash, reused)\n"
    str_architecture += "└── File C (same hash, reused)\n"
    str_architecture += "```\n\n"
    str_architecture += "**Benefits of GCS Storage:**\n"
    str_architecture += "- **Scalability**: Handle petabytes of data\n"
    str_architecture += "- **Durability**: 99.999999999% (11 9's) annual durability\n"
    str_architecture += "- **Performance**: Global edge caching\n"
    str_architecture += "- **Cost**: Pay only for what you use\n"
    str_architecture += "- **Integration**: Native GCP ecosystem support\n"

    mo.md(str_architecture)
    return


@app.cell
def _(mo):
    # GCS-specific benefits
    str_gcs_benefits = ""
    str_gcs_benefits += "**Google Cloud Storage Benefits:**\n\n"
    str_gcs_benefits += "## 🌐 **Global Scale**\n"
    str_gcs_benefits += "- **Multi-region**: Automatic replication across regions\n"
    str_gcs_benefits += "- **Edge caching**: Fast access from anywhere\n"
    str_gcs_benefits += "- **Unlimited storage**: Scale to any size\n\n"
    str_gcs_benefits += "## 🔒 **Enterprise Security**\n"
    str_gcs_benefits += "- **IAM integration**: Fine-grained access control\n"
    str_gcs_benefits += "- **Encryption**: At rest and in transit\n"
    str_gcs_benefits += "- **Audit logging**: Complete access tracking\n\n"
    str_gcs_benefits += "## 💰 **Cost Optimization**\n"
    str_gcs_benefits += "- **Lifecycle policies**: Automatic cost optimization\n"
    str_gcs_benefits += "- **Nearline/Coldline**: Lower costs for infrequent access\n"
    str_gcs_benefits += "- **No egress fees**: Free data transfer within GCP\n\n"
    str_gcs_benefits += "## 🔧 **Developer Experience**\n"
    str_gcs_benefits += "- **gsutil integration**: Familiar command-line tools\n"
    str_gcs_benefits += "- **REST API**: Programmatic access\n"
    str_gcs_benefits += "- **SDK support**: Python, Java, Go, Node.js\n"

    mo.md(str_gcs_benefits)
    return


if __name__ == "__main__":
    app.run()
