# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../../", editable = true }
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Working with Commits

    This tutorial deep dives into Kirin's commit system. You'll learn how
    commits work, how to navigate commit history, compare commits, and use
    commits effectively in your data science workflows.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What You'll Learn

    - Understanding commit structure and properties
    - Navigating linear commit history
    - Comparing commits to see what changed
    - Working with specific commits
    - Best practices for commit messages and workflows
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prerequisites

    - Completed [Your First Dataset](first-dataset.md) tutorial
    - Basic understanding of datasets and files
    """)
    return


@app.cell
def _():
    import tempfile
    from datetime import datetime
    from pathlib import Path

    from kirin import Catalog

    # Create a temporary directory for our tutorial
    # In production, you might use: Catalog(root_dir="s3://my-bucket/data")
    temp_dir = Path(tempfile.mkdtemp(prefix="kirin_commits_tutorial_"))
    catalog = Catalog(root_dir=temp_dir)

    # Create a new dataset
    dataset = catalog.create_dataset(
        "commit_demo", description="Demo dataset for commit tutorial"
    )

    # Create a directory for our data files
    data_dir = temp_dir / "sample_data"
    data_dir.mkdir(exist_ok=True)

    print(f"✅ Created dataset: {dataset.name}")
    print(f"   Dataset root: {dataset.root_dir}")
    return data_dir, dataset, datetime


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Understanding Commit Structure

    A **commit** in Kirin is an immutable snapshot of files at a specific
    point in time. Unlike Git, Kirin uses a **linear commit history** - each
    commit has exactly one parent, creating a simple chain:

    ```
    Initial Commit → Commit 2 → Commit 3 → Commit 4
    ```

    Let's create some commits and explore what makes up a commit.
    """)
    return


@app.cell
def _(data_dir, dataset, datetime):
    # Create first commit
    file1 = data_dir / "data_v1.csv"
    file1.write_text("name,value\nA,10\nB,20\n")

    commit_msg1 = f"Initial data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    commit_hash1 = dataset.commit(message=commit_msg1, add_files=[str(file1)])

    print(f"✅ Created first commit: {commit_hash1[:8]}")
    return


@app.cell
def _(data_dir, dataset, datetime):
    # Create second commit
    file2 = data_dir / "data_v2.csv"
    file2.write_text("name,value\nA,10\nB,20\nC,30\n")

    commit_msg2 = f"Add more data - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    commit_hash2 = dataset.commit(message=commit_msg2, add_files=[str(file2)])

    print(f"✅ Created second commit: {commit_hash2[:8]}")
    return


@app.cell
def _(dataset):
    # Get the current commit and explore its properties
    current_commit = dataset.current_commit
    if current_commit:
        print("📊 Commit Properties:")
        print(f"   Hash: {current_commit.hash}")
        print(f"   Short hash: {current_commit.short_hash}")
        print(f"   Message: {current_commit.message}")
        print(f"   Timestamp: {current_commit.timestamp}")
        parent_hash_display = (
            current_commit.parent_hash[:8]
            if current_commit.parent_hash
            else "None (initial)"
        )
        print(f"   Parent hash: {parent_hash_display}")
        print(f"   Files: {current_commit.list_files()}")
        print(f"   File count: {current_commit.get_file_count()}")
        print(f"   Total size: {current_commit.get_total_size()} bytes")
        print(f"   Is initial: {current_commit.is_initial}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Key properties:**

    - **Hash**: Unique identifier (SHA256) for the commit
    - **Message**: Human-readable description of what changed
    - **Timestamp**: When the commit was created
    - **Parent hash**: Reference to the previous commit (None for initial
      commit)
    - **Files**: Dictionary of File objects in this commit
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Viewing Commit History

    The commit history is a linear sequence. Let's explore it to see how
    commits are organized.
    """)
    return


@app.cell
def _(dataset):
    # Get all commits (newest to oldest)
    history = dataset.history()
    # Reverse to show oldest first for tutorial clarity
    history_oldest_first = list(reversed(history))

    print(f"📊 Total commits: {len(history)}")
    print("\nCommit History (oldest → newest):")
    print("=" * 50)

    for step_num, history_commit in enumerate(history_oldest_first, 1):
        print(f"\n{step_num}. {history_commit.short_hash}: {history_commit.message}")
        print(f"   Date: {history_commit.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Files: {', '.join(history_commit.list_files())}")
        parent_display = (
            history_commit.parent_hash[:8]
            if history_commit.parent_hash
            else "None (initial)"
        )
        print(f"   Parent: {parent_display}")
    return (history,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Understanding the history:**

    - History is returned from newest to oldest (latest commit first)
    - Each commit (except the first) has a parent
    - The latest commit is `history[0]` or use `dataset.current_commit`
    - To display oldest first, reverse the list: `list(reversed(history))`
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Limiting History

    For large datasets with many commits, you can limit how many commits to
    retrieve. This is useful for performance and focusing on recent changes.
    """)
    return


