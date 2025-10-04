# gitdata

Version controlled data storage with cloud support!

Made with ❤️ by Eric J. Ma (@ericmjl).

## Features

- 📦 Git-like versioning for datasets
- ☁️ Cloud storage support (S3, GCS, Azure, Minio, Backblaze B2, etc.)
- 🔄 Automatic filesystem detection from URIs
- 🔐 Easy authentication helpers
- 🚀 Simple, intuitive API

## Quick Start

```python
from gitdata import Dataset

# Local storage
ds = Dataset(root_dir="/path/to/data", dataset_name="my_dataset")

# Cloud storage (auto-detects from URI!)
ds = Dataset(root_dir="s3://my-bucket/datasets", dataset_name="my_dataset")
ds = Dataset(root_dir="gs://my-bucket/datasets", dataset_name="my_dataset")

# Commit files
ds.commit(commit_message="Initial commit", add_files=["file1.csv"])

# Access files
files = ds.file_dict
```

### Cloud Authentication

If you get authentication errors, see the [Cloud Storage Authentication Guide](docs/cloud-storage-auth.md) or use helper functions:

```python
from gitdata import Dataset, get_gcs_filesystem

# GCS with service account
fs = get_gcs_filesystem(token='/path/to/key.json')
ds = Dataset(root_dir="gs://my-bucket/datasets", dataset_name="my_dataset", fs=fs)
```

## Get started for development

To get started:

```bash
git clone git@github.com:ericmjl/gitdata
cd gitdata
mamba env update -f environment.yml
conda activate gitdata
python -m pip install -e .
```
