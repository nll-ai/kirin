# Kirin - Agent Guidelines

Guidelines for AI agents working on the Kirin project.

## Core Philosophy: Simplified Data Versioning

**Kirin is simplified "git" for data** - follows git conventions but with
linear-only history:

- **Linear Commits**: Simple, linear commit history without branching
  complexity
- **Content-Addressed Storage**: Files stored by content hash for integrity
  and deduplication
- **Ergonomic Python API**: Focus on ease of use and developer experience
- **Backend-Agnostic**: Works with any storage backend via fsspec
- **No Branching**: Linear-only commit history to avoid complexity

### Key Design Principles

- **Simplicity First**: Linear commit history without branching/merging
  complexity
- **Content Integrity**: Files stored by content hash ensure data integrity
- **Python-First**: Ergonomic Python API optimized for data science
  workflows
- **Backend Flexibility**: Support for local filesystem, S3, GCS, Azure,
  etc.
- **Zero-Copy Operations**: Efficient handling of large files through
  streaming

### Content-Addressed Storage Design

**CRITICAL**: Files are stored with **visible filenames** in the
content-addressed storage system:

- **Storage Path**: `root_dir/data/{hash[:2]}/{hash[2:]}/{filename}` (e.g.,
  `data/ab/cdef1234.../data.csv`)
- **Visible Filenames**: Original filenames are preserved in storage for
  transparency and debugging
- **Deduplication with Multiple Filenames**: When identical content is uploaded
  with different filenames, all filenames are stored as separate files in the
  same hash directory (all are copies of the same content)
- **File Retrieval**: Always uses the original filename from `File.name`
  metadata (preserves current API behavior)
- **Migration Strategy**: Automatically migrates old format files to new format
  on first access, with cleanup of old files
- **Content Integrity**: Files are identified by content hash, ensuring data
  integrity
- **Deduplication**: Identical content (regardless of original filename) is
  stored only once, but with multiple filename references

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
- Files stored at `root_dir/data/{hash[:2]}/{hash[2:]}/{filename}` **with
  visible filenames**
- Original filenames are preserved in storage for transparency
- Supports deduplication with multiple filenames for same content
- Automatic migration from old format to new format on first access
- Methods: `store_file()`, `store_content()`, `retrieve()`, `exists()`
- Supports local filesystem, S3, GCS, Azure, etc.

**CommitStore** (`kirin/commit_store.py`):

- Linear commit history storage in JSON format
- Single file per dataset: `root_dir/datasets/{name}/commits.json`
- Methods: `save_commit()`, `get_commit()`, `get_latest_commit()`,
  `get_commit_history()`

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

## Documentation Template Standards

### Jinja2 Template Format for User-Filled Values

**CRITICAL**: For consistency and clarity, all user-filled values in
documentation must be wrapped in Jinja2 template brackets `{{ }}`. This
makes it super obvious that users need to fill these out.

**Required Pattern**:

- **User values**: `{{ variable_name }}` - Use descriptive variable names
- **Consistent naming**: Use the same variable names across all docs
- **Clear context**: Variable names should be self-explanatory

**Common Variables**:

- `{{ bucket_name }}` - S3/GCS bucket names
- `{{ container_name }}` - Azure container names
- `{{ dataset_name }}` - Dataset names
- `{{ project_id }}` - GCP project IDs
- `{{ aws_profile }}` - AWS profile names
- `{{ username }}` - User names
- `{{ account_id }}` - AWS account IDs
- `{{ data_path }}` - Local file paths

**Examples**:

```python
# ✅ CORRECT - Jinja2 template format
catalog = Catalog(
    root_dir="s3://{{ bucket_name }}/data",
    aws_profile="{{ aws_profile }}"
)

dataset = Dataset(
    root_dir="gs://{{ bucket_name }}/data",
    name="{{ dataset_name }}",
    gcs_project="{{ project_id }}"
)
```

```bash
# ✅ CORRECT - CLI commands with templates
aws s3 ls s3://{{ bucket_name }}
gsutil ls gs://{{ bucket_name }}
az storage blob list --container-name {{ container_name }}
```

```json
# ✅ CORRECT - JSON with templates
{
  "Principal": {
    "AWS": "arn:aws:iam::{{ account_id }}:user/{{ username }}"
  },
  "Resource": [
    "arn:aws:s3:::{{ bucket_name }}",
    "arn:aws:s3:::{{ bucket_name }}/*"
  ]
}
```

**Benefits**:

- **Super obvious**: Users immediately see what they need to change
- **Consistent**: Same variable names across all documentation
- **Template-ready**: Can be used with actual templating systems
- **Clear context**: Variable names explain what the value represents

**Implementation**:

- **All user-filled values** must use `{{ }}` format
- **No hardcoded examples** like "my-bucket", "my-account", etc.
- **Descriptive variable names** that explain the purpose
- **Consistent naming** across all documentation files

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

- `.btn` with variants: `.btn-primary`, `.btn-secondary`, `.btn-ghost`,
  `.btn-destructive`
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

### CSS Architecture Decision: Component-Based + Curated Utilities

**CRITICAL ARCHITECTURAL DECISION**: This project uses a **Component-Based
CSS architecture with curated utility classes**. This hybrid approach balances
maintainability, flexibility, and developer experience.

**Decision Rationale**:

After architectural review, this approach was chosen because:

1. **Component-Based Foundation**: The project has clear, reusable UI
   components (`panel`, `btn`, `card`, `form-group`) that define the design
   system. These components provide semantic meaning and consistency.

2. **Utility Layer for Composition**: A curated set of utility classes
   handles layout, spacing, and typography. These utilities compose INSIDE
   components, not replace them.

3. **Avoids Inline Styles**: Templates were falling back to inline `style=""`
   attributes when utilities didn't exist. Adding curated utilities eliminates
   this code smell.

4. **Right Level of Abstraction**: Full utility-first (like Tailwind) would be
   overkill for this application. Pure component-based lacks flexibility for
   layout composition. The hybrid approach provides the right balance.

**Architecture Layers**:

```text
┌─────────────────────────────────────┐
│   COMPONENTS (Semantic, Reusable)   │
│   .panel, .btn, .card, .form-group  │
│   These define your design system   │
└─────────────────────────────────────┘
              ↓ uses
┌─────────────────────────────────────┐
│   UTILITIES (Layout & Spacing)      │
│   .flex, .items-center, .gap-2       │
│   These compose INSIDE components   │
└─────────────────────────────────────┘
```

**Clear Boundaries**:

- **Components** = What it is (`btn`, `panel`, `card`) - Semantic, reusable
  UI elements
- **Utilities** = How it's arranged (`flex`, `gap-*`, `text-*`) - Layout,
  spacing, typography helpers

**When to Use Components**:

Use component classes for reusable UI elements:

- Buttons: `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`,
  `.btn-destructive`
- Panels/Cards: `.panel`, `.panel-header`, `.panel-content`, `.card`
- Forms: `.form-group`, `.form-label`, `.input`, `.select`, `.textarea`
- Navigation: `.nav-bar`, `.breadcrumb`, `.breadcrumb-separator`
- File Items: `.file-item`, `.file-icon`, `.file-name`
- Alerts: `.alert`, `.alert-success`, `.alert-error`, `.alert-warning`
- Modals: `.modal`, `.modal-header`, `.modal-body`, `.modal-footer`
- Tabs: `.tabs`, `.tab`, `.tab-content`

