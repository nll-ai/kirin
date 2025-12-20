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
from .plots import save_plot as save_plot_func
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

        - **Plot objects**: Use `save_plot()` first, then commit the returned path.

        Args:
            message: Commit message
            add_files: List of files (paths) or model objects to add
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

        # Process files and model objects
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
                    # New: Handle model object
                    # Detect variable name
                    from .ml_artifacts import detect_model_variable_name

                    var_name = detect_model_variable_name(item)
                    if not var_name:
                        var_name = item.__class__.__name__

                    # Create temporary directory for model serialization
                    temp_dir = tempfile.mkdtemp(prefix=f"kirin_model_{var_name}_")
                    temp_dirs.append(temp_dir)

                    # Serialize model (raises error if fails)
                    model_path, source_path, source_hash = (
                        serialize_sklearn_model(
                            item,
                            variable_name=var_name,
                            temp_dir=temp_dir,
                            storage=self.storage,
                        )
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
                else:
                    # Unknown type - raise error
                    raise ValueError(
                        f"Unsupported item type in add_files: {type(item)}. "
                        "Expected str, Path, or scikit-learn model object."
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

    def save_plot(
        self,
        plot_object: Union[  # noqa: F821
            "matplotlib.figure.Figure", "plotly.graph_objects.Figure", object  # noqa: F821
        ],
        filename: str,
        auto_commit: bool = False,
        message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        format: Optional[str] = None,
    ) -> str:
        """Save a plot to the dataset with automatic format detection.

        This method saves plots from matplotlib, plotly, and other plotting
        libraries in optimal formats (SVG for vectors, WebP for bitmaps).

        **Two modes of operation:**

        1. **Default mode** (auto_commit=False): Returns file path, user commits
           explicitly. This allows batching multiple plots in one commit.

           Example:
               plot_path = dataset.save_plot(fig, "plot.png")
               dataset.commit(message="Add plot", add_files=[plot_path])

        2. **Auto-commit mode** (auto_commit=True): Automatically commits the
           plot and returns the commit hash. More ergonomic for single-plot
           workflows.

           Example:
               commit_hash = dataset.save_plot(
                   fig, "plot.png", auto_commit=True, message="Add plot"
               )

        **Important: Strict Content Hashing for SVG Plots**

        Kirin uses **strict content-addressed hashing** based on exact file
        content. For SVG plots saved from matplotlib:

        - **Identical plots produce different hashes**: Even if you create the
          same plot twice (same data, same code), the SVG files will have
          different hashes because matplotlib embeds creation timestamps in
          the SVG metadata.

        - **Each save creates a new commit**: Saving the same plot multiple
          times will create separate commits, each with a unique hash. This is
          the strictest form of content-addressed storage.

        - **This is by design**: The timestamp metadata is part of the file
          content, so it affects the hash. This ensures complete content
          integrity and prevents accidental overwrites.

        - **For reproducible plots**: If you need identical plots to produce
          identical hashes, consider using WebP format (raster) instead of SVG,
          or strip metadata before saving (not currently implemented).

        Args:
            plot_object: The plot object to save (matplotlib Figure, plotly Figure,
                etc.)
            filename: Desired filename for the plot (extension may be adjusted)
            auto_commit: If True, automatically commits the plot. If False, returns
                        file path for explicit commit.
            message: Commit message (required if auto_commit=True)
            metadata: Optional metadata dictionary for the commit
            tags: Optional list of tags for the commit
            format: Optional format override ('svg' or 'webp'). If None, auto-detects.

        Returns:
            If auto_commit=False: File path (str) that can be used in commit()
            If auto_commit=True: Commit hash (str) of the created commit

        Raises:
            ValueError: If auto_commit=True but message is not provided
            ValueError: If plot type is not supported
        """
        # Validate auto_commit requirements
        if auto_commit and not message:
            raise ValueError("message is required when auto_commit=True")

        # Save plot using the plots module
        # Returns: hash, filename, source path, source hash
        (
            content_hash,
            actual_filename,
            source_file_path,
            source_file_hash,
        ) = save_plot_func(plot_object, filename, self.storage, format=format)

        # Create a temporary file path that points to the stored content
        # We need to create a File object to use in the commit
        # But first, let's handle the two modes

        if auto_commit:
            # Auto-commit mode: create commit immediately
            # We need to create a File object for the stored plot
            file_size = self.storage.get_size(content_hash, actual_filename)

            # Determine content type based on format or filename
            content_type = get_image_content_type(actual_filename, format)

            # Create plot file with source metadata if available
            plot_metadata = {}
            if source_file_path and source_file_hash:
                source_filename = os.path.basename(source_file_path)
                plot_metadata = {
                    "source_file": source_filename,
                    "source_hash": source_file_hash,
                }

            file_obj = File(
                hash=content_hash,
                name=actual_filename,
                size=file_size,
                content_type=content_type,
                metadata=plot_metadata,
                _storage=self.storage,
            )

            # Build commit with the plot file
            builder = CommitBuilder(self.current_commit)
            builder.add_file(actual_filename, file_obj)

            # If source file was detected, add it to the commit as well
            if source_file_path and source_file_hash:
                source_filename = os.path.basename(source_file_path)
                source_file_size = self.storage.get_size(
                    source_file_hash, source_filename
                )

                # Determine content type for source file
                source_content_type = get_source_file_content_type(source_filename)

                source_file_obj = File(
                    hash=source_file_hash,
                    name=source_filename,
                    size=source_file_size,
                    content_type=source_content_type,
                    _storage=self.storage,
                )
                builder.add_file(source_filename, source_file_obj)

            # Set metadata and tags if provided
            if metadata:
                builder.set_metadata(metadata)
            if tags:
                builder.add_tags(tags)

            # Build and save commit
            commit = builder(message)
            self.commit_store.save_commit(commit)
            self._current_commit = commit

            logger.info(
                f"Saved and committed plot {actual_filename} "
                f"with hash {content_hash[:8]}"
            )
            return commit.hash
        else:
            # Default mode: return file path(s) for explicit commit
            # Since the file is already in content-addressed storage, we need to
            # create a temporary file that commit() can read from
            # The commit will store it again, but it will be deduplicated

            # Create temporary file with the plot content
            temp_file = tempfile.NamedTemporaryFile(
                mode="wb", delete=False, suffix=f"_{actual_filename}"
            )
            try:
                # Retrieve content from storage and write to temp file
                content = self.storage.retrieve(content_hash, actual_filename)
                temp_file.write(content)
                temp_file.close()
                temp_path = temp_file.name

                # Note: Source file is already stored in ContentStore if detected
                # In default mode, we return only the plot path for backward
                # compatibility. Source file will be automatically included in
                # auto_commit mode. For default mode, users can manually retrieve
                # and commit source if needed
                return temp_path
                # Note: We can't clean it up here because commit() needs to read it
                # The user is responsible for cleanup, or we could use a context manager
                # For now, return the path - the file will be cleaned up by the OS
                # eventually, or we could add cleanup logic later
                return temp_file.name
            except Exception:
                # Clean up temp file on error
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)
                raise

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

    def _repr_html_(self) -> str:
        """Generate HTML representation of the dataset for notebook display.

        The variable name used in code snippets can be customized by setting
        `dataset._repr_variable_name = "your_variable_name"` before displaying.

        Returns:
            HTML string with dataset information, files, and commit history
        """
        from .html_repr import (
            escape_html,
            format_file_size,
            generate_file_access_code,
            get_file_icon_html,
            get_inline_css,
            get_inline_javascript,
        )

        # Get variable name: manual override > default
        variable_name = getattr(self, "_repr_variable_name", "dataset")

        html_parts = ['<div class="kirin-dataset-view">']

        # Add inline CSS
        html_parts.append(f"<style>{get_inline_css()}</style>")

        # Dataset header panel
        html_parts.append('<div class="panel">')
        html_parts.append('<div class="panel-header">')
        html_parts.append(f'<h2 class="panel-title">{escape_html(self.name)}</h2>')
        html_parts.append("</div>")
        html_parts.append('<div class="panel-content">')

        # Dataset metadata
        html_parts.append('<div class="space-y-4">')
        if self.description:
            html_parts.append(
                f'<p class="text-muted-foreground">{escape_html(self.description)}</p>'
            )

        commit_count = self.commit_store.get_commit_count()
        html_parts.append(
            f'<div class="flex items-center gap-4">'
            f'<span class="text-sm text-muted-foreground">'
            f"Commits: {commit_count}</span>"
        )

        if self.current_commit:
            total_size = self.current_commit.get_total_size()
            html_parts.append(
                f'<span class="text-sm text-muted-foreground">'
                f"Size: {format_file_size(total_size)}</span>"
            )
        html_parts.append("</div>")

        # Current commit info
        if self.current_commit:
            html_parts.append(
                f'<div><span class="text-sm text-muted-foreground">'
                f"Current Commit:</span> "
                f'<span class="commit-hash">'
                f"{escape_html(self.current_commit.short_hash)}</span> "
                f'<span class="text-sm">'
                f"{escape_html(self.current_commit.message)}</span></div>"
            )
        else:
            html_parts.append('<p class="text-muted-foreground">No commits yet</p>')

        html_parts.append("</div>")  # space-y-4
        html_parts.append("</div>")  # panel-content
        html_parts.append("</div>")  # panel

        # Files list (from current commit)
        if self.current_commit and self.current_commit.files:
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-header">')
            html_parts.append('<h3 class="panel-title">Files</h3>')
            html_parts.append("</div>")
            html_parts.append('<div class="panel-content">')

            for filename, file_obj in sorted(self.files.items()):
                # Create unique code ID for this file
                code_id = (
                    f"code-{self.name}-"
                    f"{filename.replace('.', '-').replace('/', '-').replace(' ', '-')}"
                )
                html_parts.append(
                    f'<div class="file-item" data-code-id="{code_id}" '
                    f'style="cursor: pointer;">'
                )
                html_parts.append(
                    f'<div class="file-icon">'
                    f"{get_file_icon_html(filename, file_obj.content_type)}</div>"
                )
                html_parts.append(
                    f'<div class="file-name">{escape_html(filename)}</div>'
                )
                # Generate the code to copy
                var_name = getattr(self, "_repr_variable_name", "dataset")
                code_to_copy = (
                    f"# Get path to local clone of file\n"
                    f"with {var_name}.local_files() as files:\n"
                    f'    file_path = files["{escape_html(filename)}"]'
                )
                # Escape for HTML attribute (but keep newlines)
                code_attr = escape_html(code_to_copy).replace("\n", "&#10;")
                html_parts.append(
                    f'<button class="btn btn-sm btn-ghost copy-code-btn" '
                    f'data-code-id="{code_id}" '
                    f'data-code="{code_attr}" '
                    f'data-filename="{escape_html(filename)}" '
                    f'title="Copy code to access file">'
                    f"Copy Code to Access</button>"
                )
                html_parts.append(
                    f'<div class="file-size">{format_file_size(file_obj.size)}</div>'
                )
                html_parts.append("</div>")

                # Add code snippet for accessing this file (hidden by default)
                html_parts.append(
                    generate_file_access_code(code_id, filename, variable_name)
                )

            html_parts.append("</div>")  # panel-content
            html_parts.append("</div>")  # panel
        elif self.current_commit:
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-content">')
            html_parts.append(
                '<p class="text-muted-foreground">No files in current commit</p>'
            )
            html_parts.append("</div>")
            html_parts.append("</div>")

        # Commit history (limited to last 10 for performance)
        history = self.history(limit=10)
        if history:
            html_parts.append('<div class="panel">')
            html_parts.append('<div class="panel-header">')
            html_parts.append('<h3 class="panel-title">Recent Commits</h3>')
            html_parts.append("</div>")
            html_parts.append('<div class="panel-content">')

            for commit in history:
                html_parts.append('<div class="commit-item">')
                html_parts.append(
                    f'<div class="flex items-center justify-between gap-4">'
                    f"<div>"
                    f'<span class="commit-hash">'
                    f"{escape_html(commit.short_hash)}</span> "
                    f'<span class="commit-message">'
                    f"{escape_html(commit.message)}</span>"
                    f"</div>"
                    f'<span class="commit-timestamp">'
                    f"{escape_html(commit.timestamp.strftime('%Y-%m-%d %H:%M:%S'))}"
                    f"</span>"
                    f"</div>"
                )
                html_parts.append(
                    f'<div class="text-sm text-muted-foreground mt-2">'
                    f"{len(commit.files)} files, "
                    f"{format_file_size(commit.get_total_size())}"
                    f"</div>"
                )
                html_parts.append("</div>")  # commit-item

            html_parts.append("</div>")  # panel-content
            html_parts.append("</div>")  # panel

        # Add inline JavaScript
        html_parts.append(get_inline_javascript())

        html_parts.append("</div>")  # kirin-dataset-view

        return "".join(html_parts)
