"""FastAPI application for Kirin Web UI."""

import os
import shutil
import tempfile
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from slugify import slugify

from .. import Catalog, Dataset
from .config import CatalogConfig, CatalogManager


# Global catalog manager
catalog_manager = CatalogManager()


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


def get_catalog_manager() -> CatalogManager:
    """Dependency to get catalog manager."""
    return catalog_manager


# Cache for dataset instances to avoid re-initializing
dataset_cache: Dict[tuple, Dataset] = {}


def get_dataset(catalog_id: str, dataset_name: str) -> Dataset:
    """Get or create a dataset instance.

    Args:
        catalog_id: Catalog ID
        dataset_name: Dataset name

    Returns:
        Dataset instance
    """
    cache_key = (catalog_id, dataset_name)

    if cache_key in dataset_cache:
        return dataset_cache[cache_key]

    # Get catalog config
    catalog = catalog_manager.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    # Create filesystem
    fs = catalog_manager.create_filesystem(catalog)

    # Create dataset
    dataset = Dataset(root_dir=catalog.root_dir, name=dataset_name, fs=fs)

    # Cache dataset
    dataset_cache[cache_key] = dataset
    return dataset


# Route handlers
@app.get("/", response_class=HTMLResponse)
async def list_catalogs(
    request: Request, catalog_mgr: CatalogManager = Depends(get_catalog_manager)
):
    """List all configured catalogs."""
    catalogs = catalog_mgr.list_catalogs()

    # Get dataset counts for each catalog
    catalog_infos = []
    for catalog in catalogs:
        try:
            # Test connection and get dataset count
            catalog_mgr.create_filesystem(catalog)
            kirin_catalog = Catalog(catalog.root_dir)
            dataset_count = len(kirin_catalog.datasets())
            status = "connected"
        except Exception as e:
            logger.warning(f"Failed to connect to catalog {catalog.id}: {e}")
            dataset_count = 0
            status = "error"

        catalog_infos.append(
            {
                "id": catalog.id,
                "name": catalog.name,
                "root_dir": catalog.root_dir,
                "status": status,
                "dataset_count": dataset_count,
            }
        )

    return templates.TemplateResponse(
        "catalogs.html", {"request": request, "catalogs": catalog_infos}
    )


@app.get("/catalogs/add", response_class=HTMLResponse)
async def add_catalog_form(
    request: Request, catalog_mgr: CatalogManager = Depends(get_catalog_manager)
):
    """Show add catalog form."""
    return templates.TemplateResponse("add_catalog.html", {"request": request})


