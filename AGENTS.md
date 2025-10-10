# Kirin - Agent Guidelines

Guidelines for AI agents working on the Kirin project.

## Core Philosophy: Simplified Data Versioning

**Kirin is simplified "git" for data** - follows git conventions but with linear-only history:

- **Linear Commits**: Simple, linear commit history without branching complexity
- **Content-Addressed Storage**: Files stored by content hash for integrity and deduplication
- **Ergonomic Python API**: Focus on ease of use and developer experience
- **Backend-Agnostic**: Works with any storage backend via fsspec
- **No Branching**: Linear-only commit history to avoid complexity

### Key Design Principles

- **Simplicity First**: Linear commit history without branching/merging complexity
- **Content Integrity**: Files stored by content hash ensure data integrity
- **Python-First**: Ergonomic Python API optimized for data science workflows
- **Backend Flexibility**: Support for local filesystem, S3, GCS, Azure, etc.
- **Zero-Copy Operations**: Efficient handling of large files through streaming

### Content-Addressed Storage Design

**CRITICAL**: Files are stored **without file extensions** in the content-addressed storage system:

- **Storage Path**: `root_dir/data/{hash[:2]}/{hash[2:]}` (e.g., `data/ab/cdef1234...`)
- **No Extensions**: Original `.csv`, `.txt`, `.json` extensions are not preserved in storage
- **Metadata Storage**: File extensions are stored as metadata in the `File` entity's `name` attribute
- **Extension Restoration**: When files are downloaded or accessed, they get their original names back
- **Content Integrity**: Files are identified purely by content hash, ensuring data integrity
- **Deduplication**: Identical content (regardless of original filename) is stored only once

## Simplified Architecture (2024 Overhaul)

### Core Entity Classes

**File Entity** (`kirin/file.py`):
- Represents versioned files with content-addressed storage
- Immutable once created, identified by content hash
- Methods: `read_bytes()`, `read_text()`, `open()`, `download_to()`
- Properties: `hash`, `name`, `size`, `content_type`, `short_hash`

**Commit Entity** (`kirin/commit.py`):
- Represents immutable snapshots of files at a point in time
- Linear history with single parent (no branching)
- Methods: `get_file()`, `list_files()`, `has_file()`, `get_total_size()`
- Properties: `hash`, `message`, `timestamp`, `parent_hash`, `files`

**Dataset Entity** (`kirin/dataset.py`):
- Main interface for working with versioned file collections
- Linear commit history management
- Methods: `commit()`, `checkout()`, `get_file()`, `read_file()`, `history()`
- Properties: `name`, `description`, `current_commit`, `files`

### Storage Architecture

**ContentStore** (`kirin/storage.py`):
- Content-addressed storage using fsspec backends
- Files stored at `root_dir/data/{hash[:2]}/{hash[2:]}` **without file extensions**
- File extensions are metadata stored in the `File` entity's `name` attribute
- Storage is extension-agnostic (content is stored as pure hash)
- Extensions are restored when files are downloaded/accessed
- Methods: `store_file()`, `store_content()`, `retrieve()`, `exists()`
- Supports local filesystem, S3, GCS, Azure, etc.

**CommitStore** (`kirin/commit_store.py`):
- Linear commit history storage in JSON format
- Single file per dataset: `root_dir/datasets/{name}/commits.json`
- Methods: `save_commit()`, `get_commit()`, `get_latest_commit()`, `get_commit_history()`

### Removed Components

**Eliminated for Simplicity**:
- Branch management (`models.py`, `local_state.py`, `git_semantics.py`)
- Web UI (`web_ui.py`, templates, static files)
- Complex lineage tracking and usage databases
- Git-like branching and merging workflows

### API Design Principles

**Ergonomic Python API**:
- Simple, intuitive method names
- Clear return types and error handling
- Context managers for temporary file access
- Streaming operations for large files
- Backend-agnostic through fsspec

**Example Usage**:

```python
from kirin import Dataset, File, Commit

# Create dataset
ds = Dataset(root_dir="/path/to/data", name="my_dataset")

# Commit files
commit_hash = ds.commit(message="Initial commit", add_files=["file1.csv"])

# Access files
file_obj = ds.get_file("file1.csv")
content = file_obj.read_text()

# Checkout specific commit
ds.checkout(commit_hash)

# Get history
history = ds.history(limit=10)
```

## Design System & CSS Architecture

### UI Framework: shadcn/ui

This project uses **shadcn/ui** as the design system for all user interface components. When working on the web UI:

- **Use shadcn/ui components and styling patterns** - All UI elements should follow shadcn/ui design principles
- **CSS Variables** - The project uses CSS custom properties defined in the `:root` selector for consistent theming:
  - `--background`, `--foreground` for text and backgrounds
  - `--card`, `--card-foreground` for panel backgrounds
  - `--primary`, `--primary-foreground` for primary actions
  - `--secondary`, `--secondary-foreground` for secondary elements
  - `--muted`, `--muted-foreground` for subtle text and backgrounds
  - `--border`, `--input` for form elements
  - `--destructive`, `--destructive-foreground` for destructive actions
  - `--radius` for border radius consistency

