# Getting Started with the Web UI

This tutorial walks you through creating your first catalog and dataset using
the Kirin web interface. By the end, you'll have a working setup and
understand the basic workflow.

## Prerequisites

- Kirin installed (see [Installation Guide](../getting-started/installation.md))
- A storage location ready (local directory or cloud bucket)
- For cloud storage: Appropriate authentication configured

## Step 1: Start the Web UI

Open your terminal and run:

```bash
# Development environment
pixi run kirin ui

# Production environment
uv run kirin ui

# One-time use
uvx kirin ui
```

The server starts and prints a URL like:

```text
Starting Kirin Web UI...
Server running at http://127.0.0.1:61581
```

**Copy this URL** and open it in your browser.

## Step 2: Create Your First Catalog

A catalog connects Kirin to a storage location. You need at least one catalog
before you can work with datasets.

**On the home page:**

1. Click the blue **"+ Add Catalog"** button
2. Fill in the form:
   - **Catalog Name**: Enter a friendly name (e.g., "My Data Catalog")
   - **Root Directory**: Enter your storage path:
     - Local: `/path/to/your/data`
     - S3: `s3://your-bucket-name/path`
     - GCS: `gs://your-bucket-name/path`
     - Azure: `az://your-container-name/path`
3. For cloud storage (optional):
   - **AWS Profile**: Select from dropdown if using S3
   - **Authentication Command**: Enter CLI command (e.g., `aws sso login
     --profile production`)
4. Click **"Create Catalog"**

**What happens:**

- The catalog appears on your home page
- You can now view datasets, edit settings, or delete it
- The catalog is ready to use immediately

## Step 3: Create Your First Dataset

Datasets are versioned collections of files within a catalog.

**Navigate to your catalog:**

1. Click **"View Datasets"** on your catalog card
2. Click the **"Create Dataset"** tab
3. Fill in the form:
   - **Dataset Name**: Use lowercase letters, numbers, and hyphens only
     (e.g., `my-first-dataset`)
   - **Description**: Optional description of what this dataset contains
4. Click **"Create Dataset"**

**What happens:**

- You're taken to the dataset view
- The dataset is empty and ready for files
- You can see three tabs: Files, History, and Commit

## Step 4: Add Files to Your Dataset

Now let's add some files to your dataset.

**In the dataset view:**

1. Click the **"Commit"** tab
2. Upload files:
   - **Drag and drop** files into the upload area, or
   - Click **"Choose Files"** to browse your computer
3. Enter a commit message:
   - Describe what you're adding (e.g., "Add initial data files")
   - Be descriptive—this helps you understand changes later
4. Click **"Create Commit"**

**What happens:**

- Files are uploaded and stored
- A new commit appears in the History tab
- Files appear in the Files tab
- You can preview or download files

## Step 5: Explore Your Dataset

Take a moment to explore what you've created.

**Files Tab:**

- See all files in your dataset
- Click **"Preview"** to view file contents
- Click **"Download"** to save files locally

**History Tab:**

- See your commit history (should show one commit)
- Click **"Browse Files"** to see files at that point in time
- Notice the commit hash, message, and timestamp

**Commit Tab:**

- Upload more files or remove existing ones
- See Python code snippets for accessing your dataset programmatically

## Step 6: Make Another Commit

Let's practice the workflow by making a second commit.

**Add more files:**

1. Go to the **"Commit"** tab
2. Upload additional files (or the same files with updates)
3. Write a commit message (e.g., "Add updated sales data")
4. Click **"Create Commit"**

**What happens:**

- A second commit appears in History
- The Files tab shows the current state (latest commit)
- You can browse either commit to see differences

## Step 7: Browse Commit History

See how your dataset has changed over time.

**In the History tab:**

1. You should see two commits (newest first)
2. Click **"Browse Files"** on the older commit
3. Compare the file list with the current Files tab
4. Notice how commit messages help you understand what changed

**Key concepts:**

- **HEAD**: The current commit (marked with a blue badge)
- **Commit hash**: Unique identifier for each commit
- **Linear history**: Commits form a chain, one after another

## Next Steps

You've completed the basic workflow! Here's what to explore next:

**Common workflows:**

- **[Web UI How-To Guide](how-to.md)** - Learn common tasks and workflows
- **[Catalog Management](catalog-management.md)** - Configure cloud storage
  and authentication
- **[Basic Usage Guide](../guides/basic-usage.md)** - Deep dive into dataset
  operations

**Advanced topics:**

- Set up cloud storage catalogs (S3, GCS, Azure)
- Share datasets with your team
- Use Python API alongside the web UI
- Organize multiple catalogs and datasets

## Troubleshooting

**Server won't start:**

- Check if the port is already in use
- Kirin will automatically use a different port—check the terminal output

**Can't create catalog:**

- Verify your storage path is correct
- For cloud storage, ensure you're authenticated
- Check file permissions for local paths

**Files won't upload:**

- Verify you have write access to the catalog's storage location
- Check file size—very large files may take time
- For cloud storage, verify your authentication is working

**Can't see datasets:**

- Wait a few seconds for cloud catalogs to connect
- Verify your catalog path is correct
- Check that you have read access to the storage location

For more help, see the [Troubleshooting section](../guides/basic-usage.md#troubleshooting).
