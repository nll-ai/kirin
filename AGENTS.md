# GitData - Agent Guidelines

This document provides guidelines for AI agents working on the GitData project.

## Core Philosophy: Git for Data

**GitData is "git" for data** - this application follows git conventions and workflows for data management. This means:

- **Staging Changes**: All changes must be staged before committing (no direct modifications)
- **Commit Messages**: Every commit requires a meaningful commit message
- **Atomic Operations**: Changes are grouped into atomic commits
- **Version Control**: Full history tracking with branching and tagging capabilities
- **No Direct Removal**: Files cannot be directly removed - they must be staged for removal and committed with a message

### Git Conventions to Follow

1. **Staging Before Committing**: Users must stage changes (add/remove files) before committing
2. **Meaningful Commit Messages**: Every commit requires a descriptive message explaining the changes
3. **Atomic Commits**: Each commit should represent a logical unit of work
4. **No Direct File Operations**: Never allow direct file removal without staging and committing
5. **Branching and Tagging**: Support for git-like branching and tagging workflows
6. **History Preservation**: Maintain complete history of all changes

### UI/UX Implications

- **Staging UI**: Provide clear visual indicators for staged changes
- **Commit Button**: Primary action that requires both staged changes and commit message
- **No Direct Actions**: Remove buttons that bypass the staging/commit workflow
- **Clear Workflow**: Guide users through the stage → commit → push workflow

## Design System

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

- **Component Classes** - Use the established component classes:
  - `.btn` with variants: `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-destructive`
  - `.input` for form inputs
  - `.panel` for card-like containers
  - `.panel-header` and `.panel-title` for panel headers
  - `.panel-content` for panel body content
  - `.file-item` for file list items

- **Layout Patterns** - Follow established layout patterns:
  - Use `.container` for main content areas
  - Use `.header` for page headers with titles and descriptions
  - Use grid layouts with `.grid` and responsive breakpoints
  - Use `.space-y-*` for consistent vertical spacing

### Styling Guidelines

1. **Always use the CSS custom properties** instead of hardcoded colors
2. **Follow the established component patterns** from existing templates
3. **Use semantic class names** that match shadcn/ui conventions
4. **Maintain consistency** with the existing design system
5. **Test responsive behavior** on different screen sizes

### Examples

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

- Always maintain consistency with the existing shadcn/ui design system
- Use the established component classes and CSS variables
- Follow the responsive design patterns used throughout the application
- Test UI changes to ensure they match the overall design language

## Static File Serving

The application is configured to serve static files from the `/gitdata/static/` directory:

- **CSS Files** - Place all stylesheets in `/gitdata/static/` directory
- **Static Mount** - FastAPI StaticFiles is mounted at `/static` route
- **CSS Reference** - Templates reference CSS via `/static/styles.css`
- **Development** - Use `pixi run python -m gitdata.web_ui` to start the server with auto-reload

## CSS Architecture

### External Stylesheet System

The project now uses a centralized CSS architecture with all common styles in `/gitdata/static/styles.css`:

- **Base Template** - `base.html` includes the external stylesheet via `<link rel="stylesheet" href="/static/styles.css">`
- **No CSS Duplication** - All common component styles are defined once in the external file
- **Page-Specific Styles** - Only use `{% block extra_styles %}` for truly page-specific CSS that can't be reused

### Template Structure Guidelines

When creating new templates, follow this simplified pattern:

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

### CSS Best Practices

1. **Use External Stylesheet** - All common styles are in `/static/styles.css`
2. **Minimal Template CSS** - Only add CSS to templates for truly page-specific styles
3. **Consistent Component Classes** - Use the established classes from the stylesheet:
   - `.panel`, `.panel-header`, `.panel-title`, `.panel-content`
   - `.file-item`, `.file-icon`, `.file-name`
   - `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.btn-destructive`
   - `.nav-bar`, `.breadcrumb`, `.breadcrumb-separator`

### Common Mistakes to Avoid

❌ **DON'T** copy CSS from other templates - use the external stylesheet
❌ **DON'T** use generic CSS classes like `bg-white`, `rounded-lg`, `shadow-md`
❌ **DON'T** create custom styling that doesn't match the design system
❌ **DON'T** add common component styles to individual templates