@app.post("/catalogs/add", response_class=HTMLResponse)
async def add_catalog(
    request: Request,
    catalog_mgr: CatalogManager = Depends(get_catalog_manager),
    name: str = Form(..., min_length=1, max_length=100),
    root_dir: str = Form(..., min_length=1),
):
    """Add a new catalog."""
    try:
        # Generate catalog ID from name using slugify
        catalog_id = slugify(name)

        # Create catalog config
        logger.info(f"Creating catalog config for: {name}")
        logger.info(f"Catalog ID: {catalog_id}")
        logger.info(f"Root dir: {root_dir}")

        catalog = CatalogConfig(
            id=catalog_id,
            name=name,
            root_dir=root_dir,
        )

        # Add catalog
        catalog_mgr.add_catalog(catalog)

        # Redirect to catalog list
        return templates.TemplateResponse(
            "catalogs.html",
            {
                "request": request,
                "catalogs": catalog_mgr.list_catalogs(),
                "success": f"Catalog '{name}' added successfully",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        # Handle "already exists" error gracefully
        if "already exists" in str(e):
            logger.warning(f"Catalog '{name}' already exists: {e}")
            return templates.TemplateResponse(
                "add_catalog.html",
                {
                    "request": request,
                    "error": f"A catalog with the name '{name}' already exists. Please choose a different name or go to the existing catalog.",
                    "existing_catalog_id": catalog_id,
                    "form_data": {
                        "name": name,
                        "root_dir": root_dir,
                    },
                },
            )
        else:
            logger.error(f"Validation error adding catalog: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to add catalog: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add catalog: {str(e)}")


@app.get("/catalog/{catalog_id}", response_class=HTMLResponse)
async def list_datasets(
    request: Request,
    catalog_id: str,
    catalog_mgr: CatalogManager = Depends(get_catalog_manager),
):
    """List datasets in a catalog."""
    logger.info(f"=== Starting list_datasets for catalog {catalog_id} ===")
    overall_start = time.time()

    catalog = catalog_mgr.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    try:
        # Get filesystem and catalog
        logger.info(f"Step 1: Creating filesystem for catalog {catalog_id}")
        start_time = time.time()
        catalog_mgr.create_filesystem(catalog)
        logger.info(f"Step 1 completed in {time.time() - start_time:.2f}s")

        logger.info(f"Step 2: Creating catalog for {catalog.root_dir}")
        start_time = time.time()
        kirin_catalog = Catalog(catalog.root_dir)
        logger.info(f"Step 2 completed in {time.time() - start_time:.2f}s")

        # Get dataset information
        datasets = []
        logger.info(f"Step 3: Listing datasets")
        start_time = time.time()
        try:
            dataset_names = kirin_catalog.datasets()
            logger.info(
                f"Step 3 completed in {time.time() - start_time:.2f}s - found {len(dataset_names)} datasets"
            )
        except (FileNotFoundError, OSError) as e:
            # Handle case where datasets directory doesn't exist yet
            logger.info(
                f"Step 3 completed in {time.time() - start_time:.2f}s - No datasets directory found: {e}"
            )
            dataset_names = []
        except Exception as e:
            # Handle SSL and other connection errors gracefully
            logger.warning(
                f"Step 3 failed after {time.time() - start_time:.2f}s due to connection error: {e}"
            )
            logger.warning(f"Error type: {type(e).__name__}")
            # Return empty list instead of crashing
            dataset_names = []

        logger.info(f"Step 4: Processing {len(dataset_names)} datasets")
        start_time = time.time()
        for i, dataset_name in enumerate(dataset_names):
            try:
                logger.info(f"Step 4.{i + 1}: Processing dataset '{dataset_name}'")
                dataset_start = time.time()

                dataset = get_dataset(catalog_id, dataset_name)
                logger.info(
                    f"Step 4.{i + 1}a: get_dataset completed in {time.time() - dataset_start:.2f}s"
                )

                info_start = time.time()
                info = dataset.get_info()
                logger.info(
                    f"Step 4.{i + 1}b: get_info completed in {time.time() - info_start:.2f}s"
                )

                # Calculate total size
                size_start = time.time()
                total_size = 0
                if dataset.current_commit:
                    for file_obj in dataset.files.values():
                        total_size += file_obj.size
                logger.info(
                    f"Step 4.{i + 1}c: size calculation completed in {time.time() - size_start:.2f}s"
                )

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
                logger.info(
                    f"Step 4.{i + 1}: Dataset '{dataset_name}' processed in {time.time() - dataset_start:.2f}s"
                )
            except Exception as e:
                logger.warning(
                    f"Step 4.{i + 1}: Failed to get info for dataset {dataset_name} after {time.time() - dataset_start:.2f}s: {e}"
                )
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

        logger.info(
            f"Step 4 completed in {time.time() - start_time:.2f}s - processed {len(datasets)} datasets"
        )

        logger.info(
            f"=== list_datasets completed in {time.time() - overall_start:.2f}s ==="
        )
        return templates.TemplateResponse(
            "datasets.html",
            {"request": request, "catalog": catalog, "datasets": datasets},
        )

    except Exception as e:
        logger.error(
            f"=== list_datasets failed after {time.time() - overall_start:.2f}s: {e} ==="
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to list datasets: {str(e)}"
        )


@app.post("/catalog/{catalog_id}/datasets/create", response_class=HTMLResponse)
async def create_dataset(
    request: Request,
    catalog_id: str,
    name: str = Form(...),
    description: str = Form(""),
    catalog_mgr: CatalogManager = Depends(get_catalog_manager),
):
    """Create a new dataset."""
    catalog = catalog_mgr.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    try:
        # Create filesystem and catalog
        catalog_mgr.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir)

        # Check if dataset already exists
        existing_datasets = kirin_catalog.datasets()
        if name in existing_datasets:
            logger.warning(f"Dataset '{name}' already exists in catalog {catalog_id}")
            return templates.TemplateResponse(
                "datasets.html",
                {
                    "request": request,
                    "catalog": catalog,
                    "datasets": [],  # Will be reloaded
                    "error": f"Dataset '{name}' already exists. You can view it or choose a different name.",
                    "existing_dataset_name": name,
                },
            )

        # Create dataset
        kirin_catalog.create_dataset(name, description)

        # Clear cache for this catalog
        keys_to_remove = [k for k in dataset_cache.keys() if k[0] == catalog_id]
        for key in keys_to_remove:
            del dataset_cache[key]

        # Redirect to dataset view
        return templates.TemplateResponse(
            "datasets.html",
            {
                "request": request,
                "catalog": catalog,
                "datasets": [],  # Will be reloaded
                "success": f"Dataset '{name}' created successfully",
            },
        )

    except Exception as e:
        logger.error(f"Failed to create dataset {name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create dataset: {str(e)}"
        )


@app.get("/catalog/{catalog_id}/edit", response_class=HTMLResponse)
async def edit_catalog_form(
    request: Request,
    catalog_id: str,
    catalog_mgr: CatalogManager = Depends(get_catalog_manager),
):
    """Show edit catalog form."""
    catalog = catalog_mgr.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    return templates.TemplateResponse(
        "edit_catalog.html",
        {
            "request": request,
            "catalog": catalog,
        },
    )


@app.post("/catalog/{catalog_id}/edit", response_class=HTMLResponse)
async def update_catalog(
    request: Request,
    catalog_id: str,
    catalog_mgr: CatalogManager = Depends(get_catalog_manager),
    name: str = Form(...),
    root_dir: str = Form(...),
):
    """Update an existing catalog."""
    try:
        # Check if catalog exists
        existing_catalog = catalog_mgr.get_catalog(catalog_id)
        if not existing_catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        # Generate new catalog ID from name (may change if name changed)
        new_catalog_id = slugify(name)

        # Create new catalog config
        updated_catalog = CatalogConfig(
            id=new_catalog_id,
            name=name,
            root_dir=root_dir,
        )

        # Update catalog - handle ID changes
        if catalog_id != new_catalog_id:
            # Catalog ID changed, need to delete old and add new
            catalog_mgr.delete_catalog(catalog_id)
            # Check if new catalog ID already exists
            existing_catalog = catalog_mgr.get_catalog(new_catalog_id)
            if existing_catalog:
                # Update existing catalog with new ID
                catalog_mgr.update_catalog(updated_catalog)
            else:
                # Add new catalog
                catalog_mgr.add_catalog(updated_catalog)
        else:
            # Catalog ID didn't change, just update
            catalog_mgr.update_catalog(updated_catalog)

        # Clear dataset cache for both old and new catalog IDs
        keys_to_remove = [
            k for k in dataset_cache.keys() if k[0] in [catalog_id, new_catalog_id]
        ]
        for key in keys_to_remove:
            del dataset_cache[key]

        # Redirect to catalog list
        return templates.TemplateResponse(
            "catalogs.html",
            {
                "request": request,
                "catalogs": catalog_mgr.list_catalogs(),
                "success": f"Catalog '{name}' updated successfully",
            },
        )

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating catalog: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to update catalog: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to update catalog: {str(e)}"
        )