@app.cell
def _(dataset):
    # Get only the 5 most recent commits
    recent_commits = dataset.history(limit=5)

    print(f"📊 Recent commits: {len(recent_commits)}")
    for recent_commit in recent_commits:
        print(f"   {recent_commit.short_hash}: {recent_commit.message}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Getting Specific Commits

    You can retrieve a specific commit by its hash. This is useful when you
    know exactly which commit you want to work with.
    """)
    return


@app.cell
def _(dataset, history):
    # Get a specific commit (using the oldest commit for demonstration)
    oldest_commit_hash = history[-1].hash  # Oldest is last in newest-first list
    retrieved_commit = dataset.get_commit(oldest_commit_hash)

    if retrieved_commit:
        print(f"✅ Retrieved commit: {retrieved_commit.short_hash}")
        print(f"   Message: {retrieved_commit.message}")
        print(f"   Files: {retrieved_commit.list_files()}")
    else:
        print("❌ Commit not found")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Checking Out Commits

    "Checking out" a commit means switching the dataset to that commit's
    state. This lets you see what files were available at that point in
    time.
    """)
    return


@app.cell
def _(dataset):
    # Checkout the latest commit (default)
    dataset.checkout()
    current_commit_hash = (
        dataset.current_commit.short_hash if dataset.current_commit else "None"
    )
    print(f"📂 Current commit: {current_commit_hash}")
    print(f"   Files: {list(dataset.files.keys())}")
    return


@app.cell
def _(dataset, history):
    # Checkout a specific commit (using the oldest commit)
    oldest_commit_for_checkout = history[-1]  # Oldest is last in newest-first list
    dataset.checkout(oldest_commit_for_checkout.hash)

    print("\n📂 After checkout:")
    print(f"   Current commit: {dataset.current_commit.short_hash}")
    print(f"   Files: {list(dataset.files.keys())}")
    return


@app.cell
def _(dataset):
    # Checkout latest again
    dataset.checkout()  # No argument = latest
    print("\n📂 Back to latest:")
    print(f"   Current commit: {dataset.current_commit.short_hash}")
    print(f"   Files: {list(dataset.files.keys())}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **Important:** Checking out a commit doesn't delete anything - it just
    changes which files are "current" in the dataset. All commits and their
    files remain accessible.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6: Comparing Commits

    One of the most powerful features is comparing commits to see what
    changed between them. This helps you understand how your dataset evolved
    over time.
    """)
    return


@app.cell
def _(dataset, history):
    # Get two commits to compare (oldest vs newest)
    oldest_commit = history[-1]  # Oldest is last in newest-first list
    newest_commit = history[0]  # Newest is first in newest-first list

    # Compare them (oldest first, then newest)
    comparison = dataset.compare_commits(oldest_commit.hash, newest_commit.hash)

    print("📊 Commit Comparison:")
    print("=" * 50)
    commit1_info = comparison["commit1"]
    commit2_info = comparison["commit2"]
    print(f"Commit 1: {commit1_info['hash'][:8]} - {commit1_info['message']}")
    print(f"Commit 2: {commit2_info['hash'][:8]} - {commit2_info['message']}")

    # File changes - compute manually by comparing file lists
    print("\n📁 File Changes:")
    files1 = set(oldest_commit.list_files())
    files2 = set(newest_commit.list_files())

    added_files = list(files2 - files1)
    removed_files = list(files1 - files2)
    unchanged_files = list(files1 & files2)

    if added_files:
        print(f"   Added: {added_files}")
    if removed_files:
        print(f"   Removed: {removed_files}")
    if unchanged_files:
        print(f"   Unchanged: {unchanged_files}")

    # Metadata changes (if any)
    if comparison.get("metadata_diff"):
        metadata_diff = comparison["metadata_diff"]
        if metadata_diff.get("added"):
            print(f"\n📋 Metadata Added: {metadata_diff['added']}")
        if metadata_diff.get("changed"):
            print(f"📋 Metadata Changed: {metadata_diff['changed']}")

    # Tag changes (if any)
    if comparison.get("tags_diff"):
        tags_diff = comparison["tags_diff"]
        if tags_diff.get("added"):
            print(f"\n🏷️  Tags Added: {tags_diff['added']}")
        if tags_diff.get("removed"):
            print(f"🏷️  Tags Removed: {tags_diff['removed']}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7: Understanding File Changes

    Let's see how files change between commits by creating more commits and
    comparing them step by step.
    """)
    return