**When to Use Utilities**:

Use utility classes for layout composition and fine-tuning:

- **Layout**: `.flex`, `.items-center`, `.justify-between`, `.gap-2`, `.gap-4`
- **Typography**: `.text-sm`, `.text-muted-foreground`, `.font-medium`,
  `.font-semibold`
- **Spacing**: `.p-4`, `.mb-2`, `.mt-4`, `.space-y-4`, `.space-y-6`
- **Display**: `.hidden`, `.block`, `.inline-flex`
- **Grid**: `.grid`, `.grid-cols-1`, `.grid-cols-2`, `.md:grid-cols-2`

**Usage Pattern**:

```html
<!-- ✅ CORRECT - Component structure with utilities for layout -->
<div class="panel">
    <div class="panel-header">
        <h2 class="panel-title">Title</h2>
    </div>
    <div class="panel-content">
        <!-- Utilities used INSIDE components for layout -->
        <div class="flex items-center gap-2 mb-4">
            <span class="text-sm text-muted-foreground">Label:</span>
            <button class="btn btn-primary">Action</button>
        </div>
    </div>
</div>

<!-- ❌ WRONG - Don't rebuild components with utilities -->
<div class="bg-card border border-border rounded-lg p-6">
    <h2 class="text-lg font-semibold mb-4">Title</h2>
    <button class="bg-primary text-primary-foreground px-4 py-2 rounded-md">
        Action
    </button>
</div>

<!-- ❌ WRONG - Don't use inline styles -->
<div style="display: flex; align-items: center; gap: 1rem;">
    <button class="btn btn-primary">Action</button>
</div>
```

**External Stylesheet System**:

- **Location**: All styles in `/kirin/web/static/styles.css`
- **Base Template**: `base.html` includes via `<link rel="stylesheet"
  href="/static/styles.css">`
- **No Duplication**: All component styles defined once in the external file
- **Page-Specific Styles**: Only use `{% block extra_styles %}` for truly
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
    <div class="space-y-6">
        <div class="panel">
            <div class="panel-header">
                <h2 class="panel-title">Title</h2>
            </div>
            <div class="panel-content">
                <!-- Use utilities for layout composition -->
                <div class="flex items-center gap-2">
                    <button class="btn btn-primary">Action</button>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Styling Guidelines**:

1. **Always use CSS custom properties** instead of hardcoded colors
2. **Use components for structure** - Components define what UI elements are
3. **Use utilities for composition** - Utilities define how elements are
   arranged
4. **Never use inline styles** - Always use utility classes or components
5. **Maintain consistency** with the existing design system
6. **Test responsive behavior** on different screen sizes

**Component Standards**:

- **File Icons**: Always 16px x 16px (`width: 16px; height: 16px`), use
  `.file-icon` class, `color: hsl(var(--muted-foreground)); opacity: 0.6;`
- **Panels**: Always use `.panel` > `.panel-header` > `.panel-content`
  structure, `padding: 1.25rem 1.5rem` for headers, `padding: 1.5rem` for
  content, `border: 1px solid hsl(var(--border))`
- **Buttons**: Use `.btn` base class with modifiers (`.btn-primary`,
  `.btn-secondary`, etc.)

**Common Mistakes to Avoid**:

❌ **DON'T** rebuild components with utilities - Use `.panel`, not
  `.bg-card.border.rounded-lg`
❌ **DON'T** use inline styles - Use utility classes instead
❌ **DON'T** copy CSS from other templates - Use the external stylesheet
❌ **DON'T** create custom styling that doesn't match the design system
❌ **DON'T** add common component styles to individual templates
❌ **DON'T** use utilities to replace components - `.btn` is better than
  `.bg-primary.text-white.px-4.py-2`

✅ **DO** use components for UI elements (`btn`, `panel`, `card`)
✅ **DO** use utilities for layout and spacing (`flex`, `gap-*`, `text-*`)
✅ **DO** compose utilities INSIDE components
✅ **DO** use the external stylesheet for all common styles
✅ **DO** only add page-specific CSS when absolutely necessary
✅ **DO** maintain consistency with the shadcn/ui design system

**Examples**:

```html
<!-- ✅ CORRECT - Component with utilities for layout -->
<div class="panel">
    <div class="panel-header">
        <h2 class="panel-title">Title</h2>
    </div>
    <div class="panel-content">
        <div class="flex items-center justify-between gap-4">
            <span class="text-sm text-muted-foreground">Description</span>
            <button class="btn btn-primary">Action</button>
        </div>
    </div>
</div>

<!-- ❌ WRONG - Rebuilding component with utilities -->
<div class="bg-card border border-border rounded-lg p-6">
    <h2 class="text-lg font-semibold mb-4">Title</h2>
    <button class="bg-primary text-primary-foreground px-4 py-2 rounded-md">
        Action
    </button>
</div>

<!-- ❌ WRONG - Inline styles instead of utilities -->
<div style="display: flex; align-items: center; gap: 1rem;">
    <button class="btn btn-primary">Action</button>
</div>
```

**Reference Documentation**:

- **CSS File**: `/kirin/web/static/styles.css` - Contains all component and
  utility definitions
- **Base Template**: `/kirin/web/templates/base.html` - Shows how stylesheet
  is included
- **Example Templates**: `/kirin/web/templates/dataset_view.html`,
  `/kirin/web/templates/catalogs.html` - Show component + utility usage
