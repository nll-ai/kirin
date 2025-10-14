# Kirin API Reference

## Core Classes

### Dataset

The main class for working with Kirin datasets.

```python
from kirin import Dataset

# Create or load a dataset
dataset = Dataset(root_dir="/path/to/data", name="my-dataset")
```

#### Constructor Parameters

```python
Dataset(
    root_dir: Union[str, Path],           # Root directory for the dataset
    name: str,                           # Name of the dataset
    description: str = "",               # Description of the dataset
    fs: Optional[fsspec.AbstractFileSystem] = None,  # Filesystem to use
    # Cloud authentication parameters
    aws_profile: Optional[str] = None,   # AWS profile for S3 authentication
    gcs_token: Optional[Union[str, Path]] = None,  # GCS service account token
    gcs_project: Optional[str] = None,   # GCS project ID
    azure_account_name: Optional[str] = None,  # Azure account name
    azure_account_key: Optional[str] = None,    # Azure account key
    azure_connection_string: Optional[str] = None,  # Azure connection string
)
```

#### Basic Operations

- `commit(message, add_files=None, remove_files=None)` - Commit changes to the dataset
- `checkout(commit_hash=None)` - Switch to a specific commit (latest if None)
- `files` - Dictionary of files in the current commit
- `local_files()` - Context manager for accessing files as local paths
- `history(limit=None)` - Get commit history
- `get_file(filename)` - Get a file from the current commit
- `read_file(filename)` - Read file content as text
- `download_file(filename, target_path)` - Download file to local path

#### Examples

```python
# Basic usage
dataset = Dataset(root_dir="/data", name="project")
dataset.commit("Initial commit", add_files=["data.csv"])

# Cloud storage with authentication
dataset = Dataset(
    root_dir="s3://my-bucket/data",
    name="project",
    aws_profile="my-profile"
)

# GCS with service account
dataset = Dataset(
    root_dir="gs://my-bucket/data",
    name="project",
    gcs_token="/path/to/service-account.json",
    gcs_project="my-project"
)

# Azure with connection string
dataset = Dataset(
    root_dir="az://my-container/data",
    name="project",
    azure_connection_string=os.getenv("AZURE_CONNECTION_STRING")
)
```

### Catalog

The main class for managing collections of datasets.

```python
from kirin import Catalog

# Create or load a catalog
catalog = Catalog(root_dir="/path/to/data")
```

#### Constructor Parameters

```python
Catalog(
    root_dir: Union[str, fsspec.AbstractFileSystem],  # Root directory for the catalog
    fs: Optional[fsspec.AbstractFileSystem] = None,  # Filesystem to use
    # Cloud authentication parameters
    aws_profile: Optional[str] = None,   # AWS profile for S3 authentication
    gcs_token: Optional[Union[str, Path]] = None,  # GCS service account token
    gcs_project: Optional[str] = None,   # GCS project ID
    azure_account_name: Optional[str] = None,  # Azure account name
    azure_account_key: Optional[str] = None,    # Azure account key
    azure_connection_string: Optional[str] = None,  # Azure connection string
)
```

#### Basic Operations

- `datasets()` - List all datasets in the catalog
- `get_dataset(name)` - Get a specific dataset
- `create_dataset(name, description="")` - Create a new dataset
- `__len__()` - Number of datasets in the catalog

#### Examples

```python
# Basic usage
catalog = Catalog(root_dir="/data")
datasets = catalog.datasets()
dataset = catalog.get_dataset("my-dataset")

# Cloud storage with authentication
catalog = Catalog(
    root_dir="s3://my-bucket/data",
    aws_profile="my-profile"
)

# GCS with service account
catalog = Catalog(
    root_dir="gs://my-bucket/data",
    gcs_token="/path/to/service-account.json",
    gcs_project="my-project"
)
```

## Web UI

The web UI provides a graphical interface for Kirin operations.

### Routes

- `/` - Home page for catalog management
- `/catalogs/add` - Add new catalog
- `/catalog/{catalog_id}` - View catalog and datasets
- `/catalog/{catalog_id}/{dataset_name}` - View specific dataset
- `/catalog/{catalog_id}/{dataset_name}/commit` - Commit interface

### Catalog Management

The web UI supports cloud authentication through CatalogConfig:

```python
from kirin.web.config import CatalogConfig

# Create catalog config with cloud auth
config = CatalogConfig(
    id="my-catalog",
    name="My Catalog",
    root_dir="s3://my-bucket/data",
    aws_profile="my-profile"
)

# Convert to runtime catalog
catalog = config.to_catalog()
```

### Cloud Authentication in Web UI

The web UI automatically handles cloud authentication when you:

1. Create a catalog with cloud storage URL (s3://, gs://, az://)
2. The system will prompt for authentication parameters
3. Credentials are stored securely in the catalog configuration

## Storage Format

Kirin uses a simplified Git-like storage format:

```text
data/
├── data/                 # Content-addressed file storage
│   └── {hash[:2]}/{hash[2:]}
├── datasets/
│   └── my-dataset/
│       └── commits.json  # Linear commit history
```

## Error Handling

### Common Exceptions

- `ValueError` - Invalid operations (file not found, invalid commit hash, etc.)
- `FileNotFoundError` - File not found in dataset
- `HTTPException` - Web UI errors (catalog not found, validation errors)

### Example Error Handling

```python
try:
    dataset.checkout("nonexistent-commit")
except ValueError as e:
    print(f"Checkout failed: {e}")

try:
    content = dataset.read_file("nonexistent.txt")
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

## Best Practices

### Dataset Naming

- Use descriptive names: `user-data`, `ml-experiments`, `production-models`
- Avoid generic names: `test`, `data`, `temp`

### Workflow Patterns

- Commit changes regularly with descriptive messages
- Use linear commit history for simplicity
- Keep datasets focused on specific use cases
- Use catalogs to organize related datasets

### File Management

- Use `local_files()` context manager for library compatibility
- Commit changes after adding/removing files
- Use descriptive commit messages

## Advanced Features

### Context Managers

```python
# Access files as local paths
with dataset.local_files() as local_files:
    df = pd.read_csv(local_files["data.csv"])
    # Files automatically cleaned up
```

### Commit History

```python
# Get commit history
history = dataset.history(limit=10)
for commit in history:
    print(f"{commit.hash}: {commit.message}")
```

### File Operations

```python
# Add files to commit
dataset.commit("Add new data", add_files=["new_data.csv"])

# Remove files from commit
dataset.commit("Remove old data", remove_files=["old_data.csv"])

# Combined operations
dataset.commit("Update dataset",
              add_files=["new_data.csv"],
              remove_files=["old_data.csv"])
```

### Cloud Storage Integration

```python
# AWS S3 with profile
dataset = Dataset(
    root_dir="s3://my-bucket/data",
    name="my-dataset",
    aws_profile="production"
)

# GCS with service account
dataset = Dataset(
    root_dir="gs://my-bucket/data",
    name="my-dataset",
    gcs_token="/path/to/service-account.json",
    gcs_project="my-project"
)

# Azure with connection string
dataset = Dataset(
    root_dir="az://my-container/data",
    name="my-dataset",
    azure_connection_string=os.getenv("AZURE_CONNECTION_STRING")
)
```

For detailed examples and cloud storage setup, see the [Cloud Storage Authentication Guide](../cloud-storage-auth.md).
