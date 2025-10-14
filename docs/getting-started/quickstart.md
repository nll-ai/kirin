# Quickstart

Get up and running with Kirin in 5 minutes!

## What is Kirin?

Kirin is simplified "git" for data - it provides linear versioning for datasets
with content-addressed storage. Think of it as Git, but designed specifically
for data scientists working with large datasets.

## 5-Minute Quickstart

### 1. Install Kirin

```bash
# Option 1: Using pixi (recommended for development)
git clone git@github.com:nll-ai/kirin
cd kirin
pixi install

# Option 2: Using uv tool (recommended for production)
uv tool install kirin

# Option 3: Using pip
pip install kirin
```

### 2. Create Your First Dataset

```python
from kirin import Catalog, Dataset
from pathlib import Path

# Create a catalog (works with local and cloud storage)
catalog = Catalog(root_dir="/path/to/data")  # Local storage

# Get or create a dataset
ds = catalog.get_dataset("my_first_dataset")

# Add some files to your dataset
commit_hash = ds.commit(
    message="Initial commit",
    add_files=["data.csv", "config.json"]
)

print(f"Created commit: {commit_hash}")
```

### 3. Work with Your Data

```python
# Checkout the latest commit
ds.checkout()

# Access files from current commit
files = ds.files
print(f"Files in current commit: {list(files.keys())}")

# Work with files locally (recommended approach)
with ds.local_files() as local_files:
    # Access files as local paths
    csv_path = local_files["data.csv"]

    # Read file content
    content = Path(csv_path).read_text()
    print(f"File content: {content[:100]}...")
```

### 4. View Your Commit History

```python
# Get commit history
history = ds.history(limit=10)
for commit in history:
    print(f"{commit.short_hash}: {commit.message}")

# Checkout a specific commit
ds.checkout(commit_hash)
```

### 5. Start the Web UI (Optional)

```bash
# Using pixi (development)
pixi run kirin ui

# Using uv (production)
uv run kirin ui

# Using uvx (one-time use)
uvx kirin ui
```

The web UI provides a graphical interface for browsing datasets, viewing
commit history, and managing your data catalogs.

## Next Steps

- **[Installation Guide](installation.md)** - Detailed installation options
- **[Core Concepts](core-concepts.md)** - Understanding datasets, commits, and content-addressing
- **[Basic Usage Guide](../guides/basic-usage.md)** - Common workflows and patterns
- **[Cloud Storage Guide](../guides/cloud-storage.md)** - Working with S3, GCS, Azure

## Key Benefits

- **Linear versioning**: Simple, Git-like commits without branching complexity
- **Content-addressed storage**: Files stored by content hash for integrity and deduplication
- **Cloud support**: Works with S3, GCS, Azure, and more
- **Ergonomic API**: Designed for data science workflows
- **Zero-copy operations**: Efficient handling of large files

## Common Use Cases

- **Experiment tracking**: Version your training data and model inputs
- **Data pipeline versioning**: Track changes in ETL processes
- **Collaborative research**: Share datasets with exact version control
- **Reproducible analysis**: Ensure you can recreate your results
