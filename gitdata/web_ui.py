"""Web UI for gitdata using FastAPI and HTMX."""

import os
import random
import shutil
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from gitdata.dataset import (
    Dataset,
    DatasetNoCommitsError,
    strip_protocol,
)

# Configure loguru
logger.remove()  # Remove default handler
logger.add(
    lambda msg: print(msg, end=""),
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>"
    ),
    level="INFO",
)


@contextmanager
def perf_timer(operation_name: str, logger_instance=None):
    """Context manager for timing operations with detailed logging."""
    if logger_instance is None:
        logger_instance = logger

    start_time = time.time()
    logger_instance.info(f"PERF: Starting {operation_name}")

    try:
        yield
    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger_instance.info(f"PERF: Completed {operation_name} in {duration:.3f}s")


# Create FastAPI app
app = FastAPI(title="GitData UI")

# Get the directory where this file is located
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Create directories if they don't exist
TEMPLATES_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Set up Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Global state to store the current dataset
current_dataset: Optional[Dataset] = None

# Commit history cache: {(dataset_name, root_dir): (commits_list, timestamp)}
commit_cache = {}
CACHE_TTL = 1800  # 30 minutes cache (increased from 5 minutes)

# File dictionary cache: {(dataset_name, root_dir, commit_hash): (file_dict, timestamp)}
file_dict_cache = {}
FILE_CACHE_TTL = 600  # 10 minutes cache


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the index page with dataset URL input."""
    logger.info("Rendering index page")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "dataset_loaded": current_dataset is not None,
            "dataset_url": current_dataset.root_dir if current_dataset else "",
            "dataset_name": current_dataset.dataset_name if current_dataset else "",
        },
    )


@app.post("/load-dataset")
async def load_dataset(request: Request):
    """Load a dataset from the provided URL."""
    global current_dataset

    form = await request.form()
    dataset_url = form.get("dataset_url")
    dataset_name = form.get("dataset_name")

    logger.info(f"Loading dataset: name='{dataset_name}', url='{dataset_url}'")

    if not dataset_url or not dataset_name:
        logger.warning("Dataset URL and name are required but not provided")
        raise HTTPException(status_code=400, detail="Dataset URL and name are required")

    try:
        logger.info(f"Initializing Dataset object for '{dataset_name}'")
        with perf_timer(f"Dataset initialization for '{dataset_name}'"):
            current_dataset = Dataset(root_dir=dataset_url, dataset_name=dataset_name)
        logger.info(f"Successfully loaded dataset '{dataset_name}'")

        # Redirect to the direct dataset URL for bookmarkability
        from urllib.parse import quote

        redirect_url = f"/d/{quote(dataset_name)}?url={quote(dataset_url)}"
        content = f'<script>window.location.href = "{redirect_url}";</script>'
        return HTMLResponse(content=content, status_code=200)
    except Exception as e:
        logger.error(
            f"Error loading dataset '{dataset_name}' from '{dataset_url}': {e}",
            exc_info=True,
        )
        error_msg = (
            f'<div class="alert alert-error" role="alert">'
            f"Error loading dataset: {str(e)}</div>"
        )
        return HTMLResponse(content=error_msg, status_code=400)


@app.get("/d/{dataset_name}", response_class=HTMLResponse)
async def dataset_direct(
    request: Request, dataset_name: str, url: str = None, commit: str = None
):
    """Direct access to a dataset via URL.

    Usage: /d/my-dataset?url=/path/to/data&commit=abc123
    """
    global current_dataset

    logger.info(f"Direct dataset access: {dataset_name}, url={url}, commit={commit}")

    if url is None:
        # Try to use current dataset if name matches
        if current_dataset and current_dataset.dataset_name == dataset_name:
            logger.info(f"Using already loaded dataset: {dataset_name}")
            # If commit specified, checkout that commit
            if commit:
                logger.info(f"Checking out commit: {commit}")
                current_dataset.checkout(commit)
            return await dataset_view(request)
        else:
            raise HTTPException(
                status_code=400,
                detail="Dataset URL required. Use: /d/{name}?url=/path/to/data",
            )

    try:
        # Check if we already have this dataset loaded
        if (
            current_dataset
            and current_dataset.dataset_name == dataset_name
            and current_dataset.root_dir == url
        ):
            logger.info(f"Reusing already loaded dataset: {dataset_name}")
        else:
            # Load the dataset
            logger.info(f"Loading dataset via direct URL: {dataset_name} from {url}")
            with perf_timer(f"Dataset loading for '{dataset_name}' from {url}"):
                current_dataset = Dataset(root_dir=url, dataset_name=dataset_name)
            logger.info(f"Dataset '{dataset_name}' loaded successfully")

        # If commit specified, checkout that commit
        if commit:
            logger.info(f"Checking out commit: {commit}")
            current_dataset.checkout(commit)

        # Redirect to dataset view
        return await dataset_view(request)
    except Exception as e:
        logger.error(
            f"Error loading dataset '{dataset_name}' from '{url}': {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail=f"Error loading dataset: {str(e)}",
        )


@app.get("/dataset-view", response_class=HTMLResponse)
async def dataset_view(request: Request):
    """Render the main dataset view with commits and files."""
    logger.info("Rendering dataset view")
    if current_dataset is None:
        logger.warning("Attempted to view dataset but no dataset is loaded")
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        # Get all commits (cached)
        logger.info(f"Fetching commits for dataset '{current_dataset.dataset_name}'")
        with perf_timer(f"Commits loading for '{current_dataset.dataset_name}'"):
            all_commits = get_all_commits(current_dataset)
        logger.info(f"Found {len(all_commits)} commits total")

        # Show only first 5 commits initially
        initial_commits = all_commits[:5]
        has_more = len(all_commits) > 5
        logger.info(f"Showing {len(initial_commits)} initial commits")

        # Get files from current commit (using cached file dict)
        files = []
        if current_dataset.current_commit.file_hashes:
            logger.info(
                f"Fetching file list for current commit "
                f"({current_dataset.current_version_hash()[:8]})"
            )
            with perf_timer(
                f"File list loading for commit {current_dataset.current_version_hash()[:8]}"
            ):
                file_dict = get_cached_file_dict(current_dataset)
                files = [
                    {"name": name, "path": path} for name, path in file_dict.items()
                ]
            logger.info(f"Found {len(files)} files in current commit")
        else:
            logger.info("Current commit has no files")

        logger.info(f"PERF: Rendering dataset view template")
        start_time = time.time()
        response = templates.TemplateResponse(
            "dataset_view.html",
            {
                "request": request,
                "dataset_name": current_dataset.dataset_name,
                "dataset_url": current_dataset.root_dir,
                "current_commit_hash": current_dataset.current_version_hash()[:8],
                "current_branch": current_dataset.get_current_branch(),
                "commits": initial_commits,
                "files": files,
                "has_more_commits": has_more,
                "commits_loaded": len(initial_commits),
            },
        )
        end_time = time.time()
        logger.info(f"PERF: Template rendering took {end_time - start_time:.3f}s")
        return response
    except Exception as e:
        logger.error(f"Error loading dataset view: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error loading dataset view: {str(e)}"
        )


@app.get("/commits", response_class=HTMLResponse)
async def get_commits(request: Request, offset: int = 0, limit: int = 10):
    """Get paginated list of commits (for HTMX infinite scroll)."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        logger.info(f"Loading commits: offset={offset}, limit={limit}")
        all_commits = get_all_commits(current_dataset)

        # Paginate
        paginated_commits = all_commits[offset : offset + limit]
        has_more = (offset + limit) < len(all_commits)

        logger.info(f"Returning {len(paginated_commits)} commits, has_more={has_more}")

        return templates.TemplateResponse(
            "commits_pagination.html",
            {
                "request": request,
                "commits": paginated_commits,
                "current_commit_hash": current_dataset.current_version_hash(),
                "offset": offset + limit,
                "has_more": has_more,
            },
        )
    except Exception as e:
        logger.error(f"Error loading commits: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error loading commits: {str(e)}")


