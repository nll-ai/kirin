# Commit Management

Understanding and working with Kirin's linear commit history.

## Understanding Commits

### What is a Commit?

A **commit** in Kirin represents an immutable snapshot of files at a point in
time. Unlike Git, Kirin uses a **linear commit history** - each commit has
exactly one parent commit, creating a simple chain of changes.

```text
Commit A → Commit B → Commit C → Commit D
```

### Commit Properties

Every commit has these key properties:

- **Hash**: Unique identifier (SHA256)
- **Message**: Human-readable description
- **Timestamp**: When the commit was created
- **Parent**: Reference to previous commit (linear history)
- **Files**: Dictionary of files in this commit

```python
# Get commit information
commit = dataset.get_commit(commit_hash)
if commit:
    print(f"Commit hash: {commit.hash}")
    print(f"Short hash: {commit.short_hash}")
    print(f"Message: {commit.message}")
    print(f"Timestamp: {commit.timestamp}")
    print(f"Parent: {commit.parent_hash}")
    print(f"Files: {commit.list_files()}")
    print(f"Total size: {commit.get_total_size()} bytes")
```

## Creating Commits

### Commit Method Parameters

The `commit()` method accepts the following parameters:

- **message** (required): Human-readable description of the changes
- **add_files** (optional): List of file paths, model objects, or plot objects to add
- **remove_files** (optional): List of filenames to remove from the dataset

```python
# Add new files
dataset.commit(message="Add new data", add_files=["data.csv", "metadata.json"])

# Remove files
dataset.commit(message="Remove old files", remove_files=["old_data.csv"])

# Add and remove files in the same commit
dataset.commit(
    message="Update dataset",
    add_files=["new_data.csv"],
    remove_files=["old_data.csv"]
)
```

### Committing Plot Objects

You can commit matplotlib and plotly figure objects directly - they are automatically
converted to files with format auto-detection (SVG for vector plots, WebP for raster plots):

```python
import matplotlib.pyplot as plt

# Create a plot
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [1, 4, 9])
ax.set_title("Training Progress")

# Commit the plot object directly
dataset.commit(
    message="Add training visualization",
    add_files=[fig]  # Automatically converted to SVG
)

# Mix plots with other files
fig2, ax2 = plt.subplots()
ax2.scatter([1, 2, 3], [4, 5, 6])

dataset.commit(
    message="Add analysis plots",
    add_files=[fig, fig2, "data.csv"]  # Plots + regular file
)
```

**Format Auto-Detection:**

- **SVG (vector)**: Default format for matplotlib and plotly figures. Best for line
  plots, scatter plots, and other vector-based visualizations. Provides infinite
  scalability without quality loss.

- **WebP (raster)**: Automatically used for plots with raster elements (e.g., images,
  heatmaps). Provides good compression while maintaining quality.

The format is automatically chosen based on the plot type. You don't need to specify
it manually - Kirin handles it for you.

### Error Handling

The `commit()` method can raise the following exceptions:

- **ValueError**: If no changes are specified (both `add_files` and
  `remove_files` are empty)
- **FileNotFoundError**: If a file in `add_files` doesn't exist

```python
try:
    # This will raise ValueError
    dataset.commit(message="No changes")
except ValueError as e:
    print(f"Error: {e}")

try:
    # This will raise FileNotFoundError if file doesn't exist
    dataset.commit(message="Add file", add_files=["nonexistent.csv"])
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

## Working with Commit History

### Viewing History

```python
# Get all commits
history = dataset.history()
for commit in history:
    print(f"{commit.short_hash}: {commit.message}")
    print(f"  Date: {commit.timestamp}")
    print(f"  Files: {commit.list_files()}")
    print()

# Get limited history
recent_commits = dataset.history(limit=5)
for commit in recent_commits:
    print(f"{commit.short_hash}: {commit.message}")
```

### Navigating History

```python
# Checkout latest commit (default)
dataset.checkout()

# Checkout specific commit
dataset.checkout(commit_hash)

