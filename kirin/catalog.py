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
        return len(self.datasets())

    def datasets(self) -> List[str]:
        """Return a list of the names of the datasets in the catalog.

        For Git-based implementation, look for .git directories in the root.

        :return: A list of the names of the datasets in the catalog.
        """
        try:
            # For Git implementation, look for .git directories
            import os
            from pathlib import Path

            # Convert to local path for checking
            root_path = Path(strip_protocol(self.root_dir))

            if not root_path.exists():
                return []

            dataset_names = []
            for item in root_path.iterdir():
                # Check if this is a Git repository (has .git directory)
                if item.is_dir() and (item / ".git").exists():
                    dataset_names.append(item.name)

            return sorted(dataset_names)

        except Exception as e:
            logger.error(f"Error listing datasets from {self.root_dir}: {e}")
            logger.exception("Full traceback:")
            return []  # Return empty list instead of crashing

    def get_dataset(self, dataset_name: str) -> Dataset:
        """Get a dataset from the catalog.

        :param dataset_name: The name of the dataset to get.
        :return: The Dataset object with the given name.
        """
        # Each dataset has its own directory for Git repository
        dataset_dir = str(Path(self.root_dir) / dataset_name)
        return Dataset(root_dir=dataset_dir, name=dataset_name, fs=self.fs)

    def create_dataset(self, dataset_name: str, description: str = "") -> Dataset:
        """Create a dataset in the catalog.

        :param dataset_name: The name of the dataset to create.
        :param description: The description of the dataset.
        :return: The Dataset object with the given name.
        """
        # Each dataset gets its own directory for Git repository
        dataset_dir = str(Path(self.root_dir) / dataset_name)
        return Dataset(
            root_dir=dataset_dir,
            name=dataset_name,
            description=description,
            fs=self.fs,
        )
