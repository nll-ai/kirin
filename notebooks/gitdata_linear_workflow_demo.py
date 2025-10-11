# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "gitdata==0.0.1",
#     "loguru==0.7.3",
# ]
#
# [tool.uv.sources]
# gitdata = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.16.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    """# GitData: Linear Workflow Demonstration

    This notebook demonstrates how to use **GitData** for version-controlled data management with a clean, linear commit history. GitData brings Git-like workflows to your data, enabling you to:

    - 📁 **Track data changes** with commits and branches
    - 🔄 **Merge branches** using rebase strategy for linear history
    - 📊 **Visualize commit history** with color-coded branch diagrams
    - 🗂️ **Manage files** with add/remove operations
    - 🏷️ **Version control** your datasets like code

    ## What You'll Learn

    In this demo, we'll create a dataset, make changes on feature branches, and merge them back to main using **rebase strategy** to maintain a clean, linear history without merge commits.
    """
    mo.md(
        """# GitData: Linear Workflow Demonstration

This notebook demonstrates how to use **GitData** for version-controlled data management with a clean, linear commit history. GitData brings Git-like workflows to your data, enabling you to:

- 📁 **Track data changes** with commits and branches
- 🔄 **Merge branches** using rebase strategy for linear history
- 📊 **Visualize commit history** with color-coded branch diagrams
- 🗂️ **Manage files** with add/remove operations
- 🏷️ **Version control** your datasets like code

## What You'll Learn

In this demo, we'll create a dataset, make changes on feature branches, and merge them back to main using **rebase strategy** to maintain a clean, linear history without merge commits."""
    )
    return


@app.cell
def _(mo):
    """## Step 1: Dataset Setup

    Let's start by creating a new GitData dataset with some initial files. This simulates the beginning of a data project where you have your base dataset ready for version control.
    """
    mo.md(
        """## Step 1: Dataset Setup

Let's start by creating a new GitData dataset with some initial files. This simulates the beginning of a data project where you have your base dataset ready for version control."""
    )
    return


@app.cell
def _():
    """Setup dataset for linear history workflow."""
    import tempfile
    import time
    from pathlib import Path

    from kirin.dataset import Dataset

    # Use 3 random words for dataset name
    dataset_name = f"demo_linear_{int(time.time())}"
    temp_dir = tempfile.mkdtemp()
    dataset = Dataset(root_dir=temp_dir, dataset_name=dataset_name)

    # Create initial files
    file1 = Path(temp_dir) / "file1.txt"
    file1.write_text("Content of file 1")

    file2 = Path(temp_dir) / "file2.txt"
    file2.write_text("Content of file 2")

    # Initial commit
    dataset.commit("Initial commit with two files", add_files=[str(file1), str(file2)])

    print("✅ Dataset setup complete")
    print(f"Dataset: {dataset_name}")
    print(f"Files: {list(dataset.file_dict.keys())}")
    return dataset, temp_dir


@app.cell
def _(dataset):
    """Verify initial commit works correctly."""
    # Verify files are in dataset
    assert "file1.txt" in dataset.file_dict
    assert "file2.txt" in dataset.file_dict

    # Verify commit exists
    initial_commits = dataset.get_commits()
    assert len(initial_commits) == 1
    assert initial_commits[0]["message"] == "Initial commit with two files"

    print("✅ Initial commit verification passed")
    return


@app.cell
def _(mo):
    """## Step 2: Feature Branch Development

    Now we'll create a feature branch to add new data. This represents a common workflow where you want to experiment with new data without affecting the main branch.
    """
    mo.md(
        """## Step 2: Feature Branch Development

Now we'll create a feature branch to add new data. This represents a common workflow where you want to experiment with new data without affecting the main branch."""
    )
    return


