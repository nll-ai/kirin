# Local State Management Design

## Overview

Kirin uses a distributed local state management system that follows git-like
semantics while being optimized for Python-centric workflows. This document
outlines the key design decisions for how local state is stored and managed.

## Core Design Philosophy

### Python-Centric Workflow

Unlike git, which operates from the command line with `cd` and `git clone`,
Kirin is designed to be used from within Python environments. Users work with
datasets programmatically without needing to navigate to specific directories
or run shell commands.

### Centralized Local Workspace

Kirin uses `~/.kirin/` as the centralized local workspace where:

- Local state (branches, HEAD, configuration) is maintained
- Users can interact with the local copy of commit trees

This approach eliminates the need for users to manage multiple local
directories and provides a unified workspace for all Kirin operations.

## Local State Directory Structure

### Hierarchical Organization

Local state is organized using a hierarchical directory structure:

```text
~/.kirin/
├── {remote_url_hash}/
│   └── {dataset_name}/
│       ├── HEAD
│       ├── refs/heads/
│       │   ├── main
│       │   ├── feature
│       │   └── ...
│       └── config.json
└── {another_remote_url_hash}/
    └── {dataset_name}/
```

### Remote URL Hashing

Each remote location is identified by a 16-character hash derived from the
remote URL:

```python
remote_url_hash = hashlib.sha256(remote_url.encode()).hexdigest()[:16]
```

This ensures that:

- Datasets with the same name from different locations don't collide
- The directory structure remains stable and predictable
- Remote URLs are anonymized in the filesystem

### Dataset Name Isolation

Within each remote URL hash directory, datasets are organized by name. This
allows:

- Multiple datasets from the same remote location
- Clear separation between different datasets
- Easy identification of dataset-specific state

## State Management Components

### HEAD File

The `HEAD` file contains a reference to the current branch, following git
conventions:

```text
ref: refs/heads/main
```

### Branch References

Branch references are stored as individual files in `refs/heads/`, with each
file containing the commit hash that the branch points to.

### Configuration

The `config.json` file stores dataset-specific configuration including:

- Dataset name
- Creation timestamp
- Last sync timestamp
- Remote URL (initially null, can be set via `set_remote_url()`)

## Design Benefits

### Isolation

The hierarchical structure ensures complete isolation between:

- Different remote locations
- Different datasets
- Different test runs

### Scalability

The design supports:

- Unlimited remote locations
- Unlimited datasets per location
- Unlimited branches per dataset

### Testability

The structure enables:

- Clean test isolation
- Reproducible test environments
- Easy cleanup of test state

### User Experience

Users benefit from:

- No manual directory management
- Automatic state organization
- Clear separation of concerns
- Familiar git-like semantics

## Implementation Details

### LocalStateManager

The `LocalStateManager` class handles all local state operations:

```python
def __init__(
    self,
    dataset_name: str,
    local_state_dir: Optional[str] = None,
    remote_url: Optional[str] = None,
):
    # Create unique directory based on remote URL hash
    if local_state_dir is None:
        home_dir = Path.home()
        if remote_url:
            remote_url_hash = hashlib.sha256(remote_url.encode()).hexdigest()[:16]
            self.local_state_dir = (
                home_dir / ".kirin" / remote_url_hash / dataset_name
            )
        else:
            # Fallback for backward compatibility
            self.local_state_dir = home_dir / ".kirin" / dataset_name
    else:
        self.local_state_dir = Path(local_state_dir)
```

### Integration with Dataset

The `Dataset` class automatically passes its `root_dir` as the remote URL to
ensure proper state isolation:

```python
self.branch_manager = BranchManager(
    self.dataset_dir,
    self.fs,
    self.dataset_name,
    remote_url=self.root_dir
)
```

## Backward Compatibility

The design maintains backward compatibility by:

- Falling back to the old directory structure when no remote URL is provided
- Preserving existing functionality for legacy use cases
- Gradual migration path for existing installations

## Future Considerations

### Future File Organization

The design anticipates future enhancements for organizing local files within
the same directory structure, maintaining the centralized workspace approach.

### Remote Synchronization

The hierarchical structure supports future remote synchronization features
while maintaining local state isolation.

### Multi-User Support

The design can be extended to support multi-user scenarios by adding
user-specific directory levels if needed.
