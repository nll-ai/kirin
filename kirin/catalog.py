"""Lightweight implementation of a Data Catalog, which is a collection of Datasets."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import fsspec
from loguru import logger

from .dataset import Dataset
from .file_index import FileIndex
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

    def find_datasets_with_file(self, file_hash: str) -> Dict[str, List[Dict[str, Any]]]:
        """Find all datasets containing a file with the given hash.

        Uses the reverse index for efficient lookup.

        Args:
            file_hash: Content hash of the file to search for

        Returns:
            Dictionary mapping dataset names to list of commits containing the file.
            Each commit entry contains:
            - commit_hash: Hash of the commit
            - timestamp: Timestamp of the commit
            - filenames: List of filenames for this file hash in the commit

        Example:
            # Find datasets containing a specific file
            results = catalog.find_datasets_with_file("abc123def456...")
            
            # Results structure:
            # {
            #     "dataset1": [
            #         {
            #             "commit_hash": "commit123...",
            #             "timestamp": "2024-01-01T12:00:00",
            #             "filenames": ["data.csv"]
            #         }
            #     ],
            #     "dataset2": [
            #         {
            #             "commit_hash": "commit456...",
            #             "timestamp": "2024-01-02T10:00:00",
            #             "filenames": ["results.csv", "backup.csv"]
            #         }
            #     ]
            # }
        """
        try:
            file_index = FileIndex(self.root_dir, self.fs)
            return file_index.get_datasets_with_file(file_hash)
        except Exception as e:
            logger.error(f"Failed to find datasets with file {file_hash[:8]}: {e}")
            return {}

    def find_datasets_with_filename(self, filename: str) -> Dict[str, List[Dict[str, Any]]]:
        """Find all datasets containing a file with the given filename.

        Searches through all datasets to find files with the specified name.
        This is less efficient than hash-based search but more user-friendly.

        Args:
            filename: Name of the file to search for

        Returns:
            Dictionary mapping dataset names to list of commits containing the file.
            Each commit entry contains:
            - commit_hash: Hash of the commit
            - timestamp: Timestamp of the commit
            - filenames: List of filenames matching the search

        Example:
            # Find datasets containing a file named "data.csv"
            results = catalog.find_datasets_with_filename("data.csv")
            
            # Results structure:
            # {
            #     "dataset1": [
            #         {
            #             "commit_hash": "commit123...",
            #             "timestamp": "2024-01-01T12:00:00",
            #             "filenames": ["data.csv"]
            #         }
            #     ],
            #     "dataset2": [
            #         {
            #             "commit_hash": "commit456...",
            #             "timestamp": "2024-01-02T10:00:00",
            #             "filenames": ["data.csv"]
            #         }
            #     ]
            # }
        """
        try:
            results = {}
            dataset_names = self.datasets()
            
            for dataset_name in dataset_names:
                try:
                    dataset = self.get_dataset(dataset_name)
                    commits = dataset.get_commits()
                    
                    matching_commits = []
                    for commit in commits:
                        # Check if this commit contains a file with the target filename
                        if filename in commit.files:
                            file_obj = commit.files[filename]
                            matching_commits.append({
                                "commit_hash": commit.hash,
                                "timestamp": commit.timestamp.isoformat(),
                                "filenames": [filename],
                                "file_hash": file_obj.hash,  # Include hash for reference
                                "file_size": file_obj.size,
                            })
                    
                    if matching_commits:
                        results[dataset_name] = matching_commits
                        
                except Exception as e:
                    logger.warning(f"Failed to search dataset {dataset_name}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to find datasets with filename {filename}: {e}")
            return {}