- **Design System**: Based on shadcn/ui patterns - See
  [shadcn/ui](https://ui.shadcn.com/) for component inspiration

**Adding New Utilities**:

When adding new utility classes:

1. **Check if component exists first** - Don't create utilities that duplicate
   component functionality
2. **Follow naming conventions** - Use descriptive names (`flex`,
   `items-center`, `gap-2`)
3. **Use CSS custom properties** - Reference design tokens (`hsl(var(--primary))`)
4. **Add to utilities section** - Keep utilities organized in
   `/kirin/web/static/styles.css`
5. **Document usage** - Update this section if adding new utility categories

**Adding New Components**:

When adding new component classes:

1. **Follow shadcn/ui patterns** - Use established component structure
2. **Use CSS custom properties** - Reference design tokens for theming
3. **Make reusable** - Components should work across multiple pages
4. **Add variants** - Use modifier classes (`.btn-primary`, `.alert-error`)
5. **Document usage** - Update component standards section above

## Development Guidelines

### Code Style: No Private Methods/Functions

**CRITICAL**: Do not use private method/function naming conventions (leading
underscores). Use regular module-level functions and methods instead.

**Rationale**:

- **Pythonic**: Python doesn't have true privacy - underscores are just
  conventions
- **Testability**: Public functions are easier to test independently
- **Clarity**: Clear, descriptive names are better than hiding behind
  underscores
- **Consistency**: Keep the codebase consistent without mixing public/private
  conventions

**Pattern**:

- ✅ **Use**: `is_kirin_internal_file()`, `extract_marimo_path()`,
  `get_image_content_type()`
- ❌ **Avoid**: `_is_kirin_internal_file()`, `_extract_marimo_path()`,
  `_get_image_content_type()`

**Exception**: Only use leading underscores for truly internal implementation
details that should never be accessed externally (e.g., `__init__`, `__str__`,
dunder methods).

### Linting Guidelines

**CRITICAL**: Always run pre-commit on all files and fix all issues. This
ensures code quality and consistency across the entire codebase.

**Pre-commit Requirements**:

- **Run pre-commit on all files**: Always run `pre-commit run --all-files`
  before committing changes
- **Fix all issues**: Every single issue that pre-commit reports must be fixed
- **Zero tolerance**: No pre-commit errors are acceptable - all must be
  resolved
- **Re-run until clean**: Continue running pre-commit until all files pass with
  zero errors
- **Before committing**: Never commit files that have pre-commit errors

**Pre-commit handles automatic fixes**:

- Import sorting (handled by isort/ruff)
- Code formatting (handled by black/ruff)
- Line length issues (handled by formatters)
- Whitespace and spacing (handled by formatters)

**Manual fixes required**:

- Logic errors and bugs that require manual intervention
- Issues that cannot be automatically resolved by linters
- Code quality problems that need human judgment

**Workflow**:

```bash
# Run pre-commit on all files
pre-commit run --all-files

# If issues are found, fix them and re-run
pre-commit run --all-files

# Continue until all files pass
```

### Logging Standards

**CRITICAL**: This project uses **loguru** for all logging throughout the
codebase. Never use the standard Python `logging` module.

**Logging Requirements**:

- **Always use loguru**: Import with `from loguru import logger`
- **Never use standard logging**: Do not use `import logging` or
  `logging.getLogger()`
- **Consistent formatting**: Use the configured loguru format for all log
  messages
- **Performance logging**: Use `PERF:` prefix for performance-related log
  messages

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

All new code must follow this logging standard to maintain consistency
across the project.

### Static File Serving

The application is configured to serve static files from the
`/kirin/static/` directory:

- **CSS Files** - Place all stylesheets in `/kirin/static/` directory
- **Static Mount** - FastAPI StaticFiles is mounted at `/static` route
- **CSS Reference** - Templates reference CSS via `/static/styles.css`
- **Development** - Use `pixi run python -m kirin.web.app` to start the
  server with auto-reload

### Pixi Environment Management

**CRITICAL**: The Kirin project uses **pixi** for dependency management and
environment setup. All Python commands for testing and running the project
must be executed within the pixi environment:

- **Testing Commands**: Always use `pixi run python -m pytest` or
  `pixi run python script.py`
- **Development Server**: Use `pixi run python -m kirin.web.app` to start
  the server
- **Kirin UI**: Use `pixi run kirin ui` to run the Kirin web interface
- **CLI Commands**: Use `pixi run python -m kirin.cli` for command-line
  operations

**Dependency Management**: For core runtime dependencies, use
`pixi add --pypi <package>`. Do NOT manually edit pyproject.toml
dependencies section - pixi manages this automatically.

**Note**: The Kirin project does not use debugging scripts like
`debug_script.py`.

**Critical**: Never run Python commands directly without the `pixi run`
prefix, as this will use the system Python instead of the project's managed
environment with all required dependencies.

**MANDATORY**: All Python commands in the Kirin project must be prefixed
with `pixi run python` instead of just `python`. This is because the
project uses pixi for dependency management and environment setup. Never
run Python commands directly without the pixi prefix.

**Note**: Do not run the web UI server for the user - they will handle
running the application themselves when needed.

### Testing Dependencies

**CRITICAL**: When adding testing dependencies, use the pixi environment
management:

- **Check pyproject.toml first**: Always inspect `pyproject.toml` to see what
  features and environments exist before adding dependencies
- **Conda-installable packages**: `pixi add -f <feature_name> <package_name>`
- **PyPI-only packages**: `pixi add -f <feature_name> --pypi <package_name>`
- **Test environment**: Use `pixi run -e <environment_name> python script.py`
  to run tests with test dependencies

**Examples**:

```bash
# Check pyproject.toml first to see available features
# Then add dependencies to the correct feature
pixi add -f tests --pypi httpx

# Run tests with test dependencies
pixi run -e tests python test_ui.py
```

**Key Points**:

- **Always check pyproject.toml first** - Look for
  `[tool.pixi.environments]` and `[tool.pixi.feature.*]` sections
- **Use correct feature names** - The feature name in `pixi add -f
  <feature>` must match what's defined in pyproject.toml
- **Use correct environment names** - The environment name in `pixi run -e
  <env>` must match what's defined in `[tool.pixi.environments]`

This ensures testing dependencies are properly managed and isolated from
the main project dependencies.

## Web UI Implementation

### Commit Cache Management

The web UI uses a caching system to improve performance when displaying
commits. **Critical**: The commit cache must be invalidated after any
commit operations to ensure the UI shows the latest data.

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

When processing file uploads, the system uses temporary directories that
must be properly managed:

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
directory cleanup, otherwise files will be deleted before the commit can
access them.

### Template Escaping for Special Characters

**CRITICAL**: When working with filenames containing special characters in
HTML templates, proper escaping is essential to avoid JavaScript syntax
errors.

**Problem**: Filenames with special characters (spaces, quotes, etc.) can
break JavaScript when used in inline `onclick` attributes.

**Solution**: Use data attributes instead of inline JavaScript for complex
strings:

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

- **Use data attributes**: Store complex strings in `data-*` attributes, not
  inline JavaScript
- **HTML escaping for data attributes**: Use `|e` filter for HTML attribute
  values
- **JavaScript access**: Use `this.dataset.attributeName` to access data
  attributes
- **Avoid inline JavaScript**: Complex strings with spaces/special chars
  break HTML parsing

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
- **Proper escaping**: HTML entities (`&#39;`) work correctly in data
  attributes
- **Robust**: Handles any filename with spaces, quotes, or special
  characters

### Error Handling Patterns

The web UI follows consistent error handling patterns:

- **400 Bad Request**: Invalid input (no dataset loaded, no operations
  specified)
- **404 Not Found**: File not found for removal operations
- **422 Unprocessable Content**: Form validation errors (fixed by making
  file uploads optional)
- **500 Internal Server Error**: Unexpected errors with detailed logging

All error responses include user-friendly HTML with appropriate styling
using the design system components.

### CRUD Operation Redirects

**CRITICAL**: All CRUD operations must redirect users to a logical landing
page that shows the updated state. This ensures users see the results of
their actions immediately.

**Redirect Patterns**:

- **After commit operations**: Redirect to `/{catalog}/{dataset}` to show
  updated dataset state
- **After file operations**: Redirect to `/{catalog}/{dataset}` to show
  updated file list
- **After catalog operations**: Redirect to `/{catalog}` to show updated
  catalog state
- **After dataset operations**: Redirect to `/{catalog}` to show updated
  dataset list

**Web UI Design Pattern**: The design pattern for the web UI is that CRUD
operations redirect to views. This ensures users see the results of their
actions immediately and provides a consistent navigation flow.

**Implementation Pattern**:

```python
# ✅ CORRECT - Redirect after successful operations
@app.post("/{catalog}/{dataset}/commit")
async def commit_files(catalog: str, dataset: str, ...):
    # Perform commit operation
    commit_hash = current_dataset.commit(...)

    # Redirect to dataset view to show updated state
    return RedirectResponse(
        url=f"/{catalog}/{dataset}",
        status_code=303  # See Other
    )

# ❌ WRONG - Return JSON or stay on same page
return {"status": "success", "commit_hash": commit_hash}
```

**Benefits**:

- **Immediate feedback**: Users see the results of their actions
- **Updated state**: Landing page reflects current data state
- **Better UX**: Clear navigation flow after operations
- **Consistent behavior**: All operations follow the same redirect pattern

**Status Codes**:

- **303 See Other**: Use for POST operations that should redirect to GET
- **302 Found**: Use for general redirects
- **301 Moved Permanently**: Use for permanent URL changes

## Script Execution Standards

### Script Location and Execution Pattern

**CRITICAL**: All Python scripts in the Kirin project follow a specific
execution pattern:

- **Script Location**: All scripts are placed in the `scripts/` directory
- **Execution Method**: Scripts are run using `pixi run python` from the project
  root
- **Execution Pattern**: `pixi run python scripts/script_name.py`
- **PEP723 Metadata**: All scripts must include inline script metadata for
  dependency management

### Ephemeral Scripts for Problem Solving

**ACCEPTABLE**: It's acceptable to create ephemeral scripts for problem
solving as long as they are cleaned up once the problem is solved. This
allows for quick debugging and testing without cluttering the codebase.

**Guidelines for Ephemeral Scripts**:

- **Temporary Nature**: Scripts should be created for specific
  debugging/testing purposes
- **Clean Up**: Always delete ephemeral scripts once the problem is solved
- **Naming**: Use descriptive names like `debug_commit_history.py` or
  `test_git_semantics.py`
- **Location**: Place in `scripts/` directory for consistency

**Required Pattern**:

```bash
# Run any script using pixi run python from project root
pixi run python scripts/create_dummy_dataset.py
pixi run python scripts/other_script.py
```

**Key Requirements**:

- **Always use `pixi run python`** - Never use `python` directly
- **Run from project root** - Use full path from project root (e.g., `scripts/script_name.py`)
- **Script naming** - Use descriptive names with underscores (e.g.,
  `create_dummy_dataset.py`)

**Benefits of this pattern**:

- **Consistent execution environment** - All scripts use the pixi-managed
  environment with all dependencies
- **Proper dependency management** - `pixi run python` ensures scripts run
  with the correct Python version and dependencies
- **Isolated execution** - Scripts run in the pixi environment, not system
  Python
- **Easy maintenance** - All utility scripts are organized in one location

**Examples**:

```bash
# ✅ CORRECT - Standard script execution from project root
pixi run python scripts/create_dummy_dataset.py

# ❌ WRONG - Don't use python directly
python scripts/create_dummy_dataset.py

# ❌ WRONG - Don't use uv run
uv run scripts/create_dummy_dataset.py
```

### Script Metadata Requirements

**MANDATORY**: All Python scripts must include PEP723-style inline script
metadata for dependency management. This ensures scripts can be run with
proper dependency resolution.

**Required Pattern**:

```python
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "polars",
#     "kirin",
#     "anthropic",
#     "loguru",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///
```

**Key Requirements**:

- **Python Version**: Always specify `requires-python = ">=3.13"`
- **Kirin Dependency**: Include `kirin` in dependencies (no version pin)
- **Editable Source**: Use `[tool.uv.sources]` with `kirin = { path =
  "../", editable = true }`
- **Additional Dependencies**: Include any other libraries the script needs
  (no version pins)
- **No Version Pins**: Do not pin versions in dependencies (e.g., use
  `polars` not `polars==1.34.0`)
- **Metadata Block**: Must be at the very top of the file, before any
  imports

## The Notebook - Kirin Capabilities Showcase

The project includes a Marimo notebook at `notebooks/prototype.py` that
serves as the primary showcase for Kirin's capabilities. This notebook
demonstrates:

- **File Access Patterns**: How to work with remote files using the context
  manager
- **Lazy Loading**: Demonstrating that files are only downloaded when
  accessed
- **Integration Examples**: Real-world usage with libraries like Marimo,
  Polars, etc.
- **Visualization**: Commit history and dataset exploration

**Notebook Guidelines**:

- **Keep it updated** - Add new capabilities and examples to the notebook
- **Use real examples** - Show actual use cases, not just toy examples
- **Document patterns** - Include comments explaining the Kirin patterns
- **Test regularly** - Use `uvx marimo check notebooks/prototype.py` to
  validate the notebook
- **Interactive demos** - Make it runnable and educational
- **MANDATORY: Inline Script Metadata** - All notebooks MUST contain
  PEP723-style inline script metadata for dependency management
- **CRITICAL: Always Run Marimo Check** - ALWAYS run `uvx marimo check` on
  any notebook after editing it to ensure it's valid and has no cell
  conflicts

**Marimo Notebook Best Practices**:

When creating Marimo notebooks, follow these patterns for reliable
execution. **Note**: For tutorial and how-to guide notebooks, follow the
exemplar pattern in `docs/tutorials/first-dataset.py` (see "Marimo
Notebook Writing Standards" section below).

**Simple Cell Pattern (For Non-Tutorial Notebooks)**:

```python
# All cells use simple _() naming
@app.cell
def _():
    # Setup dataset for workflow
    # Create resources and return them
    dataset = create_dataset()
    temp_dir = get_temp_dir()
    return dataset, temp_dir

@app.cell
def _(dataset):
    # Process step with dataset
    # Work with dataset directly
    assert condition
    print("✅ Step completed")
    return

@app.cell
def _(dataset, temp_dir):
    # Another step with multiple dependencies
    # Use both variables
    return
```

**Key Requirements**:

- **Simple Cell Names** - Use `_()` for all cells to avoid complexity
- **No Docstrings** - Do not use docstrings in `@app.cell` functions
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

**MANDATORY**: Always run `uvx marimo check /path/to/notebook.py` whenever
we edit a notebook.

**Notebook Validation Process**:

1. **Edit Notebook**: Make changes to the notebook file
2. **Run Marimo Check**: Execute `uvx marimo check /path/to/notebook.py`
3. **Fix Issues**: Address any validation errors or warnings
4. **Re-run Check**: Continue until the notebook passes validation
5. **Run Notebook**: Execute `uv run /path/to/notebook.py` to verify it runs
   correctly as a script and produces expected output
6. **Verify Functionality**: Ensure all cells execute successfully and output
   is correct

**Common Marimo Check Issues**:

- **Cell Dependencies**: Ensure proper variable dependencies between cells
- **Return Statements**: All cells must return variables or have explicit
  return statements
- **Import Organization**: Keep imports at the top of cells
- **Variable Naming**: Use consistent variable naming patterns
- **Cell Structure**: Maintain proper cell structure and organization

**Common Issues to Avoid**:

- ❌ Inconsistent heading levels (skipping from H1 to H3)
- ❌ Long lines without proper wrapping
- ❌ **Temporary Directory Issues**: Never create datasets inside
  `tempfile.TemporaryDirectory()` context managers that get cleaned up
- ❌ **Content Storage Issues**: Ensure dataset root directories persist for
  the lifetime of File objects
- ❌ **Variable Naming Conflicts**: Use unique variable names across all
  cells
- ❌ **Empty Cells**: Remove cells that contain only whitespace, comments,
  or pass statements
- ❌ **Missing Return Values**: All cells should return meaningful values
  for reactive dependencies
- ❌ **Fragmented Logic**: Combine related operations into single cells for
  better organization
- ❌ **Version Numbers in Filenames**: Never use version numbers (v1, v2,
  etc.) in filenames when demonstrating versioning. Use the same filenames
  and let Kirin's commit system handle versioning. This showcases the
  actual versioning capability rather than manual filename management.
- ❌ Inconsistent list formatting
- ❌ Missing language specification in code blocks
- ❌ Trailing whitespace
- ❌ Multiple consecutive blank lines

## Marimo Notebook Writing Standards

**CRITICAL**: All Marimo notebooks in the Kirin project must follow the
exemplar pattern established in `docs/tutorials/first-dataset.py`. This
ensures consistency, readability, and maintainability across all tutorial
and how-to guide notebooks.

**Diataxis Framework**: This project uses the Diataxis framework to
categorize documentation. Marimo notebooks are used for **Tutorials** and
**How-To Guides**, which have distinct purposes and writing styles:

- **Tutorials** (`docs/tutorials/`): Learning-oriented, narrative-driven
  guides that teach concepts progressively. Assume minimal prior knowledge.
- **How-To Guides** (`docs/how-to/`): Task-oriented guides that help
  users accomplish specific goals. Assume users know the basics.

### Exemplar Reference

**Reference Notebook**: `docs/tutorials/first-dataset.py` serves as the
exemplar for **tutorial** notebooks. When creating tutorial notebooks,
always refer to this file as the standard.

### Core Principles

**1. Markdown-Only Cells with `hide_code=True`**:

All cells that contain only markdown content must use `hide_code=True`:

```python
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Understanding Datasets

    A **dataset** in Kirin is a collection of versioned files. Think of it
    like a Git repository, but specifically designed for data files.
    """)
    return
```

**2. No Docstrings in App Cells**:

Code cells should NOT have docstrings. All explanatory text belongs in
separate markdown cells:

```python
# ✅ CORRECT - No docstring, explanation in markdown cell above
@app.cell
def _(dataset):
    commit_hash = dataset.commit(
        message="Initial commit",
        add_files=["file.csv"],
    )
    return

# ❌ WRONG - Don't use docstrings in app cells
@app.cell
def _(dataset):
    """Create initial commit with sample data."""
    commit_hash = dataset.commit(...)
    return
```

**3. Descriptive Variable Names**:

Use informative variable names without underscore prefixes:

```python
# ✅ CORRECT - Descriptive names
current_commit = dataset.get_commit(commit_hash)
updated_history = dataset.history()
first_commit = history[-1]
history_commit = updated_history[0]

# ❌ WRONG - Underscore prefixes or unclear names
_commit = dataset.get_commit(commit_hash)
h = dataset.history()
c = history[-1]
```

**4. Interleaved Markdown and Code Structure**:

Markdown explanation cells must come BEFORE their corresponding code cells:

```python
# ✅ CORRECT - Markdown first, then code
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Making Your First Commit

    Now let's add these files to our dataset.
    """)
    return

@app.cell
def _(dataset, files):
    commit_hash = dataset.commit(
        message="Initial commit",
        add_files=files,
    )
    return

# ❌ WRONG - Code before explanation
@app.cell
def _(dataset, files):
    commit_hash = dataset.commit(...)
    return

@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Step 3: Making Your First Commit...""")
    return
```

**5. Markdown Cell Pattern**:

Use raw triple-quoted strings with `mo.md()` for all markdown content:

```python
# ✅ CORRECT - Raw triple-quoted strings
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Understanding Datasets

    A **dataset** in Kirin is a collection of versioned files.

    - A **name** that identifies it
    - A **linear commit history** that tracks changes
    - **Files** stored using content-addressed storage
    """)
    return
```

**6. Step-by-Step Progression**:

Structure tutorials as clear, numbered steps with markdown explanations:

```python
# Step 1: Markdown explanation
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Step 1: Understanding Datasets...""")
    return

# Step 1: Code implementation
@app.cell
def _():
    # Implementation code
    return

# Step 2: Markdown explanation
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Step 2: Preparing Your First Files...""")
    return

# Step 2: Code implementation
@app.cell
def _():
    # Implementation code
    return
```

**7. Concept Explanations vs Steps**:

Some sections explain concepts rather than being numbered steps. Use
descriptive headings. **Note**: Concept explanations are more common in
tutorials than in how-to guides:

```python
# ✅ CORRECT - Concept explanation (not a numbered step)
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Understanding Content-Addressed Storage

    One of Kirin's key features is content-addressed storage. This means:
    - Files are stored by their content hash
    - Identical files are automatically deduplicated
    """)
    return

# ❌ WRONG - Don't number concept explanations
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Step 10: Understanding Content-Addressed Storage...""")
    return
```

**8. Proper Cell Dependencies**:

Always return variables that subsequent cells need, and declare dependencies
explicitly:

```python
# ✅ CORRECT - Clear dependencies and returns
@app.cell
def _():
    dataset = create_dataset()
    return (dataset,)

@app.cell
def _(dataset):
    commit_hash = dataset.commit(...)
    return (commit_hash,)

# ❌ WRONG - Missing return or unclear dependencies
@app.cell
def _():
    dataset = create_dataset()
    # Missing return statement

@app.cell
def _():
    # Unclear where dataset comes from
    commit_hash = dataset.commit(...)
```

**9. Clean Separation of Concerns**:

Keep markdown-only cells separate from code cells. Never mix markdown and
code in the same cell:

```python
# ✅ CORRECT - Separate cells
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Explanation text""")
    return

@app.cell
def _():
    # Code here
    return

# ❌ WRONG - Don't mix markdown and code
@app.cell
def _(mo):
    mo.md(r"""## Explanation""")
    # Code mixed in same cell
    result = do_something()
    return
```

### Markdown Content Guidelines

**Raw String Pattern**:

Use raw triple-quoted strings (`r"""..."""`) for markdown content to avoid
escaping issues:

```python
# ✅ CORRECT - Raw strings
mo.md(r"""
## Step 1: Title

This is the explanation text with **bold** and `code`.

- Bullet point 1
- Bullet point 2
""")

# ❌ WRONG - Regular strings (may need escaping)
mo.md("""
## Step 1: Title
This text might need \\ escaping
""")
```

**Line Length in Markdown**:

Keep markdown content lines within reasonable length (88 characters) for
readability, but don't sacrifice clarity for strict line limits:

```python
# ✅ CORRECT - Reasonable line length
mo.md(r"""
## Step 1: Understanding Datasets

A **dataset** in Kirin is a collection of versioned files. Think of it
like a Git repository, but specifically designed for data files.
""")

# ✅ ALSO ACCEPTABLE - Longer lines for clarity
mo.md(r"""
## Step 1: Understanding Datasets

A **dataset** in Kirin is a collection of versioned files. Think of it like a Git repository, but specifically designed for data files. Each dataset has a name, a linear commit history, and files stored using content-addressed storage.
""")
```

### Complete Example Structure

Here's the complete structure pattern from the exemplar:

```python
# Import cell
@app.cell
def _():
    import marimo as mo
    return (mo,)

# Title markdown
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""# Your First Dataset...""")
    return

# Prerequisites markdown
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Prerequisites...""")
    return

# Setup code
@app.cell
def _():
    # Setup code here
    return

# Step 1 explanation
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Step 1: Understanding...""")
    return

# Step 1 code
@app.cell
def _():
    # Step 1 implementation
    return

# Step 2 explanation
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""## Step 2: Preparing...""")
    return

# Step 2 code
@app.cell
def _():
    # Step 2 implementation
    return

# ... continue pattern
```

### Demonstrating Versioning in Notebooks

**CRITICAL**: When demonstrating versioning capabilities in notebooks, never
use version numbers in filenames. Use the same filenames across commits and
let Kirin's commit system handle versioning.

**The Problem**:

Using version numbers in filenames (e.g., `model_weights_v1.pt`,
`model_weights_v2.pt`) defeats the purpose of demonstrating versioning. It
shows manual filename management instead of Kirin's versioning capabilities.

**The Solution**:

Use the same filenames across different commits. Kirin's commit system
tracks different versions of files with the same name through the commit
history.

**Example Pattern**:

```python
# ✅ CORRECT - Same filenames, versioning handled by commits
@app.cell
def _(Path, model, temp_dir, torch):
    # First version
    model_path = Path(temp_dir) / "models" / "model_weights.pt"
    torch.save(model.state_dict(), model_path)
    config_path = Path(temp_dir) / "models" / "config.json"
    config_path.write_text('{"version": "1.0.0"}')
    return config_path, model_path

@app.cell
def _(model_registry, model_path, config_path):
    # Commit first version
    commit1 = model_registry.commit(
        message="Initial model v1.0",
        add_files=[str(model_path), str(config_path)],
    )
    return (commit1,)

@app.cell
def _(Path, improved_model, temp_dir, torch):
    # Second version - SAME FILENAMES
    model_path = Path(temp_dir) / "models" / "model_weights.pt"
    torch.save(improved_model.state_dict(), model_path)
    config_path = Path(temp_dir) / "models" / "config.json"
    config_path.write_text('{"version": "2.0.0"}')
    return config_path, model_path

@app.cell
def _(model_registry, model_path, config_path):
    # Commit second version - showcases versioning
    commit2 = model_registry.commit(
        message="Improved model v2.0",
        add_files=[str(model_path), str(config_path)],
    )
    return (commit2,)

# ❌ WRONG - Version numbers in filenames
improved_model_path = Path(temp_dir) / "models" / "model_weights_v2.pt"
improved_config_path = Path(temp_dir) / "models" / "config_v2.json"
```

**Why This Matters**:

- **Shows Real Versioning**: Demonstrates that Kirin tracks file versions
  through commits, not filenames
- **Real-World Pattern**: Matches how versioning actually works in practice
- **Highlights Commit System**: Emphasizes that commits are the versioning
  mechanism
- **Better Examples**: Users learn the correct pattern for their own workflows

**Key Principle**:

Version information belongs in:

- ✅ Commit messages
- ✅ Commit metadata
- ✅ Commit tags
- ❌ NOT in filenames

### Writing Tutorials vs How-To Guides

**CRITICAL**: Tutorials and how-to guides serve different purposes and
require different writing approaches. Follow the appropriate pattern for
each type.

#### Tutorials (`docs/tutorials/`)

**Purpose**: Learning-oriented, narrative-driven guides that teach concepts
progressively. Assume minimal prior knowledge.

**Key Characteristics**:

- **Learning-Oriented**: Focus on teaching new users how to use Kirin
- **Narrative-Driven**: Tell a story that builds understanding step by step
- **Progressive**: Each step builds on previous concepts
- **Explanatory**: Explain both "how" and "why"
- **Hands-On**: Provide practical steps with learning outcomes

**Writing Pattern**:

```python
# ✅ CORRECT - Tutorial structure
# 1. Introduction markdown (explains what you'll learn)
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Understanding Datasets

    A **dataset** in Kirin is a collection of versioned files. Think of it
    like a Git repository, but specifically designed for data files. Each
    dataset has:

    - A **name** that identifies it
    - A **linear commit history** that tracks changes over time
    - **Files** that are stored using content-addressed storage
    """)
    return

# 2. Code implementation (demonstrates the concept)
@app.cell
def _():
    from kirin import Catalog
    dataset = Catalog(root_dir="...").create_dataset("my_dataset", ...)
    return (dataset,)

# 3. Explanation markdown (discusses what happened)
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What just happened?**

    - Kirin created a new dataset with a unique name
    - The dataset is ready to accept files
    - We can now start adding files to track changes
    """)
    return
```

**Tutorial Guidelines**:

- **Start with "What You'll Learn"** - Set expectations upfront
- **Include Prerequisites** - List what users need to know/have
- **Progressive Complexity** - Start simple, build to more complex concepts
- **Concept Explanations** - Include sections that explain underlying
  concepts (not just numbered steps)
- **Rich Explanations** - Explain both what to do and why it matters
- **Learning Outcomes** - Each step should teach something new
- **Summary Section** - End with a summary of what was learned

#### How-To Guides (`docs/how-to/`)

**Purpose**: Task-oriented guides that help users accomplish specific goals
efficiently. Assume users know the basics.

**Key Characteristics**:

- **Task-Oriented**: Focus on helping users achieve specific goals
- **Assume Competence**: Target users familiar with Kirin basics
- **Concise**: Provide clear sequences without unnecessary explanations
- **Action-Focused**: Emphasize "how" over "why"
- **Modular**: Steps can be more independent (less sequential dependency)

**Writing Pattern**:

```python
# ✅ CORRECT - How-to guide structure
# 1. Brief task description (what you'll accomplish)
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Track Model Training Data

    This guide shows you how to version control your machine learning models
    and training data using Kirin.
    """)
    return

# 2. Direct code implementation (how to do it)
@app.cell
def _():
    from kirin import Dataset
    model_registry = Dataset(root_dir="...", name="sentiment_classifier")
    # Create and commit model files
    commit_hash = model_registry.commit(
        message="Initial model v1.0",
        add_files=["model.pkl", "training_data.csv"],
    )
    return (commit_hash, model_registry)

# 3. Brief outcome note (what happened, if needed)
@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Your model and training data are now versioned. You can track changes
    over time and compare different model versions.
    """)
    return
```

**How-To Guide Guidelines**:

- **Clear Task Title** - State exactly what the guide accomplishes
- **Minimal Prerequisites** - Assume users know basics (link to tutorials
  if needed)
- **Direct Instructions** - Get to the point quickly
- **Actionable Steps** - Focus on what to do, not extensive explanations
- **Brief Context** - Only include essential background information
- **Link to Explanations** - Reference tutorials or reference docs for
  deeper understanding
- **Outcome-Focused** - Emphasize the result, not the learning process

#### Comparison Table

| Aspect | Tutorials | How-To Guides |
|--------|-----------|---------------|
| **Purpose** | Teach concepts | Accomplish tasks |
| **Audience** | Beginners | Users with basics |
| **Structure** | Sequential, narrative | Task-focused, modular |
| **Explanations** | Rich, explain "why" | Concise, focus on "how" |
| **Concept Sections** | Common (explain concepts) | Rare (link to explanations) |
| **Prerequisites** | Detailed list | Minimal (assume competence) |
| **Summary** | Learning outcomes | Task completion |

### Validation Requirements

**MANDATORY**: All Marimo notebooks must:

1. **Pass `uvx marimo check`** - Run `uvx marimo check <notebook.py>` and
   fix all errors
2. **Run successfully with `uv run`** - Execute `uv run <notebook.py>` to
   verify the notebook runs correctly as a script and produces expected output
3. **Follow cell dependency rules** - No circular dependencies, all variables
   properly returned
4. **Use `hide_code=True`** - For all markdown-only cells
5. **No docstrings** - In any `@app.cell` functions
6. **Descriptive variable names** - No underscore prefixes, clear and
   informative names
7. **Interleaved structure** - Markdown explanations before code
8. **Proper returns** - All cells return variables needed by subsequent cells
9. **Appropriate style** - Follow tutorial or how-to guide patterns based on
   file location (`docs/tutorials/` vs `docs/how-to/`)

## Testing Guidelines

**CRITICAL**: Always write tests FIRST before implementing functionality.
This project follows Test-Driven Development (TDD).

When writing tests for the project:

- **Always write tests FIRST** - Write tests before implementation code
- **TDD Workflow**: Write test → Run test (should fail) → Implement → Run
  test (should pass) → Refactor
- **Always write tests in the test suite** - Place test files in the
  `/tests/` directory following the existing naming conventions
- **Use the test environment** - Always run tests with `pixi run -e tests
  pytest` or `pixi run -e tests pytest tests/test_filename.py`
- **Test new functionality immediately** - Write tests for new features
  before or alongside implementation
- **Follow existing test patterns** - Use the same structure and naming
  conventions as existing tests in the test suite
- **Use pytest function style only** - Write tests as functions, not
  classes. Use `def test_function_name():` pattern
- **No test classes** - Avoid `class TestSomething:` patterns. Use
  function-based tests with descriptive names
- **PyTest Style Only** - All tests must be written with PyTest style test
  functions, NOT UnitTest test style classes

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

**CRITICAL**: All tests must be written in **pytest function style**, NOT
unittest class style. Use `def test_function_name():` pattern, not
`class TestSomething:` patterns.

**Benefits of pytest-style functions**:

- **Simpler structure** - No class overhead, just functions
- **Easier to read** - More straightforward test organization
- **Better pytest integration** - Follows pytest best practices
- **Cleaner output** - Test names are more direct in pytest output
- **Easier maintenance** - Less boilerplate code

**Documentation and Examples**:

- **Tests are the primary demonstration** - Tests serve as the main way to
  show functionality and usage patterns
- **No example scripts needed** - Do not create standalone example scripts
  to demonstrate functionality
- **Comprehensive test coverage** - Write tests that cover both basic usage
  and edge cases
- **Test documentation** - Use descriptive test names and docstrings to
  explain what each test demonstrates
- **Real-world scenarios** - Write tests that reflect actual usage patterns
  and workflows

## Test Suite Maintenance and API Evolution

### Test-Driven Development and API Consistency

**CRITICAL**: The test suite serves as the primary documentation for the
current API. When APIs evolve, tests must be updated to reflect the current
implementation, not the historical one.

**Key Principles**:

- **Tests Document Current API**: Tests should always reflect the current
  implementation, not outdated interfaces
- **API Evolution Tracking**: When APIs change, update tests immediately to
  prevent confusion
- **Remove Obsolete Tests**: Delete tests for functionality that no longer
  exists rather than keeping broken tests
- **Consistent Parameter Names**: Ensure test code uses the same parameter
  names as the actual implementation

### Common API Evolution Issues

**Dataset Constructor Changes**:

- **Old API**: `Dataset(root_dir=path, dataset_name="name")`
- **Current API**: `Dataset(root_dir=path, name="name")`
- **Fix**: Update all test fixtures and constructor calls to use `name`
  parameter

**Commit Method Changes**:

- **Old API**: `dataset.commit(commit_message="msg", add_files=file)`
- **Current API**: `dataset.commit(message="msg", add_files=[file])`
- **Fix**: Update all commit calls to use `message` parameter and ensure
  `add_files` is a list

**Property Name Changes**:

- **Old API**: `dataset.file_dict`, `dataset.dataset_name`
- **Current API**: `dataset.files`, `dataset.name`
- **Fix**: Update all property references to use current names

**Method Signature Changes**:

- **Old API**: `dataset.get_file_content(filename)`,
  `dataset.download_file(filename)`
- **Current API**: `dataset.read_file(filename)`,
  `dataset.download_file(filename, target_path)`
- **Fix**: Update method calls to match current signatures

### Test Fixing Workflow

**Systematic Approach**:

1. **Run Full Test Suite**: Get overview of all failures with `pixi run -e
   tests python -m pytest tests/ --tb=no -q`
2. **Identify Patterns**: Look for common error types (TypeError,
   AttributeError, etc.)
3. **Fix by Category**: Address similar issues together (e.g., all Dataset
   constructor issues)
4. **Verify Progress**: Re-run tests to confirm improvements
5. **Document Changes**: Note what was fixed for future reference

**Common Error Patterns**:

- **TypeError: unexpected keyword argument**: Usually means parameter name
  changed
- **AttributeError: object has no attribute**: Usually means property/method
  name changed
- **ImportError: cannot import name**: Usually means class/function was
  removed or renamed
- **AssertionError**: Usually means test logic needs updating for new API

### Test Suite Health Metrics

**Progress Tracking**:

- **Before Fixes**: Track total failed vs passing tests
- **After Each Category**: Measure improvement (e.g., "reduced failures
  from 45 to 26")
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

- **Non-existent Functionality**: Tests for classes/methods that no longer
  exist
- **Architectural Changes**: Tests for removed features (e.g., branching,
  complex lineage)
- **API Simplification**: Tests for functionality that was intentionally
  removed

**Removal Process**:

1. **Verify Obsolescence**: Confirm functionality truly doesn't exist
2. **Check Dependencies**: Ensure no other tests depend on removed
  functionality
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

- **Run Tests Frequently**: Use `pixi run -e tests python -m pytest`
  regularly
- **Fix Immediately**: Don't let test failures accumulate
- **Update Documentation**: Keep test documentation current with API
  changes
- **Monitor Dependencies**: Ensure test dependencies are properly managed

**Prevention Strategies**:

- **API Consistency**: Use consistent naming across all components
- **Comprehensive Testing**: Test both success and failure cases
- **Clear Documentation**: Document API changes clearly
- **Version Control**: Track API evolution through git history

**Quality Assurance**:

- **All Tests Pass**: Zero tolerance for failing tests in main branch
- **Clear Error Messages**: Tests should provide helpful failure
  information
- **Maintainable Code**: Tests should be easy to understand and modify
- **Performance**: Tests should run quickly and efficiently

## Design Document Reference

### Code Changes and Design Alignment

**CRITICAL**: When making changes to the codebase, always refer back to the
design document (`docs/design.md`) and explicitly mention where in the
design document the choice was made. This ensures:

- **Design Consistency**: All implementation decisions align with the
  documented architecture
- **Design Evolution**: Real usage patterns can inform design document
  updates
- **Traceability**: Clear connection between design decisions and
  implementation
- **Documentation Maintenance**: Design document stays current with actual
  usage

**Required Process**:

1. **Before Making Changes**: Review the relevant sections of
   `docs/design.md`
2. **During Implementation**: Reference specific design document sections
  that justify the approach
3. **After Changes**: Note any discrepancies between design and
  implementation that may require design document updates
4. **Design Document Updates**: When real usage reveals design issues,
  update the design document accordingly

**Example Reference Format**:

```text
This implementation follows the design document's approach for [specific feature]
as outlined in section [X.Y] of docs/design.md, which specifies [specific design
decision]. However, real usage has revealed [specific issue], suggesting we may
need to update the design document to reflect [proposed change].
```

This process ensures the design document remains a living document that
accurately reflects both the intended architecture and the lessons learned
from actual implementation and usage.

## SSL Certificate Management in Isolated Python Environments

**CRITICAL**: When using isolated Python environments (pixi, uv, venv,
conda), SSL certificates are not automatically available. This affects
HTTPS connections to cloud storage providers.

### The Problem

- **System Python**: Has SSL certificates from system installation
- **Isolated Environments**: pixi, uv, venv, conda environments lack system
  SSL certificates
- **Result**: HTTPS connections fail with `SSLCertVerificationError`

### The Solution

**Automatic Setup (Recommended)**:

```bash
# Works with any Python environment - detects automatically
python -m kirin.setup_ssl
```

**Manual Setup** (if automatic setup fails):

```bash
# The automatic setup script handles this automatically
# But if you need to do it manually, use the Python executable path:
python -c "import sys; print('Python path:', sys.executable)"
# Then create ssl directory next to that path and copy certificates
```

**For Global Tool Installs**:

- `pixi global install <tool>` creates separate environments
- `uv tool install <tool>` also creates isolated environments
- Each tool environment may need SSL certificates copied separately
- SSL certificate path is environment-specific and not shared

### Installation Impact

**For End Users**:

- **Local Development**: Run `python -m kirin.setup_ssl` once per
  environment
- **Global Tools**: Each tool installation may need separate SSL
  certificate setup
- **Production**: Use system Python or ensure SSL certificates are
  available in deployment environment

**Best Practices**:

- Document SSL certificate requirements in installation instructions
- Provide setup scripts for common environments
- Consider using system Python for production deployments
- Test HTTPS connections in all target environments

### Verification

```bash
# Check SSL paths in any Python environment
python -c "import ssl; print(ssl.get_default_verify_paths())"

# Test HTTPS connection
python -c "import requests; r = requests.get('https://storage.googleapis.com'); print('HTTPS works:', r.status_code)"

# Or use the automatic setup
python -m kirin.setup_ssl
```

## Documentation Standards

### Writing Style Guidelines

**CRITICAL**: When writing documentation, sacrifice grammar for concision.
This means:

- **Prioritize clarity over perfect grammar** - Use incomplete sentences if
  they're clearer
- **Use bullet points and fragments** - Don't force complete sentences
  everywhere
- **Be direct and concise** - Get to the point quickly without unnecessary
  words
- **Use active voice** - "Do this" instead of "This should be done"
- **Break rules for readability** - Grammar rules can be bent for better
  understanding

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

All Markdown documentation in the project must follow **Markdownlint** rules
for consistency and quality. This ensures:

- **Consistent formatting** across all documentation files
- **Improved readability** for developers and contributors
- **Automated linting** can catch style issues early
- **Professional appearance** in rendered documentation

**Required**: All Markdown files must pass Markdownlint validation with
zero errors.

**Installation and Usage**:

- The user already has `markdownlint-cli` installed - only offer to install
  it if it's not available
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

**Required Workflow**: Run markdownlint on any Markdown file that is
created or edited before committing changes.

**CRITICAL**: Always run markdownlint on any markdown file edits to ensure
consistency and quality. This is mandatory for all markdown file changes.

**MANDATORY PROCESS**:

1. **Run markdownlint CLI**: Always run `markdownlint <filename>` on every
   Markdown file that is edited
2. **Fix ALL issues**: Every single issue that markdownlint reports must be
   fixed
3. **Zero tolerance**: No markdownlint errors are acceptable - all must be
   resolved
4. **Re-run until clean**: Continue running markdownlint until the file
   passes with zero errors
5. **Run pre-commit**: Always run `pre-commit run --all-files` to ensure all
   files (including markdown) pass validation
6. **Before committing**: Never commit a Markdown file that has markdownlint
   errors or pre-commit failures

**BULK LINTING**: When working on multiple Markdown files, run markdownlint
on all files at once to identify issues across the entire documentation
set:

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

**CRITICAL**: After major architectural changes, always clean up
unnecessary files to maintain a clean repository.

**Files to Remove After Architecture Changes**:

- **Build artifacts**: Remove `build/`, `*.egg-info/` directories
- **Temporary files**: Remove temporary files created during development
  (e.g., `*_new.py`)
- **Outdated documentation**: Remove docs for features that no longer exist
  (e.g., `branching.md`)
- **Outdated scripts**: Remove scripts that test removed functionality (e.g.,
  branch switching, git semantics)
- **Outdated tests**: Remove test files that import removed classes or test
  removed functionality
- **Dummy files**: Remove test dummy files that are no longer needed
- **Backup files**: Remove `.bak` files and other backup artifacts

**Cleanup Process**:

1. **Identify outdated files** - Look for files referencing removed
  functionality
2. **Check file contents** - Verify files are actually outdated, not just
  renamed
3. **Remove systematically** - Delete files one by one to avoid mistakes
4. **Verify removal** - Ensure no imports or references are broken
5. **Update documentation** - Remove references to deleted files in docs

**Common Outdated Files After Simplification**:

- Scripts testing branch/merge functionality
- Documentation for removed features
- Test files importing removed classes
- Build artifacts from old architecture
- Temporary development files

## Bug Fix Requirements

### Tests and Documentation for Every Bug Fix

**CRITICAL**: For every bug fix we introduce, make sure to add tests and
documentation. This ensures:

- **Regression Prevention**: Tests catch if the bug returns
- **Validation**: Tests prove the fix actually works
- **Documentation**: Clear record of what was fixed and why
- **Future Maintenance**: Other developers understand the fix

**Required Process**:

1. **Write Tests First** - Create tests that reproduce the bug and verify
  the fix
2. **Add Documentation** - Update relevant docs to explain the fix
3. **Verify Tests Pass** - Ensure all tests pass with the fix
4. **Update Examples** - If applicable, update usage examples

**Test Requirements**:

- **Reproduce Bug**: Test should fail before fix, pass after fix
- **Edge Cases**: Test related scenarios that might break
- **Integration**: Test the fix in context of full system
- **Performance**: If fix affects performance, add performance tests

**Documentation Requirements**:

- **Bug Description**: What was broken and why
- **Fix Explanation**: How the fix works
- **Prevention**: How to avoid similar bugs
- **Examples**: Show correct usage patterns

## Solution Design Approach

### Propose Solutions First, Then Discuss

**CRITICAL**: When working on building solutions, the user prefers that you
propose a solution in chat first for critique, rather than asking
questions. This approach:

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

## GitHub Issue Creation Guidelines

### Plan Mode Issue Body Content

**CRITICAL**: When in plan mode and creating a GitHub issue, create the
issue body content directly instead of using a file. This approach:

- **Streamlines workflow** - Avoids unnecessary file creation and management
- **Direct content creation** - Write issue body content directly in the
  tool call
- **Cleaner process** - No temporary files to clean up after issue
  creation
- **Faster execution** - Direct content creation is more efficient

**Required Pattern**:

1. **Analyze requirements** - Understand what the issue needs to document
2. **Create content directly** - Write the issue body content in the tool
  call parameters
3. **Use markdown formatting** - Structure the content with proper markdown
  for GitHub
4. **Include all necessary details** - Ensure the issue body contains all
  required information

**Example**:

```bash
# Instead of creating a file first, write content directly:
gh issue create \
  --title "Implement file metadata structure" \
  --body "## Problem

Current file handling lacks proper metadata...

## Solution

Implement File entity with...

## Acceptance Criteria

- [ ] File entity created
- [ ] Metadata properties defined
- [ ] Tests written"
```