### Component Classes & Layout Patterns

**Component Classes** - Use the established component classes:
- `.btn` with variants: `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-destructive`
- `.input` for form inputs
- `.panel` for card-like containers
- `.panel-header` and `.panel-title` for panel headers
- `.panel-content` for panel body content
- `.file-item`, `.file-icon`, `.file-name` for file list items
- `.nav-bar`, `.breadcrumb`, `.breadcrumb-separator` for navigation

**Layout Patterns** - Follow established layout patterns:
- Use `.container` for main content areas
- Use `.header` for page headers with titles and descriptions
- Use grid layouts with `.grid` and responsive breakpoints
- Use `.space-y-*` for consistent vertical spacing

### CSS Architecture & Best Practices

**External Stylesheet System** - The project uses a centralized CSS architecture with all common styles in `/gitdata/static/styles.css`:

- **Base Template** - `base.html` includes the external stylesheet via `<link rel="stylesheet" href="/static/styles.css">`
- **No CSS Duplication** - All common component styles are defined once in the external file
- **Page-Specific Styles** - Only use `{% block extra_styles %}` for truly page-specific CSS that can't be reused

**Template Structure Guidelines**:

```html
{% extends "base.html" %}
{% block title %}Page Title{% endblock %}

{% block extra_styles %}
<style>
    /* Only include page-specific styles that aren't in the main CSS file */
    .page-specific-class {
        /* Custom styles only */
    }
</style>
{% endblock %}

{% block content %}
<div class="container">
    <div class="nav-bar">
        <!-- Breadcrumb navigation -->
    </div>
    <div class="header">
        <!-- Page title and description -->
    </div>
    <div class="content-container">
        <div class="panel">
            <div class="panel-header">
                <h2 class="panel-title">Title</h2>
            </div>
            <div class="panel-content">
                <!-- Content -->
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Styling Guidelines**:
1. **Always use the CSS custom properties** instead of hardcoded colors
2. **Follow the established component patterns** from existing templates
3. **Use semantic class names** that match shadcn/ui conventions
4. **Maintain consistency** with the existing design system
5. **Test responsive behavior** on different screen sizes

**Component Standards**:
- **File Icons**: Always 16px x 16px (`width: 16px; height: 16px`), use `.file-icon` class, `color: hsl(var(--muted-foreground)); opacity: 0.6;`
- **Panels**: Always use `.panel` > `.panel-header` > `.panel-content` structure, `padding: 1.25rem 1.5rem` for headers, `padding: 1.5rem` for content, `border: 1px solid hsl(var(--border))`

**Common Mistakes to Avoid**:

❌ **DON'T** copy CSS from other templates - use the external stylesheet
❌ **DON'T** use generic CSS classes like `bg-white`, `rounded-lg`, `shadow-md`
❌ **DON'T** create custom styling that doesn't match the design system
❌ **DON'T** add common component styles to individual templates

✅ **DO** use the external stylesheet for all common components
✅ **DO** only add page-specific CSS when absolutely necessary
✅ **DO** use the established component classes from the stylesheet
✅ **DO** maintain consistency with the shadcn/ui design system

**Examples**:

```html
<!-- Good: Using shadcn/ui patterns -->
<div class="panel">
    <div class="panel-header">
        <h2 class="panel-title">Title</h2>
    </div>
    <div class="panel-content">
        <button class="btn btn-primary">Action</button>
    </div>
</div>

<!-- Avoid: Custom styling that doesn't follow the system -->
<div class="bg-white rounded-lg shadow-md p-6">
    <h2 class="text-xl font-semibold mb-4">Title</h2>
    <button class="bg-blue-600 text-white px-4 py-2 rounded-md">Action</button>
</div>
```

## Development Guidelines

### Linting Guidelines

**IMPORTANT**: Only fix linting errors that cannot be automatically fixed by linters like ruff. The project has pre-commit hooks that handle automatic linting fixes (formatting, import sorting, etc.). Focus on:

- Logic errors and bugs that require manual intervention
- Issues that cannot be automatically resolved by linters
- Code quality problems that need human judgment

**Do NOT fix**:
- Import sorting (handled by isort/ruff)
- Code formatting (handled by black/ruff)
- Line length issues (handled by formatters)
- Whitespace and spacing (handled by formatters)

The pre-commit hooks will automatically handle these formatting issues, so focus on substantive code improvements.

### Logging Standards

**CRITICAL**: This project uses **loguru** for all logging throughout the codebase. Never use the standard Python `logging` module.

**Logging Requirements**:
- **Always use loguru**: Import with `from loguru import logger`
- **Never use standard logging**: Do not use `import logging` or `logging.getLogger()`
- **Consistent formatting**: Use the configured loguru format for all log messages
- **Performance logging**: Use `PERF:` prefix for performance-related log messages

**Implementation Pattern**:

```python
# ✅ CORRECT - Use loguru
from loguru import logger

