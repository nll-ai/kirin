# File Search Guide

Kirin provides powerful file search capabilities that allow you to find datasets containing specific files based on their content hash. This is particularly useful for:

- **Deduplication**: Finding datasets that contain identical files
- **Data lineage**: Tracking where specific files are used across datasets
- **Content discovery**: Locating datasets that contain files with specific content

## How File Search Works

Kirin uses a **reverse index** that maps file content hashes to the datasets and commits that contain them. This enables fast lookups without scanning through all datasets.

### Storage Structure

The file index is stored in a sharded structure to handle large numbers of files efficiently:

```
<root>/
├── data/                     # Content-addressed storage (existing)
├── datasets/                 # Dataset storage (existing)
└── index/                    # NEW: Reverse index storage
    └── files/                # File hash to dataset mapping
        ├── ab/               # First two characters of hash
        │   └── cdef1234.json # Rest of hash
        └── ...
```

### Index File Format

Each index file contains:

```json
{
  "file_hash": "abcdef123456...",
  "datasets": {
    "dataset1": [
      {
        "commit_hash": "abc123...",
        "timestamp": "2024-01-01T12:00:00",
        "filenames": ["data.csv"]
      }
    ],
    "dataset2": [
      {
        "commit_hash": "def456...",
        "timestamp": "2024-01-02T10:00:00",
        "filenames": ["results.csv", "backup.csv"]
      }
    ]
  }
}
```

## Basic Usage

### Finding Datasets with a Specific File

```python
from kirin import Catalog

# Create or load a catalog
catalog = Catalog(root_dir="/path/to/catalog")

# Find datasets containing a specific file hash
file_hash = "abc123def456789..."
results = catalog.find_datasets_with_file(file_hash)

# Results structure:
# {
#     "dataset1": [
#         {
#             "commit_hash": "commit123...",
#             "timestamp": "2024-01-01T12:00:00",
#             "filenames": ["data.csv"]
#         }
#     ],
#     "dataset2": [
#         {
#             "commit_hash": "commit456...",
#             "timestamp": "2024-01-02T10:00:00",
#             "filenames": ["results.csv", "backup.csv"]
#         }
#     ]
# }
```

### Working with Search Results

```python
# Process search results
for dataset_name, commits in results.items():
    print(f"Dataset: {dataset_name}")
    for commit_info in commits:
        print(f"  Commit: {commit_info['commit_hash'][:8]}")
        print(f"  Timestamp: {commit_info['timestamp']}")
        print(f"  Filenames: {commit_info['filenames']}")
        print()
```

## Advanced Usage

### Finding Duplicate Files

```python
from kirin import Catalog, Dataset
from pathlib import Path

catalog = Catalog(root_dir="/path/to/catalog")

# Get a file hash from a specific dataset
dataset = catalog.get_dataset("my_dataset")
file_obj = dataset.get_file("data.csv")
file_hash = file_obj.hash

# Find all datasets containing this file
duplicates = catalog.find_datasets_with_file(file_hash)

print(f"File {file_hash[:8]}... is found in {len(duplicates)} datasets:")
for dataset_name in duplicates.keys():
    print(f"  - {dataset_name}")
```

### Tracking File Usage Across Datasets

```python
# Find all uses of a specific file
file_hash = "abc123def456789..."
usage = catalog.find_datasets_with_file(file_hash)

total_uses = sum(len(commits) for commits in usage.values())
print(f"File is used in {len(usage)} datasets across {total_uses} commits")

# Get detailed usage information
for dataset_name, commits in usage.items():
    dataset = catalog.get_dataset(dataset_name)
    print(f"\nDataset: {dataset_name}")
    for commit_info in commits:
        commit = dataset.get_commit(commit_info['commit_hash'])
        print(f"  Commit: {commit.message}")
        print(f"  Files: {commit_info['filenames']}")
```

## Index Management

### Automatic Index Updates

The file index is automatically updated when you:

- **Commit files** to datasets
- **Remove files** from datasets (via cleanup)

You don't need to manually manage the index in most cases.

### Rebuilding the Index

If you need to rebuild the entire index (e.g., after migration or corruption):

```python
from kirin.index_utils import rebuild_file_index

# Rebuild the entire index
count = rebuild_file_index("/path/to/catalog")
print(f"Indexed {count} file references")
```

### Verifying Index Integrity

```python
from kirin.index_utils import verify_file_index

# Check index integrity
results = verify_file_index("/path/to/catalog")
print(f"Total datasets: {results['total_datasets']}")
print(f"Total files: {results['total_files']}")
print(f"Missing entries: {results['missing_index_entries']}")
print(f"Extra entries: {results['extra_index_entries']}")
```

## Performance Considerations

### Index Size

- **Small catalogs**: Index overhead is minimal
- **Large catalogs**: Index provides significant performance benefits
- **Storage**: Index files are typically small compared to data files

### Query Performance

- **Fast lookups**: O(1) hash-based lookups
- **Sharded storage**: Avoids filesystem limitations
- **Cached results**: Index files are cached in memory

### Memory Usage

- **Index files**: Loaded on-demand
- **Minimal overhead**: Only active queries consume memory
- **Automatic cleanup**: Orphaned entries are removed

## Troubleshooting

### Empty Search Results

If `find_datasets_with_file()` returns empty results:

1. **Check file hash**: Ensure you're using the correct content hash
2. **Verify index**: Run `verify_file_index()` to check integrity
3. **Rebuild index**: Use `rebuild_file_index()` if needed

### Missing Index Entries

If files aren't being indexed:

1. **Check commit process**: Ensure files are committed properly
2. **Verify permissions**: Ensure write access to index directory
3. **Check logs**: Look for error messages in the logs

### Performance Issues

If searches are slow:

1. **Check filesystem**: Ensure index directory is on fast storage
2. **Verify sharding**: Check that files are properly sharded
3. **Monitor resources**: Check disk I/O and memory usage

## Examples

### Complete Workflow

```python
from kirin import Catalog, Dataset
from pathlib import Path

# Create catalog and datasets
catalog = Catalog(root_dir="/tmp/my_catalog")
dataset1 = catalog.create_dataset("dataset1", "First dataset")
dataset2 = catalog.create_dataset("dataset2", "Second dataset")

# Create identical files
file1 = Path("/tmp/data1.csv")
file2 = Path("/tmp/data2.csv")
content = "col1,col2\n1,2\n3,4\n"
file1.write_text(content)
file2.write_text(content)

# Commit files to both datasets
commit1 = dataset1.commit("Add data", add_files=[str(file1)])
commit2 = dataset2.commit("Add data", add_files=[str(file2)])

# Get file hash from first commit
commit1_obj = dataset1.get_commit(commit1)
file_obj = list(commit1_obj.files.values())[0]
file_hash = file_obj.hash

# Find all datasets containing this file
results = catalog.find_datasets_with_file(file_hash)
print(f"File found in {len(results)} datasets:")
for dataset_name in results.keys():
    print(f"  - {dataset_name}")
```

This example demonstrates how the same file content (with different names) is automatically deduplicated and can be found across multiple datasets using the file search functionality.