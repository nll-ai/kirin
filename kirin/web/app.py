"""FastAPI application for Kirin Web UI."""

import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger

from .. import Catalog, Dataset
from .config import BackendConfig, BackendManager


# Global backend manager
backend_manager = BackendManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Kirin Web UI")
    yield
    logger.info("Shutting down Kirin Web UI")


# Create FastAPI app
app = FastAPI(
    title="Kirin Web UI",
    description="Web interface for Kirin data versioning",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="kirin/web/static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="kirin/web/templates")


def get_backend_manager() -> BackendManager:
    """Dependency to get backend manager."""
    return backend_manager


# Cache for dataset instances to avoid re-initializing
dataset_cache: Dict[tuple, Dataset] = {}


def get_dataset(backend_id: str, dataset_name: str) -> Dataset:
    """Get or create a dataset instance.

    Args:
        backend_id: Backend ID
        dataset_name: Dataset name

    Returns:
        Dataset instance
    """
    cache_key = (backend_id, dataset_name)

    if cache_key in dataset_cache:
        return dataset_cache[cache_key]

    # Get backend config
    backend = backend_manager.get_backend(backend_id)
    if not backend:
        raise HTTPException(status_code=404, detail="Backend not found")

    # Create filesystem
    fs = backend_manager.create_filesystem(backend)

    # Create dataset
    dataset = Dataset(root_dir=backend.root_dir, name=dataset_name, fs=fs)

    # Cache dataset
    dataset_cache[cache_key] = dataset
    return dataset


# Route handlers
@app.get("/", response_class=HTMLResponse)
async def list_backends(
    request: Request, backend_mgr: BackendManager = Depends(get_backend_manager)
):
    """List all configured backends."""
    backends = backend_mgr.list_backends()

    # Get dataset counts for each backend
    backend_infos = []
    for backend in backends:
        try:
            # Test connection and get dataset count
            fs = backend_mgr.create_filesystem(backend)
            catalog = Catalog(Path(backend.root_dir))
            dataset_count = len(catalog.datasets())
            status = "connected"
        except Exception as e:
            logger.warning(f"Failed to connect to backend {backend.id}: {e}")
            dataset_count = 0
            status = "error"

        backend_infos.append(
            {
                "id": backend.id,
                "name": backend.name,
                "type": backend.type,
                "root_dir": backend.root_dir,
                "status": status,
                "dataset_count": dataset_count,
            }
        )

    return templates.TemplateResponse(
        "backends.html", {"request": request, "backends": backend_infos}
    )


@app.get("/backends/add", response_class=HTMLResponse)
async def add_backend_form(
    request: Request, backend_mgr: BackendManager = Depends(get_backend_manager)
):
    """Show add backend form."""
    types = backend_mgr.get_available_types()
    return templates.TemplateResponse(
        "add_backend.html", {"request": request, "types": types}
    )


@app.post("/backends/add", response_class=HTMLResponse)
async def add_backend(
    request: Request,
    backend_mgr: BackendManager = Depends(get_backend_manager),
    name: str = Form(...),
    type: str = Form(...),
    root_dir: Optional[str] = Form(None),
    bucket: Optional[str] = Form(None),
    prefix: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    key: Optional[str] = Form(None),
    secret: Optional[str] = Form(None),
    project: Optional[str] = Form(None),
    token: Optional[str] = Form(None),
    container: Optional[str] = Form(None),
    account_name: Optional[str] = Form(None),
    account_key: Optional[str] = Form(None),
    connection_string: Optional[str] = Form(None),
    service: Optional[str] = Form(None),
    endpoint_url: Optional[str] = Form(None),
):
    """Add a new backend."""
    try:
        # Generate backend ID from name
        backend_id = name.lower().replace(" ", "-").replace("_", "-")

        # Build config based on type
        config = {}
        if type == "local":
            if not root_dir:
                raise HTTPException(
                    status_code=400,
                    detail="Root directory is required for local backend",
                )
            final_root_dir = root_dir
        elif type == "s3":
            if not bucket or not region or not key or not secret:
                raise HTTPException(
                    status_code=400,
                    detail="Bucket, region, key, and secret are required for S3",
                )
            config = {"key": key, "secret": secret, "region": region}
            final_root_dir = f"s3://{bucket}"
            if prefix:
                final_root_dir += f"/{prefix}"
        elif type == "gcs":
            if not bucket or not project:
                raise HTTPException(
                    status_code=400, detail="Bucket and project are required for GCS"
                )
            config = {"project": project}
            if token:
                config["token"] = token
            final_root_dir = f"gs://{bucket}"
            if prefix:
                final_root_dir += f"/{prefix}"
        elif type == "azure":
            if not container or not account_name:
                raise HTTPException(
                    status_code=400,
                    detail="Container and account name are required for Azure",
                )
            if account_key:
                config = {"account_name": account_name, "account_key": account_key}
            elif connection_string:
                config = {"connection_string": connection_string}
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either account key or connection string is required for Azure",
                )
            final_root_dir = f"az://{container}"
            if prefix:
                final_root_dir += f"/{prefix}"
        elif type == "s3_compatible":
            if not bucket or not key or not secret:
                raise HTTPException(
                    status_code=400,
                    detail="Bucket, key, and secret are required for S3-compatible",
                )
            config = {"key": key, "secret": secret}
            if service and service != "custom":
                config["service"] = service
            elif endpoint_url:
                config["endpoint_url"] = endpoint_url
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Either service or endpoint URL is required for S3-compatible",
                )
            final_root_dir = f"s3://{bucket}"
            if prefix:
                final_root_dir += f"/{prefix}"
        else:
            raise HTTPException(
                status_code=400, detail=f"Unsupported backend type: {type}"
            )

        # Create backend config
        backend = BackendConfig(
            id=backend_id, name=name, type=type, root_dir=final_root_dir, config=config
        )

        # Test connection
        if not backend_mgr.test_connection(backend):
            raise HTTPException(
                status_code=400,
                detail="Failed to connect to backend. Please check your credentials.",
            )

        # Add backend
        backend_mgr.add_backend(backend)

        # Redirect to backend list
        return templates.TemplateResponse(
            "backends.html",
            {
                "request": request,
                "backends": backend_mgr.list_backends(),
                "success": f"Backend '{name}' added successfully",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Handle "already exists" error gracefully
        if "already exists" in str(e):
            logger.warning(f"Backend '{name}' already exists: {e}")
            return templates.TemplateResponse(
                "add_backend.html",
                {
                    "request": request,
                    "types": backend_mgr.get_available_types(),
                    "error": f"A backend with the name '{name}' already exists. Please choose a different name or go to the existing backend.",
                    "existing_backend_id": backend_id,
                    "form_data": {
                        "name": name,
                        "type": type,
                        "root_dir": root_dir,
                        "bucket": bucket,
                        "prefix": prefix,
                        "region": region,
                        "key": key,
                        "secret": secret,
                        "project": project,
                        "token": token,
                        "container": container,
                        "account_name": account_name,
                        "account_key": account_key,
                        "connection_string": connection_string,
                        "service": service,
                        "endpoint_url": endpoint_url,
                    },
                },
            )
        else:
            logger.error(f"Validation error adding backend: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add backend: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add backend: {str(e)}")


@app.get("/backend/{backend_id}", response_class=HTMLResponse)
async def list_datasets(
    request: Request,
    backend_id: str,
    backend_mgr: BackendManager = Depends(get_backend_manager),
):
    """List datasets in a backend."""
    backend = backend_mgr.get_backend(backend_id)
    if not backend:
        raise HTTPException(status_code=404, detail="Backend not found")

    try:
        # Get filesystem and catalog
        fs = backend_mgr.create_filesystem(backend)
        catalog = Catalog(Path(backend.root_dir))

        # Get dataset information
        datasets = []
        try:
            dataset_names = catalog.datasets()
        except (FileNotFoundError, OSError) as e:
            # Handle case where datasets directory doesn't exist yet
            logger.info(f"No datasets directory found for backend {backend_id}: {e}")
            dataset_names = []

        for dataset_name in dataset_names:
            try:
                dataset = get_dataset(backend_id, dataset_name)
                info = dataset.get_info()

                # Calculate total size
                total_size = 0
                if dataset.current_commit:
                    for file_obj in dataset.files.values():
                        total_size += file_obj.size

                datasets.append(
                    {
                        "name": dataset_name,
                        "description": info.get("description", ""),
                        "commit_count": info.get("commit_count", 0),
                        "current_commit": info.get("current_commit"),
                        "total_size": total_size,
                        "last_updated": info.get("last_updated"),
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to get info for dataset {dataset_name}: {e}")
                datasets.append(
                    {
                        "name": dataset_name,
                        "description": "Error loading dataset",
                        "commit_count": 0,
                        "current_commit": None,
                        "total_size": 0,
                        "last_updated": None,
                    }
                )

        return templates.TemplateResponse(
            "datasets.html",
            {"request": request, "backend": backend, "datasets": datasets},
        )

    except Exception as e:
        logger.error(f"Failed to list datasets for backend {backend_id}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to list datasets: {str(e)}"
        )


@app.post("/backend/{backend_id}/datasets/create", response_class=HTMLResponse)
async def create_dataset(
    request: Request,
    backend_id: str,
    name: str = Form(...),
    description: str = Form(""),
    backend_mgr: BackendManager = Depends(get_backend_manager),
):
    """Create a new dataset."""
    backend = backend_mgr.get_backend(backend_id)
    if not backend:
        raise HTTPException(status_code=404, detail="Backend not found")

    try:
        # Create filesystem and catalog
        fs = backend_mgr.create_filesystem(backend)
        catalog = Catalog(Path(backend.root_dir))

        # Check if dataset already exists
        existing_datasets = catalog.datasets()
        if name in existing_datasets:
            logger.warning(f"Dataset '{name}' already exists in backend {backend_id}")
            return templates.TemplateResponse(
                "datasets.html",
                {
                    "request": request,
                    "backend": backend,
                    "datasets": [],  # Will be reloaded
                    "error": f"Dataset '{name}' already exists. You can view it or choose a different name.",
                    "existing_dataset_name": name,
                },
            )

        # Create dataset
        dataset = catalog.create_dataset(name, description)

        # Clear cache for this backend
        keys_to_remove = [k for k in dataset_cache.keys() if k[0] == backend_id]
        for key in keys_to_remove:
            del dataset_cache[key]

        # Redirect to dataset view
        return templates.TemplateResponse(
            "datasets.html",
            {
                "request": request,
                "backend": backend,
                "datasets": [],  # Will be reloaded
                "success": f"Dataset '{name}' created successfully",
            },
        )

    except Exception as e:
        logger.error(f"Failed to create dataset {name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create dataset: {str(e)}"
        )


@app.get("/backend/{backend_id}/{dataset_name}", response_class=HTMLResponse)
async def view_dataset(
    request: Request, backend_id: str, dataset_name: str, tab: str = "files"
):
    """View a dataset (files tab by default)."""
    try:
        dataset = get_dataset(backend_id, dataset_name)
        info = dataset.get_info()

        # Get files from current commit
        files = []
        total_size = 0
        if dataset.current_commit:
            for name, file_obj in dataset.files.items():
                files.append(
                    {
                        "name": name,
                        "size": file_obj.size,
                        "content_type": file_obj.content_type,
                        "hash": file_obj.hash,
                        "short_hash": file_obj.short_hash,
                    }
                )
                total_size += file_obj.size

        # Add total_size to info
        info["total_size"] = total_size

        return templates.TemplateResponse(
            "dataset_view.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "dataset_info": info,
                "files": files,
                "active_tab": tab,
            },
        )

    except Exception as e:
        logger.error(f"Failed to view dataset {dataset_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to view dataset: {str(e)}")


@app.get("/backend/{backend_id}/{dataset_name}/files", response_class=HTMLResponse)
async def dataset_files_tab(request: Request, backend_id: str, dataset_name: str):
    """HTMX partial for files tab."""
    try:
        dataset = get_dataset(backend_id, dataset_name)

        # Get files from current commit
        files = []
        if dataset.current_commit:
            for name, file_obj in dataset.files.items():
                files.append(
                    {
                        "name": name,
                        "size": file_obj.size,
                        "content_type": file_obj.content_type,
                        "hash": file_obj.hash,
                        "short_hash": file_obj.short_hash,
                    }
                )

        return templates.TemplateResponse(
            "files_tab.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "files": files,
            },
        )

    except Exception as e:
        logger.error(f"Failed to load files for dataset {dataset_name}: {e}")
        return templates.TemplateResponse(
            "files_tab.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "files": [],
                "error": str(e),
            },
        )


@app.get("/backend/{backend_id}/{dataset_name}/history", response_class=HTMLResponse)
async def dataset_history_tab(request: Request, backend_id: str, dataset_name: str):
    """HTMX partial for history tab."""
    try:
        dataset = get_dataset(backend_id, dataset_name)

        # Get commit history
        commits = []
        for commit in dataset.history(limit=50):
            commits.append(
                {
                    "hash": commit.hash,
                    "short_hash": commit.short_hash,
                    "message": commit.message,
                    "timestamp": commit.timestamp.isoformat(),
                    "files_added": len(commit.files),
                    "files_removed": 0,  # TODO: Calculate from parent
                    "total_size": sum(f.size for f in commit.files.values()),
                }
            )

        return templates.TemplateResponse(
            "history_tab.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "commits": commits,
            },
        )

    except Exception as e:
        logger.error(f"Failed to load history for dataset {dataset_name}: {e}")
        return templates.TemplateResponse(
            "history_tab.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "commits": [],
                "error": str(e),
            },
        )


