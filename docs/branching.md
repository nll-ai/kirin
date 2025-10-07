# Kirin Branching

Kirin supports Git-like branching functionality, allowing you to create parallel
development lines for your datasets. This enables collaborative data science
workflows, experimental data processing, and safe data exploration.

## Overview

Branches in Kirin work exactly like Git branches:

- **Branches are named references** to specific commit hashes
- **Each branch tracks its own commit history**
- **You can switch between branches** to work on different versions
- **Branches can be merged** (future feature) or deleted
- **The main branch** is the default and cannot be deleted

## Python API

### Basic Branch Operations

```python
from kirin import Dataset

# Load a dataset
dataset = Dataset(root_dir="/path/to/data", dataset_name="my-dataset")

# List all branches
branches = dataset.list_branches()
print(f"Available branches: {branches}")

# Get current branch
current_branch = dataset.get_current_branch()
print(f"Currently on: {current_branch}")

# Create a new branch from current commit
dataset.create_branch("feature/new-analysis")
print("Created feature branch")

# Switch to a different branch
dataset.switch_branch("feature/new-analysis")
print("Switched to feature branch")

# Delete a branch (cannot delete main)
dataset.delete_branch("feature/old-experiment")
print("Deleted old branch")
```

### Working with Branches

```python
# Create a branch from a specific commit
commit_hash = "abc123def456"
dataset.create_branch("experiment", commit_hash)

# Get the commit hash a branch points to
branch_commit = dataset.get_branch_commit("feature/new-analysis")
print(f"Feature branch points to: {branch_commit}")

# Switch branches and work with data
dataset.switch_branch("main")
files = dataset.file_dict  # Files from main branch

dataset.switch_branch("feature/new-analysis")
files = dataset.file_dict  # Files from feature branch
```

### Branch-Aware Workflows

```python
# Start with main branch
dataset = Dataset(root_dir="/data", dataset_name="project")

# Create experimental branch
dataset.create_branch("experiment/data-cleaning")
dataset.switch_branch("experiment/data-cleaning")

# Add experimental files
dataset.commit("Add experimental data cleaning", add_files=["experiment.py"])

# Switch back to main for production work
dataset.switch_branch("main")
dataset.commit("Add production feature", add_files=["production.py"])

# Both branches now have different files
print("Main branch files:", dataset.file_dict.keys())
dataset.switch_branch("experiment/data-cleaning")
print("Experiment branch files:", dataset.file_dict.keys())
```

## Web UI

### Accessing Branch Management

1. **Load a dataset** in the web UI
2. **Click the "Branches" button** in the dataset view
3. **Manage branches** through the intuitive interface

### Branch Management Interface

The web UI provides:

- **Current Branch Display**: Shows which branch you're currently on
- **Branch List**: All available branches with their status
- **Create New Branch**: Form to create branches from current commit
- **Switch Branches**: One-click branch switching
- **Delete Branches**: Safe deletion with confirmation

### Visual Indicators

- **Current branch** is highlighted in blue
- **Branch status** shows "Current" for active branch
- **Action buttons** for switch/delete operations
- **Breadcrumb navigation** shows current branch

## Branch Storage

Kirin stores branches using Git's exact model:

```text
datasets/my-dataset/
├── refs/heads/           # Branch references
│   ├── main             # Contains: commit_hash
│   ├── feature          # Contains: commit_hash
│   └── experiment       # Contains: commit_hash
└── HEAD                 # Contains: ref: refs/heads/main
```

### File Structure

- **`refs/heads/{branch_name}`**: Contains the commit hash the branch points to
- **`HEAD`**: Points to the current branch (e.g., `ref: refs/heads/main`)
- **Commit history**: Stored in individual commit directories as before

## Best Practices

### Branch Naming

```python
# Good branch names
dataset.create_branch("feature/user-authentication")
dataset.create_branch("experiment/machine-learning")
dataset.create_branch("fix/data-validation")

# Avoid
dataset.create_branch("test")  # Too generic
dataset.create_branch("new")   # Not descriptive
```

