"""Pydantic models for Kirin Web UI forms and validation."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CatalogForm(BaseModel):
    """Form model for adding/editing catalogs."""

    name: str = Field(..., min_length=1, max_length=100, description="Catalog name")
    root_dir: str = Field(..., description="Root directory path (local or cloud URL)")


class DatasetForm(BaseModel):
    """Form model for creating datasets."""

    name: str = Field(..., min_length=1, max_length=100, description="Dataset name")
    description: str = Field("", max_length=500, description="Dataset description")


class CommitForm(BaseModel):
    """Form model for creating commits."""

    message: str = Field(
        ..., min_length=1, max_length=500, description="Commit message"
    )
    remove_files: List[str] = Field(default=[], description="Files to remove")


class CatalogInfo(BaseModel):
    """Information about a catalog."""

    id: str
    name: str
    root_dir: str
    status: str  # connected, error
    dataset_count: int = 0


class DatasetInfo(BaseModel):
    """Information about a dataset."""

    name: str
    description: str
    commit_count: int
    current_commit: Optional[str] = None
    total_size: int = 0
    last_updated: Optional[str] = None


class FileInfo(BaseModel):
    """Information about a file."""

    name: str
    size: int
    content_type: str
    hash: str
    short_hash: str


class CommitInfo(BaseModel):
    """Information about a commit."""

    hash: str
    short_hash: str
    message: str
    timestamp: str
    author: Optional[str] = None
    files_added: int = 0
    files_removed: int = 0
    total_size: int = 0


class CatalogTypeInfo(BaseModel):
    """Information about a catalog type."""

    value: str
    label: str
    description: str


class CatalogFieldInfo(BaseModel):
    """Information about a form field."""

    name: str
    label: str
    type: str
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None
