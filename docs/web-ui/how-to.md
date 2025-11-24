# Web UI How-To Guide

Practical guides for common tasks in the Kirin web interface. Each section
walks you through a specific workflow with step-by-step instructions.

## Daily Workflow: Adding New Data

**Goal**: Add new files to an existing dataset.

**Steps:**

1. Navigate to your dataset (Home → Catalog → Dataset)
2. Click the **"Commit"** tab
3. Upload your files:
   - Drag and drop files into the upload area, or
   - Click **"Choose Files"** to browse
4. Write a descriptive commit message (e.g., "Add Q4 sales data from CRM")
5. Click **"Create Commit"**

**Tips:**

- Upload multiple files in one commit for related changes
- Use clear commit messages to understand changes later
- Check the summary before committing to verify what will be added

## Updating Existing Files

**Goal**: Replace old files with updated versions.

**Steps:**

1. Go to your dataset's **"Commit"** tab
2. Upload files with the same names as existing files
3. Write a commit message explaining the update (e.g., "Update customer data
   with latest export")
4. Click **"Create Commit"**

**What happens:**

- New files replace old ones with the same names
- Old versions remain in commit history
- You can browse old commits to see previous versions

## Removing Files

**Goal**: Remove files you no longer need.

**Steps:**

1. Go to your dataset's **"Commit"** tab
2. In the **"Remove Files"** section, check boxes next to files to remove
3. Write a commit message explaining why (e.g., "Remove deprecated v1 data
   files")
4. Click **"Create Commit"**

**Important:**

- Files are removed from the current commit but remain in history
- You can always browse old commits to see removed files
- Consider if you really want to remove files or just stop using them

## Combining Add and Remove Operations

**Goal**: Add new files and remove old ones in a single commit.

**Steps:**

1. Go to the **"Commit"** tab
2. Upload new files in the upload section
3. Check boxes to remove files in the remove section
4. Write a commit message describing all changes
5. Click **"Create Commit"**

**Use case example:**

- Adding updated data files while removing outdated ones
- Reorganizing dataset structure
- Cleaning up while adding new content

## Viewing File Contents

**Goal**: Quickly check what's in a file without downloading it.

**Steps:**

1. In the **"Files"** tab, click **"Preview"** next to any file
2. For text files: See syntax-highlighted content
3. For images: View the image directly
4. For code files: See formatted code with highlighting

**Features:**

- Syntax highlighting for code files
- Line numbers for text files
- Inline image display
- Source file links for generated files (like plots)

**Limitations:**

- Very large files (>1000 lines) show first 1000 lines
- Binary files show a message instead of content
- Some file types may not preview perfectly

## Comparing Versions

**Goal**: See what changed between two commits.

**Steps:**

1. Go to the **"History"** tab
2. Note the commit hashes of the two versions you want to compare
3. Click **"Browse Files"** on the older commit
4. Note the files and their sizes
5. Navigate back and click **"Browse Files"** on the newer commit
6. Compare the file lists, sizes, and contents

**What to look for:**

- Files added (appear in newer but not older)
- Files removed (appear in older but not newer)
- Files changed (same name, different size or hash)
- Total size differences

**Tip**: Good commit messages make it easier to understand why changes were
made.

## Setting Up a Cloud Catalog

**Goal**: Connect to an S3 bucket for team collaboration.

**Prerequisites:**

- AWS account with S3 access
- AWS CLI installed and configured
- Appropriate IAM permissions

**Steps:**

1. Ensure you're authenticated with AWS:

   ```bash
   aws sso login --profile your-profile
   # or
   aws configure
   ```

2. In the web UI, click **"+ Add Catalog"**

3. Fill in the form:
   - **Catalog Name**: Something descriptive (e.g., "Production S3 Data")
   - **Root Directory**: `s3://your-bucket-name/data`
   - **AWS Profile**: Select your profile from the dropdown
   - **Authentication Command**: `aws sso login --profile your-profile`
     (optional, enables auto-authentication)

4. Click **"Create Catalog"**

**What happens:**

- The catalog connects to your S3 bucket
- You can now create datasets that store data in S3
- Auto-authentication runs the command when needed

**For GCS:**

- Use path: `gs://your-bucket-name/data`
- Auth command: `gcloud auth login` or `gcloud auth application-default login`

**For Azure:**

- Use path: `az://your-container-name/data`
- Auth command: `az login`

## Sharing a Dataset with Your Team

**Goal**: Let teammates access a dataset you created.

**Steps:**

1. **Ensure the catalog is accessible:**
   - For cloud storage: Ensure teammates have access to the bucket/container
   - For local storage: Use a shared directory or network drive

2. **Share catalog configuration:**
   - Catalog name
   - Root directory path
   - Authentication requirements (if any)

3. **Teammates set up the catalog:**
   - They create the same catalog in their web UI
   - They configure authentication if needed
   - They can now see all datasets in that catalog

4. **Share dataset information:**
   - Dataset name
   - Catalog it's in
   - Any relevant commit hashes or descriptions

**Tips:**

- Use the **"Python Access Code"** section to share exact code for
  programmatic access
- Document catalog setup in your team's wiki or docs
- Consider using consistent catalog names across the team

## Organizing Multiple Catalogs

**Goal**: Structure your catalogs for easy management.

**Strategies:**

**By environment:**

- `production-data` → Production S3 bucket
- `staging-data` → Staging S3 bucket
- `local-dev` → Local development directory

**By team:**

- `analytics-team` → Analytics team's shared storage
- `ml-team` → Machine learning team's storage
- `research-team` → Research team's storage

**By project:**

- `customer-segmentation` → Project-specific storage
- `price-optimization` → Another project's storage

**Best practices:**

- Use consistent naming conventions
- Document catalog purposes
- Keep related datasets in the same catalog
- Don't create too many catalogs—group related work together

## Finding Files in Large Datasets

**Goal**: Quickly locate specific files when you have many files.

**Steps:**

1. Go to your dataset's **"Files"** tab
2. Use browser search (Ctrl+F / Cmd+F) to search file names
3. Look for file type icons to filter visually
4. Use the dataset's search functionality if available

**Tips:**

- Use descriptive filenames to make files easier to find
- Group related files with consistent naming patterns
- Consider splitting very large datasets into smaller, focused ones

## Exporting Python Code

**Goal**: Get Python code to access your dataset programmatically.

**Steps:**

1. Navigate to your dataset
2. Look for the **"Python Access Code"** section (collapsible, usually at
   the top)
3. Click to expand it
4. Click **"Copy"** to copy the code
5. Paste into your Python script or notebook

**What you get:**

- Complete code to create a Dataset object
- Proper authentication configuration
- Ready to use in your scripts

**Example output:**

```python
from kirin import Dataset

dataset = Dataset(
    root_dir="s3://my-bucket/data",
    name="my-dataset",
    aws_profile="production"
)

# Checkout to latest commit
dataset.checkout()
```

## Troubleshooting Common Issues

### Can't Connect to Cloud Storage

**Symptoms**: Catalog shows "Error" status or can't list datasets.

**Solutions:**

1. **Check authentication:**
   - Run the auth command manually: `aws sso login --profile your-profile`
   - Verify credentials are valid
   - Check expiration for temporary credentials

2. **Verify permissions:**
   - Ensure your credentials have read/write access to the bucket
   - Check IAM policies or bucket permissions

3. **Check network:**
   - Verify you can access the cloud storage from your network
   - Check for firewall or VPN issues

4. **Review error messages:**
   - The web UI shows specific error messages
   - Use these to diagnose the issue

### Files Won't Upload

**Symptoms**: Upload fails or hangs indefinitely.

**Solutions:**

1. **Check file size:**
   - Very large files (>100MB) may take time
   - Consider splitting large files

2. **Verify permissions:**
   - Ensure you have write access to the catalog's storage
   - Check cloud storage permissions

3. **Check network:**
   - For cloud storage, verify connection is stable
   - Try smaller files first to test

4. **Review browser console:**
   - Check for JavaScript errors
   - Look for network request failures

### Can't See Datasets

**Symptoms**: Catalog shows "Unknown" dataset count or empty list.

**Solutions:**

1. **Wait for connection:**
   - Cloud catalogs may take a few seconds to connect
   - Refresh the page if it seems stuck

2. **Verify path:**
   - Ensure the catalog path is correct
   - Check that the storage location exists

3. **Check authentication:**
   - Verify you're authenticated with the cloud provider
   - Run auth commands manually if needed

4. **Verify permissions:**
   - Ensure you have read access to list datasets
   - Check IAM policies or storage permissions

## Best Practices

### Commit Messages

**Write clear, descriptive messages:**

- ✅ **Good**: "Add Q4 2024 sales data from CRM export"
- ✅ **Good**: "Update customer segmentation model with new features"
- ❌ **Bad**: "update"
- ❌ **Bad**: "files"

**Why it matters**: Good commit messages help you and your team understand
what changed and why, especially when looking at history weeks or months
later.

### Dataset Organization

**Keep datasets focused:**

- ✅ **Good**: One dataset per use case or analysis
- ❌ **Bad**: One giant dataset with everything

**Why it matters**: Focused datasets are easier to understand, navigate, and
share with others.

### File Naming

**Use descriptive, consistent names:**

- ✅ **Good**: `customer-transactions-2024-q4.csv`, `model-training-features-v2.json`
- ❌ **Bad**: `data.csv`, `file1.json`, `stuff.xlsx`

**Why it matters**: Clear names make files easier to find and understand,
especially when working with multiple files.

## Next Steps

- **[Web UI Overview](overview.md)** - Understand the concepts and
  architecture
- **[Getting Started Tutorial](getting-started.md)** - Step-by-step first
  setup
- **[Catalog Management](catalog-management.md)** - Advanced catalog
  configuration
