# Basic Usage

Learn the essential workflows for working with Kirin datasets.

## Creating and Managing Datasets

### Create a New Dataset

```python
from kirin import Catalog, Dataset

# Create a catalog
catalog = Catalog(root_dir="/path/to/data")

# Create a new dataset
dataset = catalog.create_dataset(
    name="my_experiment",
    description="ML experiment data for Q1 2024"
)

print(f"Created dataset: {dataset.name}")
```

### Get an Existing Dataset

```python
# Get an existing dataset
dataset = catalog.get_dataset("my_experiment")

# Check if dataset exists
if dataset:
    print(f"Dataset has {len(dataset.history())} commits")
else:
    print("Dataset not found")
```

## Working with Files

### Adding Files to a Dataset

```python
# Add single file
commit_hash = dataset.commit(
    message="Add initial data",
    add_files=["data.csv"]
)

# Add multiple files
commit_hash = dataset.commit(
    message="Add processed data",
    add_files=["data.csv", "config.json", "results.txt"]
)

print(f"Created commit: {commit_hash}")
```

### Removing Files from a Dataset

```python
# Remove single file
dataset.commit(
    message="Remove old data",
    remove_files=["old_data.csv"]
)

# Remove multiple files
dataset.commit(
    message="Clean up dataset",
    remove_files=["temp1.csv", "temp2.json"]
)
```

### Combined Operations

```python
# Add and remove files in same commit
dataset.commit(
    message="Update dataset",
    add_files=["new_data.csv"],
    remove_files=["old_data.csv"]
)
```

## Working with Commits

### Viewing Commit History

```python
# Get all commits
history = dataset.history()
for commit in history:
    print(f"{commit.short_hash}: {commit.message}")
    print(f"  Files: {commit.list_files()}")
    print(f"  Date: {commit.timestamp}")

# Get limited history
recent_commits = dataset.history(limit=5)
```

### Checking Out Commits

```python
# Checkout latest commit (default)
dataset.checkout()

# Checkout specific commit
dataset.checkout(commit_hash)

# Get current commit info
current_commit = dataset.current_commit
if current_commit:
    print(f"Current commit: {current_commit.short_hash}")
    print(f"Message: {current_commit.message}")
```

### Comparing Commits

```python
# Get two commits
commit1 = dataset.get_commit(hash1)
commit2 = dataset.get_commit(hash2)

if commit1 and commit2:
    # Compare file lists
    files1 = set(commit1.list_files())
    files2 = set(commit2.list_files())

    added = files2 - files1
    removed = files1 - files2
    common = files1 & files2

    print(f"Added files: {added}")
    print(f"Removed files: {removed}")
    print(f"Common files: {common}")
```

## Working with Files

### File Information

```python
# List files in current commit
files = dataset.files
print(f"Files: {list(files.keys())}")

# Check if file exists
if dataset.has_file("data.csv"):
    print("File exists")

# Get file object
file_obj = dataset.get_file("data.csv")
if file_obj:
    print(f"File size: {file_obj.size} bytes")
    print(f"Content hash: {file_obj.hash}")
```

### Local File Access (Recommended Pattern)

The `local_files()` context manager is the recommended way to work with files:

```python
from pathlib import Path
import pandas as pd

# Work with files locally
with dataset.local_files() as local_files:
    for filename, local_path in local_files.items():
        print(f"{filename} -> {local_path}")

        # Process files with standard Python libraries
        if filename.endswith('.csv'):
            df = pd.read_csv(local_path)
            print(f"CSV shape: {df.shape}")
        elif filename.endswith('.json'):
            import json
            data = json.loads(Path(local_path).read_text())
            print(f"JSON keys: {list(data.keys())}")
```

**Benefits of local_files():**
- **Library compatibility**: Works with pandas, polars, etc.
- **Automatic cleanup**: Files cleaned up when done
- **Standard paths**: Use normal Python file operations
- **Memory efficient**: No need to load entire files into memory

## Dataset Information

### Get Dataset Info

```python
# Check if dataset is empty
if dataset.is_empty():
    print("Dataset has no commits")
else:
    print(f"Dataset has {len(dataset.history())} commits")

# Get dataset information
info = dataset.get_info()
print(f"Dataset info: {info}")

# Convert to dictionary
dataset_dict = dataset.to_dict()
print(f"Serialized dataset: {dataset_dict}")
```

### Cleanup Operations

```python
# Clean up orphaned files (files not referenced by any commit)
removed_count = dataset.cleanup_orphaned_files()
print(f"Removed {removed_count} orphaned files")
```

## Common Workflows

### Experiment Tracking

```python
# Track ML experiment
dataset = catalog.get_dataset("ml_experiment")

# Add training data
dataset.commit(
    message="Add training data",
    add_files=["train.csv", "train_labels.csv"]
)

# Add model
dataset.commit(
    message="Add trained model",
    add_files=["model.pkl", "model_metrics.json"]
)

# Add results
dataset.commit(
    message="Add experiment results",
    add_files=["results.csv", "plots.png"]
)
```

### Data Pipeline Versioning

```python
# Track ETL pipeline
dataset = catalog.get_dataset("etl_pipeline")

# Raw data
dataset.commit(
    message="Add raw data",
    add_files=["raw_data.csv"]
)

# Processed data
dataset.commit(
    message="Add processed data",
    add_files=["processed_data.csv", "processing_log.txt"]
)

# Final output
dataset.commit(
    message="Add final output",
    add_files=["final_data.csv", "summary.json"]
)
```

### Collaborative Research

```python
# Share dataset with team
dataset = catalog.get_dataset("research_data")

# Add initial data
dataset.commit(
    message="Initial dataset",
    add_files=["raw_data.csv", "metadata.json"]
)

# Team member adds analysis
dataset.commit(
    message="Add analysis results",
    add_files=["analysis.py", "results.csv", "plots.png"]
)
```

## Best Practices

### Commit Messages

Use descriptive commit messages:

```python
# Good commit messages
dataset.commit("Add Q1 sales data", add_files=["sales_q1.csv"])
dataset.commit("Fix data quality issues", add_files=["sales_q1.csv"])
dataset.commit("Add customer segmentation", add_files=["segments.csv"])

# Avoid vague messages
dataset.commit("Update", add_files=["data.csv"])  # Too vague
dataset.commit("Fix", add_files=["data.csv"])     # Too vague
```

### File Organization

Organize files logically:

```python
# Good organization
dataset.commit("Add raw data", add_files=["raw/sales.csv", "raw/customers.csv"])
dataset.commit("Add processed data", add_files=["processed/sales_clean.csv"])
dataset.commit("Add analysis", add_files=["analysis/results.csv", "analysis/plots.png"])

# Avoid flat structure
dataset.commit("Add files", add_files=["sales.csv", "customers.csv", "results.csv", "plots.png"])
```

### Regular Commits

Commit changes regularly:

```python
# Commit after each logical step
dataset.commit("Add initial data", add_files=["data.csv"])
# ... process data ...
dataset.commit("Add processed data", add_files=["processed.csv"])
# ... analyze data ...
dataset.commit("Add analysis", add_files=["results.csv"])
```

## Next Steps

- **[Working with Files](working-with-files.md)** - Advanced file operations
- **[Commit Management](commit-management.md)** - Understanding commit history
- **[Cloud Storage](cloud-storage.md)** - Working with cloud backends
