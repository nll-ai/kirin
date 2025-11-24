# Web UI Overview

The Kirin web interface provides a visual, browser-based way to manage your
data versioning workflows. It's designed for users who prefer graphical
interfaces over command-line tools, and for teams who need shared visibility
into datasets and their history.

## What Is the Web UI?

The web UI is a full-featured interface to Kirin's data versioning system,
running as a local web server that you access through your browser. It
provides the same core functionality as the Kirin CLI, but through an
interactive, visual interface.

**Key characteristics:**

- **Self-hosted**: Runs locally on your machine—no external services or
  accounts required
- **Browser-based**: Works in any modern web browser
- **HTMX-powered**: Fast, dynamic updates without full page reloads
- **Cloud-integrated**: Works seamlessly with S3, GCS, Azure, and local
  storage

## Why Does It Exist?

The web UI addresses several needs that the CLI doesn't:

**Visual Exploration:**

- Browse datasets and files without remembering commands
- See commit history as a timeline, not just log output
- Preview file contents directly in the browser

**Team Collaboration:**

- Shared understanding of dataset structure and history
- Easier onboarding for team members unfamiliar with CLI tools
- Visual representation of changes over time

**Workflow Integration:**

- Quick file uploads via drag-and-drop
- Immediate visual feedback on operations
- No need to switch between terminal and file browser

## How It Fits into Kirin

The web UI is one of three ways to interact with Kirin:

### 1. Web UI (this interface)

- Best for: Visual exploration, quick operations, team collaboration
- Use when: You want to browse datasets, upload files interactively, or
  share views with teammates

### 2. Python API

- Best for: Programmatic access, automation, integration with data science
  workflows
- Use when: You're writing scripts, notebooks, or applications that need to
  interact with Kirin

### 3. CLI

- Best for: Command-line workflows, automation, CI/CD pipelines
- Use when: You're comfortable with terminals and need scriptable operations

**All three interfaces work with the same underlying data.** A dataset created
via the web UI can be accessed via Python API or CLI, and vice versa. They're
different views of the same system.

## Core Concepts

### Catalogs

A catalog is a connection to a storage location. Think of it as a "data
source" that Kirin can access.

**Storage backends:**

- **Local filesystem**: Direct access to directories on your machine
- **AWS S3**: Cloud storage buckets
- **Google Cloud Storage**: GCS buckets
- **Azure Blob Storage**: Azure containers

**Key properties:**

- Catalogs are independent—each manages its own set of datasets
- Multiple catalogs can point to different storage locations
- Catalogs handle authentication and connection details

**Mental model**: A catalog is like a "workspace" or "project folder" that
contains multiple datasets.

### Datasets

A dataset is a versioned collection of files within a catalog. It's the
primary unit of organization in Kirin.

**Key properties:**

- Each dataset has a name and optional description
- Files are stored with content-addressed hashing (deduplication)
- History is linear—each commit has one parent
- Datasets are independent—changes to one don't affect others

**Mental model**: A dataset is like a git repository, but for data files
instead of source code.

### Commits

A commit is a snapshot of files at a point in time. It records what files
existed, their content hashes, and a message describing the change.

**Key properties:**

- Each commit has a unique hash (content-addressed)
- Commits form a linear history (no branching)
- Commit messages describe what changed and why
- You can browse files at any point in history

**Mental model**: A commit is like a "save point" or "checkpoint" in your
data versioning workflow.

### Files

Files in Kirin are stored by content hash, not by name. This enables:

- **Deduplication**: Identical content stored once, even if filenames differ
- **Integrity**: Content verified by hash, ensuring data hasn't changed
- **Efficiency**: Same file content referenced multiple times without
  duplication

**Key properties:**

- Files are immutable once committed
- Multiple filenames can point to the same content
- Files can have metadata (e.g., source file links for generated plots)
- Original filenames are preserved for display and access

**Mental model**: Files are like "blobs" in git—content-addressed and
immutable.

## Architecture

### Client-Server Model

The web UI runs as a local web server:

```text
Browser ←→ Web UI Server ←→ Storage Backend
         (FastAPI)        (fsspec)
```

**Server components:**

- **FastAPI application**: Handles HTTP requests and routing
- **Template engine**: Renders HTML pages (Jinja2)
- **HTMX integration**: Enables dynamic updates without JavaScript
- **fsspec integration**: Connects to various storage backends