@app.get("/commit/{commit_hash}/files", response_class=HTMLResponse)
async def get_commit_files(request: Request, commit_hash: str):
    """Get files for a specific commit."""
    logger.info(f"Fetching files for commit {commit_hash[:8]}")
    if current_dataset is None:
        logger.warning("Attempted to fetch commit files but no dataset is loaded")
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        # Checkout the commit
        logger.info(f"Checking out commit {commit_hash[:8]}")
        current_dataset.checkout(commit_hash)

        # Debug: Log commit details
        logger.info(
            f"Commit {commit_hash[:8]} details: "
            f"message='{current_dataset.current_commit.commit_message}', "
            f"file_hashes={len(current_dataset.current_commit.file_hashes)}, "
            f"hashes={current_dataset.current_commit.file_hashes}"
        )

        # Get files using cached file dictionary
        files = []
        if current_dataset.current_commit.file_hashes:
            logger.info(f"Listing files for commit {commit_hash[:8]}")
            import time

            start_time = time.time()
            file_dict = get_cached_file_dict(current_dataset, commit_hash)
            end_time = time.time()
            logger.info(
                f"File dict retrieval took {end_time - start_time:.3f}s "
                f"for commit {commit_hash[:8]}"
            )
            files = [{"name": name, "path": path} for name, path in file_dict.items()]
            logger.info(
                f"Found {len(files)} files in commit {commit_hash[:8]}: "
                f"{list(file_dict.keys())}"
            )
        else:
            logger.info(f"Commit {commit_hash[:8]} has no files")

        return templates.TemplateResponse(
            "files_list.html",
            {
                "request": request,
                "files": files,
                "commit_hash": commit_hash[:8],
            },
        )
    except Exception as e:
        logger.error(
            f"Error loading files for commit {commit_hash[:8]}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Error loading files: {str(e)}")


