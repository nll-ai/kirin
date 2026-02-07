"""Lightweight implementation of a Data Catalog, which is a collection of Datasets."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Union

import fsspec
from loguru import logger

from .dataset import Dataset
from .utils import get_filesystem, strip_protocol


@dataclass
class Catalog:
    """A class for storing a collection of datasets."""

    root_dir: Union[str, fsspec.AbstractFileSystem]
    fs: Optional[fsspec.AbstractFileSystem] = None
    # AWS/S3 authentication
    aws_profile: Optional[str] = None
    # GCP/GCS authentication
    gcs_token: Optional[Union[str, Path]] = None
    gcs_project: Optional[str] = None
    # Azure authentication
    azure_account_name: Optional[str] = None
    azure_account_key: Optional[str] = None
    azure_connection_string: Optional[str] = None

    def __post_init__(self):
        """Post-initialization function for the Catalog class."""
        # Handle filesystem initialization
        if isinstance(self.root_dir, fsspec.AbstractFileSystem):
            self.fs = self.root_dir
            self.root_dir = self.fs.root_marker
        else:
            self.root_dir = str(self.root_dir)
            self.fs = self.fs or get_filesystem(
                self.root_dir,
                aws_profile=self.aws_profile,
                gcs_token=self.gcs_token,
                gcs_project=self.gcs_project,
                azure_account_name=self.azure_account_name,
                azure_account_key=self.azure_account_key,
                azure_connection_string=self.azure_connection_string,
            )

        # Set up datasets directory path
        self.datasets_dir = f"{strip_protocol(self.root_dir)}/datasets"
        logger.debug(f"Datasets directory path: {self.datasets_dir}")

        # Note: We don't create directories upfront because:
        # - S3/GCS/Azure: Empty directories don't exist until they contain objects
        # - Local filesystem: Directories will be created when first dataset is added
        # This ensures consistent behavior across all filesystems

    def __len__(self) -> int:
        """Return the number of datasets in the catalog.

        :return: The number of datasets in the catalog.
        """
        try:
            return len([d for d in self.fs.ls(self.datasets_dir) if self.fs.isdir(d)])
        except FileNotFoundError:
            return 0

    def datasets(self) -> List[str]:
        """Return a list of the names of the datasets in the catalog.

        :return: A list of the names of the datasets in the catalog.
        """
        try:
            # List contents of datasets directory
            dataset_paths = [
                d for d in self.fs.ls(self.datasets_dir) if self.fs.isdir(d)
            ]
            # Extract dataset names from paths
            return [d.split("/")[-1] for d in dataset_paths]
        except FileNotFoundError:
            # This is normal - empty catalogs don't have a datasets directory yet
            # Works consistently across all filesystems (local, S3, GCS, Azure, etc.)
            logger.debug(
                f"Datasets directory is empty or doesn't exist yet: {self.datasets_dir}"
            )
            return []
        except Exception as e:
            logger.error(f"Error listing datasets from {self.datasets_dir}: {e}")
            logger.exception("Full traceback:")
            return []  # Return empty list instead of crashing

    def get_dataset(self, dataset_name: str) -> Dataset:
        """Get a dataset from the catalog.

        :param dataset_name: The name of the dataset to get.
        :return: The Dataset object with the given name.
        """
        return Dataset(root_dir=self.root_dir, name=dataset_name, fs=self.fs)

    def create_dataset(self, dataset_name: str, description: str = "") -> Dataset:
        """Create a dataset in the catalog.

        :param dataset_name: The name of the dataset to create.
        :param description: The description of the dataset.
        :return: The Dataset object with the given name.
        """
        # Note: We don't create directories here for S3 compatibility
        # Directories will be created when the first commit happens
        return Dataset(
            root_dir=self.root_dir,
            name=dataset_name,
            description=description,
            fs=self.fs,
        )

    def delete_dataset(self, dataset_name: str) -> None:
        """Remove a dataset from the catalog and delete its data.

        Deletes the dataset directory and all commits/files under it. This cannot
        be undone.

        :param dataset_name: The name of the dataset to remove.
        :raises ValueError: If the dataset does not exist.
        """
        if dataset_name not in self.datasets():
            raise ValueError(f"Dataset '{dataset_name}' not found in catalog")
        path = f"{self.datasets_dir}/{dataset_name}"
        try:
            self.fs.rm(path, recursive=True)
            logger.info(f"Deleted dataset: {dataset_name}")
        except Exception as e:
            logger.error(f"Failed to delete dataset {dataset_name}: {e}")
            raise

    def _get_widget_data(self) -> dict:
        """Get widget data dictionary for CatalogWidget.

        Returns:
            Dictionary with catalog data for widget rendering
        """
        from .html_repr import format_file_size

        dataset_names = self.datasets()
        dataset_count = len(dataset_names)

        datasets = []
        total_size = 0

        for dataset_name in sorted(dataset_names):
            try:
                dataset = self.get_dataset(dataset_name)
                dataset_data = {
                    "name": dataset_name,
                    "description": dataset.description,
                    "commit": None,
                }

                if dataset.current_commit:
                    commit = dataset.current_commit
                    file_count = len(commit.files)
                    dataset_size = commit.get_total_size()
                    total_size += dataset_size

                    dataset_data["commit"] = {
                        "hash": commit.short_hash,
                        "message": commit.message,
                        "file_count": file_count,
                        "size": format_file_size(dataset_size),
                    }

                datasets.append(dataset_data)
            except Exception:
                # If we can't load a dataset, just show the name
                datasets.append(
                    {
                        "name": dataset_name,
                        "description": None,
                        "commit": None,
                    }
                )

        return {
            "root_dir": self.root_dir,
            "dataset_count": dataset_count,
            "datasets": datasets,
            "total_size": format_file_size(total_size) if total_size > 0 else None,
        }

    def _repr_html_(self) -> str:
        """Generate HTML representation of the catalog for notebook display.

        Returns:
            HTML string with catalog information and dataset list
        """
        # Use widgets - let errors propagate for debugging
        from .widgets import CatalogWidget

        widget = CatalogWidget(data=self._get_widget_data())
        return widget._repr_html_()
