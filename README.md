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
from kirin import Dataset, File, Commit

# Local storage
ds = Dataset(root_dir="/path/to/data", name="my_dataset")

# Cloud storage (auto-detects from URI!)
ds = Dataset(root_dir="s3://my-bucket/datasets", name="my_dataset")
ds = Dataset(root_dir="gs://my-bucket/datasets", name="my_dataset")

# Commit files
commit_hash = ds.commit(message="Initial commit", add_files=["file1.csv"])

# Access files from current commit
files = ds.files
print(f"Files in current commit: {list(files.keys())}")

# Read a file
content = ds.read_file("file1.csv", mode="r")  # text mode
binary_content = ds.read_file("file1.csv", mode="rb")  # binary mode

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
from kirin import Dataset, get_gcs_filesystem

# GCS with service account
fs = get_gcs_filesystem(token='/path/to/key.json')
ds = Dataset(root_dir="gs://my-bucket/datasets", name="my_dataset", fs=fs)
```

## Advanced Usage

### Working with Files

```python
# Get a specific file
file_obj = ds.get_file("data.csv")
if file_obj:
    print(f"File size: {file_obj.size} bytes")
    print(f"Content hash: {file_obj.short_hash}")

    # Read file content
    content = file_obj.read_text()

    # Download to local path
    file_obj.download_to("/tmp/data.csv")

    # Open as file handle
    with file_obj.open("r") as f:
        data = f.read()
```

### Working with Commits

```python
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
# Download all files to temporary directory
with ds.local_files() as local_files:
    for filename, local_path in local_files.items():
        print(f"{filename} -> {local_path}")
        # Process files locally
        df = pd.read_csv(local_path)
```

## Documentation

- [API Reference](docs/api.md) - Complete API documentation
- [Design Document](docs/design.md) - System architecture and design goals
- [Cloud Storage Auth](docs/cloud-storage-auth.md) - Authentication setup

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
```
