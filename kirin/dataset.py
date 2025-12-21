"""Dataset entity for Kirin - represents a versioned collection of files with linear history."""  # noqa: E501

import os
import tempfile
from collections.abc import MutableMapping
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import fsspec
from loguru import logger

from .commit import Commit, CommitBuilder
from .commit_store import CommitStore
from .file import File
from .ml_artifacts import (
    extract_sklearn_hyperparameters,
    extract_sklearn_metrics,
    is_sklearn_model,
    serialize_sklearn_model,
)
from .plots import (
    detect_plot_variable_name,
    is_matplotlib_figure,
    is_plotly_figure,
    serialize_plot,
)
from .storage import ContentStore
from .utils import get_filesystem, strip_protocol


def get_image_content_type(
    filename: str, format: Optional[str] = None
) -> Optional[str]:
    """Get content type for image file based on format or filename extension.

    Args:
        filename: Filename to check
        format: Optional format override ('svg' or 'webp')

    Returns:
        Content type string or None if not determinable
    """
    if format:
        return "image/svg+xml" if format == "svg" else "image/webp"

    ext = filename.lower().split(".")[-1] if "." in filename else ""
    content_types = {
        "svg": "image/svg+xml",
        "webp": "image/webp",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
    }
    return content_types.get(ext)


def get_source_file_content_type(filename: str) -> str:
    """Get content type for source file based on extension.

    Args:
        filename: Source filename

    Returns:
        Content type string
    """
    if filename.endswith(".ipynb"):
        return "application/json"
    elif filename.endswith(".py"):
        return "text/x-python"
    else:
        return "text/plain"


class LazyLocalFiles(MutableMapping):
    """Dictionary-like object that lazily downloads files on access.

    Files are only downloaded when accessed via key lookup. Downloaded files
    are cached for fast repeated access. Iterating over keys does not trigger
    downloads.

    Args:
        files: Dictionary mapping filenames to File objects
        temp_dir: Temporary directory for downloaded files
    """

    def __init__(self, files: Dict[str, File], temp_dir: str):
        self._files = files
        self._temp_dir = temp_dir
        self._cache = {}  # filename -> local path cache

    def __getitem__(self, key: str) -> str:
        """Get local path for a file, downloading if necessary.

        Args:
            key: Filename to access

        Returns:
            Local path to the downloaded file

        Raises:
            KeyError: If file doesn't exist
        """
        # If already downloaded, return cached path
        if key in self._cache:
            return self._cache[key]

        # Download on first access
        if key not in self._files:
            raise KeyError(f"File not found: {key}")

        local_path = Path(self._temp_dir) / key
        self._files[key].download_to(local_path)
        self._cache[key] = str(local_path)
        return self._cache[key]

    def __setitem__(self, key: str, value: str) -> None:
        """Set a local path (for internal use)."""
        self._cache[key] = value

    def __delitem__(self, key: str) -> None:
        """Delete a cached file path."""
        if key in self._cache:
            del self._cache[key]

    def __iter__(self):
        """Iterate over filenames without downloading."""
        return iter(self._files)

    def __len__(self) -> int:
        """Return number of files."""
        return len(self._files)

    def __contains__(self, key: str) -> bool:
        """Check if file exists without downloading."""
        return key in self._files

    def keys(self):
        """Return filenames without downloading."""
        return self._files.keys()

    def values(self):
        """Return local paths for downloaded files only."""
        return self._cache.values()

    def items(self):
        """Return (filename, local_path) pairs for downloaded files only."""
        return self._cache.items()

    def get(self, key: str, default=None):
        """Get local path with default if not found."""
        try:
            return self[key]
        except KeyError:
            return default


