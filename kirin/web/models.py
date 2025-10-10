"""Pydantic models for Kirin Web UI forms and validation."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class BackendForm(BaseModel):
    """Form model for adding/editing backends."""

    name: str = Field(..., min_length=1, max_length=100, description="Backend name")
    type: str = Field(..., description="Backend type")
    auth_mode: str = Field("system", description="Authentication mode")

    # Common fields
    root_dir: Optional[str] = Field(None, description="Root directory path")

    # S3 fields
    bucket: Optional[str] = Field(None, description="S3 bucket name")
    prefix: Optional[str] = Field(None, description="S3 prefix")
    region: Optional[str] = Field(None, description="AWS region")
    key: Optional[str] = Field(None, description="Access key ID")
    secret: Optional[str] = Field(None, description="Secret access key")

    # GCS fields
    project: Optional[str] = Field(None, description="GCP project ID")
    token: Optional[str] = Field(None, description="Service account token")

    # Azure fields
    container: Optional[str] = Field(None, description="Azure container name")
    account_name: Optional[str] = Field(None, description="Azure storage account name")
    account_key: Optional[str] = Field(None, description="Azure storage account key")
    connection_string: Optional[str] = Field(
        None, description="Azure connection string"
    )

    # S3-compatible fields
    service: Optional[str] = Field(None, description="S3-compatible service")
    endpoint_url: Optional[str] = Field(None, description="Custom endpoint URL")


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


class BackendInfo(BaseModel):
    """Information about a backend."""

    id: str
    name: str
    type: str
    root_dir: str
    status: str  # connected, error, testing
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


class BackendTypeInfo(BaseModel):
    """Information about a backend type."""

    value: str
    label: str
    description: str


class BackendFieldInfo(BaseModel):
    """Information about a form field."""

    name: str
    label: str
    type: str
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[Dict[str, str]]] = None