@app.cell
def _(data_dir, dataset, datetime):
    # Create commits with file changes
    file3 = data_dir / "data_v3.csv"
    file3.write_text("name,value\nA,10\nB,20\nC,30\nD,40\n")

    commit_msg3 = f"Add more rows - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    dataset.commit(message=commit_msg3, add_files=[str(file3)])

    # Remove a file
    commit_msg4 = f"Remove old file - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    dataset.commit(message=commit_msg4, remove_files=["data_v1.csv"])

    print("✅ Created additional commits with file changes")
    return


@app.cell
def _(dataset):
    # Update history
    updated_history = dataset.history()

    # Compare adjacent commits (going from newest to oldest)
    print("📊 Comparing adjacent commits (newest → oldest):")
    print("=" * 50)

    for step_index in range(len(updated_history) - 1):
        commit_a = updated_history[step_index]  # Newer commit
        commit_b = updated_history[step_index + 1]  # Older commit

        # Compute file differences manually
        files_a = set(commit_a.list_files())
        files_b = set(commit_b.list_files())

        added_files_result = list(files_b - files_a)
        removed_files_result = list(files_a - files_b)

        print(f"\n{commit_a.short_hash} → {commit_b.short_hash}:")
        if added_files_result:
            print(f"   + Added: {added_files_result}")
        if removed_files_result:
            print(f"   - Removed: {removed_files_result}")
    return (updated_history,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 8: Commit Metadata and Tags

    Commits can have metadata and tags for better organization. This is
    especially useful for tracking experiments, model versions, or data
    releases.
    """)
    return


@app.cell
def _(data_dir, dataset, datetime):
    # Create a commit with metadata and tags
    file4 = data_dir / "model_v1.pkl"
    file4.write_text("fake model data")

    commit_msg5 = f"Add trained model - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    dataset.commit(
        message=commit_msg5,
        add_files=[str(file4)],
        metadata={
            "accuracy": 0.92,
            "framework": "sklearn",
            "model_type": "RandomForest",
        },
        tags=["model", "v1.0", "production"],
    )

    print("✅ Created commit with metadata and tags")
    return


@app.cell
def _(dataset):
    # Access metadata and tags
    latest_commit = dataset.current_commit
    if latest_commit:
        print(f"📊 Commit: {latest_commit.short_hash}")
        print(f"   Metadata: {latest_commit.metadata}")
        print(f"   Tags: {latest_commit.tags}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 9: Finding Commits

    You can search for commits using various criteria: tags, metadata
    filters, or message content. This makes it easy to find specific commits
    in large datasets.
    """)
    return


@app.cell
def _(dataset):
    # Find commits by tags
    production_commits = dataset.find_commits(tags=["production"])
    print(f"🏷️  Production commits: {len(production_commits)}")
    for prod_commit in production_commits:
        print(f"   {prod_commit.short_hash}: {prod_commit.message}")
    return


@app.cell
def _(dataset):
    # Find commits by metadata filter
    high_accuracy_commits = dataset.find_commits(
        metadata_filter=lambda m: m.get("accuracy", 0) > 0.9
    )
    print(f"\n📊 High accuracy commits: {len(high_accuracy_commits)}")
    for acc_commit in high_accuracy_commits:
        accuracy_value = acc_commit.metadata.get("accuracy")
        commit_info = f"{acc_commit.short_hash}: {acc_commit.message}"
        print(f"   {commit_info} (accuracy: {accuracy_value})")
    return