logger.info("This is an info message")
logger.error("This is an error message")
logger.info("PERF: Operation completed in 0.123s")

# ❌ WRONG - Don't use standard logging
import logging
logger = logging.getLogger(__name__)
```

The web UI configures loguru with a specific format that includes:
- Timestamp in green
- Log level
- Module, function, and line number in cyan
- Message content

All new code must follow this logging standard to maintain consistency across the project.

### Static File Serving

The application is configured to serve static files from the `/gitdata/static/` directory:

- **CSS Files** - Place all stylesheets in `/gitdata/static/` directory
- **Static Mount** - FastAPI StaticFiles is mounted at `/static` route
- **CSS Reference** - Templates reference CSS via `/static/styles.css`
- **Development** - Use `pixi run python -m gitdata.web_ui` to start the server with auto-reload

### Pixi Environment Management

**CRITICAL**: The Kirin project uses **pixi** for dependency management and environment setup. All Python commands for testing and running the project must be executed within the pixi environment:

- **Testing Commands**: Always use `pixi run python -m pytest` or `pixi run python script.py`
- **Development Server**: Use `pixi run python -m gitdata.web_ui` to start the server
- **Kirin UI**: Use `pixi run gitdata ui` to run the Kirin web interface
- **CLI Commands**: Use `pixi run python -m gitdata.cli` for command-line operations

**Dependency Management**: For core runtime dependencies, use `pixi add --pypi <package>`. Do NOT manually edit pyproject.toml dependencies section - pixi manages this automatically.

**Note**: The Kirin project does not use debugging scripts like `debug_script.py`.

**Critical**: Never run Python commands directly without the `pixi run` prefix, as this will use the system Python instead of the project's managed environment with all required dependencies.

**MANDATORY**: All Python commands in the Kirin project must be prefixed with `pixi run python` instead of just `python`. This is because the project uses pixi for dependency management and environment setup. Never run Python commands directly without the pixi prefix.

**Note**: Do not run the web UI server for the user - they will handle running the application themselves when needed.

### Testing Dependencies

**CRITICAL**: When adding testing dependencies, use the pixi environment management:

- **Check pyproject.toml first**: Always inspect `pyproject.toml` to see what features and environments exist before adding dependencies
- **Conda-installable packages**: `pixi add -f <feature_name> <package_name>`
- **PyPI-only packages**: `pixi add -f <feature_name> --pypi <package_name>`
- **Test environment**: Use `pixi run -e <environment_name> python script.py` to run tests with test dependencies

**Examples**:

```bash
# Check pyproject.toml first to see available features
# Then add dependencies to the correct feature
pixi add -f tests --pypi httpx

# Run tests with test dependencies
pixi run -e tests python test_ui.py
```

**Key Points**:
- **Always check pyproject.toml first** - Look for `[tool.pixi.environments]` and `[tool.pixi.feature.*]` sections
- **Use correct feature names** - The feature name in `pixi add -f <feature>` must match what's defined in pyproject.toml
- **Use correct environment names** - The environment name in `pixi run -e <env>` must match what's defined in `[tool.pixi.environments]`

This ensures testing dependencies are properly managed and isolated from the main project dependencies.

## Web UI Implementation

### Commit Cache Management

The web UI uses a caching system to improve performance when displaying commits. **Critical**: The commit cache must be invalidated after any commit operations to ensure the UI shows the latest data.

- **Cache Key**: `(dataset_name, dataset_root_dir)` tuple
- **Cache TTL**: Configurable time-to-live for cache entries
- **Invalidation Points**: Cache must be cleared after:
  - Successful file uploads and commits
  - Successful file removals
  - Any commit operation that modifies the dataset

```python
# Always clear cache after successful commits
cache_key = (current_dataset.dataset_name, current_dataset.root_dir)
if cache_key in commit_cache:
    del commit_cache[cache_key]
    logger.info(f"Cleared commit cache for dataset: {current_dataset.dataset_name}")
```

**Failure to invalidate cache** results in stale commit lists where new commits don't appear in the UI, even though they exist in the dataset.

### File Upload Validation

The commit endpoint supports multiple operation types:

- **Add files only**: Upload new files to the dataset
- **Remove files only**: Stage files for removal (no uploads required)
- **Combined operations**: Add and remove files in the same commit
- **No operations**: Properly rejected with clear error message

**Implementation Details**:
- `files: list[UploadFile] = File(default=[])` - File uploads are optional
- `remove_files: list[str] = Form([])` - File removals are optional
- Validation ensures at least one operation is specified
- Temporary files are properly cleaned up after commit operations

### Temporary File Handling

When processing file uploads, the system uses temporary directories that must be properly managed:

```python
temp_dir = tempfile.mkdtemp()
try:
    # Process files and commit
    current_dataset.commit(...)
finally:
    # Always clean up temporary directory
    if temp_dir and os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
