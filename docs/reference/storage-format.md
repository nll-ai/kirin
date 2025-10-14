# Storage Format

Technical details about Kirin's storage format and data structures.

## Overview

Kirin uses a simplified Git-like storage format optimized for data
versioning. The storage is organized into two main areas:

- **Content Store**: Content-addressed file storage
- **Dataset Store**: Commit history and metadata

## Storage Layout

```text
<root>/
├── data/                     # Content-addressed storage
│   ├── ab/                  # First two characters of hash
│   │   └── cdef1234...      # Rest of hash (no file extensions)
│   └── ...
└── datasets/                 # Dataset storage
    ├── dataset1/             # Dataset directory
    │   └── commits.json       # Linear commit history
    └── ...
```

## Content Store

### File Storage

Files are stored in the content store using their content hash:

**Storage Path**: `data/{hash[:2]}/{hash[2:]}`

**Example**:

- File hash: `abc123def456...`
- Storage path: `data/ab/c123def456...`

### Critical Design: Extension-less Storage

**Files are stored WITHOUT file extensions** in the content store:

- **Storage Path**: `data/ab/cdef1234...` (no `.csv`, `.txt`, etc.)
- **Original Extensions**: Stored as metadata in the `File` entity's `name` attribute
- **Extension Restoration**: Original filenames restored when files are accessed
- **Content Integrity**: Files identified purely by content hash
- **Deduplication**: Identical content stored only once, regardless of original filename

### Benefits of Extension-less Storage

1. **Content Integrity**: Files identified by content, not filename
2. **Deduplication**: Identical content stored once regardless of original name
3. **Tamper-proof**: Any change to content changes the hash
4. **Efficient Storage**: No duplicate storage for identical content

## Dataset Store

### Commit History Format

Each dataset maintains a single JSON file with linear commit history:

**File**: `datasets/{dataset_name}/commits.json`

```json
{
  "dataset_name": "my_dataset",
  "commits": [
    {
      "hash": "abc123...",
      "message": "Initial commit",
      "timestamp": "2024-01-01T12:00:00",
      "parent_hash": null,
      "files": {
        "data.csv": {
          "hash": "def456...",
          "name": "data.csv",
          "size": 1024,
          "content_type": "text/csv"
        }
      }
    },
    {
      "hash": "ghi789...",
      "message": "Add processed data",
      "timestamp": "2024-01-01T13:00:00",
      "parent_hash": "abc123...",
      "files": {
        "data.csv": {
          "hash": "def456...",
          "name": "data.csv",
          "size": 1024,
          "content_type": "text/csv"
        },
        "processed.csv": {
          "hash": "jkl012...",
          "name": "processed.csv",
          "size": 2048,
          "content_type": "text/csv"
        }
      }
    }
  ]
}
```

### Commit Structure

Each commit contains:

- **hash**: SHA256 hash of the commit
- **message**: Human-readable commit message
- **timestamp**: ISO 8601 timestamp
- **parent_hash**: Hash of parent commit (null for first commit)
- **files**: Dictionary mapping filename to file metadata

### File Metadata

Each file entry contains:

- **hash**: Content hash of the file
- **name**: Original filename (including extension)
- **size**: File size in bytes
- **content_type**: MIME type of the file

## Data Structures

### File Entity

```python
@dataclass(frozen=True)
class File:
    """Represents a versioned file with content-addressed storage."""

    hash: str                    # Content hash (SHA256)
    name: str                   # Original filename
    size: int                   # File size in bytes
    content_type: Optional[str] = None  # MIME type

    def read_bytes(self) -> bytes: ...
    def open(self, mode: str = "rb") -> Union[BinaryIO, TextIO]: ...
    def download_to(self, path: Union[str, Path]) -> str: ...
    def exists(self) -> bool: ...
    def to_dict(self) -> dict: ...
```

### Commit Entity

```python
@dataclass(frozen=True)
class Commit:
    """Represents an immutable snapshot of files at a point in time."""

    hash: str                           # Commit hash
    message: str                        # Commit message
    timestamp: datetime                  # Creation timestamp
    parent_hash: Optional[str]          # Parent commit hash
    files: Dict[str, File]             # filename -> File mapping

    def get_file(self, name: str) -> Optional[File]: ...
    def list_files(self) -> List[str]: ...
    def has_file(self, name: str) -> bool: ...
    def get_total_size(self) -> int: ...
```