@app.cell
def _(dataset):
    # Find commits by message content
    def find_by_message(dataset, search_term):
        history = dataset.history()
        return [c for c in history if search_term.lower() in c.message.lower()]

    model_commits = find_by_message(dataset, "model")
    print(f"\n🔍 Commits with 'model' in message: {len(model_commits)}")
    for msg_commit in model_commits:
        print(f"   {msg_commit.short_hash}: {msg_commit.message}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 10: Commit Statistics

    Let's analyze commit patterns to understand how your dataset has evolved
    over time.
    """)
    return


@app.cell
def _(dataset):
    def analyze_commits(dataset):
        history = dataset.history()

        if not history:
            print("No commits found")
            return

        print("📊 Commit Statistics:")
        print("=" * 50)

        # Basic stats
        total_commits = len(history)
        total_size = sum(c.get_total_size() for c in history)
        avg_size = total_size / total_commits if total_commits > 0 else 0

        print(f"Total commits: {total_commits}")
        print(f"Total size: {total_size / (1024 * 1024):.2f} MB")
        print(f"Average commit size: {avg_size / 1024:.2f} KB")

        # File frequency
        file_counts = {}
        for commit in history:
            for filename in commit.list_files():
                file_counts[filename] = file_counts.get(filename, 0) + 1

        print("\nMost frequently changed files:")
        sorted_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for filename, count in sorted_files:
            print(f"   {filename}: appears in {count} commits")

        # Time span
        if len(history) > 1:
            first_date = history[0].timestamp
            last_date = history[-1].timestamp
            time_span = last_date - first_date
            print(f"\nTime span: {time_span.days} days")
            print(f"   First commit: {first_date.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Last commit: {last_date.strftime('%Y-%m-%d %H:%M')}")

    analyze_commits(dataset)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 11: Working with Commit Files

    You can access files from specific commits by checking out that commit
    and then using the standard file access methods.
    """)
    return