**Communication:**

- Browser sends HTTP requests (GET for pages, POST for actions)
- Server processes requests and interacts with storage
- Responses are HTML (with HTMX for dynamic updates)
- No API endpoints—everything is page-based

### Storage Abstraction

The web UI uses the same storage abstraction as the Python API and CLI:

```text
Web UI → Catalog → Dataset → Storage Backend
```

**Layers:**

1. **Web UI**: User interface layer
2. **Catalog**: Connection and configuration management
3. **Dataset**: Versioning and file management
4. **Storage Backend**: Actual file storage (local, S3, GCS, Azure)

This abstraction means the web UI works identically with any storage backend,
without special handling for different providers.

### Authentication Flow

For cloud storage, authentication happens at the catalog level:

**Automatic authentication:**

- Catalogs can store authentication commands (e.g., `aws sso login --profile
  production`)
- When operations fail due to authentication, the web UI automatically runs
  the stored command
- Success/failure is communicated to the user via UI messages

**Manual authentication:**

- Users can authenticate via CLI before accessing catalogs
- Authentication state persists in the user's environment
- The web UI uses existing authentication from the environment

**Security model:**

- Credentials are never stored in the web UI
- Authentication commands are stored, but not credentials themselves
- The web UI executes authentication commands in the user's environment

## When to Use the Web UI

**Use the web UI when:**

- You want to explore datasets visually
- You need to quickly upload or preview files
- You're onboarding new team members
- You want to share dataset views with non-technical stakeholders
- You prefer graphical interfaces over command-line tools

**Use the Python API when:**

- You're writing scripts or notebooks
- You need programmatic access to datasets
- You're integrating Kirin into data science workflows
- You want to automate dataset operations

**Use the CLI when:**

- You're comfortable with command-line tools
- You need to script operations in shell scripts
- You're working in CI/CD pipelines
- You want lightweight, fast operations

**You can mix and match:** Use the web UI for exploration and the Python API
for automation in the same workflow.

## Design Principles

The web UI follows several design principles:

**Simplicity First:**

- Linear commit history (no branching complexity)
- Clear, focused interface without overwhelming options
- Progressive disclosure—advanced features don't clutter the main interface

**Fast and Responsive:**

- HTMX enables dynamic updates without full page reloads
- Operations are asynchronous where possible
- Timeout protection prevents UI from hanging

**Cloud-Agnostic:**

- Same interface works with any storage backend
- Storage details are abstracted away
- Users don't need to think about storage provider differences

**User-Friendly:**

- Clear error messages with actionable guidance
- Visual feedback for all operations
- Helpful defaults and sensible constraints

## Limitations and Considerations

**Local server:**

- The web UI runs on your machine—it's not a hosted service
- You need to keep the server running while using it
- Port conflicts may require using a different port

**Browser-based:**

- Requires a modern web browser
- Some operations (like large file uploads) depend on browser capabilities
- Offline use is limited—you need the server running

**Not for everything:**

- Very large datasets (>10GB) may be slow to browse
- Bulk operations are often faster via CLI or Python API
- Advanced operations may require CLI or Python API

**Security:**

- The web UI runs locally and doesn't expose data to the internet
- Authentication is handled by your environment (AWS, GCS, Azure CLIs)
- No credentials are stored in the web UI itself

## Integration with Other Tools

**Python API:**

- The web UI shows Python code snippets for accessing datasets
- You can copy-paste code from the UI into your scripts
- Both use the same underlying Kirin library

**CLI:**

- CLI operations appear in the web UI's commit history
- You can use CLI for bulk operations and web UI for exploration
- Both work with the same datasets and catalogs

**Data Science Tools:**

- Datasets created in the web UI can be loaded into pandas, polars, etc.
- File previews help you understand data before loading
- Python code snippets integrate with your existing workflows

**Version Control:**

- Kirin's linear history complements git's branching model
- Use git for code, Kirin for data
- Commit messages in Kirin follow similar best practices to git

## Next Steps

- **[Getting Started Tutorial](getting-started.md)** - Step-by-step guide to
  your first catalog and dataset
- **[Web UI How-To Guide](how-to.md)** - Common workflows and tasks
- **[Catalog Management](catalog-management.md)** - Advanced catalog
  configuration
- **[Basic Usage Guide](../guides/basic-usage.md)** - Core dataset
  operations