@app.get("/catalog/{catalog_id}/delete", response_class=HTMLResponse)
async def delete_catalog_confirmation(
    request: Request,
    catalog_id: str,
    catalog_mgr: CatalogManager = Depends(get_catalog_manager),
):
    """Show delete catalog confirmation."""
    catalog = catalog_mgr.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    # Get dataset count for this catalog
    try:
        catalog_mgr.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir)
        dataset_count = len(kirin_catalog.datasets())
    except Exception as e:
        logger.warning(f"Failed to get dataset count for catalog {catalog_id}: {e}")
        dataset_count = 0

    return templates.TemplateResponse(
        "delete_catalog.html",
        {
            "request": request,
            "catalog": catalog,
            "dataset_count": dataset_count,
        },
    )


@app.post("/catalog/{catalog_id}/delete", response_class=HTMLResponse)
async def delete_catalog(
    request: Request,
    catalog_id: str,
    catalog_mgr: CatalogManager = Depends(get_catalog_manager),
):
    """Delete a catalog."""
    try:
        catalog = catalog_mgr.get_catalog(catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        # Check if catalog has datasets
        try:
            catalog_mgr.create_filesystem(catalog)
            kirin_catalog = Catalog(catalog.root_dir)
            datasets = kirin_catalog.datasets()
            if datasets:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete catalog with {len(datasets)} existing datasets. Please delete the datasets first.",
                )
        except HTTPException:
            # Re-raise HTTP exceptions (like the 400 above)
            raise
        except Exception as e:
            logger.warning(f"Failed to check datasets for catalog {catalog_id}: {e}")
            # For other exceptions, we'll allow deletion to proceed

        # Delete catalog
        catalog_mgr.delete_catalog(catalog_id)

        # Clear dataset cache for this catalog
        keys_to_remove = [k for k in dataset_cache.keys() if k[0] == catalog_id]
        for key in keys_to_remove:
            del dataset_cache[key]

        # Redirect to catalog list
        return templates.TemplateResponse(
            "catalogs.html",
            {
                "request": request,
                "catalogs": catalog_mgr.list_catalogs(),
                "success": f"Catalog '{catalog.name}' deleted successfully",
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete catalog: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete catalog: {str(e)}"
        )


@app.get("/catalog/{catalog_id}/{dataset_name}", response_class=HTMLResponse)
async def view_dataset(
    request: Request, catalog_id: str, dataset_name: str, tab: str = "files"
):
    """View a dataset (files tab by default)."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)
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
                "catalog_id": catalog_id,
                "dataset_name": dataset_name,
                "dataset_info": info,
                "files": files,
                "active_tab": tab,
            },
        )

    except Exception as e:
        logger.error(f"Failed to view dataset {dataset_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to view dataset: {str(e)}")


@app.get("/catalog/{catalog_id}/{dataset_name}/files", response_class=HTMLResponse)
async def dataset_files_tab(request: Request, catalog_id: str, dataset_name: str):
    """HTMX partial for files tab."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)

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
                "catalog_id": catalog_id,
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
                "catalog_id": catalog_id,
                "dataset_name": dataset_name,
                "files": [],
                "error": str(e),
            },
        )