@app.get("/file/preview", response_class=HTMLResponse)
async def preview_file(request: Request, filename: str):
    """Preview a file (text-based only)."""
    logger.info(f"Previewing file: {filename}")
    if current_dataset is None:
        logger.warning("Attempted to preview file but no dataset is loaded")
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        file_dict = current_dataset.file_dict
        if filename not in file_dict:
            logger.warning(f"File not found: {filename}")
            raise HTTPException(status_code=404, detail="File not found")

        file_path = file_dict[filename]
        logger.info(f"Reading file from path: {file_path}")

        # Try to read as text
        try:
            with current_dataset.fs.open(strip_protocol(file_path), "r") as f:
                content = f.read()

            original_size = len(content)
            # Limit preview to first 10000 characters
            if len(content) > 10000:
                truncated_msg = "\n\n... (truncated, file is too large)"
                content = content[:10000] + truncated_msg
                logger.info(
                    f"File '{filename}' truncated from {original_size} to 10000 chars"
                )
            else:
                logger.info(f"File '{filename}' loaded ({original_size} chars)")

            return templates.TemplateResponse(
                "file_preview.html",
                {
                    "request": request,
                    "filename": filename,
                    "content": content,
                    "is_text": True,
                },
            )
        except UnicodeDecodeError:
            # Binary file
            logger.info(f"File '{filename}' is binary, cannot preview as text")
            return templates.TemplateResponse(
                "file_preview.html",
                {
                    "request": request,
                    "filename": filename,
                    "content": None,
                    "is_text": False,
                },
            )
    except Exception as e:
        logger.error(f"Error previewing file '{filename}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error previewing file: {str(e)}")


@app.get("/commit", response_class=HTMLResponse)
async def commit_page(request: Request):
    """Render the commit page for file management."""
    logger.info("Rendering commit page")
    if current_dataset is None:
        logger.warning("Attempted to access commit page but no dataset is loaded")
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        # Get current files
        files = []
        if current_dataset.current_commit.file_hashes:
            logger.info("Fetching current files for commit page")
            file_dict = current_dataset.file_dict
            files = [{"name": name, "path": path} for name, path in file_dict.items()]
            logger.info(f"Found {len(files)} files in current commit")
        else:
            logger.info("Current commit has no files")

        return templates.TemplateResponse(
            "commit.html",
            {
                "request": request,
                "dataset_name": current_dataset.dataset_name,
                "dataset_url": current_dataset.root_dir,
                "current_commit_hash": current_dataset.current_version_hash()[:8],
                "files": files,
            },
        )
    except Exception as e:
        logger.error(f"Error loading commit page: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error loading commit page: {str(e)}"
        )


