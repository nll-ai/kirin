"""FastAPI application for Kirin Web UI."""

import os
import shutil
import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import (
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from loguru import logger
from slugify import slugify

from .. import Catalog
from .config import CatalogConfig, CatalogManager

# Global catalog manager
catalog_manager = CatalogManager()


def get_aws_profiles():
    """Get available AWS profiles from config files."""
    import configparser
    import os

    profiles = []

    # Check AWS config file locations
    aws_config_paths = [
        os.path.expanduser("~/.aws/config"),
        os.path.expanduser("~/.aws/credentials"),
    ]

    for config_path in aws_config_paths:
        if os.path.exists(config_path):
            try:
                config = configparser.ConfigParser()
                config.read(config_path)

                # Extract profile names from sections
                for section_name in config.sections():
                    if section_name.startswith("profile "):
                        profile_name = section_name.replace("profile ", "")
                        if profile_name not in profiles:
                            profiles.append(profile_name)
                    elif section_name == "default":
                        if "default" not in profiles:
                            profiles.append("default")
                    elif (
                        not section_name.startswith("profile ")
                        and section_name != "default"
                    ):
                        # This might be a profile name without "profile " prefix
                        if section_name not in profiles:
                            profiles.append(section_name)
            except Exception as e:
                logger.warning(f"Failed to parse AWS config at {config_path}: {e}")
                continue

    # Always include 'default' if no profiles found
    if not profiles:
        profiles = ["default"]

    # Sort profiles with 'default' first
    profiles = sorted(profiles, key=lambda x: (x != "default", x))

    return profiles


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


# No more caching - direct creation like notebook


# Route handlers
@app.get("/api/aws-profiles", response_class=JSONResponse)
async def get_aws_profiles_endpoint():
    """Get available AWS profiles."""
    try:
        profiles = get_aws_profiles()
        return {"profiles": profiles}
    except Exception as e:
        logger.error(f"Failed to get AWS profiles: {e}")
        return {"profiles": ["default"]}


@app.get("/", response_class=HTMLResponse)
async def list_catalogs(
    request: Request, catalog_manager: CatalogManager = Depends(get_catalog_manager)
):
    """List all configured catalogs."""
    catalogs = catalog_manager.list_catalogs()

    # Simple catalog info - no connection testing, just like notebook
    catalog_infos = []
    for catalog in catalogs:
        catalog_infos.append(
            {
                "id": catalog.id,
                "name": catalog.name,
                "root_dir": catalog.root_dir,
                "status": "ready",  # Always ready, like notebook
                "dataset_count": "?",  # Will be shown when user clicks
            }
        )

    return templates.TemplateResponse(
        "catalogs.html", {"request": request, "catalogs": catalog_infos}
    )


@app.get("/catalogs/add", response_class=HTMLResponse)
async def add_catalog_form(
    request: Request, catalog_manager: CatalogManager = Depends(get_catalog_manager)
):
    """Show add catalog form."""
    return templates.TemplateResponse(
        "catalog_form.html",
        {
            "request": request,
            "page_title": "Add Data Catalog",
            "page_description": "Configure a new data catalog for your datasets",
            "form_action": "/catalogs/add",
            "submit_button_text": "Create Catalog",
        },
    )


@app.post("/catalogs/add", response_class=HTMLResponse)
async def add_catalog(
    request: Request,
    catalog_manager: CatalogManager = Depends(get_catalog_manager),
    name: str = Form(..., min_length=1, max_length=100),
    root_dir: str = Form(..., min_length=1),
    aws_profile: str = Form(""),
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
            aws_profile=aws_profile if aws_profile else None,
        )

        # Add catalog
        catalog_manager.add_catalog(catalog)

        # Redirect to catalog list
        return templates.TemplateResponse(
            "catalogs.html",
            {
                "request": request,
                "catalogs": catalog_manager.list_catalogs(),
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
                "catalog_form.html",
                {
                    "request": request,
                    "error": (
                        f"A catalog with the name '{name}' already exists. "
                        "Please choose a different name or go to the existing catalog."
                    ),
                    "existing_catalog_id": catalog_id,
                    "form_data": {
                        "name": name,
                        "root_dir": root_dir,
                        "aws_profile": aws_profile,
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
    catalog_manager: CatalogManager = Depends(get_catalog_manager),
):
    """List datasets in a catalog - automatically load datasets."""
    catalog = catalog_manager.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    try:
        # Create authenticated filesystem and load datasets automatically
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset_names = kirin_catalog.datasets()

        # Simple dataset info - no expensive operations
        datasets = []
        for dataset_name in dataset_names:
            datasets.append(
                {
                    "name": dataset_name,
                    "description": "",  # Will load when viewing
                    "commit_count": 0,  # Will load when viewing
                    "current_commit": None,  # Will load when viewing
                    "total_size": 0,  # Will load when viewing
                    "last_updated": None,  # Will load when viewing
                }
            )

        return templates.TemplateResponse(
            "datasets.html",
            {
                "request": request,
                "catalog": catalog,
                "datasets": datasets,
                "lazy_loading": False,  # We actually loaded the data
            },
        )

    except Exception as e:
        logger.error(f"Failed to load datasets: {e}")
        logger.exception("Full traceback:")
        # Return error page instead of crashing
        return templates.TemplateResponse(
            "datasets.html",
            {
                "request": request,
                "catalog": catalog,
                "datasets": [],
                "error": f"Failed to connect to catalog: {str(e)}",
                "lazy_loading": False,
            },
        )


@app.post("/catalog/{catalog_id}/datasets/create", response_class=HTMLResponse)
async def create_dataset(
    request: Request,
    catalog_id: str,
    name: str = Form(...),
    description: str = Form(""),
    catalog_manager: CatalogManager = Depends(get_catalog_manager),
):
    """Create a new dataset - fast like notebook."""
    catalog = catalog_manager.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    try:
        # Create authenticated filesystem before creating Catalog
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)

        # Check if dataset exists like notebook
        existing_datasets = kirin_catalog.datasets()
        if name in existing_datasets:
            return templates.TemplateResponse(
                "datasets.html",
                {
                    "request": request,
                    "catalog": catalog,
                    "datasets": [],
                    "error": (
                        f"Dataset '{name}' already exists. "
                        "You can view it or choose a different name."
                    ),
                },
            )

        # Create dataset like notebook
        kirin_catalog.create_dataset(name, description)

        # Redirect to the dataset page instead of showing empty catalog list
        # This works better with S3 lazy directory creation
        return RedirectResponse(url=f"/catalog/{catalog_id}/{name}", status_code=302)

    except Exception as e:
        logger.error(f"Failed to create dataset {name}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to create dataset: {str(e)}"
        )


@app.get("/catalog/{catalog_id}/edit", response_class=HTMLResponse)
async def edit_catalog_form(
    request: Request,
    catalog_id: str,
    catalog_manager: CatalogManager = Depends(get_catalog_manager),
):
    """Show edit catalog form."""
    catalog = catalog_manager.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    return templates.TemplateResponse(
        "catalog_form.html",
        {
            "request": request,
            "catalog": catalog,
            "page_title": "Edit Catalog",
            "page_description": "Update catalog configuration",
            "form_action": f"/catalog/{catalog_id}/edit",
            "submit_button_text": "Update Catalog",
        },
    )


@app.post("/catalog/{catalog_id}/edit", response_class=HTMLResponse)
async def update_catalog(
    request: Request,
    catalog_id: str,
    catalog_manager: CatalogManager = Depends(get_catalog_manager),
    name: str = Form(...),
    root_dir: str = Form(...),
    aws_profile: str = Form(""),
):
    """Update an existing catalog."""
    try:
        # Check if catalog exists
        existing_catalog = catalog_manager.get_catalog(catalog_id)
        if not existing_catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        # Generate new catalog ID from name (may change if name changed)
        new_catalog_id = slugify(name)

        # Create new catalog config
        updated_catalog = CatalogConfig(
            id=new_catalog_id,
            name=name,
            root_dir=root_dir,
            aws_profile=aws_profile if aws_profile else None,
        )

        # Update catalog - handle ID changes
        if catalog_id != new_catalog_id:
            # Catalog ID changed, need to delete old and add new
            catalog_manager.delete_catalog(catalog_id)
            # Check if new catalog ID already exists
            existing_catalog = catalog_manager.get_catalog(new_catalog_id)
            if existing_catalog:
                # Update existing catalog with new ID
                catalog_manager.update_catalog(updated_catalog)
            else:
                # Add new catalog
                catalog_manager.add_catalog(updated_catalog)
        else:
            # Catalog ID didn't change, just update
            catalog_manager.update_catalog(updated_catalog)

        # No more caching - direct creation like notebook

        # Redirect to catalog list
        return templates.TemplateResponse(
            "catalogs.html",
            {
                "request": request,
                "catalogs": catalog_manager.list_catalogs(),
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
    catalog_manager: CatalogManager = Depends(get_catalog_manager),
):
    """Show delete catalog confirmation."""
    catalog = catalog_manager.get_catalog(catalog_id)
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog not found")

    # Get dataset count for this catalog
    try:
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
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
    catalog_manager: CatalogManager = Depends(get_catalog_manager),
):
    """Delete a catalog."""
    try:
        catalog = catalog_manager.get_catalog(catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        # Check if catalog has datasets
        try:
            fs = catalog_manager.create_filesystem(catalog)
            kirin_catalog = Catalog(catalog.root_dir, fs=fs)
            datasets = kirin_catalog.datasets()
            if datasets:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Cannot delete catalog with {len(datasets)} "
                        "existing datasets. Please delete the datasets first."
                    ),
                )
        except HTTPException:
            # Re-raise HTTP exceptions (like the 400 above)
            raise
        except Exception as e:
            logger.warning(f"Failed to check datasets for catalog {catalog_id}: {e}")
            # For other exceptions, we'll allow deletion to proceed

        # Delete catalog
        catalog_manager.delete_catalog(catalog_id)

        # No more caching - direct creation like notebook

        # Redirect to catalog list
        return templates.TemplateResponse(
            "catalogs.html",
            {
                "request": request,
                "catalogs": catalog_manager.list_catalogs(),
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
    """View a dataset - fast like notebook."""
    try:
        # Get catalog config
        catalog = catalog_manager.get_catalog(catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        # Create authenticated filesystem before creating Catalog
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)

        # Get files like notebook: dataset.list_files()
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

        # Simple info
        info = {
            "description": dataset.description or "",
            "commit_count": len(dataset.history()),
            "current_commit": dataset.current_commit.hash
            if dataset.current_commit
            else None,
            "total_size": sum(f["size"] for f in files),
            "last_updated": dataset.current_commit.timestamp.isoformat()
            if dataset.current_commit
            else None,
        }

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
    """HTMX partial for files tab - fast like notebook."""
    try:
        # Create authenticated filesystem before creating Catalog
        catalog = catalog_manager.get_catalog(catalog_id)
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)

        # Get files like notebook: dataset.list_files()
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
    """HTMX partial for history tab - fast like notebook."""
    try:
        # Create authenticated filesystem before creating Catalog
        catalog = catalog_manager.get_catalog(catalog_id)
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)

        # Get commit history like notebook: dataset.history()
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
    """Show commit form - fast like notebook."""
    try:
        # Create authenticated filesystem before creating Catalog
        catalog = catalog_manager.get_catalog(catalog_id)
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)

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
    """Create a new commit - fast like notebook."""
    try:
        # Create authenticated filesystem before creating Catalog
        catalog = catalog_manager.get_catalog(catalog_id)
        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)

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

                # Create commit like notebook
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

        # Simple info calculation
        total_size = 0
        if dataset.current_commit:
            for file_obj in dataset.files.values():
                total_size += file_obj.size

        # Calculate dataset info for potential future use
        # dataset_info = {
        #     "description": dataset.description or "",
        #     "commit_count": len(dataset.history()),
        #     "current_commit": dataset.current_commit.hash
        #     if dataset.current_commit
        #     else None,
        #     "total_size": total_size,
        #     "last_updated": dataset.current_commit.timestamp.isoformat()
        #     if dataset.current_commit
        #     else None,
        # }

        # Redirect back to dataset view to refresh the state
        return RedirectResponse(
            url=f"/catalog/{catalog_id}/{dataset_name}", status_code=302
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
        # Create authenticated filesystem before creating Catalog
        catalog = catalog_manager.get_catalog(catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)
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
        # Create authenticated filesystem before creating Catalog
        catalog = catalog_manager.get_catalog(catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)
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
                """Generate file chunks for streaming response."""
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
        # Create authenticated filesystem before creating Catalog
        catalog = catalog_manager.get_catalog(catalog_id)
        if not catalog:
            raise HTTPException(status_code=404, detail="Catalog not found")

        fs = catalog_manager.create_filesystem(catalog)
        kirin_catalog = Catalog(catalog.root_dir, fs=fs)
        dataset = kirin_catalog.get_dataset(dataset_name)

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