@app.cell
def _(dataset, temp_dir):
    """Create branch and commit new file."""
    from pathlib import Path as PathLib

    # Create branch and switch to it
    dataset.create_branch("branch-add")
    dataset.switch_branch("branch-add")

    # Verify branch switch
    assert dataset.get_current_branch() == "branch-add"

    # Add new file to branch
    file3 = PathLib(temp_dir) / "file3.txt"
    file3.write_text("Content of file 3")
    dataset.commit("Add file3 on branch-add", add_files=str(file3))

    # Verify file is in branch
    assert "file3.txt" in dataset.file_dict

    print("✅ Branch creation and commit successful")
    return


@app.cell
def _(mo):
    """## Step 3: Rebase Merge Strategy

    Here's where GitData shines! Instead of creating a merge commit (which would create a "branchy" history), we use the **rebase strategy** to replay our feature branch commits on top of main, creating a clean linear history.
    """
    mo.md(
        """## Step 3: Rebase Merge Strategy

Here's where GitData shines! Instead of creating a merge commit (which would create a "branchy" history), we use the **rebase strategy** to replay our feature branch commits on top of main, creating a clean linear history."""
    )
    return


@app.cell
def _(dataset):
    """Rebase merge branch-add into main."""
    # Switch to main and merge
    dataset.switch_branch("main")
    merge_result_add = dataset.merge("branch-add", "main", strategy="rebase")

    # Verify merge was successful
    assert merge_result_add["success"] is True
    assert merge_result_add["source_branch"] == "branch-add"
    assert merge_result_add["target_branch"] == "main"

    # Verify all files are present in main
    dataset.checkout(dataset.current_version_hash())
    files_after_add = dataset.file_dict
    assert "file1.txt" in files_after_add
    assert "file2.txt" in files_after_add
    assert "file3.txt" in files_after_add

    print("✅ Rebase merge add successful")
    return


@app.cell
def _(mo):
    """## Step 4: Data Cleanup Workflow

    Let's demonstrate another common data workflow: removing outdated or incorrect data. We'll create another branch for this cleanup operation.
    """
    mo.md(
        """## Step 4: Data Cleanup Workflow

Let's demonstrate another common data workflow: removing outdated or incorrect data. We'll create another branch for this cleanup operation."""
    )
    return


@app.cell
def _(dataset):
    """Create branch-remove and remove file1."""
    # Create branch for removal
    dataset.create_branch("branch-remove")
    dataset.switch_branch("branch-remove")

    # Remove file1
    dataset.commit("Remove file1", remove_files="file1.txt")

    # Verify file1 is removed
    assert "file1.txt" not in dataset.file_dict
    assert "file2.txt" in dataset.file_dict  # Should remain
    assert "file3.txt" in dataset.file_dict  # Should remain

    print("✅ Branch remove creation successful")
    return


@app.cell
def _(dataset):
    """Rebase merge branch-remove into main."""
    # Switch to main and merge
    dataset.switch_branch("main")
    merge_result_remove = dataset.merge("branch-remove", "main", strategy="rebase")

    # Verify merge was successful
    assert merge_result_remove["success"] is True
    assert merge_result_remove["source_branch"] == "branch-remove"
    assert merge_result_remove["target_branch"] == "main"

    # Verify final file state
    dataset.checkout(dataset.current_version_hash())
    files_final = dataset.file_dict
    assert "file1.txt" not in files_final  # Should be removed
    assert "file2.txt" in files_final  # Should remain
    assert "file3.txt" in files_final  # Should remain

    print("✅ Rebase merge remove successful")
    return


@app.cell
def _(mo):
    """## Step 5: Linear History Verification

    Let's verify that our commit history is clean and linear - no merge commits cluttering the history!
    """
    mo.md(
        """## Step 5: Linear History Verification

Let's verify that our commit history is clean and linear - no merge commits cluttering the history!"""
    )
    return


