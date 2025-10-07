# GitData API Reference

## Core Classes

### Dataset

The main class for working with GitData datasets.

```python
from gitdata import Dataset

# Create or load a dataset
dataset = Dataset(root_dir="/path/to/data", dataset_name="my-dataset")
```

#### Basic Operations

- `commit(message, add_files=None, remove_files=None)` - Commit changes to the dataset
- `checkout(commit_hash)` - Switch to a specific commit
- `file_dict` - Dictionary of files in the current commit
- `local_files()` - Context manager for accessing files as local paths

#### Branch Operations

- `create_branch(name, commit_hash=None)` - Create a new branch
- `list_branches()` - List all branches
- `get_current_branch()` - Get the current branch name
- `switch_branch(name)` - Switch to a different branch
- `delete_branch(name)` - Delete a branch
- `get_branch_commit(name)` - Get the commit hash a branch points to

#### Examples

```python
# Basic usage
dataset = Dataset(root_dir="/data", dataset_name="project")
dataset.commit("Initial commit", add_files=["data.csv"])

# Branching
dataset.create_branch("feature/analysis")
dataset.switch_branch("feature/analysis")
dataset.commit("Add analysis script", add_files=["analyze.py"])

# Switch back to main
dataset.switch_branch("main")
```

### BranchManager

Low-level branch management (used internally by Dataset).

```python
from gitdata.models import BranchManager

# Create branch manager
branch_manager = BranchManager(dataset_dir, filesystem)
```

#### Methods

- `create_branch(name, commit_hash)` - Create a branch
- `get_branch_commit(name)` - Get branch commit hash
- `update_branch(name, commit_hash)` - Update branch pointer
- `delete_branch(name)` - Delete a branch
- `list_branches()` - List all branches
- `get_current_branch()` - Get current branch
- `set_current_branch(name)` - Set current branch

## Web UI

The web UI provides a graphical interface for GitData operations.

### Routes

- `/` - Home page for loading datasets
- `/dataset-view` - Main dataset view
- `/branches` - Branch management interface
- `/commit` - Commit interface
- `/d/{dataset_name}` - Direct dataset access

### Branch Management

Access branch management through the web UI:

1. Load a dataset
2. Click the "Branches" button
3. Create, switch, or delete branches through the interface

## Storage Format

GitData uses a Git-like storage format:

```text
data/
├── objects/              # Content-addressed file storage
├── datasets/
│   └── my-dataset/
│       ├── refs/heads/  # Branch references
│       │   ├── main     # Contains commit hash
│       │   └── feature  # Contains commit hash
│       ├── HEAD         # Points to current branch
│       └── {commit}/    # Individual commits
│           └── commit.json
```

## Error Handling

### Common Exceptions

- `DatasetNoCommitsError` - No commits found in dataset
- `ValueError` - Invalid branch operations (branch exists, doesn't exist, etc.)
- `FileNotFoundError` - File not found in dataset

### Example Error Handling

```python
try:
    dataset.create_branch("feature")
except ValueError as e:
    print(f"Branch creation failed: {e}")

try:
    dataset.switch_branch("nonexistent")
except ValueError as e:
    print(f"Branch switch failed: {e}")
```

## Best Practices

### Branch Naming

- Use descriptive names: `feature/user-auth`, `experiment/ml-model`
- Avoid generic names: `test`, `new`, `temp`

### Workflow Patterns

- Create feature branches for new work
- Use experimental branches for testing
- Keep main branch stable
- Delete branches when work is complete

### File Management

- Use `local_files()` context manager for library compatibility
- Check branch before file operations
- Commit changes regularly

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
# Get commit history as Mermaid diagram
mermaid = dataset.commit_history_mermaid()
print(mermaid)  # Can be rendered in Jupyter
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

For detailed examples and advanced usage, see the [Branching Documentation](branching.md).