```

**Critical**: The commit operation must happen **before** the temporary directory cleanup, otherwise files will be deleted before the commit can access them.

### Template Escaping for Special Characters

**CRITICAL**: When working with filenames containing special characters in HTML templates, proper escaping is essential to avoid JavaScript syntax errors.

**Problem**: Filenames with special characters (spaces, quotes, etc.) can break JavaScript when used in inline `onclick` attributes.

**Solution**: Use data attributes instead of inline JavaScript for complex strings:

```html
<!-- ❌ WRONG - Inline JavaScript with special characters -->
<button onclick="openPreview('{{ file.name|e }}')" class="btn btn-ghost btn-sm">

<!-- ❌ WRONG - JSON escaping can break HTML parsing -->
<button onclick="openPreview({{ file.name|tojson }})" class="btn btn-ghost btn-sm">

<!-- ✅ CORRECT - Data attributes approach -->
<button onclick="openPreview(this.dataset.filename)"
        data-filename="{{ file.name|e }}"
        class="btn btn-ghost btn-sm">
```

**Key Principles**:
- **Use data attributes**: Store complex strings in `data-*` attributes, not inline JavaScript
- **HTML escaping for data attributes**: Use `|e` filter for HTML attribute values
- **JavaScript access**: Use `this.dataset.attributeName` to access data attributes
- **Avoid inline JavaScript**: Complex strings with spaces/special chars break HTML parsing

**Example Implementation**:

```html
<!-- Template -->
<button onclick="openPreview(this.dataset.filename)"
        data-filename="{{ file.name|e }}"
        class="btn btn-ghost btn-sm">

<!-- JavaScript -->
function openPreview(fileName) {
    // fileName comes from this.dataset.filename
    // No need for additional escaping
}
```

**Why This Works**:
- **HTML parsing**: Data attributes are properly handled by HTML parsers
- **No JavaScript syntax errors**: No complex strings in inline JavaScript
- **Proper escaping**: HTML entities (`&#39;`) work correctly in data attributes
- **Robust**: Handles any filename with spaces, quotes, or special characters

### Error Handling Patterns

The web UI follows consistent error handling patterns:

- **400 Bad Request**: Invalid input (no dataset loaded, no operations specified)
- **404 Not Found**: File not found for removal operations
- **422 Unprocessable Content**: Form validation errors (fixed by making file uploads optional)
- **500 Internal Server Error**: Unexpected errors with detailed logging

All error responses include user-friendly HTML with appropriate styling using the design system components.

## Script Execution Standards

### Script Location and Execution Pattern

**CRITICAL**: All Python scripts in the Kirin project follow a specific execution pattern:

- **Script Location**: All scripts are placed in the `scripts/` directory
- **Execution Method**: Scripts are run using `uv run` from the scripts directory
- **Execution Pattern**: `cd scripts && uv run script_name.py`
- **PEP723 Metadata**: All scripts must include inline script metadata for dependency management

### Ephemeral Scripts for Problem Solving

**ACCEPTABLE**: It's acceptable to create ephemeral scripts for problem solving as long as they are cleaned up once the problem is solved. This allows for quick debugging and testing without cluttering the codebase.

**Guidelines for Ephemeral Scripts**:
- **Temporary Nature**: Scripts should be created for specific debugging/testing purposes
- **Clean Up**: Always delete ephemeral scripts once the problem is solved
- **Naming**: Use descriptive names like `debug_commit_history.py` or `test_git_semantics.py`
- **Location**: Place in `scripts/` directory for consistency

**Required Pattern**:

```bash
# Navigate to scripts directory
cd scripts

# Run any script using uv run
uv run create_dummy_dataset.py
uv run other_script.py
```

**Key Requirements**:
- **Always use `uv run`** - Never use `python` directly
- **Always run from scripts directory** - Change to `scripts/` directory first
- **Script naming** - Use descriptive names with underscores (e.g., `create_dummy_dataset.py`)

**Benefits of this pattern**:
- **Consistent execution environment** - All scripts use the same dependency resolution
- **Proper dependency management** - `uv run` handles script dependencies automatically
- **Isolated execution** - Scripts don't interfere with the main project environment
- **Easy maintenance** - All utility scripts are organized in one location

**Examples**:

```bash
# ✅ CORRECT - Standard script execution
cd scripts
uv run create_dummy_dataset.py

# ❌ WRONG - Don't run from project root
uv run scripts/create_dummy_dataset.py

# ❌ WRONG - Don't use python directly
python scripts/create_dummy_dataset.py
```

### Script Metadata Requirements

**MANDATORY**: All Python scripts must include PEP723-style inline script metadata for dependency management. This ensures scripts can be run with proper dependency resolution.

**Required Pattern**:

```python
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars==1.34.0",
#     "gitdata==0.0.1",
#     "anthropic==0.69.0",
#     "loguru==0.7.3",
# ]
#
# [tool.uv.sources]
# gitdata = { path = "../", editable = true }
# ///
```