# Get current commit
current_commit = dataset.current_commit
if current_commit:
    print(f"Current commit: {current_commit.short_hash}")
    print(f"Message: {current_commit.message}")
```

### Comparing Commits

```python
def compare_commits(dataset, commit1_hash, commit2_hash):
    """Compare two commits to see what changed."""
    commit1 = dataset.get_commit(commit1_hash)
    commit2 = dataset.get_commit(commit2_hash)

    if not commit1 or not commit2:
        print("One or both commits not found")
        return

    files1 = set(commit1.list_files())
    files2 = set(commit2.list_files())

    added = files2 - files1
    removed = files1 - files2
    common = files1 & files2

    print(f"Added files: {added}")
    print(f"Removed files: {removed}")
    print(f"Common files: {common}")

    # Check if common files changed
    for filename in common:
        file1 = commit1.get_file(filename)
        file2 = commit2.get_file(filename)
        if file1.hash != file2.hash:
            print(f"Changed: {filename}")

# Use the comparison function
compare_commits(dataset, "abc123", "def456")
```

## Commit Workflows

### Linear Development

Kirin's linear history is perfect for data science workflows:

```python
# Initial data
dataset.commit(message="Add raw data", add_files=["raw_data.csv"])

# Data cleaning
dataset.commit(message="Clean data", add_files=["cleaned_data.csv"])

# Feature engineering
dataset.commit(message="Add features", add_files=["features.csv"])

# Model training
dataset.commit(message="Add trained model", add_files=["model.pkl"])

# Results
dataset.commit(message="Add results", add_files=["results.csv", "plots.png"])
```

### Experiment Tracking

Track different experiments as separate commits:

```python
# Experiment 1: Random Forest
dataset.commit(message="RF experiment", add_files=["rf_model.pkl", "rf_results.csv"])

# Experiment 2: Gradient Boosting
dataset.commit(message="GB experiment", add_files=["gb_model.pkl", "gb_results.csv"])

# Experiment 3: Neural Network
dataset.commit(message="NN experiment", add_files=["nn_model.pkl", "nn_results.csv"])
```

### Data Pipeline Versioning

Version your data processing pipeline outputs:

```python
# Raw data ingestion
dataset.commit(message="Ingest raw data", add_files=["raw/sales.csv", "raw/customers.csv"])

# Data validation
dataset.commit(message="Validate data", add_files=["validated/sales.csv", "validated/customers.csv"])

# Data transformation
dataset.commit(message="Transform data", add_files=["transformed/sales_clean.csv"])

# Feature engineering
dataset.commit(message="Create features", add_files=["features/engineered_features.csv"])

# Final output
dataset.commit(message="Final dataset", add_files=["final/dataset.csv"])
```

## Advanced Commit Operations

### Commit Information

```python
def analyze_commit(commit):
    """Analyze a commit for detailed information."""
    print(f"Commit: {commit.short_hash}")
    print(f"Message: {commit.message}")
    print(f"Date: {commit.timestamp}")
    print(f"Parent: {commit.parent_hash}")
    print(f"Files: {len(commit.files)}")
    print(f"Total size: {commit.get_total_size()} bytes")

    # File details
    for filename, file_obj in commit.files.items():
        print(f"  {filename}: {file_obj.size} bytes ({file_obj.short_hash})")

# Analyze current commit
current_commit = dataset.current_commit
if current_commit:
    analyze_commit(current_commit)
```

### Commit Statistics

```python
def commit_statistics(dataset):
    """Get statistics about the commit history."""
    history = dataset.history()

    if not history:
        print("No commits found")
        return

    total_commits = len(history)
    total_size = sum(commit.get_total_size() for commit in history)
    avg_size = total_size / total_commits

    print(f"Total commits: {total_commits}")
    print(f"Total size: {total_size / (1024*1024):.1f} MB")
    print(f"Average commit size: {avg_size / (1024*1024):.1f} MB")

    # File frequency
    file_counts = {}
    for commit in history:
        for filename in commit.list_files():
            file_counts[filename] = file_counts.get(filename, 0) + 1

    print(f"Most frequently changed files:")
    for filename, count in sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {filename}: {count} commits")

