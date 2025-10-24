# Web UI Overview

Kirin includes a comprehensive web interface for managing datasets and
catalogs through your browser.

## Getting Started

### Starting the Web UI

```bash
# Development (with pixi)
pixi run kirin ui

# Production (with uv)
uv run kirin ui

# One-time use (with uvx)
uvx kirin ui
```

The web UI will start on a random port (usually 8000+) and display the URL
in your terminal.

### First Time Setup

1. **Start the web UI**: Run `pixi run kirin ui`
2. **Open your browser**: Navigate to the displayed URL
3. **Create your first catalog**: Click "Add Catalog" to get started

## Key Features

### Catalog Management

- **Multiple Catalogs**: Manage different data collections
- **Cloud Integration**: Connect to S3, GCS, Azure, and more
- **Authentication**: Secure credential management
- **Catalog Overview**: See all datasets at a glance

### Dataset Operations

- **Browse Datasets**: View all datasets in a catalog
- **File Management**: Upload, remove, and organize files
- **Commit History**: Visual commit timeline
- **File Preview**: View file contents directly in browser

### User Interface

- **Modern Design**: Clean, responsive interface
- **Fast Interactions**: HTMX-powered dynamic updates
- **Mobile Friendly**: Works on all device sizes
- **Accessible**: Keyboard navigation and screen reader support

## Navigation

### Main Pages

1. **Home** (`/`): Catalog management and overview
2. **Catalog View** (`/{catalog_id}`): Dataset listing for a catalog
3. **Dataset View** (`/{catalog_id}/{dataset}`): Individual dataset with files
   and history
4. **File Preview** (`/{catalog_id}/{dataset}/files/{filename}`): File content
   viewer

### Navigation Flow

```text
Home → Catalog → Dataset → File Preview
  ↑       ↑        ↑         ↑
Catalogs  Datasets  Files    Content
```

## Working with Catalogs

### Creating a Catalog

1. **Click "Add Catalog"** on the home page
2. **Enter catalog details**:
   - **ID**: Unique identifier (e.g., `my-data`)
   - **Name**: Display name (e.g., `My Data Catalog`)
   - **Root Directory**: Storage location
3. **Configure authentication** (for cloud storage)
4. **Save and test** the connection

## Working with Datasets

### Dataset View

The dataset view shows:

- **Files Tab**: Current files in the dataset
- **History Tab**: Commit history timeline
- **Actions**: Upload files, remove files, commit changes

### File Operations

#### Uploading Files

1. **Click "Upload Files"** in the dataset view
2. **Select files** from your computer
3. **Add commit message** describing the changes
4. **Click "Commit Changes"** to save

#### Removing Files

1. **Click "Remove Files"** in the dataset view
2. **Select files** to remove (checkboxes)
3. **Add commit message** explaining the removal
4. **Click "Commit Changes"** to save

#### Combined Operations

You can upload and remove files in the same commit:

1. **Upload new files** and **select files to remove**
2. **Add commit message** describing all changes
3. **Click "Commit Changes"** to save everything together

### Commit History

The History tab shows:

- **Commit Timeline**: Chronological list of commits
- **Commit Details**: Files added/removed in each commit
- **File Information**: Size, hash, and metadata
- **Navigation**: Click to view specific commits

## File Preview

### Supported File Types

The web UI can preview:

- **Text files**: `.txt`, `.csv`, `.json`, `.py`, `.md`
- **Code files**: `.py`, `.js`, `.html`, `.css`
- **Data files**: `.csv`, `.json`, `.yaml`
- **Configuration**: `.ini`, `.toml`, `.yaml`

### Preview Features

- **Syntax highlighting** for code files
- **Line numbers** for easy reference
- **Download button** for saving files
- **Responsive layout** for different screen sizes

## Cloud Storage Integration

### Setting Up Cloud Catalogs

1. **Create catalog** with cloud URL (e.g., `s3://bucket/path`)
2. **Configure authentication**:
   - **AWS**: Profile name or access keys
   - **GCS**: Service account key file
   - **Azure**: Connection string or account details
3. **Test connection** to verify setup

### Cloud Authentication

The web UI handles cloud authentication automatically:

- **Credential Storage**: Secure storage in catalog configuration
- **Profile Detection**: Automatic AWS profile detection
- **Token Management**: GCS service account token handling
- **Connection Testing**: Verify authentication before saving

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# If port is busy, Kirin will use a different port
# Check the terminal output for the actual URL
```

#### SSL Certificate Issues

```bash
# Set up SSL certificates for cloud storage
pixi run setup-ssl
```

#### Cloud Authentication Failures

**Automatic Authentication (NEW):**

Kirin now automatically handles authentication for catalogs with stored auth commands:

1. **Auto-retry**: When authentication fails, Kirin executes the stored auth command
2. **Success feedback**: Green banner shows successful authentication
3. **Failure guidance**: Error message with manual instructions if auto-auth fails

**Manual Authentication:**

If auto-authentication isn't configured or fails:

1. **Check credentials**: Verify AWS profiles, GCS tokens, etc.
2. **Run auth command**: Execute the CLI command manually (shown in error message)
3. **Refresh page**: Try accessing the catalog again
4. **Review logs**: Check terminal output for error messages

**Timeout Protection:**

- **10-second timeout** for catalog operations prevents UI from hanging
- **Clear error messages** indicate when timeouts occur
- **Retry button** allows you to try again after authentication

### Performance Tips

#### Large Datasets

- **Use file filtering** to focus on specific files
- **Limit commit history** display for better performance
- **Consider chunking** very large files

#### Cloud Storage

- **Use appropriate regions** for better performance
- **Enable compression** for text files
- **Batch operations** when possible

## Next Steps

- **[Catalog Management](catalog-management.md)** - Advanced catalog configuration
- **[Basic Usage Guide](../guides/basic-usage.md)** - Core dataset operations
- **[Cloud Storage Guide](../guides/cloud-storage.md)** - Cloud backend setup