**Key Requirements**:
- **Python Version**: Always specify `requires-python = ">=3.13"`
- **Kirin Dependency**: Include `gitdata==0.0.1` in dependencies
- **Editable Source**: Use `[tool.uv.sources]` with `gitdata = { path = "../", editable = true }`
- **Additional Dependencies**: Include any other libraries the script needs
- **Metadata Block**: Must be at the very top of the file, before any imports

## The Notebook - Kirin Capabilities Showcase

The project includes a Marimo notebook at `notebooks/prototype.py` that serves as the primary showcase for Kirin's capabilities. This notebook demonstrates:

- **File Access Patterns**: How to work with remote files using the context manager
- **Lazy Loading**: Demonstrating that files are only downloaded when accessed
- **Integration Examples**: Real-world usage with libraries like Marimo, Polars, etc.
- **Visualization**: Commit history and dataset exploration

**Notebook Guidelines**:
- **Keep it updated** - Add new capabilities and examples to the notebook
- **Use real examples** - Show actual use cases, not just toy examples
- **Document patterns** - Include comments explaining the Kirin patterns
- **Test regularly** - Use `uvx marimo check notebooks/prototype.py` to validate the notebook
- **Interactive demos** - Make it runnable and educational
- **MANDATORY: Inline Script Metadata** - All notebooks MUST contain PEP723-style inline script metadata for dependency management
- **CRITICAL: Always Run Marimo Check** - ALWAYS run `uvx marimo check` on any notebook after editing it to ensure it's valid and has no cell conflicts

**Marimo Notebook Best Practices**:

When creating Marimo notebooks, follow these patterns for reliable execution:

**Simple Cell Pattern (RECOMMENDED)**:

```python
# All cells use simple _() naming
@app.cell
def _():
    """Setup dataset for workflow."""
    # Create resources and return them
    return dataset, temp_dir

@app.cell
def _(dataset):
    """Process step with dataset."""
    # Work with dataset directly
    assert condition
    print("✅ Step completed")
    return

@app.cell
def _(dataset, temp_dir):
    """Another step with multiple dependencies."""
    # Use both variables
    return
```

**Key Requirements**:
- **Simple Cell Names** - Use `_()` for all cells to avoid complexity
- **No Test Functions** - Execute workflow steps directly in cells
- **No Fixtures** - Each cell does what it needs to do
- **Clear Dependencies** - Use explicit parameter names to declare what variables each cell needs
- **Return Variables** - Always return variables that subsequent cells need
- **Display Output** - Always assign display objects to variables and explicitly display them

**Notebook Validation**:

```bash
# Check notebook for issues
uvx marimo check notebooks/prototype.py

# Run the notebook
uvx marimo run notebooks/prototype.py
```

**MANDATORY**: Always run `uvx marimo check /path/to/notebook.py` whenever we edit a notebook.

**Notebook Validation Process**:
1. **Edit Notebook**: Make changes to the notebook file
2. **Run Marimo Check**: Execute `uvx marimo check /path/to/notebook.py`
3. **Fix Issues**: Address any validation errors or warnings
4. **Re-run Check**: Continue until the notebook passes validation
5. **Verify Functionality**: Ensure the notebook runs correctly

**Common Marimo Check Issues**:
- **Cell Dependencies**: Ensure proper variable dependencies between cells
- **Return Statements**: All cells must return variables or have explicit return statements
- **Import Organization**: Keep imports at the top of cells
- **Variable Naming**: Use consistent variable naming patterns
- **Cell Structure**: Maintain proper cell structure and organization

**Common Issues to Avoid**:
- ❌ Inconsistent heading levels (skipping from H1 to H3)
- ❌ Long lines without proper wrapping
- ❌ **Temporary Directory Issues**: Never create datasets inside `tempfile.TemporaryDirectory()` context managers that get cleaned up
- ❌ **Content Storage Issues**: Ensure dataset root directories persist for the lifetime of File objects
- ❌ **Variable Naming Conflicts**: Use unique variable names across all cells
- ❌ **Empty Cells**: Remove cells that contain only whitespace, comments, or pass statements
- ❌ **Missing Return Values**: All cells should return meaningful values for reactive dependencies
- ❌ **Fragmented Logic**: Combine related operations into single cells for better organization
- ❌ Inconsistent list formatting
- ❌ Missing language specification in code blocks
- ❌ Trailing whitespace
- ❌ Multiple consecutive blank lines

## Marimo Markdown Cell Pattern

**CRITICAL**: When writing markdown cells in Marimo notebooks, use the string concatenation pattern instead of f-strings or multi-line strings with `mo.md()`.

**Required Pattern**:

```python
# ✅ CORRECT - String concatenation pattern
str_content = ""
str_content += "**Section Title:**\n"
str_content += f"- **Item 1**: {variable1}\n"
str_content += f"- **Item 2**: {variable2}\n"
str_content += "\n**Subsection:**\n"
str_content += "```python\n"
str_content += "code_example()\n"
str_content += "```\n"