@app.post("/commit-files", response_class=HTMLResponse)
async def commit_files(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    commit_message: str = Form(...),
    remove_files: list[str] = Form([]),
):
    """Add files and commit them to the dataset."""
    logger.info(
        f"Adding {len(files)} files, removing {len(remove_files)} files "
        f"with message: {commit_message}"
    )
    if current_dataset is None:
        logger.warning("Attempted to commit files but no dataset is loaded")
        raise HTTPException(status_code=400, detail="No dataset loaded")

    # Validate that at least one operation is specified
    if not files and not remove_files:
        logger.warning("No files to add or remove specified")
        raise HTTPException(
            status_code=400,
            detail="At least one file must be added or removed for a commit",
        )

    try:
        temp_paths = []
        temp_dir = None

        # Handle file uploads if any
        if files:
            # Create temporary directory for uploaded files
            temp_dir = tempfile.mkdtemp()
            try:
                # Save files to temporary directory
                for file in files:
                    if file.filename:
                        temp_path = os.path.join(temp_dir, file.filename)
                        temp_paths.append(temp_path)

                        # Write file content
                        with open(temp_path, "wb") as f:
                            content = await file.read()
                            f.write(content)

                        logger.info(
                            f"Saved file: {file.filename} ({len(content)} bytes)"
                        )

                # Commit changes to dataset
                logger.info(
                    f"Committing {len(temp_paths)} files to add, "
                    f"{len(remove_files)} files to remove"
                )
                current_dataset.commit(
                    commit_message=commit_message,
                    add_files=temp_paths if temp_paths else None,
                    remove_files=remove_files if remove_files else None,
                )

                # Clear commit cache after successful commit
                cache_key = (current_dataset.dataset_name, current_dataset.root_dir)
                if cache_key in commit_cache:
                    del commit_cache[cache_key]
                    logger.info(
                        f"Cleared commit cache for dataset: "
                        f"{current_dataset.dataset_name}"
                    )
            finally:
                # Clean up temporary directory
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
        else:
            # No files to upload, just commit removals
            logger.info(
                f"Committing {len(temp_paths)} files to add, "
                f"{len(remove_files)} files to remove"
            )
            current_dataset.commit(
                commit_message=commit_message,
                add_files=temp_paths if temp_paths else None,
                remove_files=remove_files if remove_files else None,
            )

            # Clear commit cache after successful commit
            cache_key = (current_dataset.dataset_name, current_dataset.root_dir)
            if cache_key in commit_cache:
                del commit_cache[cache_key]
                logger.info(
                    f"Cleared commit cache for dataset: {current_dataset.dataset_name}"
                )

        action_summary = []
        if temp_paths:
            action_summary.append(f"added {len(temp_paths)} files")
        if remove_files:
            action_summary.append(f"removed {len(remove_files)} files")

        logger.info(f"Successfully committed changes: {', '.join(action_summary)}")

        # Clear caches after successful commit
        cache_key = (current_dataset.dataset_name, current_dataset.root_dir)
        if cache_key in commit_cache:
            del commit_cache[cache_key]
            logger.info(
                f"Cleared commit cache for dataset: {current_dataset.dataset_name}"
            )

        # Clear file dict cache for this dataset
        keys_to_remove = [key for key in file_dict_cache.keys() if key[:2] == cache_key]
        for key in keys_to_remove:
            del file_dict_cache[key]
        if keys_to_remove:
            logger.info(
                f"Cleared {len(keys_to_remove)} file dict cache entries "
                f"for dataset: {current_dataset.dataset_name}"
            )

        # Clear dataset's internal caches
        if hasattr(current_dataset, "_commits_data_cache"):
            current_dataset._commits_data_cache = None
            logger.info(
                f"Cleared commits data cache for dataset: {current_dataset.dataset_name}"
            )
        if hasattr(current_dataset, "_latest_version_hash_cache"):
            current_dataset._latest_version_hash_cache = None
            logger.info(
                f"Cleared latest version hash cache for dataset: {current_dataset.dataset_name}"
            )

        # Return success message
        success_html = f"""
        <div class="bg-green-50 border border-green-200 rounded-md p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20"
                         fill="currentColor">
                        <path fill-rule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 "
                              "00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 "
                              "00-1.414 1.414l2 2a1 1 0 "
                              "001.414 0l4-4z"
                              clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-green-800">
                        Successfully committed changes!
                    </h3>
                    <div class="mt-2 text-sm text-green-700">
                        <p>Actions: {", ".join(action_summary) if action_summary else "No changes"}</p>
                        <p>Commit message: {commit_message}</p>
                        <p>New commit hash: {current_dataset.current_version_hash()[:8]}</p>
                    </div>
                    <div class="mt-4">
                        <a href="/dataset-view"
                           class="text-sm font-medium text-green-800 hover:text-green-600">
                            View Dataset →
                        </a>
                    </div>
                    <div class="mt-3 text-sm text-green-600">
                        <p id="redirect-notification">Redirecting to dataset in <span id="countdown">5</span> seconds...</p>
                    </div>
                </div>
            </div>
        </div>
        <script>
            let countdown = 5;
            const countdownElement = document.getElementById('countdown');
            const redirectNotification = document.getElementById('redirect-notification');

            const timer = setInterval(() => {{
                countdown--;
                countdownElement.textContent = countdown;

                if (countdown <= 0) {{
                    clearInterval(timer);
                    window.location.href = '/dataset-view';
                }}
            }}, 1000);
        </script>
        """
        return HTMLResponse(content=success_html, status_code=200)

    except Exception as e:
        logger.error(f"Error committing files: {e}", exc_info=True)
        error_html = f"""
        <div class="bg-red-50 border border-red-200 rounded-md p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20"
                         fill="currentColor">
                        <path fill-rule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                              clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">
                        Error committing files
                    </h3>
                    <div class="mt-2 text-sm text-red-700">
                        <p>{str(e)}</p>
                    </div>
                </div>
            </div>
        </div>
        """
        return HTMLResponse(content=error_html, status_code=400)