@app.get("/backend/{backend_id}/{dataset_name}/commit", response_class=HTMLResponse)
async def commit_form(request: Request, backend_id: str, dataset_name: str):
    """Show commit form (staging area)."""
    try:
        dataset = get_dataset(backend_id, dataset_name)

        # Get current files for removal selection
        files = []
        if dataset.current_commit:
            for name, file_obj in dataset.files.items():
                files.append(
                    {
                        "name": name,
                        "size": file_obj.size,
                        "content_type": file_obj.content_type,
                    }
                )

        return templates.TemplateResponse(
            "commit_form.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "files": files,
            },
        )

    except Exception as e:
        logger.error(f"Failed to load commit form for dataset {dataset_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to load commit form: {str(e)}"
        )


@app.post("/backend/{backend_id}/{dataset_name}/commit", response_class=HTMLResponse)
async def create_commit(
    request: Request,
    backend_id: str,
    dataset_name: str,
    message: str = Form(...),
    remove_files: List[str] = Form([]),
    files: List[UploadFile] = File([]),
):
    """Create a new commit."""
    try:
        dataset = get_dataset(backend_id, dataset_name)

        # Handle file uploads
        temp_files = []
        add_files = []

        if files:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix=f"kirin_{dataset_name}_")
            temp_files.append(temp_dir)

            try:
                for file in files:
                    if file.filename:
                        # Save uploaded file to temp directory
                        temp_path = os.path.join(temp_dir, file.filename)
                        with open(temp_path, "wb") as f:
                            content = await file.read()
                            f.write(content)
                        add_files.append(temp_path)

                # Create commit
                commit_hash = dataset.commit(
                    message=message, add_files=add_files, remove_files=remove_files
                )

                logger.info(f"Created commit {commit_hash} for dataset {dataset_name}")

            finally:
                # Clean up temporary files
                for temp_file in temp_files:
                    if os.path.exists(temp_file):
                        shutil.rmtree(temp_file)
        else:
            # No files uploaded, just remove files
            if not remove_files:
                raise HTTPException(status_code=400, detail="No changes specified")

            commit_hash = dataset.commit(message=message, remove_files=remove_files)

            logger.info(f"Created commit {commit_hash} for dataset {dataset_name}")

        # Get updated dataset info and calculate total_size
        info = dataset.get_info()
        total_size = 0
        if dataset.current_commit:
            for file_obj in dataset.files.values():
                total_size += file_obj.size
        info["total_size"] = total_size

        # Redirect back to dataset view
        return templates.TemplateResponse(
            "dataset_view.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "dataset_info": info,
                "files": [],  # Will be reloaded
                "active_tab": "files",
                "success": f"Commit created successfully: {commit_hash[:8]}",
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 400 errors) as-is
        raise
    except Exception as e:
        logger.error(f"Failed to create commit for dataset {dataset_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create commit: {str(e)}"
        )