mo.md(str_content)
```

**Why This Pattern**:
- **Marimo Compatibility**: Avoids issues with nested f-strings and complex string formatting
- **Reliable Rendering**: Ensures markdown content renders correctly in Marimo
- **Maintainable**: Easy to modify and extend markdown content
- **Consistent**: Works reliably across different Marimo versions

**Avoid These Patterns**:

```python
# ❌ WRONG - Multi-line f-strings
mo.md(f"""
**Section Title:**
- **Item 1**: {variable1}
- **Item 2**: {variable2}
""")

# ❌ WRONG - Nested f-strings in loops
for item in items:
    mo.md(f"**{item.title}**: {item.value}")

# ❌ WRONG - Complex string formatting
mo.md(f"**Title**: {complex_expression if condition else 'default'}")
```

**Best Practices**:
- **Initialize Empty String**: Always start with `str_content = ""`
- **Explicit Newlines**: Add `\n` at the end of each line for proper formatting
- **Consistent Indentation**: Use consistent spacing for code blocks and lists
- **Single mo.md() Call**: Use only one `mo.md()` call per cell at the end
- **Variable Substitution**: Use f-strings within the concatenation pattern for dynamic content

## Testing Guidelines

**CRITICAL**: Always write tests FIRST before implementing functionality. This project follows Test-Driven Development (TDD).

When writing tests for the project:

- **Always write tests FIRST** - Write tests before implementation code
- **TDD Workflow**: Write test → Run test (should fail) → Implement → Run test (should pass) → Refactor
- **Always write tests in the test suite** - Place test files in the `/tests/` directory following the existing naming conventions
- **Use the test environment** - Always run tests with `pixi run -e tests pytest` or `pixi run -e tests pytest tests/test_filename.py`
- **Test new functionality immediately** - Write tests for new features before or alongside implementation
- **Follow existing test patterns** - Use the same structure and naming conventions as existing tests in the test suite
- **Use pytest function style only** - Write tests as functions, not classes. Use `def test_function_name():` pattern
- **No test classes** - Avoid `class TestSomething:` patterns. Use function-based tests with descriptive names

**Pytest-Style Test Functions** (PREFERRED):

```python
# ✅ CORRECT - Pytest function style
def test_local_state_initialization():
    """Test that local state initializes correctly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        lsm = LocalStateManager("test-dataset", temp_dir)
        assert lsm.get_current_branch() == "main"

def test_branch_operations():
    """Test basic branch operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        lsm = LocalStateManager("test-dataset", temp_dir)
        # Test implementation...

# ❌ AVOID - Unittest class style
class TestLocalStateManager:
    def test_local_state_initialization(self):
        # Test implementation...
```

**Benefits of pytest-style functions**:
- **Simpler structure** - No class overhead, just functions
- **Easier to read** - More straightforward test organization
- **Better pytest integration** - Follows pytest best practices
- **Cleaner output** - Test names are more direct in pytest output
- **Easier maintenance** - Less boilerplate code

**Documentation and Examples**:
- **Tests are the primary demonstration** - Tests serve as the main way to show functionality and usage patterns
- **No example scripts needed** - Do not create standalone example scripts to demonstrate functionality
- **Comprehensive test coverage** - Write tests that cover both basic usage and edge cases
- **Test documentation** - Use descriptive test names and docstrings to explain what each test demonstrates
- **Real-world scenarios** - Write tests that reflect actual usage patterns and workflows

## Test Suite Maintenance and API Evolution

### Test-Driven Development and API Consistency

**CRITICAL**: The test suite serves as the primary documentation for the current API. When APIs evolve, tests must be updated to reflect the current implementation, not the historical one.

**Key Principles**:
- **Tests Document Current API**: Tests should always reflect the current implementation, not outdated interfaces
- **API Evolution Tracking**: When APIs change, update tests immediately to prevent confusion
- **Remove Obsolete Tests**: Delete tests for functionality that no longer exists rather than keeping broken tests
- **Consistent Parameter Names**: Ensure test code uses the same parameter names as the actual implementation

### Common API Evolution Issues

**Dataset Constructor Changes**:
- **Old API**: `Dataset(root_dir=path, dataset_name="name")`
- **Current API**: `Dataset(root_dir=path, name="name")`
- **Fix**: Update all test fixtures and constructor calls to use `name` parameter

**Commit Method Changes**:
- **Old API**: `dataset.commit(commit_message="msg", add_files=file)`
- **Current API**: `dataset.commit(message="msg", add_files=[file])`
- **Fix**: Update all commit calls to use `message` parameter and ensure `add_files` is a list

**Property Name Changes**:
- **Old API**: `dataset.file_dict`, `dataset.dataset_name`
- **Current API**: `dataset.files`, `dataset.name`
- **Fix**: Update all property references to use current names

**Method Signature Changes**:
- **Old API**: `dataset.get_file_content(filename)`, `dataset.download_file(filename)`
- **Current API**: `dataset.read_file(filename)`, `dataset.download_file(filename, target_path)`
- **Fix**: Update method calls to match current signatures

### Test Fixing Workflow

**Systematic Approach**:
1. **Run Full Test Suite**: Get overview of all failures with `pixi run -e tests python -m pytest tests/ --tb=no -q`
2. **Identify Patterns**: Look for common error types (TypeError, AttributeError, etc.)
3. **Fix by Category**: Address similar issues together (e.g., all Dataset constructor issues)
4. **Verify Progress**: Re-run tests to confirm improvements
5. **Document Changes**: Note what was fixed for future reference

**Common Error Patterns**:
- **TypeError: unexpected keyword argument**: Usually means parameter name changed
- **AttributeError: object has no attribute**: Usually means property/method name changed
- **ImportError: cannot import name**: Usually means class/function was removed or renamed
- **AssertionError**: Usually means test logic needs updating for new API

### Test Suite Health Metrics

**Progress Tracking**:
- **Before Fixes**: Track total failed vs passing tests
- **After Each Category**: Measure improvement (e.g., "reduced failures from 45 to 26")
- **Final State**: Document final test suite health
- **Regression Prevention**: Ensure fixes don't break other tests

**Example Progress Report**:

```text
✅ Fixed Dataset API issues: commit_message → message, file_dict → files
✅ Fixed CommitStore API issues: name → dataset_name, removed obsolete methods
✅ Fixed File Access API issues: get_file_content → read_file, download_file signature
📊 Results: 45 failed → 26 failed, 182 passing → 202 passing
```

### Obsolete Test Removal

**When to Remove Tests**:
- **Non-existent Functionality**: Tests for classes/methods that no longer exist
- **Architectural Changes**: Tests for removed features (e.g., branching, complex lineage)
- **API Simplification**: Tests for functionality that was intentionally removed

**Removal Process**:
1. **Verify Obsolescence**: Confirm functionality truly doesn't exist
2. **Check Dependencies**: Ensure no other tests depend on removed functionality
3. **Remove Cleanly**: Delete entire test files for removed features
4. **Update Documentation**: Remove references to deleted functionality

**Example**:

```python
# ❌ REMOVE - Tests for non-existent functionality
def test_resolve_commit_hash():
    # This method doesn't exist in current Dataset API
    pass