@app.post("/remove-file", response_class=HTMLResponse)
async def remove_file(
    request: Request,
    filename: str = Form(...),
    commit_message: str = Form(...),
):
    """Remove a file from the dataset."""
    logger.info(f"Removing file: {filename} with message: {commit_message}")
    if current_dataset is None:
        logger.warning("Attempted to remove file but no dataset is loaded")
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        # Check if file exists
        file_dict = current_dataset.file_dict
        if filename not in file_dict:
            logger.warning(f"File not found: {filename}")
            raise HTTPException(status_code=404, detail="File not found")

        # Remove file from dataset
        logger.info(f"Removing file '{filename}' from dataset")
        current_dataset.commit(
            commit_message=commit_message,
            remove_files=[filename],
        )

        # Clear commit cache after successful commit
        cache_key = (current_dataset.dataset_name, current_dataset.root_dir)
        if cache_key in commit_cache:
            del commit_cache[cache_key]
            logger.info(
                f"Cleared commit cache for dataset: {current_dataset.dataset_name}"
            )

        logger.info(f"Successfully removed file '{filename}'")

        # Return success message
        success_html = f"""
        <div class="bg-green-50 border border-green-200 rounded-md p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                        <svg class="h-5 w-5 text-green-400" viewBox="0 0 20 20"
                             fill="currentColor">
                            <path fill-rule="evenodd"
                                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                  clip-rule="evenodd" />
                        </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-green-800">
                        Successfully removed file!
                    </h3>
                    <div class="mt-2 text-sm text-green-700">
                        <p>File: {filename}</p>
                        <p>Commit message: {commit_message}</p>
                        <p>New commit hash: {current_dataset.current_version_hash()[:8]}</p>
                    </div>
                    <div class="mt-4">
                        <a href="/dataset-view"
                           class="text-sm font-medium text-green-800 hover:text-green-600">
                            View Dataset →
                        </a>
                    </div>
                </div>
            </div>
        </div>
        """
        return HTMLResponse(content=success_html, status_code=200)

    except Exception as e:
        logger.error(f"Error removing file '{filename}': {e}", exc_info=True)
        error_html = f"""
        <div class="bg-red-50 border border-red-200 rounded-md p-4">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20"
                         fill="currentColor">
                        <path fill-rule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                              clip-rule="evenodd" />
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">
                        Error removing file
                    </h3>
                    <div class="mt-2 text-sm text-red-700">
                        <p>{str(e)}</p>
                    </div>
                </div>
            </div>
        </div>
        """
        return HTMLResponse(content=error_html, status_code=400)