### Workflow Patterns

#### 1. Experimental Data Processing

```python
# Create experimental branch
dataset.create_branch("experiment/new-algorithm")
dataset.switch_branch("experiment/new-algorithm")

# Try new approach
dataset.commit("Try new ML algorithm", add_files=["new_model.py"])

# If successful, merge back to main
# If not, delete the branch
```

#### 2. Collaborative Development

```python
# Developer A creates feature branch
dataset.create_branch("feature/user-dashboard")
dataset.switch_branch("feature/user-dashboard")
dataset.commit("Add dashboard components", add_files=["dashboard.py"])

# Developer B can switch to the same branch
dataset.switch_branch("feature/user-dashboard")
# Work on the same feature
```

#### 3. Data Versioning

```python
# Create version branches for different data states
dataset.create_branch("v1.0-clean-data")
dataset.create_branch("v2.0-enhanced-data")

# Switch between versions
dataset.switch_branch("v1.0-clean-data")  # Original clean data
dataset.switch_branch("v2.0-enhanced-data")  # Enhanced version
```

## Error Handling

### Common Errors

```python
# Branch already exists
try:
    dataset.create_branch("main")  # Fails - main is default
except ValueError as e:
    print(f"Error: {e}")

# Branch doesn't exist
try:
    dataset.switch_branch("nonexistent")
except ValueError as e:
    print(f"Error: {e}")

# Cannot delete main branch
try:
    dataset.delete_branch("main")
except ValueError as e:
    print(f"Error: {e}")
```

### Safe Operations

```python
# Check if branch exists before switching
if "feature" in dataset.list_branches():
    dataset.switch_branch("feature")
else:
    print("Feature branch doesn't exist")

# Get current branch before operations
current = dataset.get_current_branch()
print(f"Working on branch: {current}")
```

## Integration with Existing Features

### Commit History

- **Each branch maintains its own commit history**
- **Branch switching updates the current commit**
- **Commit operations update the current branch**

### File Access

- **`dataset.file_dict`** returns files from the current branch
- **`dataset.local_files()`** context manager works with current branch
- **File operations** (add/remove) affect the current branch

### Web UI Integration

- **Branch information** displayed in dataset view
- **Commit history** shows commits for current branch
- **File operations** work within the current branch context

## Advanced Usage

### Branch Inspection

```python
# Get detailed branch information
for branch in dataset.list_branches():
    commit_hash = dataset.get_branch_commit(branch)
    print(f"Branch '{branch}' points to commit {commit_hash[:8]}")
```

### Branch Comparison

```python
# Compare files between branches
main_files = set(dataset.file_dict.keys())
dataset.switch_branch("feature")
feature_files = set(dataset.file_dict.keys())

added_files = feature_files - main_files
removed_files = main_files - feature_files

print(f"Added: {added_files}")
print(f"Removed: {removed_files}")
```

## Future Enhancements

- **Branch merging**: Combine changes from different branches
- **Branch protection**: Prevent accidental deletion of important branches
- **Branch history**: Track when branches were created/modified
- **Remote branches**: Sync branches across different storage locations
- **Branch tags**: Add metadata to branches (description, owner, etc.)

## Troubleshooting

### Common Issues

1. **Branch not found**: Ensure the branch exists with `dataset.list_branches()`
2. **Cannot delete main**: The main branch cannot be deleted
3. **Branch already exists**: Use a different name or delete the existing branch
4. **Files not updating**: Make sure you're on the correct branch

### Debug Information

```python
# Get comprehensive branch information
print(f"Current branch: {dataset.get_current_branch()}")
print(f"All branches: {dataset.list_branches()}")
print(f"Current commit: {dataset.current_version_hash()[:8]}")

# Check branch commit
for branch in dataset.list_branches():
    commit = dataset.get_branch_commit(branch)
    print(f"{branch}: {commit[:8]}")
```

This branching system provides Git-like functionality for data versioning,
enabling sophisticated workflows for data science teams while maintaining the
simplicity and power of Git's branching model.