# ❌ REMOVE - Tests for removed features
def test_branch_operations():
    # Branching was removed in architecture simplification
    pass
```

### Test Maintenance Best Practices

**Regular Maintenance**:
- **Run Tests Frequently**: Use `pixi run -e tests python -m pytest` regularly
- **Fix Immediately**: Don't let test failures accumulate
- **Update Documentation**: Keep test documentation current with API changes
- **Monitor Dependencies**: Ensure test dependencies are properly managed

**Prevention Strategies**:
- **API Consistency**: Use consistent naming across all components
- **Comprehensive Testing**: Test both success and failure cases
- **Clear Documentation**: Document API changes clearly
- **Version Control**: Track API evolution through git history

**Quality Assurance**:
- **All Tests Pass**: Zero tolerance for failing tests in main branch
- **Clear Error Messages**: Tests should provide helpful failure information
- **Maintainable Code**: Tests should be easy to understand and modify
- **Performance**: Tests should run quickly and efficiently

## Design Document Reference

### Code Changes and Design Alignment

**CRITICAL**: When making changes to the codebase, always refer back to the design document (`docs/design.md`) and explicitly mention where in the design document the choice was made. This ensures:

- **Design Consistency**: All implementation decisions align with the documented architecture
- **Design Evolution**: Real usage patterns can inform design document updates
- **Traceability**: Clear connection between design decisions and implementation
- **Documentation Maintenance**: Design document stays current with actual usage

**Required Process**:
1. **Before Making Changes**: Review the relevant sections of `docs/design.md`
2. **During Implementation**: Reference specific design document sections that justify the approach
3. **After Changes**: Note any discrepancies between design and implementation that may require design document updates
4. **Design Document Updates**: When real usage reveals design issues, update the design document accordingly

**Example Reference Format**:

```text
This implementation follows the design document's approach for [specific feature]
as outlined in section [X.Y] of docs/design.md, which specifies [specific design
decision]. However, real usage has revealed [specific issue], suggesting we may
need to update the design document to reflect [proposed change].
```

This process ensures the design document remains a living document that accurately reflects both the intended architecture and the lessons learned from actual implementation and usage.

## Documentation Standards

### Writing Style Guidelines

**CRITICAL**: When writing documentation, sacrifice grammar for concision. This means:

- **Prioritize clarity over perfect grammar** - Use incomplete sentences if they're clearer
- **Use bullet points and fragments** - Don't force complete sentences everywhere
- **Be direct and concise** - Get to the point quickly without unnecessary words
- **Use active voice** - "Do this" instead of "This should be done"
- **Break rules for readability** - Grammar rules can be bent for better understanding

**Examples**:

```markdown
<!-- Good: Concise and clear -->
- **Always use loguru**: Import with `from loguru import logger`
- **Never use standard logging**: Do not use `import logging`

