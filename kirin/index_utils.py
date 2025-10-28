"""Utilities for managing the file hash reverse index."""

from pathlib import Path
from typing import Optional, Union

import fsspec
from loguru import logger

from .catalog import Catalog
from .file_index import FileIndex
from .utils import get_filesystem, strip_protocol


def rebuild_file_index(
    root_dir: Union[str, Path],
    fs: Optional[fsspec.AbstractFileSystem] = None,
) -> int:
    """Rebuild the entire file index from scratch.

    This function iterates through all datasets in the catalog and rebuilds
    the file index by examining all commits and their files. This is useful
    for migration, corruption recovery, or when the index needs to be
    completely refreshed.

    Args:
        root_dir: Root directory of the catalog
        fs: Filesystem to use (auto-detected if None)

    Returns:
        Number of file references indexed

    Example:
        # Rebuild index for a local catalog
        count = rebuild_file_index("/path/to/catalog")
        print(f"Indexed {count} file references")

        # Rebuild index for an S3 catalog
        import s3fs
        s3 = s3fs.S3FileSystem()
        count = rebuild_file_index("s3://my-bucket/catalog", s3)
    """
    root_dir = str(root_dir)
    fs = fs or get_filesystem(root_dir)
    
    logger.info(f"Starting file index rebuild for {root_dir}")
    
    try:
        # Initialize catalog and file index
        catalog = Catalog(root_dir=root_dir, fs=fs)
        file_index = FileIndex(root_dir, fs)
        
        # Clear existing index
        _clear_file_index(file_index)
        logger.info("Cleared existing file index")
        
        # Get all datasets
        dataset_names = catalog.datasets()
        logger.info(f"Found {len(dataset_names)} datasets to index")
        
        indexed_count = 0
        
        # Process each dataset
        for dataset_name in dataset_names:
            try:
                dataset = catalog.get_dataset(dataset_name)
                logger.info(f"Processing dataset: {dataset_name}")
                
                # Get all commits for this dataset
                commits = dataset.get_commits()
                logger.debug(f"Found {len(commits)} commits in {dataset_name}")
                
                # Process each commit
                for commit in commits:
                    # Index all files in this commit
                    for file_obj in commit.files.values():
                        file_index.add_file_reference(
                            file_hash=file_obj.hash,
                            dataset_name=dataset_name,
                            commit_hash=commit.hash,
                            timestamp=commit.timestamp.isoformat(),
                            filename=file_obj.name,
                        )
                        indexed_count += 1
                
                logger.info(f"Indexed {len(commits)} commits from {dataset_name}")
                
            except Exception as e:
                logger.error(f"Failed to process dataset {dataset_name}: {e}")
                continue
        
        logger.info(f"File index rebuild completed. Indexed {indexed_count} file references")
        return indexed_count
        
    except Exception as e:
        logger.error(f"Failed to rebuild file index: {e}")
        raise IOError(f"Failed to rebuild file index: {e}") from e


def _clear_file_index(file_index: FileIndex) -> None:
    """Clear all entries from the file index.

    Args:
        file_index: FileIndex instance to clear
    """
    try:
        # Get all file hashes in the index
        file_hashes = file_index.list_file_hashes()
        
        # Delete each index file
        for file_hash in file_hashes:
            try:
                file_index._delete_index(file_hash)
            except Exception as e:
                logger.warning(f"Failed to delete index for {file_hash[:8]}: {e}")
        
        logger.info(f"Cleared {len(file_hashes)} index entries")
        
    except Exception as e:
        logger.error(f"Failed to clear file index: {e}")
        raise


def verify_file_index(
    root_dir: Union[str, Path],
    fs: Optional[fsspec.AbstractFileSystem] = None,
) -> dict:
    """Verify the integrity of the file index.

    This function checks that the file index is consistent with the actual
    data in the catalog by comparing indexed files with files referenced
    in commits.

    Args:
        root_dir: Root directory of the catalog
        fs: Filesystem to use (auto-detected if None)

    Returns:
        Dictionary with verification results:
        - total_datasets: Number of datasets checked
        - total_commits: Number of commits checked
        - total_files: Number of files checked
        - missing_index_entries: Number of files missing from index
        - extra_index_entries: Number of index entries not in commits
        - errors: List of error messages

    Example:
        # Verify index integrity
        results = verify_file_index("/path/to/catalog")
        if results["missing_index_entries"] > 0:
            print("Index is missing some entries, consider rebuilding")
    """
    root_dir = str(root_dir)
    fs = fs or get_filesystem(root_dir)
    
    logger.info(f"Starting file index verification for {root_dir}")
    
    try:
        # Initialize catalog and file index
        catalog = Catalog(root_dir=root_dir, fs=fs)
        file_index = FileIndex(root_dir, fs)
        
        # Track verification results
        total_datasets = 0
        total_commits = 0
        total_files = 0
        missing_index_entries = 0
        extra_index_entries = 0
        errors = []
        
        # Get all datasets
        dataset_names = catalog.datasets()
        total_datasets = len(dataset_names)
        
        # Collect all file references from commits
        commit_file_refs = set()
        
        for dataset_name in dataset_names:
            try:
                dataset = catalog.get_dataset(dataset_name)
                commits = dataset.get_commits()
                total_commits += len(commits)
                
                for commit in commits:
                    for file_obj in commit.files.values():
                        ref = (file_obj.hash, dataset_name, commit.hash)
                        commit_file_refs.add(ref)
                        total_files += 1
                        
            except Exception as e:
                error_msg = f"Failed to process dataset {dataset_name}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Check for missing index entries
        for file_hash, dataset_name, commit_hash in commit_file_refs:
            try:
                datasets_with_file = file_index.get_datasets_with_file(file_hash)
                if dataset_name not in datasets_with_file:
                    missing_index_entries += 1
                    logger.warning(
                        f"Missing index entry: {file_hash[:8]} in {dataset_name}:{commit_hash[:8]}"
                    )
            except Exception as e:
                error_msg = f"Failed to check index for {file_hash[:8]}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Check for extra index entries (not in commits)
        try:
            indexed_file_hashes = file_index.list_file_hashes()
            for file_hash in indexed_file_hashes:
                datasets_with_file = file_index.get_datasets_with_file(file_hash)
                for dataset_name, commits in datasets_with_file.items():
                    for commit_info in commits:
                        ref = (file_hash, dataset_name, commit_info["commit_hash"])
                        if ref not in commit_file_refs:
                            extra_index_entries += 1
                            logger.warning(
                                f"Extra index entry: {file_hash[:8]} in {dataset_name}:{commit_info['commit_hash'][:8]}"
                            )
        except Exception as e:
            error_msg = f"Failed to check extra index entries: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        results = {
            "total_datasets": total_datasets,
            "total_commits": total_commits,
            "total_files": total_files,
            "missing_index_entries": missing_index_entries,
            "extra_index_entries": extra_index_entries,
            "errors": errors,
        }
        
        logger.info(f"File index verification completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Failed to verify file index: {e}")
        raise IOError(f"Failed to verify file index: {e}") from e