@app.get("/catalog/{catalog_id}/{dataset_name}/history", response_class=HTMLResponse)
async def dataset_history_tab(request: Request, catalog_id: str, dataset_name: str):
    """HTMX partial for history tab."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)

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
                "catalog_id": catalog_id,
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
                "catalog_id": catalog_id,
                "dataset_name": dataset_name,
                "commits": [],
                "error": str(e),
            },
        )


@app.get("/catalog/{catalog_id}/{dataset_name}/commit", response_class=HTMLResponse)
async def commit_form(request: Request, catalog_id: str, dataset_name: str):
    """Show commit form (staging area)."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)

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
                "catalog_id": catalog_id,
                "dataset_name": dataset_name,
                "files": files,
            },
        )

    except Exception as e:
        logger.error(f"Failed to load commit form for dataset {dataset_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to load commit form: {str(e)}"
        )


@app.post("/catalog/{catalog_id}/{dataset_name}/commit", response_class=HTMLResponse)
async def create_commit(
    request: Request,
    catalog_id: str,
    dataset_name: str,
    message: str = Form(...),
    remove_files: List[str] = Form([]),
    files: List[UploadFile] = File([]),
):
    """Create a new commit."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)

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
                "catalog_id": catalog_id,
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
    "/catalog/{catalog_id}/{dataset_name}/file/{file_name}/preview",
    response_class=HTMLResponse,
)
async def preview_file(
    request: Request, catalog_id: str, dataset_name: str, file_name: str
):
    """Preview a file (text only)."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)
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
                    "catalog_id": catalog_id,
                    "dataset_name": dataset_name,
                    "file_name": file_name,
                    "file_size": file_obj.size,
                    "content": None,
                    "is_binary": True,
                    "content_type": content_type,
                    "truncated": False,
                },
            )

        # Use local_files() context manager for file access
        try:
            with dataset.local_files() as local_files:
                if file_name not in local_files:
                    raise HTTPException(status_code=404, detail="File not found")

                # Read file content using local path
                local_path = Path(local_files[file_name])
                content = local_path.read_text()
                lines = content.split("\n")
                preview_lines = lines[:1000]
                preview_content = "\n".join(preview_lines)
        except UnicodeDecodeError:
            # File appears to be binary despite extension
            return templates.TemplateResponse(
                "file_preview.html",
                {
                    "request": request,
                    "catalog_id": catalog_id,
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
                "catalog_id": catalog_id,
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


@app.get("/catalog/{catalog_id}/{dataset_name}/file/{file_name}/download")
async def download_file(catalog_id: str, dataset_name: str, file_name: str):
    """Download a file."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)
        file_obj = dataset.get_file(file_name)

        if not file_obj:
            raise HTTPException(status_code=404, detail="File not found")

        # Use download_to() to create a temporary file, then stream it
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_path = temp_file.name
        temp_file.close()

        try:
            # Download file to temporary location
            file_obj.download_to(temp_path)

            # Stream the temporary file
            def generate():
                with open(temp_path, "rb") as f:
                    while chunk := f.read(8192):
                        yield chunk

            return StreamingResponse(
                generate(),
                media_type=file_obj.content_type,
                headers={"Content-Disposition": f"attachment; filename={file_name}"},
            )
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except Exception:
                pass  # Ignore cleanup errors

    except Exception as e:
        logger.error(f"Failed to download file {file_name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to download file: {str(e)}"
        )


@app.get(
    "/catalog/{catalog_id}/{dataset_name}/checkout/{commit_hash}",
    response_class=HTMLResponse,
)
async def checkout_commit(
    request: Request, catalog_id: str, dataset_name: str, commit_hash: str
):
    """Browse files at a specific commit (read-only)."""
    try:
        dataset = get_dataset(catalog_id, dataset_name)

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
                "catalog_id": catalog_id,
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