<!-- Avoid: Overly formal and wordy -->
- **You should always use loguru**: You should import it with
  `from loguru import logger`
- **You should never use standard logging**: You should not use `import logging`
```

### Markdown Style Guidelines

All Markdown documentation in the project must follow **Markdownlint** rules for consistency and quality. This ensures:

- **Consistent formatting** across all documentation files
- **Improved readability** for developers and contributors
- **Automated linting** can catch style issues early
- **Professional appearance** in rendered documentation

**Required**: All Markdown files must pass Markdownlint validation with zero errors.

**Installation and Usage**:
- The user already has `markdownlint-cli` installed - only offer to install it if it's not available
- Run `markdownlint <filename>` on any Markdown file before committing
- All documentation changes must pass markdownlint validation

**Key Markdownlint Rules to Follow**:
- Use consistent heading hierarchy (no skipped levels)
- Use proper list formatting (consistent bullet points or numbers)
- Wrap lines at 80 characters for readability
- Use proper link formatting with descriptive text
- Ensure consistent spacing around headers and lists
- Use proper code block formatting with language specification
- Avoid trailing whitespace and multiple consecutive blank lines

**Validation**:

```bash
# Install markdownlint using pixi (recommended)
pixi global install markdownlint-cli

# Alternative: Install using npm
npm install -g markdownlint-cli

# Check all Markdown files
markdownlint docs/*.md

# Check specific file
markdownlint docs/design.md
```

**Required Workflow**: Run markdownlint on any Markdown file that is created or edited before committing changes.

**CRITICAL**: Always run markdownlint on any markdown file edits to ensure consistency and quality. This is mandatory for all markdown file changes.

**MANDATORY PROCESS**:
1. **Run markdownlint CLI**: Always run `markdownlint <filename>` on every Markdown file that is edited
2. **Fix ALL issues**: Every single issue that markdownlint reports must be fixed
3. **Zero tolerance**: No markdownlint errors are acceptable - all must be resolved
4. **Re-run until clean**: Continue running markdownlint until the file passes with zero errors
5. **Before committing**: Never commit a Markdown file that has markdownlint errors

**BULK LINTING**: When working on multiple Markdown files, run markdownlint on all files at once to identify issues across the entire documentation set:

```bash
# Lint all Markdown files in the repository
markdownlint AGENTS.md README.md docs/*.md

# Or use fd to find all Markdown files
fd -e md | xargs markdownlint
```

**PRIORITY FIXES**: Focus on critical issues first:
- **MD040**: Fenced code blocks without language specification
- **MD032**: Lists not surrounded by blank lines
- **MD031**: Fenced code blocks not surrounded by blank lines
- **MD047**: Missing trailing newline
- **MD013**: Line length issues (can be addressed systematically)

## Repository Cleanup Standards

**CRITICAL**: After major architectural changes, always clean up unnecessary files to maintain a clean repository.

**Files to Remove After Architecture Changes**:
- **Build artifacts**: Remove `build/`, `*.egg-info/` directories
- **Temporary files**: Remove temporary files created during development (e.g., `*_new.py`)
- **Outdated documentation**: Remove docs for features that no longer exist (e.g., `branching.md`)
- **Outdated scripts**: Remove scripts that test removed functionality (e.g., branch switching, git semantics)
- **Outdated tests**: Remove test files that import removed classes or test removed functionality
- **Dummy files**: Remove test dummy files that are no longer needed
- **Backup files**: Remove `.bak` files and other backup artifacts

**Cleanup Process**:
1. **Identify outdated files** - Look for files referencing removed functionality
2. **Check file contents** - Verify files are actually outdated, not just renamed
3. **Remove systematically** - Delete files one by one to avoid mistakes
4. **Verify removal** - Ensure no imports or references are broken
5. **Update documentation** - Remove references to deleted files in docs

**Common Outdated Files After Simplification**:
- Scripts testing branch/merge functionality
- Documentation for removed features
- Test files importing removed classes
- Build artifacts from old architecture
- Temporary development files

## Solution Design Approach

### Propose Solutions First, Then Discuss

**CRITICAL**: When working on building solutions, the user prefers that you propose a solution in chat first for critique, rather than asking questions. This approach:

- **Saves time** - Avoids back-and-forth question sessions
- **Shows initiative** - Demonstrates understanding of the problem
- **Enables critique** - User can point out flaws and improvements
- **Faster iteration** - More efficient problem-solving process

**Required Pattern**:
1. **Analyze the problem** - Understand what needs to be solved
2. **Propose a solution** - Present a concrete approach with details
3. **Wait for critique** - Let the user identify issues and improvements
4. **Refine based on feedback** - Iterate on the solution
5. **Implement** - Only after the solution is agreed upon

**Example**:

```text
User: "Let's design the file metadata structure"
Assistant: "Here's my proposed approach: [detailed solution]"
User: "I see issues with X, Y, Z. What about this alternative?"
Assistant: "Good points! Here's the revised approach: [updated solution]"
```