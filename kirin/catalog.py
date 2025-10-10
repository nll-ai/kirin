"""Lightweight implementation of a Data Catalog, which is a collection of Datasets."""

from dataclasses import dataclass
from typing import List, Union, Optional
import fsspec
from loguru import logger

from .dataset import Dataset
from .utils import get_filesystem, strip_protocol


@dataclass
class Catalog:
    """A class for storing a collection of datasets."""

    root_dir: Union[str, fsspec.AbstractFileSystem]
    fs: Optional[fsspec.AbstractFileSystem] = None

    def __post_init__(self):
        """Post-initialization function for the Catalog class."""
        # Handle filesystem initialization
        if isinstance(self.root_dir, fsspec.AbstractFileSystem):
            self.fs = self.root_dir
            self.root_dir = self.fs.root_marker
        else:
            self.root_dir = str(self.root_dir)
            self.fs = self.fs or get_filesystem(self.root_dir)

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
