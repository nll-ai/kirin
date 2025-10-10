"""Commit history storage for Kirin datasets."""

import json
from pathlib import Path
from typing import Dict, List, Optional, Union

import fsspec
from loguru import logger

from .commit import Commit
from .storage import ContentStore
from .utils import strip_protocol, get_filesystem


class CommitStore:
    """Manages commit history for a dataset.

    Commits are stored in a single JSON file at:
    root_dir/datasets/{dataset_name}/commits.json

    The JSON structure is:
    {
        "commits": [
            {
                "hash": "...",
                "message": "...",
                "timestamp": "...",
                "parent_hash": "...",
                "files": {"name": "hash", ...}
            }
        ]
    }
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        dataset_name: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
        storage: Optional[ContentStore] = None,
    ):
        """Initialize the commit store.

        Args:
            root_dir: Root directory for the dataset
            dataset_name: Name of the dataset
            fs: Filesystem to use (auto-detected if None)
            storage: Content store for files (created if None)
        """
        self.root_dir = str(root_dir)
        self.dataset_name = dataset_name
        self.fs = fs or get_filesystem(self.root_dir)
        self.storage = storage or ContentStore(self.root_dir, self.fs)

        # Set up paths
        self.dataset_dir = f"{self.root_dir}/datasets/{dataset_name}"
        self.commits_file = f"{self.dataset_dir}/commits.json"

        # Note: We don't create directories here for S3 compatibility
        # Directories will be created when the first commit is saved

        # Load existing commits
        self._commits_cache: Dict[str, Commit] = {}
        self._load_commits()

        logger.info(
            f"Commit store initialized for dataset '{dataset_name}' at {self.dataset_dir}"
        )

    def save_commit(self, commit: Commit) -> None:
        """Save a commit to the store.

        Args:
            commit: Commit to save
        """
        # Add to cache
        self._commits_cache[commit.hash] = commit

        # Save to file
        self._save_commits()

        logger.info(f"Saved commit {commit.short_hash}: {commit.message}")

    def get_commit(self, commit_hash: str) -> Optional[Commit]:
        """Get a commit by hash.

        Args:
            commit_hash: Hash of the commit to get

        Returns:
            Commit if found, None otherwise
        """
        # Try cache first
        if commit_hash in self._commits_cache:
            return self._commits_cache[commit_hash]

        # Try to resolve partial hash
        if len(commit_hash) < 64:
            full_hash = self._resolve_partial_hash(commit_hash)
            if full_hash:
                return self._commits_cache.get(full_hash)

        return None

    def get_latest_commit(self) -> Optional[Commit]:
        """Get the latest commit in the history.

        Returns:
            Latest commit if any exist, None otherwise
        """
        if not self._commits_cache:
            return None

        # Find commit that is not a parent of any other commit (latest in linear history)
        all_parent_hashes = {
            commit.parent_hash
            for commit in self._commits_cache.values()
            if commit.parent_hash
        }

        for commit in self._commits_cache.values():
            if commit.hash not in all_parent_hashes:
                return commit

        # Fallback: return any commit (shouldn't happen in normal operation)
        return next(iter(self._commits_cache.values()))

    def get_commit_history(self, limit: Optional[int] = None) -> List[Commit]:
        """Get the commit history in chronological order (newest first).

        Args:
            limit: Maximum number of commits to return

        Returns:
            List of commits in chronological order
        """
        if not self._commits_cache:
            return []

        # Build linear history by following parent links
        history = []
        current = self.get_latest_commit()

        while current and (limit is None or len(history) < limit):
            history.append(current)
            current = (
                self._commits_cache.get(current.parent_hash)
                if current.parent_hash
                else None
            )

        return history

    def get_commits(self) -> List[Commit]:
        """Get all commits in the store.

        Returns:
            List of all commits
        """
        return list(self._commits_cache.values())

    def has_commit(self, commit_hash: str) -> bool:
        """Check if a commit exists in the store.

        Args:
            commit_hash: Hash of the commit to check

        Returns:
            True if commit exists, False otherwise
        """
        return commit_hash in self._commits_cache

    def get_commit_count(self) -> int:
        """Get the number of commits in the store.

        Returns:
            Number of commits
        """
        return len(self._commits_cache)

    def is_empty(self) -> bool:
        """Check if the commit store is empty.

        Returns:
            True if no commits exist, False otherwise
        """
        return len(self._commits_cache) == 0

    def _load_commits(self) -> None:
        """Load commits from the JSON file."""
        try:
            if not self.fs.exists(strip_protocol(self.commits_file)):
                logger.info(f"No commits file found at {self.commits_file}")
                return

            with self.fs.open(strip_protocol(self.commits_file), "r") as f:
                data = json.load(f)

            # Load commits from JSON data
            for commit_data in data.get("commits", []):
                try:
                    commit = Commit.from_dict(commit_data, self.storage)
                    self._commits_cache[commit.hash] = commit
                except Exception as e:
                    logger.warning(
                        f"Failed to load commit {commit_data.get('hash', 'unknown')}: {e}"
                    )

            logger.info(
                f"Loaded {len(self._commits_cache)} commits from {self.commits_file}"
            )

        except Exception as e:
            logger.error(f"Failed to load commits from {self.commits_file}: {e}")
            raise IOError(f"Failed to load commits: {e}") from e

    def _save_commits(self) -> None:
        """Save commits to the JSON file."""
        try:
            # Ensure dataset directory exists before writing commits file
            # This is where we actually create directories for S3 compatibility
            self.fs.makedirs(strip_protocol(self.dataset_dir), exist_ok=True)

            # Convert commits to dictionary format
            commits_data = []
            for commit in self._commits_cache.values():
                commits_data.append(commit.to_dict())

            # Create data structure
            data = {"dataset_name": self.dataset_name, "commits": commits_data}

            # Write to file
            with self.fs.open(strip_protocol(self.commits_file), "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"Saved {len(commits_data)} commits to {self.commits_file}")

        except Exception as e:
            logger.error(f"Failed to save commits to {self.commits_file}: {e}")
            raise IOError(f"Failed to save commits: {e}") from e

    def _resolve_partial_hash(self, partial_hash: str) -> Optional[str]:
        """Resolve a partial commit hash to a full hash.

        Args:
            partial_hash: Partial hash to resolve

        Returns:
            Full hash if unique match found, None otherwise
        """
        matches = []
        for commit_hash in self._commits_cache:
            if commit_hash.startswith(partial_hash):
                matches.append(commit_hash)

        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            logger.warning(
                f"Multiple commits match partial hash '{partial_hash}': {matches}"
            )
            return None
        else:
            return None

    def cleanup_orphaned_files(self) -> int:
        """Remove files that are no longer referenced by any commit.

        Returns:
            Number of files removed
        """
        # Get all file hashes referenced by commits
        used_hashes = set()
        for commit in self._commits_cache.values():
            for file in commit.files.values():
                used_hashes.add(file.hash)

        # Clean up orphaned files
        return self.storage.cleanup_orphaned_files(used_hashes)

    def get_dataset_info(self) -> dict:
        """Get information about the dataset.

        Returns:
            Dictionary with dataset information
        """
        latest_commit = self.get_latest_commit()
        history = self.get_commit_history(limit=10)

        return {
            "dataset_name": self.dataset_name,
            "commit_count": len(self._commits_cache),
            "latest_commit": (latest_commit.hash if latest_commit else None),
            "latest_message": (latest_commit.message if latest_commit else None),
            "latest_timestamp": (
                latest_commit.timestamp.isoformat() if latest_commit else None
            ),
            "recent_commits": [
                {
                    "hash": commit.hash,
                    "short_hash": commit.short_hash,
                    "message": commit.message,
                    "timestamp": commit.timestamp.isoformat(),
                    "file_count": len(commit.files),
                }
                for commit in history
            ],
        }