@app.get(
    "/backend/{backend_id}/{dataset_name}/file/{file_name}/preview",
    response_class=HTMLResponse,
)
async def preview_file(
    request: Request, backend_id: str, dataset_name: str, file_name: str
):
    """Preview a file (text only)."""
    try:
        dataset = get_dataset(backend_id, dataset_name)
        file_obj = dataset.get_file(file_name)

        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")

        # Check if file is text-based by content type
        content_type = file_obj.content_type or ""
        is_text_file = (
            content_type.startswith("text/")
            or content_type
            in ["application/json", "application/xml", "application/javascript"]
            or file_name.lower().endswith(
                (
                    ".txt",
                    ".csv",
                    ".json",
                    ".xml",
                    ".yaml",
                    ".yml",
                    ".md",
                    ".py",
                    ".js",
                    ".html",
                    ".css",
                    ".sql",
                    ".log",
                )
            )
        )

        if not is_text_file:
            # For binary files, show a message instead of content
            return templates.TemplateResponse(
                "file_preview.html",
                {
                    "request": request,
                    "backend_id": backend_id,
                    "dataset_name": dataset_name,
                    "file_name": file_name,
                    "file_size": file_obj.size,
                    "content": None,
                    "is_binary": True,
                    "content_type": content_type,
                    "truncated": False,
                },
            )

        # Read file content (limit to first 1000 lines for preview)
        try:
            content = file_obj.read_text()
            lines = content.split("\n")
            preview_lines = lines[:1000]
            preview_content = "\n".join(preview_lines)
        except UnicodeDecodeError:
            # File appears to be binary despite extension
            return templates.TemplateResponse(
                "file_preview.html",
                {
                    "request": request,
                    "backend_id": backend_id,
                    "dataset_name": dataset_name,
                    "file_name": file_name,
                    "file_size": file_obj.size,
                    "content": None,
                    "is_binary": True,
                    "content_type": content_type,
                    "truncated": False,
                },
            )

        return templates.TemplateResponse(
            "file_preview.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "file_name": file_name,
                "file_size": file_obj.size,
                "content": preview_content,
                "is_binary": False,
                "truncated": len(lines) > 1000,
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 404 errors) as-is
        raise
    except Exception as e:
        logger.error(f"Failed to preview file {file_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to preview file: {str(e)}")