@app.cell
def _(dataset):
    """Verify linear history with no merge commits."""
    history_commits = dataset.get_commits()

    # Check that no commit messages contain "Merge"
    merge_commits = [
        commit for commit in history_commits if "Merge" in commit.get("message", "")
    ]
    assert len(merge_commits) == 0, (
        f"Found merge commits: {[c['message'] for c in merge_commits]}"
    )

    # Verify we have the expected commits
    expected_messages = [
        "Remove file1",
        "Add file3 on branch-add",
        "Initial commit with two files",
    ]

    actual_messages = [commit.get("message", "") for commit in history_commits]

    # Check that all expected messages are present
    for expected_msg in expected_messages:
        assert expected_msg in actual_messages, (
            f"Expected message '{expected_msg}' not found in {actual_messages}"
        )

    # Verify linear history
    assert len(history_commits) >= 3, (
        f"Expected at least 3 commits, got {len(history_commits)}"
    )

    print("✅ Linear history verification passed!")
    print(f"✅ Dataset: {dataset.dataset_name}")
    print(f"✅ Commits: {len(history_commits)}")
    print("✅ No merge commits found")

    # Display commit history
    print("\n📋 Commit History:")
    for i, commit in enumerate(history_commits):
        print(f"  {i + 1}. {commit['message']} ({commit['short_hash']})")
    return


@app.cell
def _(mo):
    """## Step 6: Visual Commit History

    Now let's see the beautiful result! The Mermaid diagram below shows our clean, linear commit history with color-coded branches:

    - 🟢 **Green commits** = Main branch
    - 🎨 **Other colors** = Feature branches
    - 🔴 **Red border** = Current HEAD position
    """
    mo.md(
        """## Step 6: Visual Commit History

Now let's see the beautiful result! The Mermaid diagram below shows our clean, linear commit history with color-coded branches:

- 🟢 **Green commits** = Main branch
- 🎨 **Other colors** = Feature branches
- 🔴 **Red border** = Current HEAD position"""
    )
    return


@app.cell
def _(dataset, mo):
    """Visualize commit history as Mermaid diagram."""
    viz_commits = dataset.get_commits()
    if viz_commits:
        display_viz = mo.mermaid(dataset.commit_history_mermaid())
    else:
        display_viz = mo.md(
            "**No commits to visualize yet** - Run the previous cells to create commits first."
        )
    display_viz
    return


@app.cell
def _(mo):
    """## Key Takeaways

    🎉 **Congratulations!** You've successfully demonstrated GitData's linear workflow capabilities:

    ### What We Accomplished:
    - ✅ Created a version-controlled dataset
    - ✅ Developed features on separate branches
    - ✅ Merged using rebase strategy for clean history
    - ✅ Performed data cleanup operations
    - ✅ Maintained linear commit history

    ### Why This Matters:
    - **Clean History**: No messy merge commits cluttering your data lineage
    - **Clear Attribution**: Each commit represents a logical unit of work
    - **Easy Debugging**: Linear history makes it easy to trace data changes
    - **Professional Workflow**: Git-like practices for data management

    ### Next Steps:
    - Try this workflow with your own datasets
    - Experiment with different merge strategies
    - Explore GitData's other features
    """
    mo.md(
        """## Key Takeaways

🎉 **Congratulations!** You've successfully demonstrated GitData's linear workflow capabilities:

### What We Accomplished:
- ✅ Created a version-controlled dataset
- ✅ Developed features on separate branches
- ✅ Merged using rebase strategy for clean history
- ✅ Performed data cleanup operations
- ✅ Maintained linear commit history

### Why This Matters:
- **Clean History**: No messy merge commits cluttering your data lineage
- **Clear Attribution**: Each commit represents a logical unit of work
- **Easy Debugging**: Linear history makes it easy to trace data changes
- **Professional Workflow**: Git-like practices for data management

### Next Steps:
- Try this workflow with your own datasets
- Experiment with different merge strategies
- Explore GitData's other features"""
    )
    return


@app.cell
def _(temp_dir):
    """Cleanup temporary directory."""
    import shutil

    shutil.rmtree(temp_dir)
    print("🧹 Cleanup complete - temporary directory removed")
    return


if __name__ == "__main__":
    app.run()
