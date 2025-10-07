# Kirin - Agent Guidelines

This document provides guidelines for AI agents working on the Kirin project.

## Core Philosophy: Git for Data

**Kirin is "git" for data** - this application follows git conventions and
workflows for data management. This means:

- **Staging Changes**: All changes must be staged before committing (no direct
  modifications)
- **Commit Messages**: Every commit requires a meaningful commit message
- **Atomic Operations**: Changes are grouped into atomic commits
- **Version Control**: Full history tracking with branching and tagging
  capabilities
- **No Direct Removal**: Files cannot be directly removed - they must be staged
  for removal and committed with a message

### UI/UX Implications

- **Staging UI**: Provide clear visual indicators for staged changes
- **Commit Button**: Primary action that requires both staged changes and commit
  message
- **No Direct Actions**: Remove buttons that bypass the staging/commit workflow
- **Clear Workflow**: Guide users through the stage → commit → push workflow

## Design System & CSS Architecture

### UI Framework: shadcn/ui

This project uses **shadcn/ui** as the design system for all user interface
components. When working on the web UI:

- **Use shadcn/ui components and styling patterns** - All UI elements should
  follow shadcn/ui design principles
- **CSS Variables** - The project uses CSS custom properties defined in the
  `:root` selector for consistent theming:
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

**External Stylesheet System** - The project uses a centralized CSS
architecture with all common styles in `/gitdata/static/styles.css`:

- **Base Template** - `base.html` includes the external stylesheet via
  `<link rel="stylesheet" href="/static/styles.css">`
- **No CSS Duplication** - All common component styles are defined once in the
  external file
- **Page-Specific Styles** - Only use `{% block extra_styles %}` for truly
  page-specific CSS that can't be reused

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

- **File Icons**: Always 16px x 16px (`width: 16px; height: 16px`), use
  `.file-icon` class, `color: hsl(var(--muted-foreground)); opacity: 0.6;`
- **Panels**: Always use `.panel` > `.panel-header` > `.panel-content`
  structure, `padding: 1.25rem 1.5rem` for headers, `padding: 1.5rem` for
  content, `border: 1px solid hsl(var(--border))`

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

**IMPORTANT**: Only fix linting errors that cannot be automatically fixed by
linters like ruff. The project has pre-commit hooks that handle automatic
linting fixes (formatting, import sorting, etc.). Focus on:

- Logic errors and bugs that require manual intervention
- Issues that cannot be automatically resolved by linters
- Code quality problems that need human judgment

**Do NOT fix**:

- Import sorting (handled by isort/ruff)
- Code formatting (handled by black/ruff)
- Line length issues (handled by formatters)
- Whitespace and spacing (handled by formatters)

The pre-commit hooks will automatically handle these formatting issues, so focus
on substantive code improvements.

### Logging Standards

**CRITICAL**: This project uses **loguru** for all logging throughout the
codebase. Never use the standard Python `logging` module.

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

All new code must follow this logging standard to maintain consistency across
the project.

### Static File Serving

The application is configured to serve static files from the
`/gitdata/static/` directory:

- **CSS Files** - Place all stylesheets in `/gitdata/static/` directory
- **Static Mount** - FastAPI StaticFiles is mounted at `/static` route
- **CSS Reference** - Templates reference CSS via `/static/styles.css`
- **Development** - Use `pixi run python -m gitdata.web_ui` to start the server
  with auto-reload

## Web UI Implementation

### Commit Cache Management

The web UI uses a caching system to improve performance when displaying
commits. **Critical**: The commit cache must be invalidated after any commit
operations to ensure the UI shows the latest data.

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

**Failure to invalidate cache** results in stale commit lists where new
commits don't appear in the UI, even though they exist in the dataset.

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

When processing file uploads, the system uses temporary directories that must
be properly managed:

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

**Critical**: The commit operation must happen **before** the temporary
directory cleanup, otherwise files will be deleted before the commit can access
them.

### Error Handling Patterns

The web UI follows consistent error handling patterns:

- **400 Bad Request**: Invalid input (no dataset loaded, no operations specified)
- **404 Not Found**: File not found for removal operations
- **422 Unprocessable Content**: Form validation errors (fixed by making file
  uploads optional)
- **500 Internal Server Error**: Unexpected errors with detailed logging

All error responses include user-friendly HTML with appropriate styling using
the design system components.

## Development Environment

### Pixi Environment

This project uses **pixi** for dependency management and environment setup.
All shell commands for testing and running the project must be executed within
the pixi environment:

- **Testing Commands**: Always use `pixi run python -m pytest` or
  `pixi run python script.py`
- **Development Server**: Use `pixi run python -m gitdata.web_ui` to start the server
- **Kirin UI**: Use `pixi run gitdata ui` to run the Kirin web interface
- **CLI Commands**: Use `pixi run python -m gitdata.cli` for command-line operations
- **Debug Scripts**: Use `pixi run python debug_script.py` for debugging