def get_all_commits(dataset: Dataset, use_cache: bool = True) -> list:
    """Get all commits for a dataset in chronological order.

    Uses caching to avoid re-reading commit files on every request.
    """
    cache_key = (dataset.dataset_name, dataset.root_dir)

    # Check cache first
    if use_cache and cache_key in commit_cache:
        cached_commits, timestamp = commit_cache[cache_key]
        age = time.time() - timestamp
        if age < CACHE_TTL:
            logger.debug(
                f"Using cached commits for {dataset.dataset_name} (age: {age:.1f}s)"
            )
            return cached_commits
        else:
            logger.debug(f"Cache expired for {dataset.dataset_name}")

    logger.debug(f"Retrieving commits for dataset: {dataset.dataset_name}")
    try:
        dataset_path = strip_protocol(dataset.dataset_dir)
        logger.debug(f"Searching for commit.json files in: {dataset_path}")

        # Use cached commits data to avoid duplicate file reads
        logger.info(f"PERF: Getting cached commits data for {dataset.dataset_name}")
        start_time = time.time()
        commits_dict = dataset._get_commits_data()
        end_time = time.time()
        logger.info(
            f"PERF: Getting cached commits data took {end_time - start_time:.3f}s"
        )

        if not commits_dict:
            logger.info("No commits found in dataset")
            return []

        logger.debug(f"Found {len(commits_dict)} commits")

        logger.debug(f"Parsed {len(commits_dict)} commits")

        # Build chronological order (from newest to oldest)
        ordered_commits = []

        # Find the latest commit (no one has it as parent)
        all_parents = {
            c["parent_hash"] for c in commits_dict.values() if c["parent_hash"]
        }
        latest = None
        for commit_hash in commits_dict.keys():
            if commit_hash not in all_parents:
                latest = commit_hash
                break

        logger.debug(f"Latest commit identified: {latest[:8] if latest else 'None'}")

        # Traverse from latest to earliest
        current = latest
        while current and current in commits_dict:
            commit_data = commits_dict[current]
            ordered_commits.append(
                {
                    "hash": current,
                    "short_hash": current[:8],
                    "message": commit_data.get("commit_message", "(initial)"),
                    "parent_hash": commit_data.get("parent_hash", ""),
                    "file_count": len(commit_data.get("file_hashes", [])),
                }
            )
            current = commit_data.get("parent_hash")
            if not current:  # Empty string means no parent
                break

        logger.debug(f"Ordered {len(ordered_commits)} commits chronologically")

        # Cache the results
        commit_cache[cache_key] = (ordered_commits, time.time())
        logger.debug(
            f"Cached {len(ordered_commits)} commits for {dataset.dataset_name}"
        )

        return ordered_commits
    except DatasetNoCommitsError:
        logger.info("Dataset has no commits yet")
        return []


def get_cached_file_dict(dataset: Dataset, commit_hash: str = None) -> dict:
    """Get file dictionary with caching to improve performance.

    :param dataset: The dataset to get files from
    :param commit_hash: Optional commit hash to get files from specific commit
    :return: Dictionary mapping filenames to file paths
    """
    if commit_hash is None:
        commit_hash = dataset.current_version_hash()

    cache_key = (dataset.dataset_name, dataset.root_dir, commit_hash)

    # Check cache first
    if cache_key in file_dict_cache:
        cached_dict, timestamp = file_dict_cache[cache_key]
        age = time.time() - timestamp
        if age < FILE_CACHE_TTL:
            logger.debug(
                f"Using cached file dict for {dataset.dataset_name} "
                f"commit {commit_hash[:8]} (age: {age:.1f}s)"
            )
            return cached_dict
        else:
            logger.debug(f"File dict cache expired for {dataset.dataset_name}")

    logger.debug(
        f"Building file dict for {dataset.dataset_name} commit {commit_hash[:8]}"
    )

    try:
        # Get file dictionary from dataset
        logger.info(f"PERF: Building file dict for commit {commit_hash[:8]}")
        start_time = time.time()

        if commit_hash == dataset.current_version_hash():
            file_dict = dataset.file_dict
        else:
            # Get file dict for specific commit
            commit = dataset.current_commit
            dataset.checkout(commit_hash)
            file_dict = dataset.file_dict
            dataset.checkout(commit.version_hash)  # Restore original commit

        end_time = time.time()
        logger.info(f"PERF: File dict building took {end_time - start_time:.3f}s")

        # Cache the results
        file_dict_cache[cache_key] = (file_dict, time.time())
        logger.debug(f"Cached file dict with {len(file_dict)} files")

        return file_dict
    except Exception as e:
        logger.error(f"Error building file dict: {e}")
        return {}


