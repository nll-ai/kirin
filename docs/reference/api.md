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

- `commit(message, add_files=None, remove_files=None, metadata=None,
  tags=None)` - Commit changes to the dataset
- `checkout(commit_hash=None)` - Switch to a specific commit (latest if None)
- `files` - Dictionary of files in the current commit
- `local_files()` - Context manager for accessing files as local paths
- `history(limit=None)` - Get commit history
- `get_file(filename)` - Get a file from the current commit
- `read_file(filename)` - Read file content as text
- `download_file(filename, target_path)` - Download file to local path
- `save_plot(plot_object, filename, auto_commit=False, message=None, ...)` -
  Save plots with automatic format detection

#### Plot Versioning Operations

- `save_plot(plot_object, filename, auto_commit=False, message=None,
  metadata=None, tags=None, format=None)` - Save plots from matplotlib,
  plotly, etc. with automatic format detection (SVG for vectors, WebP for
  bitmaps)

#### Model Versioning Operations

- `find_commits(tags=None, metadata_filter=None, limit=None)` - Find commits
  matching criteria
- `compare_commits(hash1, hash2)` - Compare metadata between two commits

#### Method Details

##### `commit(message, add_files=None, remove_files=None, metadata=None, tags=None)`

Create a new commit with changes to the dataset.

**Parameters:**

- `message` (str): Commit message describing the changes
- `add_files` (List[Union[str, Path]], optional): List of files to add or update
- `remove_files` (List[str], optional): List of filenames to remove
- `metadata` (Dict[str, Any], optional): Metadata dictionary for model versioning
- `tags` (List[str], optional): List of tags for staging/versioning

**Returns:**

- `str`: Hash of the new commit

**Examples:**

```python
# Basic commit
dataset.commit("Add new data", add_files=["data.csv"])

# Model versioning commit
dataset.commit(
    message="Improved model v2.0",
    add_files=["model.pt", "config.json"],
    metadata={
        "framework": "pytorch",
        "accuracy": 0.92,
        "hyperparameters": {"lr": 0.001, "epochs": 10}
    },
    tags=["production", "v2.0"]
)
```

##### `find_commits(tags=None, metadata_filter=None, limit=None)`

Find commits matching specified criteria.

**Parameters:**

- `tags` (List[str], optional): Filter by tags (commits must have ALL
  specified tags)
- `metadata_filter` (Callable[[Dict], bool], optional): Function that takes
  metadata dict and returns bool
- `limit` (int, optional): Maximum number of commits to return

**Returns:**

- `List[Commit]`: List of matching commits (newest first)

**Examples:**

```python
# Find production models
production_models = dataset.find_commits(tags=["production"])

# Find high-accuracy models
high_accuracy = dataset.find_commits(
    metadata_filter=lambda m: m.get("accuracy", 0) > 0.9
)

# Find PyTorch production models
pytorch_prod = dataset.find_commits(
    tags=["production"],
    metadata_filter=lambda m: m.get("framework") == "pytorch"
)
```

##### `compare_commits(hash1, hash2)`

Compare metadata between two commits.

**Parameters:**

- `hash1` (str): First commit hash
- `hash2` (str): Second commit hash

**Returns:**

- `dict`: Dictionary with comparison results including metadata and tag
  differences

**Example:**

```python
comparison = dataset.compare_commits("abc123", "def456")
print("Metadata changes:", comparison["metadata_diff"]["changed"])
print("Tag changes:", comparison["tags_diff"])
```

##### save_plot

Save a plot to the dataset with automatic format detection.

**Signature:**

```python
save_plot(
    plot_object,
    filename,
    auto_commit=False,
    message=None,
    metadata=None,
    tags=None,
    format=None
)
```

**Parameters:**

- `plot_object`: The plot object to save (matplotlib Figure, plotly Figure,
  etc.)
- `filename` (str): Desired filename for the plot (extension may be adjusted)
- `auto_commit` (bool): If True, automatically commits the plot. If False,
  returns file path for explicit commit
- `message` (str, optional): Commit message (required if auto_commit=True)
- `metadata` (Dict[str, Any], optional): Metadata dictionary for the commit
- `tags` (List[str], optional): List of tags for the commit
- `format` (str, optional): Format override ('svg' or 'webp'). If None, auto-detects

**Returns:**

- If `auto_commit=False`: File path (str) that can be used in `commit()`
- If `auto_commit=True`: Commit hash (str) of the created commit

#### Strict Content Hashing for SVG Plots

Kirin uses strict content-addressed hashing based on exact file content.
This means:

