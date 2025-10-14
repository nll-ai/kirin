# Kirin Documentation

Welcome to Kirin - simplified "git" for data versioning!

## What is Kirin?

Kirin is a simplified tool for version-controlling data using content-addressed storage. It provides linear commit history for datasets without the complexity of branching and merging.

**Key Benefits:**
- **Linear versioning**: Simple, Git-like commits without branching complexity
- **Content-addressed storage**: Files stored by content hash for integrity and deduplication
- **Cloud support**: Works with S3, GCS, Azure, and more
- **Ergonomic API**: Designed for data science workflows
- **Zero-copy operations**: Efficient handling of large files

## Quick Start

```python
from kirin import Catalog, Dataset

# Create a catalog (works with local and cloud storage)
catalog = Catalog(root_dir="/path/to/data")  # Local storage
catalog = Catalog(root_dir="s3://my-bucket")  # S3 storage

# Get or create a dataset
ds = catalog.get_dataset("my_dataset")

# Commit files
commit_hash = ds.commit(message="Initial commit", add_files=["file1.csv"])

# Work with files locally
with ds.local_files() as local_files:
    csv_path = local_files["file1.csv"]
    content = Path(csv_path).read_text()
```

## Documentation

### Getting Started

- **[Quickstart](getting-started/quickstart.md)** - Get up and running in 5 minutes
- **[Installation](getting-started/installation.md)** - Installation options and setup
- **[Core Concepts](getting-started/core-concepts.md)** - Understanding datasets, commits, and content-addressing

### User Guides

- **[Basic Usage](guides/basic-usage.md)** - Essential workflows for working with datasets
- **[Cloud Storage](guides/cloud-storage.md)** - Set up and use cloud storage backends
- **[Working with Files](guides/working-with-files.md)** - File operations and data science integration
- **[Commit Management](guides/commit-management.md)** - Understanding and working with commit history

### Web UI

- **[Web UI Overview](web-ui/overview.md)** - Getting started with the web interface
- **[Catalog Management](web-ui/catalog-management.md)** - Advanced catalog configuration

### Reference

- **[API Reference](reference/api.md)** - Complete API documentation
- **[Storage Format](reference/storage-format.md)** - Technical storage details

### Architecture

- **[Architecture Overview](architecture/overview.md)** - System architecture and design principles

## Why Kirin Exists

Kirin addresses critical needs in machine learning and data science workflows:

- **Linear Data Versioning**: Track changes to datasets with simple, linear commits
- **Content-Addressed Storage**: Ensure data integrity and enable deduplication
- **Multi-Backend Support**: Work with S3, GCS, Azure, local filesystem, and more
- **Serverless Architecture**: No dedicated servers required
- **Ergonomic Python API**: Focus on ease of use and developer experience
- **File Versioning**: Track changes to individual files over time

## Common Use Cases

- **Experiment tracking**: Version your training data and model inputs
- **Data pipeline versioning**: Track changes in ETL processes
- **Collaborative research**: Share datasets with exact version control
- **Reproducible analysis**: Ensure you can recreate your results
- **MLOps workflows**: Deploy models with exact data dependencies

## Installation

```bash
# Option 1: Using pixi (recommended for development)
git clone git@github.com:nll-ai/kirin
cd kirin
pixi install
pixi run kirin ui

# Option 2: Using uv tool (recommended for production)
uv tool install kirin
uv run kirin ui

# Option 3: Using uvx (one-time use)
uvx kirin ui
```

## Next Steps

1. **[Quickstart](getting-started/quickstart.md)** - Try Kirin with a simple example
2. **[Core Concepts](getting-started/core-concepts.md)** - Understand how Kirin works
3. **[Basic Usage](guides/basic-usage.md)** - Learn common workflows
4. **[Cloud Storage](guides/cloud-storage.md)** - Set up cloud storage