**Critical**: Never run Python commands directly without the `pixi run` prefix,
as this will use the system Python instead of the project's managed environment
with all required dependencies.

**Note**: Do not run the web UI server for the user - they will handle running
the application themselves when needed.

### Script Metadata Requirements

**MANDATORY**: All Python scripts must include PEP723-style inline script
metadata for dependency management. This ensures scripts can be run with
proper dependency resolution.

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
- **Editable Source**: Use `[tool.uv.sources]` with
  `gitdata = { path = "../", editable = true }`
- **Additional Dependencies**: Include any other libraries the script needs
- **Metadata Block**: Must be at the very top of the file, before any imports

### The Notebook - Kirin Capabilities Showcase

The project includes a Marimo notebook at `notebooks/prototype.py` that serves
as the primary showcase for Kirin's capabilities. This notebook demonstrates:

- **File Access Patterns**: How to work with remote files using the context
  manager
- **Lazy Loading**: Demonstrating that files are only downloaded when accessed
- **Integration Examples**: Real-world usage with libraries like Marimo,
  Polars, etc.
- **Visualization**: Commit history and dataset exploration

**Notebook Guidelines**:

- **Keep it updated** - Add new capabilities and examples to the notebook
- **Use real examples** - Show actual use cases, not just toy examples
- **Document patterns** - Include comments explaining the Kirin patterns
- **Test regularly** - Use `uvx marimo check notebooks/prototype.py` to validate
  the notebook
- **Interactive demos** - Make it runnable and educational
- **MANDATORY: Inline Script Metadata** - All notebooks MUST contain PEP723-style
  inline script metadata for dependency management
- **CRITICAL: Always Run Marimo Check** - ALWAYS run `uvx marimo check` on any notebook
  after editing it to ensure it's valid and has no cell conflicts

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
- **Clear Dependencies** - Use explicit parameter names to declare what
  variables each cell needs
- **Return Variables** - Always return variables that subsequent cells need
- **Display Output** - Always assign display objects to variables and
  explicitly display them

**Notebook Validation**:

```bash
# Check notebook for issues
uvx marimo check notebooks/prototype.py

# Run the notebook
uvx marimo run notebooks/prototype.py
```

### Testing Guidelines

When writing tests for the project:

- **Always write tests in the test suite** - Place test files in the `/tests/`
  directory following the existing naming conventions
- **Use the test environment** - Always run tests with
  `pixi run -e tests pytest` or `pixi run -e tests pytest tests/test_filename.py`
- **Test new functionality immediately** - Write tests for new features before
  or alongside implementation
- **Follow existing test patterns** - Use the same structure and naming
  conventions as existing tests in the test suite
- **Use pytest function style only** - Write tests as functions, not classes.
  Use `def test_function_name():` pattern
- **No test classes** - Avoid `class TestSomething:` patterns. Use
  function-based tests with descriptive names

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

- **Tests are the primary demonstration** - Tests serve as the main way to show
  functionality and usage patterns
- **No example scripts needed** - Do not create standalone example scripts to
  demonstrate functionality
- **Comprehensive test coverage** - Write tests that cover both basic usage and
  edge cases
- **Test documentation** - Use descriptive test names and docstrings to explain
  what each test demonstrates
- **Real-world scenarios** - Write tests that reflect actual usage patterns and
  workflows

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

```
This implementation follows the design document's approach for [specific feature]
as outlined in section [X.Y] of docs/design.md, which specifies [specific design
decision]. However, real usage has revealed [specific issue], suggesting we may
need to update the design document to reflect [proposed change].
```

This process ensures the design document remains a living document that accurately reflects both the intended architecture and the lessons learned from actual implementation and usage.

## Documentation Standards

### Markdown Style Guidelines

All Markdown documentation in the project must follow **Markdownlint** rules
for consistency and quality. This ensures:

- **Consistent formatting** across all documentation files
- **Improved readability** for developers and contributors
- **Automated linting** can catch style issues early
- **Professional appearance** in rendered documentation

**Required**: All Markdown files must pass Markdownlint validation with zero errors.

**Installation and Usage**:

- The user already has `markdownlint-cli` installed - only offer to install it
  if it's not available
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

**Required Workflow**: Run markdownlint on any Markdown file that is created
or edited before committing changes.

**Common Issues to Avoid**:

- ❌ Inconsistent heading levels (skipping from H1 to H3)
- ❌ Long lines without proper wrapping
- ❌ Inconsistent list formatting
- ❌ Missing language specification in code blocks
- ❌ Trailing whitespace
- ❌ Multiple consecutive blank lines

**Examples**:

```markdown
<!-- Good: Proper heading hierarchy -->
# Main Title
## Section
### Subsection

<!-- Bad: Skipped heading level -->
# Main Title
### Subsection (skipped H2)

<!-- Good: Proper code block -->
```python
def example_function():
    return "Hello, World!"
```

<!-- Bad: Missing language specification -->
```python
def example_function():
    return "Hello, World!"
```