@app.get("/backend/{backend_id}/{dataset_name}/file/{file_name}/download")
async def download_file(backend_id: str, dataset_name: str, file_name: str):
    """Download a file."""
    try:
        dataset = get_dataset(backend_id, dataset_name)
        file_obj = dataset.get_file(file_name)

        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")

        # Stream file content
        def generate():
            with file_obj.open("rb") as f:
                while chunk := f.read(8192):
                    yield chunk

        return StreamingResponse(
            generate(),
            media_type=file_obj.content_type,
            headers={"Content-Disposition": f"attachment; filename={file_name}"},
        )

    except Exception as e:
        logger.error(f"Failed to download file {file_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to download file: {str(e)}"
        )


@app.get(
    "/backend/{backend_id}/{dataset_name}/checkout/{commit_hash}",
    response_class=HTMLResponse,
)
async def checkout_commit(
    request: Request, backend_id: str, dataset_name: str, commit_hash: str
):
    """Browse files at a specific commit (read-only)."""
    try:
        dataset = get_dataset(backend_id, dataset_name)

        try:
            commit = dataset.get_commit(commit_hash)
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                raise HTTPException(status_code=404, detail="Commit not found")
            else:
                raise e

        if not commit:
            raise HTTPException(status_code=404, detail="Commit not found")

        # Get files from that commit
        files = []
        for name, file_obj in commit.files.items():
            files.append(
                {
                    "name": name,
                    "size": file_obj.size,
                    "content_type": file_obj.content_type,
                    "hash": file_obj.hash,
                    "short_hash": file_obj.short_hash,
                }
            )

        # Get dataset info and calculate total_size
        info = dataset.get_info()
        total_size = 0
        if commit:
            for file_obj in commit.files.values():
                total_size += file_obj.size
        info["total_size"] = total_size

        return templates.TemplateResponse(
            "dataset_view.html",
            {
                "request": request,
                "backend_id": backend_id,
                "dataset_name": dataset_name,
                "dataset_info": info,
                "files": files,
                "active_tab": "files",
                "checkout_commit": commit_hash,
                "checkout_message": commit.message,
                "checkout_timestamp": commit.timestamp.isoformat(),
            },
        )

    except HTTPException:
        # Re-raise HTTP exceptions (like 404 errors) as-is
        raise
    except Exception as e:
        logger.error(f"Failed to checkout commit {commit_hash}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to checkout commit: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