# Branch management routes
@app.get("/branches", response_class=HTMLResponse)
async def list_branches(request: Request):
    """List all branches for the current dataset."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        branches = current_dataset.list_branches()
        current_branch = current_dataset.get_current_branch()

        return templates.TemplateResponse(
            "branches_list.html",
            {
                "request": request,
                "branches": branches,
                "current_branch": current_branch,
                "dataset_name": current_dataset.dataset_name,
            },
        )
    except Exception as e:
        logger.error(f"Error listing branches: {e}", exc_info=True)
        error_html = (
            f'<div class="alert alert-error">Error listing branches: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=500)


@app.post("/branches/create")
async def create_branch(request: Request):
    """Create a new branch."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    form = await request.form()
    branch_name = form.get("branch_name")

    if not branch_name:
        raise HTTPException(status_code=400, detail="Branch name is required")

    try:
        # Create branch pointing to current commit
        current_commit = current_dataset.current_version_hash()
        current_dataset.create_branch(branch_name, current_commit)

        # Return success message
        success_html = f"""
        <div class="alert alert-success">
            Branch '{branch_name}' created successfully
        </div>
        <script>
            // Refresh the branches list
            htmx.trigger('#branches-list', 'refresh');
        </script>
        """
        return HTMLResponse(content=success_html, status_code=200)
    except ValueError as e:
        error_html = (
            f'<div class="alert alert-error">Error creating branch: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=400)
    except Exception as e:
        logger.error(f"Error creating branch: {e}", exc_info=True)
        error_html = (
            f'<div class="alert alert-error">Error creating branch: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=500)


@app.post("/branches/switch")
async def switch_branch(request: Request):
    """Switch to a different branch."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    form = await request.form()
    branch_name = form.get("branch_name")

    if not branch_name:
        raise HTTPException(status_code=400, detail="Branch name is required")

    try:
        current_dataset.switch_branch(branch_name)

        # Clear commit cache since we switched branches
        cache_key = (current_dataset.dataset_name, current_dataset.root_dir)
        if cache_key in commit_cache:
            del commit_cache[cache_key]
            logger.info(
                f"Cleared commit cache for dataset: {current_dataset.dataset_name}"
            )

        # Return success message and redirect to dataset view
        success_html = f"""
        <div class="alert alert-success">
            Switched to branch '{branch_name}'
        </div>
        <script>
            // Redirect to dataset view
            window.location.href = '/dataset-view';
        </script>
        """
        return HTMLResponse(content=success_html, status_code=200)
    except ValueError as e:
        error_html = (
            f'<div class="alert alert-error">Error switching branch: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=400)
    except Exception as e:
        logger.error(f"Error switching branch: {e}", exc_info=True)
        error_html = (
            f'<div class="alert alert-error">Error switching branch: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=500)


@app.post("/branches/delete")
async def delete_branch(request: Request):
    """Delete a branch."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    form = await request.form()
    branch_name = form.get("branch_name")

    if not branch_name:
        raise HTTPException(status_code=400, detail="Branch name is required")

    try:
        current_dataset.delete_branch(branch_name)

        # Return success message
        success_html = f"""
        <div class="alert alert-success">
            Branch '{branch_name}' deleted successfully
        </div>
        <script>
            // Refresh the branches list
            htmx.trigger('#branches-list', 'refresh');
        </script>
        """
        return HTMLResponse(content=success_html, status_code=200)
    except ValueError as e:
        error_html = (
            f'<div class="alert alert-error">Error deleting branch: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=400)
    except Exception as e:
        logger.error(f"Error deleting branch: {e}", exc_info=True)
        error_html = (
            f'<div class="alert alert-error">Error deleting branch: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=500)


# Merge operations
@app.get("/merge", response_class=HTMLResponse)
async def merge_page(request: Request):
    """Show merge interface."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    try:
        branches = current_dataset.list_branches()
        current_branch = current_dataset.get_current_branch()

        return templates.TemplateResponse(
            "merge.html",
            {
                "request": request,
                "branches": branches,
                "current_branch": current_branch,
                "dataset_name": current_dataset.dataset_name,
            },
        )
    except Exception as e:
        logger.error(f"Error loading merge page: {e}", exc_info=True)
        error_html = (
            f'<div class="alert alert-error">Error loading merge page: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=500)


@app.post("/merge/preview")
async def preview_merge(request: Request):
    """Preview merge conflicts without performing the merge."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    form = await request.form()
    source_branch = form.get("source_branch")
    target_branch = form.get("target_branch")

    if not source_branch or not target_branch:
        raise HTTPException(
            status_code=400, detail="Both source and target branches are required"
        )

    try:
        # Get commit hashes for both branches
        source_commit_hash = current_dataset.get_branch_commit(source_branch)
        target_commit_hash = current_dataset.get_branch_commit(target_branch)

        # Load the commits
        from .dataset import DatasetCommit

        source_commit = DatasetCommit.from_json(
            root_dir=current_dataset.root_dir,
            dataset_name=current_dataset.dataset_name,
            version_hash=source_commit_hash,
            fs=current_dataset.fs,
        )
        target_commit = DatasetCommit.from_json(
            root_dir=current_dataset.root_dir,
            dataset_name=current_dataset.dataset_name,
            version_hash=target_commit_hash,
            fs=current_dataset.fs,
        )

        # Detect conflicts
        conflicts = current_dataset._detect_merge_conflicts(
            source_commit, target_commit
        )

        # Get file lists for both branches
        source_files = source_commit._file_dict()
        target_files = target_commit._file_dict()

        return templates.TemplateResponse(
            "merge_preview.html",
            {
                "request": request,
                "source_branch": source_branch,
                "target_branch": target_branch,
                "source_commit": source_commit_hash[:8],
                "target_commit": target_commit_hash[:8],
                "conflicts": conflicts,
                "source_files": source_files,
                "target_files": target_files,
                "dataset_name": current_dataset.dataset_name,
            },
        )
    except Exception as e:
        logger.error(f"Error previewing merge: {e}", exc_info=True)
        error_html = (
            f'<div class="alert alert-error">Error previewing merge: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=500)


@app.post("/merge/execute")
async def execute_merge(request: Request):
    """Execute the merge operation."""
    if current_dataset is None:
        raise HTTPException(status_code=400, detail="No dataset loaded")

    form = await request.form()
    source_branch = form.get("source_branch")
    target_branch = form.get("target_branch")
    strategy = form.get("strategy", "auto")

    if not source_branch or not target_branch:
        raise HTTPException(
            status_code=400, detail="Both source and target branches are required"
        )

    try:
        # Execute the merge
        result = current_dataset.merge(source_branch, target_branch, strategy)

        if result["success"]:
            # Clear commit cache since we created a new commit
            cache_key = (current_dataset.dataset_name, current_dataset.root_dir)
            if cache_key in commit_cache:
                del commit_cache[cache_key]
                logger.info(
                    f"Cleared commit cache for dataset: {current_dataset.dataset_name}"
                )

            success_html = f"""
            <div class="alert alert-success">
                <h3>Merge Successful!</h3>
                <p>Successfully merged '{source_branch}' into '{target_branch}'</p>
                <p>Merge commit: {result["merge_commit"][:8]}</p>
            </div>
            <script>
                // Redirect to dataset view
                window.location.href = '/dataset-view';
            </script>
            """
            return HTMLResponse(content=success_html, status_code=200)
        else:
            # Merge requires manual resolution
            error_html = f"""
            <div class="alert alert-warning">
                <h3>Manual Resolution Required</h3>
                <p>Merge conflicts detected. Please resolve conflicts manually.</p>
                <p>Conflicts: {len(result["conflicts"])} files</p>
            </div>
            """
            return HTMLResponse(content=error_html, status_code=400)

    except ValueError as e:
        error_html = (
            f'<div class="alert alert-error">Error merging branches: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=400)
    except Exception as e:
        logger.error(f"Error executing merge: {e}", exc_info=True)
        error_html = (
            f'<div class="alert alert-error">Error executing merge: {str(e)}</div>'
        )
        return HTMLResponse(content=error_html, status_code=500)


def run_server(
    dataset_url: str = None,
    dataset_name: str = None,
    port: int = None,
    auto_reload: bool = True,
):
    """Run the web UI server.

    :param dataset_url: Optional dataset URL to load on startup
    :param dataset_name: Optional dataset name to load on startup
    :param port: Port to run the server on (default: random port)
    :param auto_reload: Enable auto-reload mode (default: True)
    """
    global current_dataset

    logger.info("Initializing GitData UI server")

    # Load dataset if provided
    if dataset_url and dataset_name:
        logger.info(
            f"Pre-loading dataset on startup: "
            f"name='{dataset_name}', url='{dataset_url}'"
        )
        current_dataset = Dataset(root_dir=dataset_url, dataset_name=dataset_name)
        logger.info(
            f"Dataset '{dataset_name}' loaded successfully "
            f"with {len(current_dataset.current_commit.file_hashes)} files"
        )

    # Use random port if not specified
    if port is None:
        port = random.randint(8000, 9000)
        logger.info(f"Using randomly assigned port: {port}")
    else:
        logger.info(f"Using specified port: {port}")

    import uvicorn

    logger.info(f"Starting server at http://0.0.0.0:{port}")
    logger.info(f"Auto-reload: {'enabled' if auto_reload else 'disabled'}")

    print(f"Starting GitData UI server at http://localhost:{port}")
    if current_dataset:
        dataset_info = (
            f"Loaded dataset: {current_dataset.dataset_name} "
            f"from {current_dataset.root_dir}"
        )
        print(dataset_info)

    uvicorn.run(
        "gitdata.web_ui:app",
        host="0.0.0.0",
        port=port,
        reload=auto_reload,
    )
