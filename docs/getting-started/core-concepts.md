# Core Concepts

Understanding the fundamental concepts behind Kirin's data versioning system.

## What is Kirin?

Kirin is a simplified tool for version-controlling data using content-addressed
storage. It provides linear commit history for datasets without the complexity
of branching and merging.

## Key Concepts

### Datasets

A **dataset** is a logical collection of files that you want to version
together. Think of it as a folder that tracks changes over time.

```python
from kirin import Dataset

# Create a dataset
dataset = Dataset(root_dir="/path/to/data", name="my_dataset")
```

**Characteristics:**

- Contains multiple files
- Has a linear commit history
- Can be shared and collaborated on
- Maintains data integrity through content-addressing

### Files

A **file** in Kirin represents a versioned file with content-addressed storage.
Files are immutable once created and identified by their content hash.

```python
# Get a file from the current commit
file_obj = dataset.get_file("data.csv")
print(f"File hash: {file_obj.hash}")
print(f"File size: {file_obj.size} bytes")
print(f"Content type: {file_obj.content_type}")
print(f"Short hash: {file_obj.short_hash}")
```

**Key Properties:**

- **Content-addressed**: Identified by content hash, not filename
- **Immutable**: Cannot be changed once created
- **Deduplicated**: Identical content stored only once
- **Backend-agnostic**: Works with any storage backend

### Commits

A **commit** represents an immutable snapshot of files at a point in time.
Commits form a linear history with single parent relationships.

```python
# Create a commit
commit_hash = dataset.commit(
    message="Add new data",
    add_files=["data.csv", "config.json"]
)

# Get commit information
commit = dataset.get_commit(commit_hash)
print(f"Commit: {commit.hash}")
print(f"Message: {commit.message}")
print(f"Timestamp: {commit.timestamp}")
print(f"Files: {commit.list_files()}")
print(f"Short hash: {commit.short_hash}")
```

**Characteristics:**

- **Linear history**: No branching, simple parent-child relationships
- **Immutable**: Cannot be changed once created
- **Atomic**: All files in a commit are added/removed together
- **Traceable**: Full history of changes over time

### Content-Addressed Storage

**Content-addressed storage** means files are stored and identified by their
content hash, not their filename or location.

**Benefits:**

- **Data integrity**: Files cannot be corrupted without detection
- **Deduplication**: Identical content stored only once
- **Efficient storage**: Saves space by avoiding duplicate files
- **Tamper-proof**: Any change to content changes the hash

**Storage Layout:**

```text
data/
├── ab/                  # First two characters of hash
│   └── cdef1234...      # Rest of hash (no file extensions)
└── ...
```

**Important**: Files are stored **without extensions** in the content store.
Original extensions are preserved as metadata in the File entity's `name`
attribute and restored when files are accessed.

### Catalogs

A **catalog** is a collection of datasets that you want to manage together.
It's like a workspace for multiple related datasets.

```python
from kirin import Catalog

# Create a catalog
catalog = Catalog(root_dir="/path/to/data")

# List all datasets
datasets = catalog.datasets()
print(f"Available datasets: {datasets}")

# Get a specific dataset
dataset = catalog.get_dataset("my_dataset")
```

**Use Cases:**

- **Project organization**: Group related datasets
- **Team collaboration**: Share multiple datasets
- **Workflow management**: Organize data processing pipelines

## How It Works

### 1. File Storage

When you add a file to Kirin:

1. **Hash calculation**: File content is hashed (SHA256)
2. **Content storage**: File stored at `data/{hash[:2]}/{hash[2:]}`
3. **Metadata tracking**: Original filename stored as metadata
4. **Deduplication**: If file already exists, no duplicate storage

### 2. Commit Process

When you create a commit:

1. **File staging**: Files to be added/removed are identified
2. **Hash resolution**: Content hashes are calculated/resolved
3. **Commit creation**: New commit object created with file references
4. **History update**: Commit added to linear history

### 3. Data Access

When you access files:

1. **Commit resolution**: Current commit or specific commit identified
2. **File lookup**: File references resolved to content hashes
3. **Content retrieval**: Files retrieved from content store
4. **Extension restoration**: Original filenames restored

## Linear vs. Branching

Kirin uses **linear commit history** instead of Git's branching model:

**Linear History (Kirin):**

```text
Commit A → Commit B → Commit C → Commit D
```

**Branching History (Git):**

```text
Commit A → Commit B → Commit C
         ↘
           Commit D → Commit E
```

**Benefits of Linear History:**

- **Simpler**: No merge conflicts or complex branching
- **Clearer**: Easy to understand data evolution
- **Safer**: No risk of losing data through complex merges
- **Faster**: No need to resolve merge conflicts

### Creating "Branches" with New Datasets

If you need branching-like functionality, create a new dataset using existing files:

```python
# Original dataset
original_dataset = catalog.get_dataset("experiment_v1")

# Create a "branch" by starting a new dataset with existing files
branch_dataset = catalog.create_dataset("experiment_v2")

# Copy files from the original dataset to the new one
with original_dataset.local_files() as local_files:
    for filename, local_path in local_files.items():
        # Copy file to new dataset
        import shutil
        shutil.copy2(local_path, filename)

# Commit the copied files to the new dataset
branch_dataset.commit(
    message="Branch from experiment_v1",
    add_files=["data.csv", "config.json"]
)

# Now you can develop independently in each dataset
original_dataset.commit("Continue original work", add_files=["new_data.csv"])
branch_dataset.commit("Try different approach", add_files=["alternative_data.csv"])
```

**Benefits of Dataset-based "Branching":**

- **Clear separation**: Each dataset is independent
- **Easy comparison**: Compare datasets side by side
- **No conflicts**: No merge conflicts between datasets
- **Flexible**: Can share files between datasets as needed

## Backend-Agnostic Design

Kirin works with any storage backend through the fsspec library:

**Supported Backends:**

- **Local filesystem**: `/path/to/data`
- **AWS S3**: `s3://bucket/path`
- **Google Cloud Storage**: `gs://bucket/path`
- **Azure Blob Storage**: `az://container/path`
- **And many more**: Dropbox, Google Drive, etc. (sync/auth handled by backend)

**Benefits:**

- **Flexibility**: Use any storage backend
- **Scalability**: Scale from local to cloud
- **Portability**: Move between backends easily
- **Cost optimization**: Choose the right storage for your needs

## Zero-Copy Operations

Kirin is designed with zero-copy philosophy for efficient large file handling:

**Zero-Copy Features:**

- **Memory-mapped files**: Avoid loading entire files into memory
- **Chunked processing**: Process data incrementally using libraries like pandas
- **Direct transfers**: Stream between storage backends
- **Reference-based operations**: Use references instead of copying

**Benefits:**

- **Memory efficient**: Handle files larger than RAM
- **Fast operations**: No unnecessary data copying
- **Scalable**: Work with datasets of any size

## Next Steps

- **[Quickstart](quickstart.md)** - Try Kirin with a simple example
- **[Basic Usage Guide](../guides/basic-usage.md)** - Learn common workflows
- **[Working with Files](../guides/working-with-files.md)** - File operations and
  patterns