✅ **DO** use the external stylesheet for all common components
✅ **DO** only add page-specific CSS when absolutely necessary
✅ **DO** use the established component classes from the stylesheet
✅ **DO** maintain consistency with the shadcn/ui design system

### File Icon Standards

- **Size**: Always 16px x 16px (`width: 16px; height: 16px`)
- **Class**: Use `.file-icon` class
- **SVG**: Use the exact SVG path from `files_list.html`
- **Styling**: `color: hsl(var(--muted-foreground)); opacity: 0.6;`

### Panel Standards

- **Structure**: Always use `.panel` > `.panel-header` > `.panel-content`
- **Spacing**: `padding: 1.25rem 1.5rem` for headers, `padding: 1.5rem` for content
- **Borders**: `border: 1px solid hsl(var(--border))`
- **Shadows**: `box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)`

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

### Error Handling Patterns

The web UI follows consistent error handling patterns:

- **400 Bad Request**: Invalid input (no dataset loaded, no operations specified)
- **404 Not Found**: File not found for removal operations
- **422 Unprocessable Content**: Form validation errors (fixed by making file uploads optional)
- **500 Internal Server Error**: Unexpected errors with detailed logging

All error responses include user-friendly HTML with appropriate styling using the design system components.

## Development Environment

### Pixi Environment

This project uses **pixi** for dependency management and environment setup. All shell commands for testing and running the project must be executed within the pixi environment:

- **Testing Commands**: Always use `pixi run python -m pytest` or `pixi run python script.py`
- **Development Server**: Use `pixi run python -m gitdata.web_ui` to start the server
- **GitData UI**: Use `pixi run gitdata ui` to run the GitData web interface
- **CLI Commands**: Use `pixi run python -m gitdata.cli` for command-line operations
- **Debug Scripts**: Use `pixi run python debug_script.py` for debugging

**Critical**: Never run Python commands directly without the `pixi run` prefix, as this will use the system Python instead of the project's managed environment with all required dependencies.

### The Notebook - GitData Capabilities Showcase

The project includes a Marimo notebook at `notebooks/prototype.py` that serves as the primary showcase for GitData's capabilities. This notebook demonstrates:

- **File Access Patterns**: How to work with remote files using the context manager
- **Lazy Loading**: Demonstrating that files are only downloaded when accessed
- **Integration Examples**: Real-world usage with libraries like Marimo, Polars, etc.
- **Visualization**: Commit history and dataset exploration

**Notebook Guidelines**:
- **Keep it updated** - Add new capabilities and examples to the notebook
- **Use real examples** - Show actual use cases, not just toy examples
- **Document patterns** - Include comments explaining the GitData patterns
- **Test regularly** - Use `uvx marimo check notebooks/prototype.py` to validate the notebook
- **Interactive demos** - Make it runnable and educational

**Notebook Validation**:
```bash
# Check notebook for issues
uvx marimo check notebooks/prototype.py

# Run the notebook
uvx marimo run notebooks/prototype.py
```

### Testing Guidelines

When writing tests for the project:

- **Always write tests in the test suite** - Place test files in the `/tests/` directory following the existing naming conventions
- **Use the test environment** - Always run tests with `pixi run -e tests pytest` or `pixi run -e tests pytest tests/test_filename.py`
- **Test new functionality immediately** - Write tests for new features before or alongside implementation
- **Follow existing test patterns** - Use the same structure and naming conventions as existing tests in the test suite
- **Use pytest function style only** - Write tests as functions, not classes. Use `def test_function_name():` pattern
- **No test classes** - Avoid `class TestSomething:` patterns. Use function-based tests with descriptive names

### Documentation and Examples

- **Tests are the primary demonstration** - Tests serve as the main way to show functionality and usage patterns
- **No example scripts needed** - Do not create standalone example scripts to demonstrate functionality
- **Comprehensive test coverage** - Write tests that cover both basic usage and edge cases
- **Test documentation** - Use descriptive test names and docstrings to explain what each test demonstrates
- **Real-world scenarios** - Write tests that reflect actual usage patterns and workflows
