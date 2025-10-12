<!-- 201d6c06-31b0-47b6-8017-59df03ef85e8 5d47212c-729c-4681-b0d6-e36fe2c8313a -->
# Build Kirin TUI with Rich

## Overview

Create a terminal user interface using Rich library that mimics the web UI functionality, starting with the most critical feature: committing files to a dataset.

## Architecture

The TUI will be organized as follows:

- Main TUI module: `kirin/tui.py` - Core TUI logic with Rich components
- CLI integration: Update `kirin/cli.py` to add `kirin tui` command
- Reuse existing infrastructure: `CatalogManager` from `kirin/web/config.py`

## Implementation Details

### 1. Add Rich Dependency

Update `pyproject.toml` to include Rich library:

- Add `rich` to the dependencies list (around line 80)

### 2. Create TUI Module

Create new file `kirin/tui.py` with the following components:

**Interactive Selection Functions:**

- `select_catalog()` - Display numbered table of catalogs, prompt for selection
  - Use `CatalogManager.list_catalogs()` to get available catalogs
  - Use `rich.table.Table` to display catalog names and root_dir
  - Use `rich.prompt.Prompt.ask()` with choices validation
  - Return selected `CatalogConfig` object

- `select_dataset()` - Display numbered table of datasets in a catalog
  - Call `catalog.to_catalog().datasets()` to list datasets
  - Display dataset names in a Rich table
  - Prompt for selection with validation
  - Return selected dataset name

**File Handling:**

- `get_files_to_commit()` - Handle file path input
  - Check if files provided as CLI args (option 3c)
  - If no args, use `Prompt.ask()` to get comma-separated file paths
  - Validate that files exist on local filesystem
  - Return list of file paths

**Commit Operation:**

- `commit_files()` - Execute the commit operation
  - Take catalog, dataset name, file paths, and commit message
  - Create Dataset instance: `catalog.to_catalog().get_dataset(dataset_name)`
  - Call `dataset.commit(message=msg, add_files=files)`
  - Use `rich.console.Console` with status spinner during operation
  - Display success message with commit hash using `rich.panel.Panel`

**Main TUI Entry Point:**

- `run_tui()` - Main orchestration function
  - Display welcome banner using `rich.panel.Panel`
  - Call `select_catalog()`
  - Call `select_dataset()`
  - Call `get_files_to_commit()`
  - Prompt for commit message
  - Call `commit_files()`
  - Handle errors with styled error messages

### 3. Update CLI Module

Modify `kirin/cli.py`:

- Import the new TUI module
- Add `tui()` function that calls `run_tui()`
- Update `main()` to handle `"tui"` command alongside `"ui"`
- Update help text to document both commands

Pattern:

```python
def tui() -> None:
    \"\"\"Launch the Kirin TUI.\"\"\"
    from kirin.tui import run_tui
    run_tui()
```

### 4. Error Handling

Implement graceful error handling:

- No catalogs configured: Display helpful message directing user to add catalogs
- No datasets in catalog: Offer to create a new dataset (future enhancement)
- File not found: Display error and re-prompt for files
- Commit failures: Display error details with suggestions
- Keyboard interrupt (Ctrl+C): Clean exit with goodbye message

### 5. Rich Styling

Use consistent Rich styling:

- Titles: Bold cyan panels
- Success messages: Green panels with ✓ emoji
- Error messages: Red panels with ✗ emoji
- Tables: Default Rich table styling with headers
- Progress: Use `Console.status()` for operations
- Prompts: Use default Rich prompt styling

## Key Files Modified

- `pyproject.toml` - Add rich dependency
- `kirin/tui.py` - New file with TUI implementation (≈200-300 lines)
- `kirin/cli.py` - Update to add `tui` command (≈10 lines added)

## Testing Strategy

Following TDD approach:

- Create `tests/test_tui.py` before implementation
- Mock Rich components (Console, Prompt, Table)
- Test catalog selection logic
- Test dataset selection logic
- Test file path handling (both CLI args and interactive)
- Test commit operation
- Test error cases (no catalogs, no datasets, invalid files)

## Future Enhancements (Not in This Phase)

- File removal functionality
- View commit history
- Browse files in dataset
- Checkout specific commits
- Create new datasets
- Manage catalogs (add/edit/delete)

### To-dos

- [ ] Add rich library to pyproject.toml dependencies
- [ ] Write tests for TUI functionality (TDD approach) in tests/test_tui.py
- [ ] Create kirin/tui.py with catalog selection, dataset selection, file handling, and commit functionality
- [ ] Update kirin/cli.py to add 'kirin tui' command
- [ ] Manually test the TUI with different scenarios (existing catalog, multiple datasets, file commits)