- SVG plots will produce different hashes even when the plot content is
  identical, because matplotlib embeds creation timestamps in the SVG metadata
  (`<dc:date>` elements). This is the strictest form of hashing and ensures
  complete content integrity.

- Identical plots = different commits: If you save the same plot twice (same
  data, same code), you'll get different hashes and thus different commits,
  because the SVG files differ by their timestamps.

- This is by design: Content-addressed storage requires exact byte matching.
  The timestamp metadata is part of the file content, so it affects the hash.

- For deterministic hashing: If you need identical plots to produce identical
  hashes, consider using WebP format (raster) instead of SVG, or strip metadata
  before saving (not currently implemented).

**Examples:**

```python
import matplotlib.pyplot as plt

# Create a plot
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])

# Auto-commit mode (convenient for single plots)
commit_hash = dataset.save_plot(
    fig, "plot.png", auto_commit=True, message="Add visualization"
)

# Default mode (allows batching multiple plots)
plot_path = dataset.save_plot(fig, "plot1.png")
plot_path2 = dataset.save_plot(fig2, "plot2.png")
dataset.commit(message="Add multiple plots", add_files=[plot_path, plot_path2])
```

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

### save_plot (standalone function)

Standalone function for saving plots to content-addressed storage.

```python
from kirin import save_plot
from kirin.storage import ContentStore

storage = ContentStore("/path/to/data")
hash, filename = save_plot(fig, "plot.png", storage)
```

#### Strict Content Hashing for SVG Plots (save_plot function)

Kirin uses strict content-addressed hashing - files are identified by their
exact byte content. SVG plots from matplotlib will produce different hashes
even when the plot content is identical, because matplotlib embeds creation
timestamps in the SVG metadata. This is the strictest form of hashing and
ensures complete content integrity. See `Dataset.save_plot()` documentation
for more details.

**Parameters:**

- `plot_object`: The plot object to save (matplotlib Figure, plotly Figure, etc.)
- `filename` (str): Desired filename for the plot (extension may be adjusted)
- `storage` (ContentStore): ContentStore instance to use for storage
- `format` (str, optional): Format override ('svg' or 'webp'). If None, auto-detects

**Returns:**

- `tuple[str, str]`: Tuple of (content_hash, actual_filename) where
  actual_filename is the filename used (may have extension adjusted based on
  format)

**Example:**

```python
import matplotlib.pyplot as plt
from kirin import save_plot
from kirin.storage import ContentStore

storage = ContentStore("/path/to/data")

fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])

# Save plot (returns hash and actual filename)
content_hash, actual_filename = save_plot(fig, "plot.png", storage)
print(f"Saved plot with hash: {content_hash[:8]}")
print(f"Actual filename: {actual_filename}")  # May be "plot.svg"
```

### Catalog

The main class for managing collections of datasets.

```python
from kirin import Catalog

# Create or load a catalog
catalog = Catalog(root_dir="/path/to/data")
```

#### Catalog Constructor Parameters

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

#### Catalog Basic Operations

- `datasets()` - List all datasets in the catalog
- `get_dataset(name)` - Get a specific dataset
- `create_dataset(name, description="")` - Create a new dataset
- `__len__()` - Number of datasets in the catalog

#### Catalog Examples

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

### Commit

Represents an immutable snapshot of files at a point in time with optional
metadata and tags.

#### Properties

- `hash` (str): Unique commit identifier
- `message` (str): Commit message
- `timestamp` (datetime): When the commit was created
- `parent_hash` (Optional[str]): Hash of the parent commit (None for initial commit)
- `files` (Dict[str, File]): Dictionary of files in this commit
- `metadata` (Dict[str, Any]): Metadata dictionary for model versioning
- `tags` (List[str]): List of tags for staging/versioning

#### Methods

- `get_file(name)` - Get a file by name
- `list_files()` - List all file names
- `has_file(name)` - Check if file exists
- `get_file_count()` - Get number of files
- `get_total_size()` - Get total size of all files
- `to_dict()` - Convert to dictionary representation
- `from_dict(data, storage)` - Create from dictionary

#### Commit Examples

```python
# Access commit properties
commit = dataset.current_commit
print(f"Commit: {commit.short_hash}")
print(f"Message: {commit.message}")
print(f"Files: {len(commit.files)}")
print(f"Metadata: {commit.metadata}")
print(f"Tags: {commit.tags}")

# Check if commit has specific metadata
if commit.metadata.get("accuracy", 0) > 0.9:
    print("High accuracy model!")

# Check if commit has specific tags
if "production" in commit.tags:
    print("Production model")
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

For detailed examples and cloud storage setup, see the
[Cloud Storage Authentication Guide](../cloud-storage-auth.md).