# Get statistics
commit_statistics(dataset)
```

## Commit Best Practices

### Commit Messages

Write clear, descriptive commit messages:

```python
# Good commit messages
dataset.commit(message="Add Q1 2024 sales data", add_files=["sales_q1_2024.csv"])
dataset.commit(message="Fix data quality issues in customer records", add_files=["customers_cleaned.csv"])
dataset.commit(message="Add feature engineering for ML model", add_files=["features.csv"])

# Avoid vague messages
dataset.commit(message="Update", add_files=["data.csv"])
dataset.commit(message="Fix", add_files=["file.csv"])
dataset.commit(message="Add stuff", add_files=["file1.csv", "file2.csv"])
```

### Commit Frequency

Commit changes regularly:

```python
# Commit after each logical step
dataset.commit(message="Add raw data", add_files=["raw_data.csv"])
# ... process data ...
dataset.commit(message="Add cleaned data", add_files=["cleaned_data.csv"])
# ... analyze data ...
dataset.commit(message="Add analysis results", add_files=["results.csv"])
```

### Atomic Commits

Make commits atomic (single logical change):

```python
# Good: Single logical change
dataset.commit(message="Add customer data", add_files=["customers.csv"])

# Good: Related changes together
dataset.commit(message="Update customer data and add validation",
               add_files=["customers_updated.csv", "validation_rules.json"])

# Avoid: Unrelated changes
dataset.commit(message="Add customer data and fix bug",
               add_files=["customers.csv", "bug_fix.py"])
```

## Working with Specific Commits

### Accessing Files from Specific Commits

```python
def get_files_from_commit(dataset, commit_hash):
    """Get files from a specific commit."""
    commit = dataset.get_commit(commit_hash)
    if not commit:
        print("Commit not found")
        return

    # Checkout the commit
    dataset.checkout(commit_hash)

    # Access files
    files = dataset.files
    print(f"Files in commit {commit_hash}:")
    for filename, file_obj in files.items():
        print(f"  {filename}: {file_obj.size} bytes")

    return files

# Get files from specific commit
files = get_files_from_commit(dataset, "abc123")
```

## Commit History Visualization

### Commit Timeline

```python
def create_timeline(dataset):
    """Create a timeline of commits."""
    history = dataset.history()

    print("Commit Timeline:")
    print("=" * 30)

    for commit in history:
        date_str = commit.timestamp.strftime("%Y-%m-%d %H:%M")
        print(f"{date_str} | {commit.short_hash} | {commit.message}")

# Create timeline
create_timeline(dataset)
```

## Troubleshooting Commits

### Finding Lost Commits

```python
def find_commit_by_message(dataset, search_term):
    """Find commits by message content."""
    history = dataset.history()

    for commit in history:
        if search_term.lower() in commit.message.lower():
            print(f"Found: {commit.short_hash} - {commit.message}")
            return commit

    print(f"No commits found matching '{search_term}'")
    return None

# Find commit
commit = find_commit_by_message(dataset, "model")
```

### Recovering from Mistakes

```python
def recover_from_mistake(dataset, good_commit_hash):
    """Recover from a mistake by checking out a good commit."""
    # Checkout the good commit
    dataset.checkout(good_commit_hash)

    # Verify we're on the right commit
    current_commit = dataset.current_commit
    if current_commit and current_commit.hash == good_commit_hash:
        print(f"Successfully recovered to commit {good_commit_hash}")
        print(f"Current commit: {current_commit.message}")
    else:
        print("Failed to recover to specified commit")

# Recover from mistake
recover_from_mistake(dataset, "abc123")
```

## Next Steps

- **[Working with Files](working-with-files.md)** - File operations and patterns
- **[Basic Usage](basic-usage.md)** - Core dataset operations
- **[Cloud Storage](cloud-storage.md)** - Working with cloud backends
