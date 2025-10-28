"""File hash reverse index for finding datasets containing specific files."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import fsspec
from loguru import logger

from .utils import get_filesystem, strip_protocol


class FileIndex:
    """Manages reverse index mapping file hashes to datasets and commits.

    The index allows efficient lookup of which datasets contain files with
    specific content hashes. Files are stored in a sharded structure to
    avoid filesystem limitations with large numbers of files.

    Storage structure:
    <root>/index/files/{hash[:2]}/{hash[2:]}.json

    Each index file contains:
    {
        "file_hash": "abcdef123456...",
        "datasets": {
            "dataset1": [
                {
                    "commit_hash": "abc123...",
                    "timestamp": "2024-01-01T12:00:00",
                    "filenames": ["data.csv"]
                }
            ]
        }
    }

    Args:
        root_dir: Root directory for the index
        fs: Filesystem to use (auto-detected if None)
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        fs: Optional[fsspec.AbstractFileSystem] = None,
    ):
        self.root_dir = str(root_dir)
        self.fs = fs or get_filesystem(self.root_dir)
        self.index_dir = f"{self.root_dir}/index/files"

        # Ensure index directory exists
        self.fs.makedirs(strip_protocol(self.index_dir), exist_ok=True)
        logger.info(f"File index initialized at {self.index_dir}")

    def add_file_reference(
        self,
        file_hash: str,
        dataset_name: str,
        commit_hash: str,
        timestamp: str,
        filename: str,
    ) -> None:
        """Add or update a file reference in the index.

        Args:
            file_hash: Content hash of the file
            dataset_name: Name of the dataset containing the file
            commit_hash: Hash of the commit containing the file
            timestamp: Timestamp of the commit
            filename: Original filename of the file
        """
        try:
            # Load existing index data
            index_data = self.load_index(file_hash)
            
            # Initialize structure if needed
            if "file_hash" not in index_data:
                index_data["file_hash"] = file_hash
                index_data["datasets"] = {}
            
            if "datasets" not in index_data:
                index_data["datasets"] = {}
            
            if dataset_name not in index_data["datasets"]:
                index_data["datasets"][dataset_name] = []
            
            # Check if this commit already exists for this dataset
            commit_exists = False
            for entry in index_data["datasets"][dataset_name]:
                if entry["commit_hash"] == commit_hash:
                    # Update existing entry
                    if filename not in entry["filenames"]:
                        entry["filenames"].append(filename)
                    entry["timestamp"] = timestamp
                    commit_exists = True
                    break
            
            # Add new commit entry if it doesn't exist
            if not commit_exists:
                index_data["datasets"][dataset_name].append({
                    "commit_hash": commit_hash,
                    "timestamp": timestamp,
                    "filenames": [filename]
                })
            
            # Save updated index
            self.save_index(file_hash, index_data)
            
            logger.debug(
                f"Added file reference: {file_hash[:8]} -> "
                f"{dataset_name}:{commit_hash[:8]} ({filename})"
            )
            
        except Exception as e:
            logger.error(f"Failed to add file reference {file_hash[:8]}: {e}")
            raise IOError(f"Failed to add file reference: {e}") from e

    def remove_file_reference(
        self,
        file_hash: str,
        dataset_name: str,
        commit_hash: str,
    ) -> None:
        """Remove a file reference from the index.

        Args:
            file_hash: Content hash of the file
            dataset_name: Name of the dataset
            commit_hash: Hash of the commit to remove
        """
        try:
            # Load existing index data
            index_data = self.load_index(file_hash)
            
            if "datasets" not in index_data:
                return
            
            if dataset_name not in index_data["datasets"]:
                return
            
            # Remove the commit entry
            index_data["datasets"][dataset_name] = [
                entry for entry in index_data["datasets"][dataset_name]
                if entry["commit_hash"] != commit_hash
            ]
            
            # Remove dataset if no commits remain
            if not index_data["datasets"][dataset_name]:
                del index_data["datasets"][dataset_name]
            
            # Remove entire index file if no datasets remain
            if not index_data["datasets"]:
                self.delete_index(file_hash)
                logger.debug(f"Deleted empty index file for {file_hash[:8]}")
            else:
                # Save updated index
                self.save_index(file_hash, index_data)
            
            logger.debug(
                f"Removed file reference: {file_hash[:8]} -> "
                f"{dataset_name}:{commit_hash[:8]}"
            )
            
        except Exception as e:
            logger.error(f"Failed to remove file reference {file_hash[:8]}: {e}")
            raise IOError(f"Failed to remove file reference: {e}") from e

    def get_datasets_with_file(self, file_hash: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all datasets containing a file with the given hash.

        Args:
            file_hash: Content hash of the file to search for

        Returns:
            Dictionary mapping dataset names to list of commits containing the file
        """
        try:
            index_data = self.load_index(file_hash)
            
            if "datasets" not in index_data:
                return {}
            
            return index_data["datasets"].copy()
            
        except Exception as e:
            logger.warning(f"Failed to get datasets for file {file_hash[:8]}: {e}")
            return {}

    def get_index_path(self, file_hash: str) -> str:
        """Get the storage path for an index file.

        Args:
            file_hash: Content hash of the file

        Returns:
            Storage path for the index file
        """
        # Create sharded path: index/files/{hash[:2]}/{hash[2:]}.json
        hash_dir = f"{self.index_dir}/{file_hash[:2]}"
        index_file = f"{hash_dir}/{file_hash[2:]}.json"
        return index_file

    def load_index(self, file_hash: str) -> Dict[str, Any]:
        """Load index data for a file hash.

        Args:
            file_hash: Content hash of the file

        Returns:
            Index data dictionary
        """
        index_path = self.get_index_path(file_hash)
        
        try:
            if not self.fs.exists(strip_protocol(index_path)):
                return {}
            
            with self.fs.open(strip_protocol(index_path), "r") as f:
                return json.load(f)
                
        except Exception as e:
            logger.warning(f"Failed to load index for {file_hash[:8]}: {e}")
            return {}

    def save_index(self, file_hash: str, data: Dict[str, Any]) -> None:
        """Save index data for a file hash.

        Args:
            file_hash: Content hash of the file
            data: Index data to save
        """
        index_path = self.get_index_path(file_hash)
        
        try:
            # Ensure directory exists
            hash_dir = f"{self.index_dir}/{file_hash[:2]}"
            self.fs.makedirs(strip_protocol(hash_dir), exist_ok=True)
            
            # Write index file
            with self.fs.open(strip_protocol(index_path), "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save index for {file_hash[:8]}: {e}")
            raise IOError(f"Failed to save index: {e}") from e

    def delete_index(self, file_hash: str) -> None:
        """Delete index file for a file hash.

        Args:
            file_hash: Content hash of the file
        """
        index_path = self.get_index_path(file_hash)
        
        try:
            if self.fs.exists(strip_protocol(index_path)):
                self.fs.rm(strip_protocol(index_path))
                
        except Exception as e:
            logger.warning(f"Failed to delete index for {file_hash[:8]}: {e}")

    def list_file_hashes(self) -> List[str]:
        """List all file hashes in the index.

        Returns:
            List of file hashes
        """
        try:
            # Get all index files
            pattern = f"{strip_protocol(self.index_dir)}/*/*.json"
            files = self.fs.glob(pattern)
            
            # Extract hashes from file paths
            hashes = []
            for file_path in files:
                # Extract hash from path: index_dir/hash[:2]/hash[2:].json
                path_parts = file_path.split("/")
                if len(path_parts) >= 2:
                    hash_prefix = path_parts[-2]
                    hash_suffix = path_parts[-1].replace(".json", "")
                    full_hash = hash_prefix + hash_suffix
                    hashes.append(full_hash)
            
            return hashes
            
        except Exception as e:
            logger.warning(f"Failed to list file hashes: {e}")
            return []

    def cleanup_orphaned_entries(self, used_hashes: set[str]) -> int:
        """Remove index entries for files that are no longer referenced.

        Args:
            used_hashes: Set of file hashes that are still in use

        Returns:
            Number of index entries removed
        """
        try:
            all_hashes = set(self.list_file_hashes())
            orphaned_hashes = all_hashes - used_hashes
            
            removed_count = 0
            for file_hash in orphaned_hashes:
                try:
                    self.delete_index(file_hash)
                    removed_count += 1
                    logger.debug(f"Removed orphaned index entry: {file_hash[:8]}")
                except Exception as e:
                    logger.warning(f"Failed to remove orphaned index {file_hash[:8]}: {e}")
            
            logger.info(f"Cleaned up {removed_count} orphaned index entries")
            return removed_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned index entries: {e}")
            return 0