### Dataset Entity

```python
class Dataset:
    """Represents a logical collection of files with linear history."""

    def __init__(self, root_dir: Union[str, Path], name: str,
                 description: str = "",
                 fs: Optional[fsspec.AbstractFileSystem] = None,
                 # AWS/S3 authentication
                 aws_profile: Optional[str] = None,
                 # GCP/GCS authentication
                 gcs_token: Optional[Union[str, Path]] = None,
                 gcs_project: Optional[str] = None,
                 # Azure authentication
                 azure_account_name: Optional[str] = None,
                 azure_account_key: Optional[str] = None,
                 azure_connection_string: Optional[str] = None): ...

    def commit(self, message: str, add_files: List[Union[str, Path]] = None,
               remove_files: List[str] = None) -> str: ...
    def checkout(self, commit_hash: Optional[str] = None) -> None: ...
    def get_file(self, name: str) -> Optional[File]: ...
    def list_files(self) -> List[str]: ...
    def has_file(self, name: str) -> bool: ...
    def read_file(self, name: str, mode: str = "r") -> Union[str, bytes]: ...
    def download_file(self, name: str, target_path: Union[str, Path]) -> str: ...
    def open_file(self, name: str, mode: str = "rb") -> Union[BinaryIO,
                                                               TextIO]: ...
    def local_files(self): ...  # Context manager for local file access
    def history(self, limit: Optional[int] = None) -> List[Commit]: ...
    def get_commit(self, commit_hash: str) -> Optional[Commit]: ...
    def get_commits(self) -> List[Commit]: ...
    def is_empty(self) -> bool: ...
    def cleanup_orphaned_files(self) -> int: ...
    def get_info(self) -> dict: ...
    def to_dict(self) -> dict: ...

    # Properties
    @property
    def current_commit(self) -> Optional[Commit]: ...
    @property
    def head(self) -> Optional[Commit]: ...  # Alias for current_commit
    @property
    def files(self) -> Dict[str, File]: ...  # Files from current commit
```

### Catalog Entity

```python
@dataclass
class Catalog:
    """Represents a collection of datasets."""

    root_dir: Union[str, fsspec.AbstractFileSystem]
    fs: Optional[fsspec.AbstractFileSystem] = None
    # AWS/S3 authentication
    aws_profile: Optional[str] = None
    # GCP/GCS authentication
    gcs_token: Optional[Union[str, Path]] = None
    gcs_project: Optional[str] = None
    # Azure authentication
    azure_account_name: Optional[str] = None
    azure_account_key: Optional[str] = None
    azure_connection_string: Optional[str] = None

    def datasets(self) -> List[str]: ...  # List dataset names
    def get_dataset(self, dataset_name: str) -> Dataset: ...  # Get existing dataset
    def create_dataset(self, dataset_name: str,
                       description: str = "") -> Dataset: ...  # Create new dataset
    def __len__(self) -> int: ...  # Number of datasets
```

## Content Addressing

### Hash Calculation

Files are hashed using SHA256 directly on content bytes:

```python
import hashlib

def calculate_hash(content: bytes) -> str:
    """Calculate SHA256 hash of content bytes."""
    return hashlib.sha256(content).hexdigest()

# Example usage in storage
def store_file(file_path: Path) -> str:
    with open(file_path, "rb") as f:
        content = f.read()
    return hashlib.sha256(content).hexdigest()
```

### Deduplication

Identical content is stored only once:

```python
# Two files with identical content
file1_content = b"Hello, World!"
file2_content = b"Hello, World!"

# Both files get the same hash
hash1 = hashlib.sha256(file1_content).hexdigest()
hash2 = hashlib.sha256(file2_content).hexdigest()

assert hash1 == hash2  # Same hash = same storage location
```

### Content Integrity

Any change to file content changes the hash:

```python
# Original content
content1 = b"Hello, World!"
hash1 = hashlib.sha256(content1).hexdigest()

# Modified content
content2 = b"Hello, World!"  # Even a single character change
hash2 = hashlib.sha256(content2).hexdigest()

assert hash1 != hash2  # Different hash = different storage location
```

### Commit Hash Generation

Commit hashes are generated using file hashes, message, and timestamp:

```python
def generate_commit_hash(files: Dict[str, File], message: str,
                        parent_hash: Optional[str],
                        timestamp: datetime) -> str:
    """Generate commit hash from file hashes, message, and timestamp."""
    import hashlib

    # Sort file hashes for consistency
    file_hashes = sorted(file.hash for file in files.values())
    parent_hash = parent_hash or ""

    # Combine all components
    content = (
        "\n".join(file_hashes) + "\n" +
        message + "\n" +
        parent_hash + "\n" +
        str(timestamp)
    )

    # Generate hash
    hasher = hashlib.sha256()
    hasher.update(content.encode("utf-8"))
    return hasher.hexdigest()
```

## Backend Integration

### FSSpec Backends

Kirin supports any fsspec backend:

```python
# Local filesystem
fs = fsspec.filesystem("file")

# S3
fs = fsspec.filesystem("s3", profile="my-profile")

# GCS
fs = fsspec.filesystem("gcs", token="/path/to/key.json")

# Azure
fs = fsspec.filesystem("az", connection_string="...")
```

### Storage Operations

```python
# Store file content
def store_file(fs, file_path: Path) -> str:
    """Store file and return content hash."""
    with open(file_path, "rb") as f:
        content = f.read()

    hash_value = hashlib.sha256(content).hexdigest()
    storage_path = f"data/{hash_value[:2]}/{hash_value[2:]}"

    fs.write_bytes(storage_path, content)
    return hash_value

# Retrieve file content
def retrieve_file(fs, hash_value: str) -> bytes:
    """Retrieve file content by hash."""
    storage_path = f"data/{hash_value[:2]}/{hash_value[2:]}"
    return fs.read_bytes(storage_path)
```

## Performance Considerations

### Zero-Copy Operations

Kirin is designed with zero-copy philosophy:

- **Reference-based operations**: Use File objects as references instead of
  copying content
- **Lazy loading**: File content is only downloaded when accessed
- **Deduplication**: Identical content is stored only once regardless of filename

### Caching

Kirin implements commit-level caching for improved performance:

```python
# Commit objects are cached in memory
class CommitStore:
    def __init__(self):
        self._commits_cache: Dict[str, Commit] = {}

    def get_commit(self, commit_hash: str) -> Commit:
        # Try cache first
        if commit_hash in self._commits_cache:
            return self._commits_cache[commit_hash]
        # Load from storage if not cached
        # ...
```

### Lazy Loading

Content loaded only when needed:

```python
# Lazy file loading
class LazyFile:
    def __init__(self, fs, hash_value: str, name: str):
        self.fs = fs
        self.hash_value = hash_value
        self.name = name
        self._content = None

    def read_bytes(self) -> bytes:
        if self._content is None:
            self._content = retrieve_file(self.fs, self.hash_value)
        return self._content
```

## Migration and Backup

### Backup Strategies

```bash
# Backup content store
rsync -av data/ backup/data/

# Backup dataset metadata
rsync -av datasets/ backup/datasets/
```

### Migration Between Backends

```python
# Migrate from local to S3
local_fs = fsspec.filesystem("file")
s3_fs = fsspec.filesystem("s3", profile="my-profile")

# Copy content store
for root, dirs, files in os.walk("data"):
    for file in files:
        local_path = os.path.join(root, file)
        s3_path = f"s3://my-bucket/{local_path}"
        s3_fs.put(local_path, s3_path)
```

## Security Considerations

### Access Control

- **File permissions**: Respect filesystem permissions
- **Cloud IAM**: Use appropriate cloud permissions
- **Encryption**: Support for encrypted storage backends

### Data Integrity

- **Hash verification**: Verify content hashes on retrieval
- **Tamper detection**: Detect any content changes
- **Audit trails**: Track all storage operations

## Next Steps

- **[API Reference](api.md)** - Complete API documentation
- **[Architecture Overview](../architecture/overview.md)** - System architecture