@app.cell
def _(dataset, updated_history):
    # Get files from a specific commit (using oldest for demonstration)
    target_commit = updated_history[-1]  # Oldest is last in newest-first list
    dataset.checkout(target_commit.hash)

    print(f"📁 Files in commit {target_commit.short_hash}:")
    with dataset.local_files() as local_files:
        for filename, local_path in local_files.items():
            file_obj = dataset.get_file(filename)
            print(f"   {filename}:")
            print(f"      Size: {file_obj.size} bytes")
            print(f"      Hash: {file_obj.hash[:16]}...")
            print(f"      Local path: {local_path}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 12: Commit Workflows

    Here are common commit workflow patterns that you can use in your data
    science projects.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Pattern 1: Linear Data Processing

    Sequential data processing pipeline where each step commits its output.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ```python
    # Sequential data processing pipeline
    dataset.commit(message="Add raw data", add_files=["raw_data.csv"])
    # ... process data ...
    dataset.commit(message="Add cleaned data", add_files=["cleaned_data.csv"])
    # ... analyze data ...
    dataset.commit(message="Add analysis results", add_files=["results.csv"])
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Pattern 2: Experiment Tracking

    Track different experiments with metadata and tags for easy comparison.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ```python
    # Track different experiments
    dataset.commit(
        message="Experiment 1: Random Forest",
        add_files=["rf_model.pkl", "rf_results.csv"],
        metadata={"model": "RandomForest", "accuracy": 0.85},
        tags=["experiment", "rf"]
    )

    dataset.commit(
        message="Experiment 2: Gradient Boosting",
        add_files=["gb_model.pkl", "gb_results.csv"],
        metadata={"model": "GradientBoosting", "accuracy": 0.90},
        tags=["experiment", "gb"]
    )
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Pattern 3: Versioned Releases

    Version your data releases with tags for easy reference.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ```python
    # Version your data releases
    dataset.commit(
        message="Release v1.0: Initial dataset",
        add_files=["dataset_v1.csv"],
        tags=["release", "v1.0"]
    )

    dataset.commit(
        message="Release v1.1: Added features",
        add_files=["dataset_v1.1.csv"],
        tags=["release", "v1.1"]
    )
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 13: Best Practices

    Following best practices helps you maintain a clean, understandable
    commit history that makes it easy to track changes and understand your
    dataset's evolution.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Write Clear Commit Messages

    Good commit messages are descriptive and specific. They explain what
    changed and why, making it easy to understand the dataset's history.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ```python
    # ✅ Good: Descriptive and specific
    dataset.commit(
        message="Add Q1 2024 sales data with customer demographics",
        add_files=["sales_q1_2024.csv"]
    )

    # ✅ Good: Explains the change
    dataset.commit(
        message="Fix data quality issues: remove duplicates and handle missing values",
        add_files=["customers_cleaned.csv"]
    )

    # ❌ Bad: Vague and unhelpful
    dataset.commit(message="Update", add_files=["data.csv"])
    dataset.commit(message="Fix", add_files=["file.csv"])
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Make Atomic Commits

    Each commit should represent a single logical change. This makes it
    easier to understand what changed and to revert specific changes if
    needed.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ```python
    # ✅ Good: Single logical change
    dataset.commit(message="Add customer data", add_files=["customers.csv"])

    # ✅ Good: Related changes together
    dataset.commit(
        message="Update customer data and add validation rules",
        add_files=["customers_updated.csv", "validation_rules.json"]
    )

    # ❌ Bad: Unrelated changes
    dataset.commit(
        message="Add customer data and fix bug",
        add_files=["customers.csv", "bug_fix.py"]
    )
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Commit Regularly

    Commit after each logical step in your workflow. This creates a clear
    history of how your dataset evolved and makes it easier to track
    changes.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ```python
    # ✅ Good: Commit after each logical step
    dataset.commit(message="Add raw data", add_files=["raw_data.csv"])
    # ... process data ...
    dataset.commit(message="Add cleaned data", add_files=["cleaned_data.csv"])

    # ❌ Bad: Too many changes in one commit
    # ... many processing steps ...
    dataset.commit(
        message="All changes",
        add_files=["file1.csv", "file2.csv", "file3.csv", ...],
    )
    ```
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 14: Troubleshooting

    Sometimes you need to find a specific commit or recover to a previous
    state. Here are some helpful techniques.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Finding Lost Commits

    If you have a partial commit hash, you can search for the full commit.
    """)
    return


@app.cell
def _(dataset, updated_history):
    def find_commit_by_hash(dataset, partial_hash):
        history = dataset.history()
        for commit in history:
            if commit.hash.startswith(partial_hash):
                return commit
        return None

    # Find commit using a partial hash (using oldest for demonstration)
    found_commit = None
    partial_hash = None
    if updated_history:
        partial_hash = updated_history[-1].hash[:8]  # Oldest is last
        found_commit = find_commit_by_hash(dataset, partial_hash)
        if found_commit:
            print(f"✅ Found: {found_commit.short_hash} - {found_commit.message}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### Recovering from Mistakes

    You can recover your dataset to a specific commit state by checking out
    that commit.
    """)
    return


@app.cell
def _(dataset, updated_history):
    def recover_to_commit(dataset, commit_hash):
        commit = dataset.get_commit(commit_hash)
        if not commit:
            print(f"❌ Commit {commit_hash} not found")
            return False

        # Checkout the commit
        dataset.checkout(commit_hash)

        # Verify
        if dataset.current_commit and dataset.current_commit.hash == commit_hash:
            print(f"✅ Successfully recovered to commit {commit_hash[:8]}")
            print(f"   Message: {dataset.current_commit.message}")
            return True
        else:
            print("❌ Failed to recover")
            return False

    # Recover to a known good commit (using oldest for demonstration)
    recover_to_commit(dataset, updated_history[-1].hash)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    Congratulations! You've learned how to work with commits in Kirin:

    - ✅ **Understanding commit structure** - Hash, message, timestamp,
      parent, files
    - ✅ **Navigating history** - Viewing, limiting, and finding commits
    - ✅ **Checking out commits** - Switching between different commit
      states
    - ✅ **Comparing commits** - Seeing what changed between commits
    - ✅ **Using metadata and tags** - Organizing commits with additional
      information
    - ✅ **Finding commits** - Searching by tags, metadata, or message
    - ✅ **Best practices** - Writing good commit messages and workflows

    ## Key Concepts

    - **Linear History**: Each commit has one parent, creating a simple
      chain
    - **Immutable Snapshots**: Commits are immutable - they never change
    - **Content-Addressed Files**: Files are stored by content hash, not
      filename
    - **Checkout**: Switching the dataset to a specific commit's state

    ## Next Steps

    - **[Cloud Storage Overview](cloud-storage.md)** - Learn about using
      cloud storage backends
    - **[Web UI Basics](web-ui-basics.md)** - Use the web interface to
      browse commits
    - **[Track Model Training Data](../how-to/track-model-data.md)** - See
      commits in action with ML workflows
    """)
    return


if __name__ == "__main__":
    app.run()