class Dataset:
    """Represents a versioned collection of files with linear commit history.

    This is the main interface for working with Kirin datasets. It provides
    methods for committing changes, checking out specific versions, and
    accessing files from the current commit.

    The dataset maintains a linear commit history where each commit represents
    a snapshot of files at a point in time. You can checkout any commit to
    access files from that version, or checkout the latest commit by calling
    checkout() without arguments.

    **Important:** New commits can only be created when checked out to the
    latest commit. This ensures linear history without divergent branches.
    If you've checked out an older commit, you must first checkout() to the
    latest commit before making new commits.

    Example:
        # Create a dataset
        dataset = Dataset(root_dir="/path/to/data", name="my_dataset")

        # Commit some files
        commit_hash = dataset.commit(message="Initial commit", add_files=["file1.csv"])

        # Checkout an older commit to view files
        dataset.checkout(commit_hash)

        # Must checkout to latest before committing again
        dataset.checkout()  # Move to latest
        dataset.commit(message="New commit", add_files=["file2.csv"])

    Args:
        root_dir: Root directory for the dataset
        name: Name of the dataset
        description: Description of the dataset
        fs: Filesystem to use (auto-detected if None)
    """

    def __init__(
        self,
        root_dir: Union[str, Path],
        name: str,
        description: str = "",
        fs: Optional[fsspec.AbstractFileSystem] = None,
        # AWS/S3 authentication
        aws_profile: Optional[str] = None,
        # GCP/GCS authentication
        gcs_token: Optional[Union[str, Path]] = None,
        gcs_project: Optional[str] = None,
        # Azure authentication
        azure_account_name: Optional[str] = None,
        azure_account_key: Optional[str] = None,
        azure_connection_string: Optional[str] = None,
    ):
        self.root_dir = str(root_dir)
        self.name = name
        self.description = description
        self.fs = fs or get_filesystem(
            self.root_dir,
            aws_profile=aws_profile,
            gcs_token=gcs_token,
            gcs_project=gcs_project,
            azure_account_name=azure_account_name,
            azure_account_key=azure_account_key,
            azure_connection_string=azure_connection_string,
        )

        # Initialize storage and commit store
        self.storage = ContentStore(self.root_dir, self.fs)
        self.commit_store = CommitStore(self.root_dir, name, self.fs, self.storage)

        # Current commit (lazy loaded)
        self._current_commit: Optional[Commit] = None

        logger.info(f"Dataset '{name}' initialized at {self.root_dir}")

    @property
    def current_commit(self) -> Optional[Commit]:
        """Get the current commit.

        Returns:
            Current commit if any exist, None otherwise
        """
        if self._current_commit is None:
            self._current_commit = self.commit_store.get_latest_commit()
        return self._current_commit

    @current_commit.setter
    def current_commit(self, commit: Optional[Commit]):
        """Set the current commit.

        Args:
            commit: Commit to set as current
        """
        self._current_commit = commit

    @property
    def head(self) -> Optional[Commit]:
        """Get the latest commit (alias for current_commit)."""
        return self.current_commit

    @property
    def files(self) -> Dict[str, File]:
        """Get files from the current commit.

        Returns:
            Dictionary mapping filenames to File objects
        """
        if self.current_commit is None:
            return {}
        return self.current_commit.files

    def commit(
        self,
        message: str,
        add_files: List[Union[str, Path, Any]] = None,
        remove_files: List[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
    ) -> str:
        """Create a new commit with changes.

        **Enhanced for ML artifacts:**

        - **Model objects**: If `add_files` contains scikit-learn model objects,
          they are automatically serialized, and hyperparameters/metrics are
          extracted and added to metadata.

        - **Plot objects**: If `add_files` contains matplotlib or plotly figure
          objects, they are automatically converted to files (SVG for vector plots,
          WebP for raster plots) with format auto-detection.

        Args:
            message: Commit message
            add_files: List of files (paths), model objects, or plot objects to add.
                      Can include:
                      - File paths (str or Path): Regular files
                      - scikit-learn model objects: Automatically serialized
                      - matplotlib/plotly figures: Automatically converted to
                        SVG/WebP
            remove_files: List of filenames to remove
            metadata: Optional metadata dictionary (merged with auto-extracted metadata)
            tags: Optional list of tags for staging/versioning

        Returns:
            Hash of the new commit

        Raises:
            ValueError: If no changes are specified or if not on latest commit
            FileNotFoundError: If a file to add doesn't exist
        """
        if not add_files and not remove_files:
            raise ValueError(
                "No changes specified - at least one of add_files or "
                "remove_files must be provided"
            )

        # Ensure we're on the latest commit before allowing new commits
        latest_commit = self.commit_store.get_latest_commit()
        if latest_commit is not None:  # Only check if commits exist
            if (
                self.current_commit is None
                or self.current_commit.hash != latest_commit.hash
            ):
                raise ValueError(
                    "Cannot commit: currently checked out to non-latest commit. "
                    "Use checkout() to move to the latest commit first."
                )

        # Start building commit from current state
        builder = CommitBuilder(self.current_commit)

        # Process files, model objects, and plot objects
        models_metadata = {}
        processed_files = []
        temp_dirs = []  # Track temp dirs for cleanup

        if add_files:
            for item in add_files:
                if isinstance(item, (str, Path)):
                    # Existing file path handling
                    file_path = str(item)

                    # Check if file exists
                    source_fs = get_filesystem(file_path)
                    if not source_fs.exists(strip_protocol(file_path)):
                        raise FileNotFoundError(f"File not found: {file_path}")

                    processed_files.append(file_path)
                elif is_sklearn_model(item):
                    # Handle model object
                    # Detect variable name - required, no fallback
                    from .ml_artifacts import detect_model_variable_name

                    var_name = detect_model_variable_name(item)
                    if not var_name:
                        raise ValueError(
                            f"Could not detect variable name for model object of type "
                            f"{item.__class__.__name__}. "
                            "Variable name detection is required for model objects. "
                            "Ensure the model is assigned to a variable before passing "
                            "it to commit()."
                        )

                    # Create temporary directory for model serialization
                    temp_dir = tempfile.mkdtemp(prefix=f"kirin_model_{var_name}_")
                    temp_dirs.append(temp_dir)

                    # Serialize model (raises error if fails)
                    model_path, source_path, source_hash = serialize_sklearn_model(
                        item,
                        variable_name=var_name,
                        temp_dir=temp_dir,
                        storage=self.storage,
                    )
                    processed_files.append(model_path)

                    # Extract metadata
                    from .ml_artifacts import get_sklearn_version

                    model_meta = {
                        "model_type": item.__class__.__name__,
                        "hyperparameters": extract_sklearn_hyperparameters(item),
                        "metrics": extract_sklearn_metrics(item),
                    }

                    # Add scikit-learn version if available
                    sklearn_version = get_sklearn_version()
                    if sklearn_version:
                        model_meta["sklearn_version"] = sklearn_version

                    # Add source linking if available
                    if source_path and source_hash:
                        model_meta["source_file"] = os.path.basename(source_path)
                        model_meta["source_hash"] = source_hash

                    models_metadata[var_name] = model_meta
                elif is_matplotlib_figure(item) or is_plotly_figure(item):
                    # Handle plot object
                    # Detect variable name - required, no fallback
                    var_name = detect_plot_variable_name(item)
                    if not var_name:
                        raise ValueError(
                            f"Could not detect variable name for plot object of type "
                            f"{item.__class__.__name__}. "
                            "Variable name detection is required for plot objects. "
                            "Ensure the plot is assigned to a variable before passing "
                            "it to commit()."
                        )

                    # Clean up variable name for filename:
                    # - Remove leading underscore (private variables)
                    clean_name = var_name.lstrip("_")

                    # Create temporary directory for plot serialization
                    temp_dir = tempfile.mkdtemp(prefix=f"kirin_plot_{clean_name}_")
                    temp_dirs.append(temp_dir)

                    # Serialize plot (auto-detects format: SVG for vector,
                    # WebP for raster). Use cleaned name for filename
                    plot_path, source_path, source_hash = serialize_plot(
                        item,
                        variable_name=clean_name,
                        temp_dir=temp_dir,
                        storage=self.storage,
                    )
                    processed_files.append(plot_path)

                    # Note: Plot metadata could be added here if needed in the future
                    # For now, plots are just stored as files
                else:
                    # Unknown type - raise error
                    raise ValueError(
                        f"Unsupported item type in add_files: {type(item)}. "
                        "Expected str, Path, scikit-learn model, or "
                        "matplotlib/plotly figure."
                    )

        # Add processed files to commit
        if processed_files:
            for file_path in processed_files:
                file_path = str(file_path)

                # Check if file exists
                source_fs = get_filesystem(file_path)
                if not source_fs.exists(strip_protocol(file_path)):
                    raise FileNotFoundError(f"File not found: {file_path}")

                # Store file in content store
                content_hash = self.storage.store_file(file_path)

                # Create File object
                file_size = source_fs.size(strip_protocol(file_path))
                file_obj = File(
                    hash=content_hash,
                    name=Path(file_path).name,
                    size=file_size,
                    _storage=self.storage,
                )

                # Add to commit
                builder.add_file(file_obj.name, file_obj)

        # Structure metadata for multiple models
        auto_metadata = {}
        if models_metadata:
            auto_metadata["models"] = models_metadata

        # Merge with user-provided metadata
        final_metadata = {**auto_metadata, **(metadata or {})}

        # If user provided model-specific metadata, merge it into each model's entry
        if "models" in (metadata or {}) and "models" in auto_metadata:
            user_models_metadata = metadata["models"]
            for var_name, model_meta in models_metadata.items():
                if var_name in user_models_metadata:
                    # Merge user-provided model metadata (user wins on conflicts)
                    models_metadata[var_name] = {
                        **model_meta,  # Auto-extracted first
                        **user_models_metadata[var_name],  # User-provided overrides
                    }
            final_metadata["models"] = models_metadata

        # Remove files
        if remove_files:
            for filename in remove_files:
                builder.remove_file(filename)

        # Set metadata and tags
        if final_metadata:
            builder.set_metadata(final_metadata)

        if tags:
            builder.add_tags(tags)

        # Build and save commit
        commit = builder(message)
        self.commit_store.save_commit(commit)
        self._current_commit = commit

        # Clean up temporary directories
        import shutil

        for temp_dir in temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary directory {temp_dir}: {e}"
                )

        logger.info(f"Created commit {commit.short_hash}: {message}")
        return commit.hash

    def checkout(self, commit_hash: Optional[str] = None) -> None:
        """Checkout a specific commit or the latest commit.

        This method allows you to switch between different versions of your dataset.
        You can checkout a specific commit by providing its hash, or checkout the
        latest commit by calling without arguments.

        Args:
            commit_hash: Hash of the commit to checkout (can be partial hash).
                        If None or not provided, checks out the latest commit.

        Raises:
            ValueError: If commit not found or no commits exist in dataset

        Examples:
            # Checkout the latest commit
            dataset.checkout()

            # Checkout a specific commit by full hash
            dataset.checkout("abc123def456...")

            # Checkout a specific commit by partial hash
            dataset.checkout("abc123")
        """
        if commit_hash is None:
            # Checkout the latest commit
            commit = self.commit_store.get_latest_commit()
            if commit is None:
                raise ValueError("No commits found in dataset")
        else:
            # Checkout specific commit
            commit = self.commit_store.get_commit(commit_hash)
            if commit is None:
                raise ValueError(f"Commit not found: {commit_hash}")

        self.current_commit = commit
        logger.info(f"Checked out commit {commit.short_hash}: {commit.message}")

    def get_file(self, name: str) -> Optional[File]:
        """Get a file from the current commit.

        Args:
            name: Name of the file to get

        Returns:
            File object if found, None otherwise
        """
        if self.current_commit is None:
            return None
        return self.current_commit.get_file(name)

    def list_files(self) -> List[str]:
        """List files in the current commit.

        Returns:
            List of filenames
        """
        if self.current_commit is None:
            return []
        return self.current_commit.list_files()

    def has_file(self, name: str) -> bool:
        """Check if a file exists in the current commit.

        Args:
            name: Name of the file to check

        Returns:
            True if file exists, False otherwise
        """
        if self.current_commit is None:
            return False
        return self.current_commit.has_file(name)

    def read_file(self, name: str, mode: str = "r") -> Union[str, bytes]:
        """Read a file from the current commit.

        Args:
            name: Name of the file to read
            mode: Read mode ('r' for text, 'rb' for bytes)

        Returns:
            File content

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_obj = self.get_file(name)
        if file_obj is None:
            raise FileNotFoundError(f"File not found: {name}")

        return file_obj.read(mode)

    def download_file(self, name: str, target_path: Union[str, Path]) -> str:
        """Download a file from the current commit.

        Args:
            name: Name of the file to download
            target_path: Local path to save the file

        Returns:
            Path where the file was saved

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_obj = self.get_file(name)
        if file_obj is None:
            raise FileNotFoundError(f"File not found: {name}")

        return file_obj.download_to(target_path)

    def open_file(self, name: str, mode: str = "rb"):
        """Open a file from the current commit.

        Args:
            name: Name of the file to open
            mode: Open mode

        Returns:
            File-like object

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_obj = self.get_file(name)
        if file_obj is None:
            raise FileNotFoundError(f"File not found: {name}")

        return file_obj.open(mode)

    @contextmanager
    def local_files(self):
        """Context manager for accessing files as local paths.

        Files are downloaded lazily on first access and cached for fast repeated
        access. Iterating over keys does not trigger downloads. Files are
        automatically cleaned up when exiting the context.

        Yields:
            LazyLocalFiles object that behaves like a dictionary mapping
            filenames to local file paths
        """
        if self.current_commit is None:
            yield {}
            return

        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"kirin_{self.name}_")

        try:
            # Return lazy-loading dict-like object
            yield LazyLocalFiles(self.current_commit.files, temp_dir)

        finally:
            # Clean up all downloaded files
            import shutil

            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary directory {temp_dir}: {e}"
                )

    def history(self, limit: Optional[int] = None) -> List[Commit]:
        """Get commit history.

        Args:
            limit: Maximum number of commits to return

        Returns:
            List of commits in chronological order (newest first)
        """
        return self.commit_store.get_commit_history(limit)

    def get_commit(self, commit_hash: str) -> Optional[Commit]:
        """Get a specific commit.

        Args:
            commit_hash: Hash of the commit to get

        Returns:
            Commit if found, None otherwise
        """
        return self.commit_store.get_commit(commit_hash)

    def get_commits(self) -> List[Commit]:
        """Get all commits in the dataset.

        Returns:
            List of all commits
        """
        return self.commit_store.get_commits()

    def is_empty(self) -> bool:
        """Check if the dataset is empty (no commits).

        Returns:
            True if no commits exist, False otherwise
        """
        return self.commit_store.is_empty()

    def get_info(self) -> dict:
        """Get information about the dataset.

        Returns:
            Dictionary with dataset information
        """
        info = self.commit_store.get_dataset_info()
        info.update(
            {
                "name": self.name,
                "description": self.description,
                "root_dir": self.root_dir,
                "current_commit": self.current_commit.hash
                if self.current_commit
                else None,
            }
        )
        return info

    def cleanup_orphaned_files(self) -> int:
        """Remove files that are no longer referenced by any commit.

        Returns:
            Number of files removed
        """
        return self.commit_store.cleanup_orphaned_files()

    def to_dict(self) -> dict:
        """Convert the dataset to a dictionary representation.

        Returns:
            Dictionary with dataset properties
        """
        return {
            "name": self.name,
            "description": self.description,
            "root_dir": self.root_dir,
            "current_commit": self.current_commit.hash if self.current_commit else None,
            "commit_count": self.commit_store.get_commit_count(),
        }

    def __str__(self) -> str:
        """String representation of the dataset."""
        commit_count = self.commit_store.get_commit_count()
        current_hash = self.current_commit.short_hash if self.current_commit else "None"
        return (
            f"Dataset(name='{self.name}', commits={commit_count}, "
            f"current={current_hash})"
        )

    def find_commits(
        self,
        tags: Optional[List[str]] = None,
        metadata_filter: Optional[Callable[[Dict[str, Any]], bool]] = None,
        limit: Optional[int] = None,
    ) -> List[Commit]:
        """Find commits matching criteria.

        Args:
            tags: Filter by tags (commits must have ALL specified tags)
            metadata_filter: Callable that takes metadata dict and returns bool
            limit: Maximum number of commits to return

        Returns:
            List of matching commits (newest first)

        Examples:
            # Find production models
            ds.find_commits(tags=["production"])

            # Find models with accuracy > 0.9
            ds.find_commits(metadata_filter=lambda m: m.get("accuracy", 0) > 0.9)

            # Combine criteria
            ds.find_commits(
                tags=["production"],
                metadata_filter=lambda m: m.get("framework") == "pytorch"
            )
        """
        commits = self.history()

        # Filter by tags
        if tags:
            commits = [c for c in commits if all(tag in c.tags for tag in tags)]

        # Filter by metadata
        if metadata_filter:
            commits = [c for c in commits if metadata_filter(c.metadata)]

        # Apply limit
        if limit:
            commits = commits[:limit]

        return commits

    def compare_commits(self, hash1: str, hash2: str) -> dict:
        """Compare metadata between two commits.

        Args:
            hash1: First commit hash
            hash2: Second commit hash

        Returns:
            Dictionary with comparison results
        """
        commit1 = self.get_commit(hash1)
        commit2 = self.get_commit(hash2)

        if not commit1 or not commit2:
            raise ValueError("One or both commits not found")

        return {
            "commit1": {"hash": commit1.short_hash, "message": commit1.message},
            "commit2": {"hash": commit2.short_hash, "message": commit2.message},
            "metadata_diff": {
                "added": {
                    k: v
                    for k, v in commit2.metadata.items()
                    if k not in commit1.metadata
                },
                "removed": {
                    k: v
                    for k, v in commit1.metadata.items()
                    if k not in commit2.metadata
                },
                "changed": {
                    k: {"old": commit1.metadata[k], "new": commit2.metadata[k]}
                    for k in set(commit1.metadata) & set(commit2.metadata)
                    if commit1.metadata[k] != commit2.metadata[k]
                },
            },
            "tags_diff": {
                "added": [t for t in commit2.tags if t not in commit1.tags],
                "removed": [t for t in commit1.tags if t not in commit2.tags],
            },
        }

    def __repr__(self) -> str:
        """Detailed string representation of the dataset."""
        return (
            f"Dataset(name='{self.name}', description='{self.description}', "
            f"root_dir='{self.root_dir}')"
        )

    def _get_widget_data(self) -> dict:
        """Get widget data dictionary for DatasetWidget.

        Returns:
            Dictionary with dataset data for widget rendering
        """
        from .html_repr import format_file_size, get_file_icon_html

        commit_count = self.commit_store.get_commit_count()
        total_size = None
        current_commit_data = None

        if self.current_commit:
            total_size = format_file_size(self.current_commit.get_total_size())
            current_commit_data = {
                "hash": self.current_commit.short_hash,
                "message": self.current_commit.message,
                "timestamp": self.current_commit.timestamp.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }

        # Build files list with content for preview
        files = []
        if self.current_commit and self.files:
            for filename, file_obj in sorted(self.files.items()):
                file_data = {
                    "name": filename,
                    "size": format_file_size(file_obj.size),
                    "icon_html": get_file_icon_html(filename, file_obj.content_type),
                    "content_type": file_obj.content_type,
                }

                # Add file content for preview (only for small text files)
                # Limit to 100KB for text files
                max_preview_size = 100 * 1024  # 100KB
                # Check if file is text-based
                is_text_file = (
                    file_obj.content_type
                    and (
                        file_obj.content_type.startswith("text/")
                        or file_obj.content_type
                        in ["application/json", "application/xml"]
                    )
                ) or filename.lower().endswith((".txt", ".csv", ".json", ".md", ".py"))
                is_image = (
                    file_obj.content_type
                    and file_obj.content_type.startswith("image/")
                    or filename.lower().endswith(
                        (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg")
                    )
                )

                if is_text_file and file_obj.size <= max_preview_size:
                    try:
                        content = file_obj.read_text()
                        file_data["content"] = content
                        file_data["is_text"] = True
                    except Exception as e:
                        logger.debug(f"Failed to read file {filename} for preview: {e}")
                        file_data["content"] = None
                        file_data["is_text"] = False
                elif is_image:
                    # For images, we'll need to get the data URL or path
                    # For now, mark it as an image
                    file_data["is_image"] = True
                    file_data["is_text"] = False
                else:
                    file_data["is_text"] = False
                    file_data["is_image"] = False

                files.append(file_data)

        # Build commit history (last 10)
        history = []
        for commit in self.history(limit=10):
            history.append(
                {
                    "hash": commit.short_hash,
                    "message": commit.message,
                    "timestamp": commit.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "file_count": len(commit.files),
                    "size": format_file_size(commit.get_total_size()),
                }
            )

        # Get variable name for code snippets
        variable_name = getattr(self, "_repr_variable_name", "dataset")

        return {
            "name": self.name,
            "description": self.description,
            "commit_count": commit_count,
            "total_size": total_size,
            "current_commit": current_commit_data,
            "files": files,
            "history": history,
            "has_commit": self.current_commit is not None,
            "variable_name": variable_name,
        }

    def _repr_html_(self) -> str:
        """Generate HTML representation of the dataset for notebook display.

        The variable name used in code snippets can be customized by setting
        `dataset._repr_variable_name = "your_variable_name"` before displaying.

        Returns:
            HTML string with dataset information, files, and commit history
        """
        # Use widgets - let errors propagate for debugging
        from .widgets import DatasetWidget

        widget = DatasetWidget(data=self._get_widget_data())
        return widget._repr_html_()
