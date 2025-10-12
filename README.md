# kirin

Version controlled data storage with cloud support!

Made with ❤️ by Eric J. Ma (@ericmjl).

## Features

- 📦 **Linear versioning for datasets** - Simple, Git-like commits without branching
  complexity
- 🔗 **Content-addressed storage** - Files stored by content hash for integrity and
  deduplication
- ☁️ **Cloud storage support** - S3, GCS, Azure, Minio, Backblaze B2, etc.
- 🔄 **Automatic filesystem detection** from URIs
- 🔐 **Easy authentication helpers**
- 🚀 **Simple, intuitive API** - Focus on ergonomic Python interface
- 📊 **File versioning** - Track changes to individual files over time

## Quick Start

```python
from kirin import Catalog, Dataset, File, Commit
from pathlib import Path

# Create a catalog (works with local and cloud storage)
catalog = Catalog(root_dir="/path/to/data")  # Local storage
catalog = Catalog(root_dir="s3://my-bucket")  # S3 storage
catalog = Catalog(root_dir="gs://my-bucket")  # GCS storage

# Get or create a dataset
ds = catalog.get_dataset("my_dataset")

# Commit files
commit_hash = ds.commit(message="Initial commit", add_files=["file1.csv"])

# Checkout the latest commit
ds.checkout()

# Access files from current commit
files = ds.files
print(f"Files in current commit: {list(files.keys())}")

# Work with files locally
with ds.local_files() as local_files:
    # Access files as local paths
    csv_path = local_files["file1.csv"]
    content = Path(csv_path).read_text()  # text mode
    binary_content = Path(csv_path).read_bytes()  # binary mode

# Checkout a specific commit
ds.checkout(commit_hash)

# Get commit history
history = ds.history(limit=10)
for commit in history:
    print(f"{commit.short_hash}: {commit.message}")
```

### Cloud Authentication

If you get authentication errors, see the [Cloud Storage Authentication
Guide](docs/cloud-storage-auth.md) or use helper functions:

```python
from kirin import Catalog, get_gcs_filesystem

# GCS with service account
fs = get_gcs_filesystem(token='/path/to/key.json')
catalog = Catalog(root_dir="gs://my-bucket", fs=fs)
ds = catalog.get_dataset("my_dataset")
```

## Advanced Usage

### Working with Files

```python
from kirin import Catalog
from pathlib import Path

# Create catalog and get dataset
catalog = Catalog(root_dir="s3://my-bucket")
ds = catalog.get_dataset("my_dataset")
ds.checkout()

# Work with files locally (recommended approach)
with ds.local_files() as local_files:
    # Access files as local paths
    csv_path = local_files["data.csv"]

    # Read file content
    content = Path(csv_path).read_text()

    # Get file info
    file_size = Path(csv_path).stat().st_size
    print(f"File size: {file_size} bytes")

    # Open as file handle
    with open(csv_path, "r") as f:
        data = f.read()
```

### Working with Commits

```python
from kirin import Catalog

# Create catalog and get dataset
catalog = Catalog(root_dir="gs://my-bucket")
ds = catalog.get_dataset("my_dataset")

# Get specific commit
commit = ds.get_commit(commit_hash)
if commit:
    print(f"Commit: {commit.short_hash}")
    print(f"Message: {commit.message}")
    print(f"Files: {commit.list_files()}")
    print(f"Total size: {commit.get_total_size()} bytes")
```

### Local File Access

```python
from kirin import Catalog
from pathlib import Path
import pandas as pd

# Create catalog and get dataset
catalog = Catalog(root_dir="s3://my-bucket")
ds = catalog.get_dataset("my_dataset")
ds.checkout()

# Work with all files locally (recommended pattern)
with ds.local_files() as local_files:
    for filename, local_path in local_files.items():
        print(f"{filename} -> {local_path}")

        # Process files with standard Python libraries
        if filename.endswith('.csv'):
            df = pd.read_csv(local_path)
        elif filename.endswith('.txt'):
            text = Path(local_path).read_text()
        elif filename.endswith('.json'):
            import json
            data = json.loads(Path(local_path).read_text())
```

## Documentation

- [API Reference](docs/api.md) - Complete API documentation
- [Design Document](docs/design.md) - System architecture and design goals
- [Cloud Storage Auth](docs/cloud-storage-auth.md) - Authentication setup

## Installation

### Option 1: Pixi (Recommended for Development)

```bash
# Clone and install
git clone git@github.com:ericmjl/kirin
cd kirin
pixi install

# Set up SSL certificates for cloud storage (one-time setup)
pixi run setup-ssl

# Start the web UI
pixi run python -m kirin.web.app
```

### Option 2: UV Tool (Recommended for Production)

```bash
# Install with uv
uv tool install gitdata

# Set up SSL certificates (one-time setup)
uv run python -m kirin.setup_ssl

# Start the web UI
uv run gitdata ui
```

### Option 3: UVX (One-time Use)

```bash
# Run directly with uvx
uvx gitdata ui

# If SSL issues occur, set up certificates
uvx python -m kirin.setup_ssl
```

### Option 4: System Python

```bash
# Install with pip
pip install gitdata

# No SSL setup needed - uses system certificates
gitdata ui
```

## Get started for development

To get started:

```bash
git clone git@github.com:ericmjl/kirin
cd kirin
pixi install
```

### Development Commands

Once installed, you can use these common development commands:

```bash
# Run tests
pixi run -e tests pytest

# Run tests for a specific file
pixi run -e tests pytest tests/test_filename.py

# Run all tests with verbose output
pixi run -e tests pytest -v

# Run tests without coverage
pixi run -e tests pytest --no-cov

# Set up SSL certificates (if needed)
pixi run setup-ssl
```
