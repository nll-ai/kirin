# kirin

Version controlled data storage with cloud support!

Made with ❤️ by Eric J. Ma (@ericmjl).

## Features

- 📦 Git-like versioning for datasets
- 🌿 **Branching support** - Create, switch, and manage branches just like Git
- ☁️ Cloud storage support (S3, GCS, Azure, Minio, Backblaze B2, etc.)
- 🔄 Automatic filesystem detection from URIs
- 🔐 Easy authentication helpers
- 🚀 Simple, intuitive API
- 🌐 Web UI with branch management

## Quick Start

```python
from kirin import Dataset

# Local storage
ds = Dataset(root_dir="/path/to/data", dataset_name="my_dataset")

# Cloud storage (auto-detects from URI!)
ds = Dataset(root_dir="s3://my-bucket/datasets", dataset_name="my_dataset")
ds = Dataset(root_dir="gs://my-bucket/datasets", dataset_name="my_dataset")

# Commit files
ds.commit(commit_message="Initial commit", add_files=["file1.csv"])

# Access files
files = ds.file_dict

# Branching (NEW!)
ds.create_branch("feature/new-analysis")
ds.switch_branch("feature/new-analysis")
ds.commit("Add analysis script", add_files=["analyze.py"])
```

### Cloud Authentication

If you get authentication errors, see the [Cloud Storage Authentication Guide](docs/cloud-storage-auth.md) or use helper functions:

```python
from kirin import Dataset, get_gcs_filesystem

# GCS with service account
fs = get_gcs_filesystem(token='/path/to/key.json')
ds = Dataset(root_dir="gs://my-bucket/datasets", dataset_name="my_dataset", fs=fs)
```

## Web UI

Kirin includes a web interface for easy dataset management:

```bash
# Start the web UI
pixi run kirin ui

# Or with a pre-loaded dataset
pixi run kirin ui --url /path/to/data --name my-dataset
```

### Features
- 📊 **Dataset visualization** - Browse commits and files
- 🌿 **Branch management** - Create, switch, and delete branches
- 📝 **Commit interface** - Add/remove files with commit messages
- 🔄 **Real-time updates** - See changes instantly

### Branch Management
1. Load a dataset in the web UI
2. Click the "Branches" button
3. Create new branches, switch between them, or delete branches
4. Each branch maintains its own commit history

## Documentation

- [API Reference](docs/api.md) - Complete API documentation
- [Branching Guide](docs/branching.md) - Detailed branching documentation
- [Cloud Storage Auth](docs/cloud-storage-auth.md) - Authentication setup

## Get started for development

To get started:

```bash
git clone git@github.com:ericmjl/gitdata
cd gitdata
mamba env update -f environment.yml
conda activate gitdata
python -m pip install -e .
```
