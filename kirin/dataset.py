"""Implementation for the Dataset and DatasetCommit classes."""

import os
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import List, Optional

import fsspec
import json5 as json
from loguru import logger

from .models import BranchManager
from .utils import strip_protocol


def get_filesystem(path: str | Path) -> fsspec.AbstractFileSystem:
    """Get the appropriate filesystem based on the path URI.

    Automatically detects the filesystem type from the URI scheme:
    - s3://bucket/path → S3 (requires s3fs)
      - Also works with S3-compatible services like Minio, Backblaze B2,
        DigitalOcean Spaces
      - Configure via environment variables or pass custom fs with endpoint_url
    - gs://bucket/path or gcs://bucket/path → GCS (requires gcsfs)
    - az://container/path or abfs://container/path → Azure (requires adlfs)
    - /local/path or file:///local/path → Local filesystem
    - http://... or https://... → HTTP/HTTPS (requires aiohttp)
    - And many more supported by fsspec (ftp, sftp, hdfs, github, etc.)

    :param path: The path or URI to parse (can be str or Path object).
    :return: An fsspec filesystem instance.
    :raises ValueError: If protocol not recognized or dependencies missing.

    Examples:
        >>> # Local filesystem
        >>> fs = get_filesystem("/path/to/data")
        >>> # S3
        >>> fs = get_filesystem("s3://my-bucket/path")
        >>> # Minio (S3-compatible)
        >>> fs = get_filesystem("s3://my-bucket/path")  # Use env vars for endpoint
        >>> # Google Cloud Storage
        >>> fs = get_filesystem("gs://my-bucket/path")
    """
    # Convert Path objects to string
    path_str = str(path)

    # Handle relative or absolute local paths without scheme
    if "://" not in path_str:
        return fsspec.filesystem("file")

    # Extract protocol from URI
    protocol = path_str.split("://")[0]

    # Mapping of protocols to their required packages
    protocol_packages = {
        "s3": "s3fs",
        "gs": "gcsfs",
        "gcs": "gcsfs",
        "az": "adlfs",
        "abfs": "adlfs",
        "adl": "adlfs",
        "hdfs": "hdfs3 or pyarrow",
        "http": "aiohttp",
        "https": "aiohttp",
        "ftp": "fsspec",
        "sftp": "paramiko",
        "ssh": "paramiko",
        "github": "fsspec",
        "zip": "fsspec",
        "tar": "fsspec",
        "memory": "fsspec",
        "cached": "fsspec",
    }

    try:
        return fsspec.filesystem(protocol)
    except ImportError as e:
        # Get the package name for the protocol if known
        package = protocol_packages.get(protocol, f"fsspec[{protocol}]")
        raise ValueError(
            f"The '{protocol}' protocol requires additional dependencies. "
            f"Please install with: pip install {package}\n"
            f"Original error: {e}"
        ) from e
    except ValueError as e:
        # Protocol not recognized by fsspec
        available_protocols = ", ".join(sorted(fsspec.available_protocols()))
        raise ValueError(
            f"Protocol '{protocol}' is not recognized by fsspec. "
            f"Available protocols: {available_protocols}\n"
            f"Original error: {e}"
        ) from e
    except Exception as e:
        # Catch any other errors and provide helpful message
        raise ValueError(
            f"Failed to create filesystem for protocol '{protocol}'. Error: {e}"
        ) from e


def hash_file(filepath: str, fs: Optional[fsspec.AbstractFileSystem] = None) -> str:
    """Hash a file's contents using sha256 and return the hash hex digest.

    :param filepath: The path to the file to hash.
    :param fs: The filesystem to use. If None, uses local filesystem.
    :return: The hash hex digest, a hex string.
    """
    if fs is None:
        fs = fsspec.filesystem("file")

    hash = sha256()
    with fs.open(str(filepath), "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash.update(chunk)
    return hash.hexdigest()


def default_return_value(return_val):
    """A decorator that sets the return value of a function to a default value.

    :param return_val: The default return value.
    :return: The outer wrapper function.
    """

    def outer_wrapper(func):
        """Wrapper function for the decorated function.

        :param func: The function to decorate.
        :return: The inner_wrapper function for the decorated function.
        """

        def inner_wrapper(*args, **kwargs):
            """Inner decorator function for the wrapper function.

            :param args: The arguments to pass to the decorated function.
            :param kwargs: The keyword arguments to pass to the decorated function.
            :return: The return value of the decorated function,
                or else the return value of the default_return_value.
            """
            try:
                return func(*args, **kwargs)
            except Exception:
                return return_val

        return inner_wrapper

    return outer_wrapper


# A decorator on a class method that automatically calls self.to_json()
# and writes it to self.json_path.
def autowrite_json(func):
    """A decorator on a class method to auto dump to the object's json_path.

    :param func: The function to decorate.
    """

    def inner(self, *args, **kwargs):
        """Wrapper function for the decorated function.

        :param self: The object to decorate.
        :param args: The arguments to pass to the decorated function.
        :param kwargs: The keyword arguments to pass to the decorated function.
        """
        out = func(self, *args, **kwargs)

        # Write the json to the json_path.
        # Strip protocol for filesystem operations
        json_path = strip_protocol(self.json_path)

        # Get parent directory
        if "/" in json_path:
            parent_path = json_path.rsplit("/", 1)[0]
        else:
            parent_path = "."

        if not self.fs.exists(parent_path):
            self.fs.makedirs(parent_path, exist_ok=True)
        with self.fs.open(json_path, "w") as f:
            f.write(json.dumps(self.to_dict()))

        return out

    return inner


@dataclass
class DatasetCommit:
    """The definition of a commit is the state of the dataset as checked in by a user.

    The state of the dataset is defined by the files that are present in the dataset.
    This is represented by hashing all of the files in the dataset.
    The source of truth for the DatasetCommit
    is stored in the commit.json file of each commit hash.
    Any class method that modifies the state of the dataset
    must be decorated with @autowrite_json.

    A DatasetCommit is always associated with a Dataset.
    """

    root_dir: str | Path
    dataset_name: str
    version_hash: str = field(default="")
    commit_message: str = field(default="")
    file_hashes: list[str] = field(default_factory=list)
    parent_hash: str = field(default="")
    parent_hashes: list[str] = field(default_factory=list)
    fs: Optional[fsspec.AbstractFileSystem] = field(default=None, repr=False)
    _file_dict_cache: Optional[dict] = field(default=None, init=False, repr=False)

    @autowrite_json
    def __post_init__(self):
        """Post-init function for the DatasetCommit class."""
        # Convert root_dir to string for consistent handling
        self.root_dir = str(self.root_dir)

        # Initialize filesystem if not provided - auto-detect from root_dir
        if self.fs is None:
            self.fs = get_filesystem(self.root_dir)

        if self.version_hash == "":
            # generate a random hash from uuidv4
            self.version_hash = sha256(self.dataset_name.encode()).hexdigest()

        # Use string path joining for cross-platform compatibility
        self.data_dir = f"{self.root_dir}/data"
        self.dataset_dir = f"{self.root_dir}/datasets/{self.dataset_name}"
        self.json_path = f"{self.dataset_dir}/{self.version_hash}/commit.json"

    def _read_json(self) -> dict:
        """Read the commit.json file for this commit.

        The commit.json file is a json file
        that serves as the on-disk source of truth of information for the DatasetCommit.

        :return: A dictionary that follows the schema as specified in to_dict().
        """
        with self.fs.open(strip_protocol(self.json_path), "r") as f:
            return json.loads(f.read())

    def _file_dict(self) -> dict:
        """Return a file dictionary associated with this commit.

        :return: A dictionary of the form {filename: file_hash_dir}
        """
        # Use cache if available
        if self._file_dict_cache is not None:
            return self._file_dict_cache

        # Return a dictionary of the form {filename: file_hash_dir}
        file_dict = {}
        # Track which (hash, filename) combinations we've already added
        used_files = set()

        # Optimize: batch glob operations when possible
        if len(self.file_hashes) > 1:
            # Try to get all files at once if possible
            data_dir_stripped = strip_protocol(self.data_dir)
            all_files = self.fs.glob(f"{data_dir_stripped}/*/*")

            # Group files by hash directory
            files_by_hash = {}
            for filepath in all_files:
                # Extract hash from path: data_dir/hash/filename
                path_parts = filepath.split("/")
                if len(path_parts) >= 2:
                    hash_part = path_parts[-2]  # Second to last part should be the hash
                    if hash_part in self.file_hashes:
                        if hash_part not in files_by_hash:
                            files_by_hash[hash_part] = []
                        files_by_hash[hash_part].append(filepath)

            # Process files for each hash
            for file_hash in self.file_hashes:
                if file_hash in files_by_hash:
                    filepaths = sorted(files_by_hash[file_hash])
                    # Find a file in this hash directory that we haven't added yet
                    for filepath in filepaths:
                        filename = filepath.split("/")[-1]
                        file_key = (file_hash, filename)

                        # Only add this file if we haven't used it yet
                        if file_key not in used_files:
                            file_dict[filename] = filepath
                            used_files.add(file_key)
                            break  # Move to next hash in file_hashes
        else:
            # Fallback to individual glob operations for single hash
            for file_hash in self.file_hashes:
                hash_dir = f"{self.data_dir}/{file_hash}"
                filepaths = sorted(self.fs.glob(f"{strip_protocol(hash_dir)}/*"))

                # Find a file in this hash directory that we haven't added yet
                for filepath in filepaths:
                    filename = filepath.split("/")[-1]
                    file_key = (file_hash, filename)

                    # Only add this file if we haven't used it yet
                    if file_key not in used_files:
                        file_dict[filename] = filepath
                        used_files.add(file_key)
                        break  # Move to next hash in file_hashes

        # Cache the result
        self._file_dict_cache = file_dict
        return file_dict

    def _clear_file_dict_cache(self):
        """Clear the file dictionary cache."""
        self._file_dict_cache = None

    @autowrite_json
    def create(
        self,
        commit_message: str,
        add_files: str | Path | List[str | Path] = None,
        remove_files: str | Path | List[str | Path] = None,
    ) -> str:
        """Create a new version of the dataset.

        :param commit_message: The commit message for the new commit.
        :param add_files: The files to add to the dataset.
        :param remove_files: The files to remove from the dataset.
        """
        # Error handling:
        if add_files is None and remove_files is None:
            raise ValueError(
                "At least one of add_files or remove_files must be specified."
            )

        # First off, calculate the new state of the dataset,
        # i.e. which files are going to be present.

        hash_hexes = []
        # Start with existing file hashes
        hash_hexes.extend(self.file_hashes)

        # For each file, create the hash directory and copy the file to it
        if add_files is not None:
            if isinstance(add_files, (str, Path)):
                add_files = [add_files]
            for filepath in add_files:
                filepath_str = str(filepath)
                filename = Path(filepath).name

                # Check if this file already exists in the dataset
                # If it does, we need to remove the old version first
                if filename in self._file_dict():
                    old_file_path = self._file_dict()[filename]
                    old_hash = old_file_path.split("/")[-2]  # Extract hash from path
                    if old_hash in hash_hexes:
                        hash_hexes.remove(old_hash)

                # Detect the source filesystem
                # (files could be local or from another cloud)
                source_fs = get_filesystem(filepath_str)
                # Hash the file using its source filesystem
                hash_hex = hash_file(strip_protocol(filepath_str), source_fs)
                hash_hexes.append(hash_hex)
                file_hash_dir = f"{self.data_dir}/{hash_hex}"
                self.fs.makedirs(strip_protocol(file_hash_dir), exist_ok=True)
                # Copy the file to the destination
                dest_path = f"{file_hash_dir}/{filename}"
                # Use put_file for cross-filesystem copying
                with source_fs.open(strip_protocol(filepath_str), "rb") as src:
                    with self.fs.open(strip_protocol(dest_path), "wb") as dst:
                        dst.write(src.read())

        # Finally, compute the hash of the removed files
        # and remove them from the hash_hexes
        if remove_files is not None:
            if isinstance(remove_files, (str, Path)):
                remove_files = [remove_files]

            for filename in remove_files:
                file_path = self._file_dict()[str(filename)]
                # Extract hash from path (second to last component)
                hash_hex = file_path.split("/")[-2]
                hash_hexes.remove(hash_hex)

        # Sort the hash_hexes so that the order of the files in the dataset
        # is deterministic.
        hash_hexes = sorted(hash_hexes)

        # Create a new version of the dataset by hashing
        # the concatenation of the hash_hexes and the commit message.
        hash_concat = "\n".join(hash_hexes) + "\n" + commit_message + "\n"
        # Add in datetime.now() to the hash_concat
        hash_concat = hash_concat + "\n" + str(datetime.now()) + "\n"
        hasher = sha256()
        hasher.update(hash_concat.encode("utf-8"))
        version_hash = hasher.hexdigest()

        # Write the new version of the dataset to the dataset directory.
        dataset_version_dir = f"{self.dataset_dir}/{version_hash}"
        self.fs.makedirs(strip_protocol(dataset_version_dir), exist_ok=True)

        return DatasetCommit(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=version_hash,
            commit_message=commit_message,
            file_hashes=hash_hexes,
            parent_hash=self.version_hash,
            fs=self.fs,
        )

    def to_dict(self) -> dict:
        """Return a dictionary representation of the DatasetCommit.

        :return: A dictionary representation of the DatasetCommit.
        """
        info = {
            "root_dir": str(self.root_dir),
            "dataset_name": self.dataset_name,
            "version_hash": self.version_hash,
            "commit_message": self.commit_message,
            "parent_hash": self.parent_hash,
            "parent_hashes": self.parent_hashes,
            "file_hashes": self.file_hashes,
        }
        return info

    @classmethod
    def from_json(
        cls,
        root_dir: str | Path,
        dataset_name: str,
        version_hash: str,
        fs: Optional[fsspec.AbstractFileSystem] = None,
    ) -> "DatasetCommit":
        """Create a DatasetCommit from a commit.json file.

        :param root_dir: The root directory path (can be str or Path).
        :param dataset_name: The name of the dataset.
        :param version_hash: The version hash of the commit.
        :param fs: The filesystem to use. If None, auto-detects from root_dir.
        :return: A DatasetCommit object.
        """
        root_dir = str(root_dir)
        if fs is None:
            fs = get_filesystem(root_dir)

        commit_json_path = (
            f"{root_dir}/datasets/{dataset_name}/{version_hash}/commit.json"
        )
        with fs.open(commit_json_path, "r") as f:
            commit_dict = json.loads(f.read())

        return DatasetCommit(
            root_dir=commit_dict["root_dir"],
            dataset_name=commit_dict["dataset_name"],
            version_hash=commit_dict["version_hash"],
            commit_message=commit_dict["commit_message"],
            file_hashes=commit_dict["file_hashes"],
            parent_hash=commit_dict.get("parent_hash", ""),
            parent_hashes=commit_dict.get("parent_hashes", []),
            fs=fs,
        )


class LocalFilesContext:
    """Context manager for accessing dataset files as local paths with lazy loading."""

    def __init__(self, dataset: "Dataset"):
        self.dataset = dataset
        self.local_files = {}
        self.remote_file_dict = None

    def __enter__(self):
        """Return lazy loading dictionary that downloads files on demand."""
        self.remote_file_dict = self.dataset.current_commit._file_dict()
        return LazyLocalFilesDict(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up all temporary files."""
        import os

        for local_path in self.local_files.values():
            if os.path.exists(local_path):
                os.unlink(local_path)
        self.local_files.clear()


class LazyLocalFilesDict:
    """Dictionary-like object that downloads files lazily on access."""

    def __init__(self, context: LocalFilesContext):
        self.context = context

    def __getitem__(self, filename: str) -> str:
        """Download file on first access and return local path."""
        if filename not in self.context.local_files:
            if filename not in self.context.remote_file_dict:
                raise KeyError(f"File '{filename}' not found in dataset")

            # Download file on demand
            local_path = self.context.dataset.download_file(filename)
            self.context.local_files[filename] = local_path

        return self.context.local_files[filename]

    def __contains__(self, filename: str) -> bool:
        """Check if file exists in dataset."""
        return filename in self.context.remote_file_dict

    def keys(self):
        """Return all available filenames."""
        return self.context.remote_file_dict.keys()

    def items(self):
        """Return (filename, local_path) pairs, downloading files on demand."""
        for filename in self.context.remote_file_dict.keys():
            yield filename, self[filename]

    def values(self):
        """Return local paths, downloading files on demand."""
        for filename in self.context.remote_file_dict.keys():
            yield self[filename]

    def get(self, filename: str, default=None):
        """Get local path for file, returning default if not found."""
        if filename in self.context.remote_file_dict:
            return self[filename]
        return default

    def __len__(self):
        """Return number of files in dataset."""
        return len(self.context.remote_file_dict)


@dataclass
class Dataset:
    """A class for storing data in a git-like structure.

    `dataset.json` defines the latest commit hash of the dataset.
    """

    root_dir: str | Path
    dataset_name: str
    description: str = field(default="")
    fs: Optional[fsspec.AbstractFileSystem] = field(default=None, repr=False)

    @autowrite_json
    def __post_init__(self) -> None:
        """Create the data and dataset directories."""
        # Convert root_dir to string for consistent handling
        self.root_dir = str(self.root_dir)

        # Initialize filesystem if not provided - auto-detect from root_dir
        if self.fs is None:
            logger.info(f"PERF: Initializing filesystem for {self.root_dir}")
            start_time = time.time()
            self.fs = get_filesystem(self.root_dir)
            end_time = time.time()
            logger.info(
                f"PERF: Filesystem initialization took {end_time - start_time:.3f}s"
            )

        self.data_dir = f"{self.root_dir}/data"
        logger.info(f"PERF: Creating data directory: {self.data_dir}")
        start_time = time.time()
        self.fs.makedirs(strip_protocol(self.data_dir), exist_ok=True)
        end_time = time.time()
        logger.info(f"PERF: Data directory creation took {end_time - start_time:.3f}s")

        self.dataset_dir = f"{self.root_dir}/datasets/{self.dataset_name}"
        logger.info(f"PERF: Creating dataset directory: {self.dataset_dir}")
        start_time = time.time()
        self.fs.makedirs(strip_protocol(self.dataset_dir), exist_ok=True)
        end_time = time.time()
        logger.info(
            f"PERF: Dataset directory creation took {end_time - start_time:.3f}s"
        )

        self.json_path = f"{self.dataset_dir}/dataset.json"

        # Initialize branch manager first
        logger.info(f"PERF: Initializing branch manager for {self.dataset_dir}")
        start_time = time.time()
        self.branch_manager = BranchManager(
            self.dataset_dir, self.fs, self.dataset_name
        )
        end_time = time.time()
        logger.info(
            f"PERF: Branch manager initialization took {end_time - start_time:.3f}s"
        )

        # Initialize current_commit lazily to avoid expensive operations during init
        self._current_commit = None
        self._file_dict = {}
        self._latest_version_hash_cache = None
        self._commits_data_cache = (
            None  # Cache for commit data to avoid duplicate reads
        )

    @property
    def current_commit(self) -> "DatasetCommit":
        """Lazily load the current commit to avoid expensive operations during init."""
        if self._current_commit is None:
            logger.info(f"Lazy loading current commit for dataset: {self.dataset_name}")
            try:
                # Try to get the current branch's commit
                logger.info(f"PERF: Getting current branch for {self.dataset_name}")
                start_time = time.time()
                current_branch = self.branch_manager.get_current_branch()
                end_time = time.time()
                logger.info(
                    f"PERF: Get current branch took {end_time - start_time:.3f}s"
                )

                if current_branch == "main":
                    # For main branch, use the latest version hash
                    version_hash = self.latest_version_hash()
                else:
                    # For other branches, get the commit from the branch
                    logger.info(f"PERF: Getting branch commit for {current_branch}")
                    start_time = time.time()
                    version_hash = self.branch_manager.get_branch_commit(current_branch)
                    end_time = time.time()
                    logger.info(
                        f"PERF: Get branch commit took {end_time - start_time:.3f}s"
                    )

                logger.info(
                    f"PERF: Creating DatasetCommit from JSON for {version_hash[:8]}"
                )
                start_time = time.time()
                self._current_commit = DatasetCommit.from_json(
                    root_dir=self.root_dir,
                    dataset_name=self.dataset_name,
                    version_hash=version_hash,
                    fs=self.fs,
                )
                end_time = time.time()
                logger.info(
                    f"PERF: DatasetCommit.from_json took {end_time - start_time:.3f}s"
                )
            except (DatasetNoCommitsError, ValueError):
                # No commits or branch doesn't exist, create initial commit
                initial_hash = sha256(self.dataset_name.encode()).hexdigest()
                self._current_commit = DatasetCommit(
                    root_dir=self.root_dir,
                    dataset_name=self.dataset_name,
                    version_hash=initial_hash,
                    commit_message="",
                    file_hashes=[],
                    parent_hash="",
                    fs=self.fs,
                )
                # Create main branch with the initial commit
                self.branch_manager.create_branch("main", initial_hash)

        return self._current_commit

    @current_commit.setter
    def current_commit(self, value: "DatasetCommit"):
        """Set the current commit."""
        self._current_commit = value

    @default_return_value(return_val="")
    def current_version_hash(self) -> str:
        """Return the hash of the current version of the dataset.

        :return: The hash of the current version of the dataset.
        """
        return self.current_commit.version_hash

    def latest_version_hash(self) -> str:
        """Find the latest version hash.

        We traverse the commit history of the dataset
        and return the hash of the latest version of the dataset.

        :return: The hash of the latest version of the dataset.
        """
        # Use cache if available
        if self._latest_version_hash_cache is not None:
            return self._latest_version_hash_cache

        logger.info(f"Computing latest version hash for dataset: {self.dataset_name}")

        # Use cached commits data to avoid duplicate file reads
        commits_data = self._get_commits_data()

        if not commits_data:
            raise DatasetNoCommitsError(
                "No commit.json files found in "
                + str(self.dataset_dir)
                + ". It appears that the dataset has not yet had data committed to it."
            )

        # Build commit_to_parent mapping from cached data
        commit_to_parent = {
            version_hash: data["parent_hash"]
            for version_hash, data in commits_data.items()
        }

        # Now, find the commit that is not a parent to any other commit.

        # If we are at the HEAD of a new dataset,
        # there should only be one commit
        # with no parents and no files that is automatically created.
        if len(commit_to_parent) == 1:
            result = list(commit_to_parent.keys())[0]
        else:
            # Otherwise, find the commit that is not a parent to any other commit.
            commits = set(commit_to_parent.keys())
            parents = set(commit_to_parent.values())
            commit_set = parents.symmetric_difference(commits)
            result = [c for c in commit_set if c][0]

        # Cache the result
        self._latest_version_hash_cache = result
        return result

    def _get_commits_data(self) -> dict:
        """Get commit data with caching to avoid duplicate file reads."""
        if self._commits_data_cache is not None:
            logger.info(f"PERF: Using cached commits data for {self.dataset_name}")
            return self._commits_data_cache

        logger.info(f"PERF: Loading commits data for {self.dataset_name}")
        start_time = time.time()

        jsons = self.fs.glob(f"{strip_protocol(self.dataset_dir)}/*/commit.json")
        if not jsons:
            self._commits_data_cache = {}
            return {}

        commits_data = {}
        for json_file in jsons:
            try:
                with self.fs.open(json_file, "r") as f:
                    data = json.loads(f.read())
                    commits_data[data["version_hash"]] = data
            except Exception as e:
                logger.warning(f"Failed to read commit file {json_file}: {e}")
                continue

        end_time = time.time()
        logger.info(f"PERF: Loading commits data took {end_time - start_time:.3f}s")

        # Cache the results
        self._commits_data_cache = commits_data
        return commits_data

    def resolve_commit_hash(self, partial_hash: str) -> str:
        """Resolve a partial commit hash to a full commit hash.

        Given a partial commit hash (e.g., first 8 characters), find the full
        commit hash that starts with that partial hash. If multiple commits
        match, raises an error. If no commits match, raises an error.

        :param partial_hash: The partial commit hash to resolve
        :return: The full commit hash
        :raises ValueError: If no commits match or multiple commits match
        """
        if not partial_hash:
            raise ValueError("Partial hash cannot be empty")

        # Get all commit.json files
        jsons = self.fs.glob(f"{strip_protocol(self.dataset_dir)}/*/commit.json")
        if not jsons:
            raise DatasetNoCommitsError(
                "No commit.json files found in "
                + str(self.dataset_dir)
                + ". It appears that the dataset has not yet had data committed to it."
            )

        matching_hashes = []
        for json_file in jsons:
            with self.fs.open(json_file, "r") as f:
                data = json.loads(f.read())
                full_hash = data["version_hash"]
                if full_hash.startswith(partial_hash):
                    matching_hashes.append(full_hash)

        if not matching_hashes:
            raise ValueError(f"No commit found matching partial hash '{partial_hash}'")
        elif len(matching_hashes) > 1:
            raise ValueError(
                f"Multiple commits match partial hash '{partial_hash}': "
                f"{matching_hashes}. Please provide more characters to make it unique."
            )

        return matching_hashes[0]

    @autowrite_json
    def commit(
        self,
        commit_message: str,
        add_files: str | Path | List[Path] = None,
        remove_files: str | List[str] = None,
    ) -> str:
        """Commit data files to the dataset.

        :param commit_message: The commit message.
        :param add_files: The files to add to the dataset.
        :param remove_files: The files to remove from the dataset.
            Should be a list of filenames
        """

        new_commit = self.current_commit.create(
            commit_message=commit_message,
            add_files=add_files,
            remove_files=remove_files,
        )
        self.current_commit = new_commit

        # Update the current branch to point to the new commit
        self.branch_manager.update_current_branch(new_commit.version_hash)

        return new_commit.version_hash

    def metadata(self) -> dict:
        """Return the metadata for the dataset.

        :return: The metadata for the dataset.
        """
        dataset_json_path = f"{self.dataset_dir}/dataset.json"
        with self.fs.open(strip_protocol(dataset_json_path), "r") as f:
            return json.loads(f.read())

    def checkout(self, version_hash: str = "") -> None:
        """Checkout a version of the dataset."""
        # Checkout the latest version of the dataset if it is not specified.
        if version_hash == "":
            version_hash = self.latest_version_hash()
        else:
            # Try to resolve partial hash to full hash
            try:
                version_hash = self.resolve_commit_hash(version_hash)
            except ValueError:
                # If resolution fails, assume it's already a full hash
                pass

        # Clear any existing cache before setting new commit
        if hasattr(self, "current_commit") and self.current_commit:
            self.current_commit._clear_file_dict_cache()

        # Clear latest version hash cache
        self._latest_version_hash_cache = None
        # Clear commits data cache
        self._commits_data_cache = None

        self.current_commit = DatasetCommit.from_json(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=version_hash,
            fs=self.fs,
        )

    @property
    def file_dict(self) -> dict:
        """Return a dictionary of the files in the dataset.

        The dictionary maps the filename to the path to the file.

        :return: A dictionary of the files in the dataset.
        """
        return self.current_commit._file_dict()

    def get_local_file_dict(self) -> dict:
        """Return a dictionary of the files in the dataset with local paths.

        Downloads all files to temporary locations and returns a dictionary
        mapping filenames to local paths. Useful when you need local file paths
        for libraries that don't support remote paths.

        :return: A dictionary mapping filenames to local file paths.
        """
        remote_file_dict = self.current_commit._file_dict()
        local_file_dict = {}

        for filename, remote_path in remote_file_dict.items():
            local_path = self.download_file(filename)
            local_file_dict[filename] = local_path

        return local_file_dict

    def local_files(self):
        """Context manager for accessing files as local paths.

        Downloads all files to temporary locations and provides a dictionary
        mapping filenames to local paths. Automatically cleans up temporary
        files when exiting the context.

        :return: A context manager that yields a dictionary of local file paths.

        Example:
            >>> with ds.local_files() as local_files:
            ...     audio_file = local_files["audio.mp3"]
            ...     mo.audio(src=audio_file)
            ...     df = pl.read_csv(local_files["data.csv"])
            >>> # Files are automatically cleaned up
        """
        return LocalFilesContext(self)

    def to_dict(self) -> dict:
        """Return a dictionary representation of the dataset.

        :return: A dictionary representation of the dataset.
        """
        return {
            "dataset_name": self.dataset_name,
            "current_version_hash": self.current_version_hash(),
            "description": self.description,
        }

    def commit_history_mermaid(self, short_hash_length: int = 8) -> str:
        """Generate a Mermaid diagram representing the commit history.

        This creates a visual graph showing all commits and their parent-child
        relationships, making it easy to see the lineage of the dataset.

        :param short_hash_length: Number of characters to show for commit hashes.
        :return: A Mermaid diagram string that can be rendered.

        Example:
            >>> ds = Dataset(root_dir="/data", dataset_name="my_dataset")
            >>> print(ds.commit_history_mermaid())
            >>> # Can also save to file or display in Jupyter
        """
        # Get all commits
        jsons = self.fs.glob(f"{strip_protocol(self.dataset_dir)}/*/commit.json")

        if not jsons:
            return "graph TD\n    A[No commits yet]"

        # Build commit information
        commits = {}
        for json_file in jsons:
            with self.fs.open(json_file, "r") as f:
                data = json.loads(f.read())
                commits[data["version_hash"]] = data

        # Start building the Mermaid diagram
        lines = ["graph TD"]

        # Add nodes and edges
        for version_hash, commit_data in commits.items():
            short_hash = version_hash[:short_hash_length]
            commit_msg = commit_data.get("commit_message", "").replace('"', "'")

            # Truncate long commit messages
            if len(commit_msg) > 50:
                commit_msg = commit_msg[:47] + "..."

            # Format the node with hash and message
            if commit_msg:
                node_label = f"{short_hash}<br/>{commit_msg}"
            else:
                node_label = f"{short_hash}<br/>(initial)"

            # Escape special characters for Mermaid
            node_label = node_label.replace("[", "(").replace("]", ")")

            # Create a safe node ID (alphanumeric only)
            node_id = f"commit_{short_hash}"

            # Add the node
            lines.append(f'    {node_id}["{node_label}"]')

            # Add edge from parent to this commit if parent exists
            parent_hash = commit_data.get("parent_hash", "")
            if parent_hash and parent_hash in commits:
                parent_short = parent_hash[:short_hash_length]
                parent_id = f"commit_{parent_short}"
                lines.append(f"    {parent_id} --> {node_id}")

        # Color-code commits by branch
        current_branch = self.get_current_branch()

        # Get all branches and their commits
        branch_commits = {}
        for branch_name in self.branch_manager.list_branches():
            branch_hash = self.branch_manager.get_branch_commit(branch_name)
            if branch_hash and branch_hash in commits:
                # Get all commits reachable from this branch
                branch_commits[branch_name] = set()
                to_visit = [branch_hash]
                visited = set()

                while to_visit:
                    commit_hash = to_visit.pop(0)
                    if commit_hash in visited or commit_hash not in commits:
                        continue
                    visited.add(commit_hash)
                    branch_commits[branch_name].add(commit_hash)

                    # Add parent commits
                    commit_data = commits[commit_hash]
                    parent_hash = commit_data.get("parent_hash", "")
                    if parent_hash and parent_hash in commits:
                        to_visit.append(parent_hash)

        # Define colors for different branches
        branch_colors = {
            "main": "#90EE90",  # Light green for main
            "master": "#90EE90",  # Light green for master (alias)
        }

        # Assign colors to other branches
        other_branches = [
            b for b in branch_commits.keys() if b not in ["main", "master"]
        ]
        other_colors = [
            "#FFB6C1",
            "#87CEEB",
            "#DDA0DD",
            "#F0E68C",
            "#FFA07A",
            "#98FB98",
            "#F5DEB3",
        ]

        for i, branch in enumerate(other_branches):
            if i < len(other_colors):
                branch_colors[branch] = other_colors[i]
            else:
                # Cycle through colors if we have more branches than colors
                branch_colors[branch] = other_colors[i % len(other_colors)]

        # Apply colors to commits
        for version_hash, commit_data in commits.items():
            short_hash = version_hash[:short_hash_length]
            node_id = f"commit_{short_hash}"

            # Find which branch this commit belongs to (prefer main/master)
            commit_branch = None
            for branch_name, branch_commit_set in branch_commits.items():
                if version_hash in branch_commit_set:
                    if commit_branch is None or branch_name in ["main", "master"]:
                        commit_branch = branch_name

            if commit_branch and commit_branch in branch_colors:
                color = branch_colors[commit_branch]
                lines.append(
                    f"    style {node_id} fill:{color},stroke:#333,stroke-width:2px"
                )

        # Highlight current commit with thicker border
        current_hash = self.current_version_hash()
        if current_hash:
            current_short = current_hash[:short_hash_length]
            current_id = f"commit_{current_short}"
            lines.append(f"    style {current_id} stroke:#FF0000,stroke-width:4px")

        return "\n".join(lines)

    def download_file(self, filename: str, local_path: str = None) -> str:
        """Download a file from the dataset to a local path.

        :param filename: The name of the file to download.
        :param local_path: Optional local path to save the file.
                           If None, uses a temporary file.
        :return: The local path where the file was saved.
        """
        if filename not in self.file_dict:
            raise FileNotFoundError(f"File '{filename}' not found in dataset")

        remote_path = self.file_dict[filename]

        if local_path is None:
            import os
            import tempfile

            # Create a temporary file with the same extension
            file_ext = os.path.splitext(filename)[1]
            temp_fd, local_path = tempfile.mkstemp(suffix=file_ext)
            os.close(temp_fd)  # Close the file descriptor, we'll use the path

        # Download the file using the filesystem
        with self.fs.open(strip_protocol(remote_path), "rb") as src:
            with open(local_path, "wb") as dst:
                dst.write(src.read())

        return local_path

    def get_file_content(self, filename: str, mode: str = "rb") -> bytes | str:
        """Get the content of a file as bytes or string.

        :param filename: The name of the file to read.
        :param mode: The mode to open the file ('rb' for bytes, 'r' for string).
        :return: The file content as bytes or string.
        """
        if filename not in self.file_dict:
            raise FileNotFoundError(f"File '{filename}' not found in dataset")

        remote_path = self.file_dict[filename]

        with self.fs.open(strip_protocol(remote_path), mode) as f:
            return f.read()

    def get_file_lines(self, filename: str) -> list[str]:
        """Get the lines of a text file.

        :param filename: The name of the file to read.
        :return: A list of lines from the file.
        """
        content = self.get_file_content(filename, mode="r")
        return content.splitlines()

    def open_file(self, filename: str, mode: str = "rb"):
        """Open a file for reading, returning a file-like object.

        This is useful for streaming large files or when you need to pass
        a file-like object to libraries like pandas, polars, etc.

        :param filename: The name of the file to open.
        :param mode: The mode to open the file ('rb', 'r', etc.).
        :return: A file-like object that can be used with libraries
                 expecting file paths.
        """
        if filename not in self.file_dict:
            raise FileNotFoundError(f"File '{filename}' not found in dataset")

        remote_path = self.file_dict[filename]
        return self.fs.open(strip_protocol(remote_path), mode)

    def get_local_path(self, filename: str) -> str:
        """Get a local path for a file, downloading it if necessary.

        This method is a convenience wrapper around download_file() that
        provides a local path that can be used with libraries expecting file paths.

        :param filename: The name of the file to get a local path for.
        :return: The local path to the file.
        """
        return self.download_file(filename)

    def show_commit_history(self, short_hash_length: int = 8) -> None:
        """Print the commit history as a Mermaid diagram.

        This is a convenience method that prints the Mermaid diagram to stdout.
        In Jupyter/IPython environments with Mermaid support, the diagram will
        be rendered. Otherwise, it prints the Mermaid syntax.

        :param short_hash_length: Number of characters to show for commit hashes.
        """
        mermaid = self.commit_history_mermaid(short_hash_length)
        print(mermaid)

    # Branch management methods
    def create_branch(self, name: str, commit_hash: str = None) -> str:
        """Create a new branch.

        Args:
            name: Name of the branch to create
            commit_hash: Commit hash to point to (defaults to current commit)

        Returns:
            The commit hash the branch was created with
        """
        if commit_hash is None:
            commit_hash = self.current_version_hash()

        return self.branch_manager.create_branch(name, commit_hash)

    def list_branches(self) -> list[str]:
        """List all branches.

        Returns:
            List of branch names
        """
        return self.branch_manager.list_branches()

    def get_current_branch(self) -> str:
        """Get the current branch name.

        Returns:
            Name of the current branch
        """
        return self.branch_manager.get_current_branch()

    def switch_branch(self, name: str):
        """Switch to a different branch.

        Args:
            name: Name of the branch to switch to

        Raises:
            ValueError: If branch doesn't exist
        """
        # Get the commit hash for the branch
        commit_hash = self.branch_manager.get_branch_commit(name)

        # Switch to the branch
        self.branch_manager.set_current_branch(name)

        # Update current commit to match the branch
        self.checkout(commit_hash)

    def delete_branch(self, name: str):
        """Delete a branch.

        Args:
            name: Name of the branch to delete

        Raises:
            ValueError: If trying to delete main branch or branch doesn't exist
        """
        self.branch_manager.delete_branch(name)

    def get_branch_commit(self, name: str) -> str:
        """Get the commit hash that a branch points to.

        Args:
            name: Name of the branch

        Returns:
            The commit hash the branch points to
        """
        return self.branch_manager.get_branch_commit(name)

    def merge(
        self, source_branch: str, target_branch: str = None, strategy: str = "auto"
    ) -> dict:
        """Merge one branch into another.

        Args:
            source_branch: The branch to merge from
            target_branch: The branch to merge into (defaults to current branch)
            strategy: Conflict resolution strategy ("auto", "ours", "theirs", "manual")

        Returns:
            Dictionary with merge result information including conflicts if any

        Raises:
            ValueError: If branches don't exist or merge is not possible
        """
        if target_branch is None:
            target_branch = self.get_current_branch()

        # Validate branches exist
        if source_branch not in self.list_branches():
            raise ValueError(f"Source branch '{source_branch}' does not exist")
        if target_branch not in self.list_branches():
            raise ValueError(f"Target branch '{target_branch}' does not exist")

        # Get commit hashes for both branches
        source_commit_hash = self.get_branch_commit(source_branch)
        target_commit_hash = self.get_branch_commit(target_branch)

        # Load the commits
        source_commit = DatasetCommit.from_json(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=source_commit_hash,
            fs=self.fs,
        )
        target_commit = DatasetCommit.from_json(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=target_commit_hash,
            fs=self.fs,
        )

        # Detect conflicts at file level
        conflicts = self._detect_merge_conflicts(source_commit, target_commit)

        result = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "source_commit": source_commit_hash,
            "target_commit": target_commit_hash,
            "conflicts": conflicts,
            "strategy": strategy,
        }

        # Handle different merge strategies
        if strategy == "rebase":
            # Rebase strategy: replay source branch commits on top of target branch
            result = self._rebase_merge(
                source_commit, target_commit, source_branch, target_branch
            )
            result.update(
                {
                    "source_branch": source_branch,
                    "target_branch": target_branch,
                    "source_commit": source_commit_hash,
                    "target_commit": target_commit_hash,
                    "conflicts": conflicts,
                    "strategy": strategy,
                }
            )
        elif conflicts and strategy != "manual":
            resolved_files = self._resolve_conflicts(
                conflicts, strategy, source_commit, target_commit
            )
            result["resolved_files"] = resolved_files

            # Create merge commit
            merge_commit_hash = self._create_merge_commit(
                source_commit,
                target_commit,
                resolved_files,
                conflicts,
                source_branch,
                target_branch,
            )
            result["merge_commit"] = merge_commit_hash

            # Update target branch to point to merge commit
            self.branch_manager.create_branch(
                f"{target_branch}_backup", target_commit_hash
            )
            self.branch_manager.set_current_branch(target_branch)
            branch_file = self.branch_manager._get_branch_file(target_branch)
            with self.fs.open(strip_protocol(branch_file), "w") as f:
                f.write(merge_commit_hash)

            result["success"] = True
        elif conflicts and strategy == "manual":
            result["success"] = False
            result["requires_manual_resolution"] = True
        else:
            # No conflicts, create merge commit
            merge_commit_hash = self._create_merge_commit(
                source_commit, target_commit, {}, [], source_branch, target_branch
            )
            result["merge_commit"] = merge_commit_hash
            result["success"] = True

        return result

    def _detect_merge_conflicts(
        self, source_commit: DatasetCommit, target_commit: DatasetCommit
    ) -> list:
        """Detect file-level conflicts between two commits.

        Args:
            source_commit: The source commit
            target_commit: The target commit

        Returns:
            List of conflict information for files that exist in both commits
            with different content
        """
        conflicts = []

        # Get file dictionaries for both commits
        source_files = source_commit._file_dict()
        target_files = target_commit._file_dict()

        # Find files that exist in both commits
        common_files = set(source_files.keys()) & set(target_files.keys())

        for filename in common_files:
            source_path = source_files[filename]
            target_path = target_files[filename]

            # Extract content hashes from paths
            source_hash = source_path.split("/")[-2]  # Second to last component
            target_hash = target_path.split("/")[-2]

            # If hashes are different, we have a conflict
            if source_hash != target_hash:
                conflicts.append(
                    {
                        "filename": filename,
                        "source_hash": source_hash,
                        "target_hash": target_hash,
                        "source_path": source_path,
                        "target_path": target_path,
                    }
                )

        return conflicts

    def _resolve_conflicts(
        self,
        conflicts: list,
        strategy: str,
        source_commit: DatasetCommit,
        target_commit: DatasetCommit,
    ) -> dict:
        """Resolve conflicts using the specified strategy.

        Args:
            conflicts: List of conflict information
            strategy: Resolution strategy ("ours", "theirs")
            source_commit: Source commit
            target_commit: Target commit

        Returns:
            Dictionary mapping filenames to chosen file paths
        """
        resolved_files = {}

        for conflict in conflicts:
            filename = conflict["filename"]

            if strategy == "ours":
                # Keep target branch version
                resolved_files[filename] = conflict["target_path"]
            elif strategy == "theirs":
                # Keep source branch version
                resolved_files[filename] = conflict["source_path"]
            else:
                # Default to target branch version
                resolved_files[filename] = conflict["target_path"]

        return resolved_files

    def _create_merge_commit(
        self,
        source_commit: DatasetCommit,
        target_commit: DatasetCommit,
        resolved_files: dict,
        conflicts: list,
        source_branch: str = None,
        target_branch: str = None,
    ) -> str:
        """Create a merge commit combining files from both branches using hash-based approach.

        Args:
            source_commit: Source commit
            target_commit: Target commit
            resolved_files: Files resolved from conflicts
            conflicts: List of conflicts
            source_branch: Source branch name
            target_branch: Target branch name

        Returns:
            Hash of the created merge commit
        """
        logger.info("MERGE_PERF: Starting hash-based merge commit creation")
        start_time = time.time()

        # Get file dictionaries and hashes
        source_files = source_commit._file_dict()
        target_files = target_commit._file_dict()
        source_hashes = source_commit.file_hashes
        target_hashes = target_commit.file_hashes

        logger.info(
            f"MERGE_PERF: Source has {len(source_files)} files, "
            f"target has {len(target_files)} files"
        )

        # Start with target branch file hashes
        merged_hashes = target_hashes.copy()

        # Handle file deletions: remove files that exist in target but not in source
        for filename, file_path in target_files.items():
            if filename not in source_files:
                # This file was deleted in source branch
                logger.info(f"MERGE_PERF: Removing file deleted in source: {filename}")
                # Find and remove the hash for this file
                target_file_hash = None
                for hash_hex in target_hashes:
                    if hash_hex in file_path:
                        target_file_hash = hash_hex
                        break

                if target_file_hash and target_file_hash in merged_hashes:
                    merged_hashes.remove(target_file_hash)
                    logger.info(
                        f"MERGE_PERF: Removed hash {target_file_hash[:8]} for deleted file {filename}"
                    )
                else:
                    logger.warning(
                        f"MERGE_PERF: Could not find hash for deleted file {filename}"
                    )

        # Add files from source branch that don't exist in target
        for filename, file_path in source_files.items():
            if filename not in target_files:
                # This is a new file from source branch
                logger.info(f"MERGE_PERF: Adding new file from source: {filename}")
                # Find the hash for this file in source commit
                source_file_hash = None
                for hash_hex in source_hashes:
                    if hash_hex in file_path:
                        source_file_hash = hash_hex
                        break

                if source_file_hash:
                    merged_hashes.append(source_file_hash)
                else:
                    logger.warning(
                        f"MERGE_PERF: Could not find hash for {filename} in source commit"
                    )

        # Handle resolved files (conflict resolution)
        for filename, file_path in resolved_files.items():
            logger.info(f"MERGE_PERF: Processing resolved file: {filename}")
            # Remove old version if it exists
            if filename in target_files:
                old_file_path = target_files[filename]
                old_hash = old_file_path.split("/")[-2]
                if old_hash in merged_hashes:
                    merged_hashes.remove(old_hash)

            # Add resolved file
            resolved_hash = file_path.split("/")[-2]
            merged_hashes.append(resolved_hash)

        # Sort hashes for deterministic ordering
        merged_hashes = sorted(merged_hashes)

        logger.info(f"MERGE_PERF: Final merged state has {len(merged_hashes)} files")

        # Create merge commit message
        if source_branch and target_branch:
            commit_message = f"Merge branch '{source_branch}' into {target_branch}"
        else:
            commit_message = "Merge commit"
        if conflicts:
            commit_message += f"\n\nResolved {len(conflicts)} conflicts"

        # Create the merge commit directly using hashes
        logger.info("MERGE_PERF: Creating merge commit with hash-based approach")
        commit_start = time.time()

        # Switch to target commit first
        self.checkout(target_commit.version_hash)

        # Create new commit with merged file hashes
        # We'll create a new DatasetCommit directly instead of using self.commit()
        hash_concat = "\n".join(merged_hashes) + "\n" + commit_message + "\n"
        hash_concat = hash_concat + "\n" + str(datetime.now()) + "\n"
        hasher = sha256()
        hasher.update(hash_concat.encode("utf-8"))
        merge_version_hash = hasher.hexdigest()

        # Create the merge commit object with both parents (proper git semantics)
        merge_commit = DatasetCommit(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=merge_version_hash,
            commit_message=commit_message,
            file_hashes=merged_hashes,
            parent_hash="",  # Clear single parent
            parent_hashes=[
                target_commit.version_hash,
                source_commit.version_hash,
            ],  # Both parents
            fs=self.fs,
        )

        # Update current commit and branch
        self.current_commit = merge_commit
        self.branch_manager.update_current_branch(merge_version_hash)

        commit_time = time.time() - commit_start
        total_time = time.time() - start_time
        logger.info(
            f"MERGE_PERF: Hash-based merge commit created in {commit_time:.2f}s"
        )
        logger.info(f"MERGE_PERF: Total merge time: {total_time:.2f}s")

        return merge_version_hash

    def _rebase_merge(
        self,
        source_commit: DatasetCommit,
        target_commit: DatasetCommit,
        source_branch: str,
        target_branch: str,
    ) -> dict:
        """Perform a rebase merge by replaying source branch commits on top of target branch.

        This creates a linear history without merge commits by:
        1. Getting all commits from source branch
        2. Replaying them on top of target branch
        3. Updating target branch to point to the new linear history

        Args:
            source_commit: The latest commit from source branch
            target_commit: The latest commit from target branch
            source_branch: Name of source branch
            target_branch: Name of target branch

        Returns:
            Dictionary with rebase result information
        """
        logger.info(
            f"REBASE: Starting rebase merge from '{source_branch}' into '{target_branch}'"
        )
        start_time = time.time()

        # Get all commits from source branch (excluding the target branch commits)
        source_commits = self._get_branch_commits(
            source_commit.version_hash, target_commit.version_hash
        )

        if not source_commits:
            logger.info("REBASE: No commits to rebase")
            return {
                "success": True,
                "rebase_commits": [],
                "final_commit": target_commit.version_hash,
            }

        logger.info(f"REBASE: Found {len(source_commits)} commits to rebase")

        # Start from target branch
        current_commit_hash = target_commit.version_hash

        # Replay each source commit on top of the current state
        rebased_commits = []
        for i, commit_data in enumerate(source_commits):
            logger.info(
                f"REBASE: Replaying commit {i + 1}/{len(source_commits)}: {commit_data['message'][:50]}..."
            )

            # Create new commit with same content but new parent
            new_commit_hash = self._replay_commit(commit_data, current_commit_hash)
            rebased_commits.append(new_commit_hash)
            current_commit_hash = new_commit_hash

        # Update target branch to point to the final rebased commit
        self.branch_manager.set_current_branch(target_branch)
        self.branch_manager.update_branch(target_branch, current_commit_hash)

        # Update current commit
        self.current_commit = DatasetCommit.from_json(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=current_commit_hash,
            fs=self.fs,
        )

        total_time = time.time() - start_time
        logger.info(f"REBASE: Rebase completed in {total_time:.2f}s")
        logger.info(f"REBASE: Created {len(rebased_commits)} rebased commits")

        return {
            "success": True,
            "rebase_commits": rebased_commits,
            "final_commit": current_commit_hash,
        }

    def _get_branch_commits(
        self, source_commit_hash: str, target_commit_hash: str
    ) -> list:
        """Get all commits from source branch that are not in target branch.

        Args:
            source_commit_hash: Latest commit from source branch
            target_commit_hash: Latest commit from target branch

        Returns:
            List of commit data dictionaries in chronological order
        """
        commits = []
        current = source_commit_hash

        # Traverse source branch commits until we reach target branch
        while current and current != target_commit_hash:
            try:
                commit = DatasetCommit.from_json(
                    root_dir=self.root_dir,
                    dataset_name=self.dataset_name,
                    version_hash=current,
                    fs=self.fs,
                )

                commits.append(
                    {
                        "hash": current,
                        "message": commit.commit_message,
                        "file_hashes": commit.file_hashes,
                    }
                )

                # Get parent (for single parent commits)
                if commit.parent_hashes:
                    current = commit.parent_hashes[
                        0
                    ]  # First parent for linear traversal
                else:
                    current = commit.parent_hash

            except Exception as e:
                logger.warning(f"REBASE: Could not load commit {current[:8]}: {e}")
                break

        # Reverse to get chronological order (oldest first)
        commits.reverse()
        return commits

    def _replay_commit(self, commit_data: dict, new_parent_hash: str) -> str:
        """Replay a commit with a new parent to create a rebased version.

        Args:
            commit_data: Original commit data
            new_parent_hash: New parent commit hash

        Returns:
            Hash of the new rebased commit
        """
        # Create new commit with same content but new parent
        hash_concat = (
            "\n".join(commit_data["file_hashes"]) + "\n" + commit_data["message"] + "\n"
        )
        hash_concat = hash_concat + "\n" + str(datetime.now()) + "\n"
        hasher = sha256()
        hasher.update(hash_concat.encode("utf-8"))
        new_commit_hash = hasher.hexdigest()

        # Create the rebased commit object
        rebased_commit = DatasetCommit(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=new_commit_hash,
            commit_message=commit_data["message"],
            file_hashes=commit_data["file_hashes"],
            parent_hash=new_parent_hash,  # Single parent for linear history
            parent_hashes=[],  # No multiple parents in rebase
            fs=self.fs,
        )

        return new_commit_hash

    def get_commits(self) -> list:
        """Get all commits for the current branch in chronological order.

        Returns:
            List of commit dictionaries with hash, message, and other metadata
        """
        current_branch = self.get_current_branch()
        current_commit_hash = self.get_branch_commit(current_branch)

        # Get all commits data
        commits_dict = self._get_commits_data()
        if not commits_dict:
            return []

        # Build chronological order (from newest to oldest)
        ordered_commits = []
        current = current_commit_hash

        while current and current in commits_dict:
            commit_data = commits_dict[current]

            # Handle both single parent and multiple parents (merge commits)
            parent_hash = commit_data.get("parent_hash", "")
            parent_hashes = commit_data.get("parent_hashes", [])

            # For merge commits, use the first parent (main branch) for linear traversal
            if parent_hashes:
                current = parent_hashes[0]  # First parent is the main branch
            else:
                current = parent_hash

            ordered_commits.append(
                {
                    "hash": current,
                    "short_hash": current[:8],
                    "message": commit_data.get("commit_message", "(initial)"),
                    "parent_hash": parent_hash,
                    "parent_hashes": parent_hashes,
                    "is_merge": len(parent_hashes) > 1,
                    "file_count": len(commit_data.get("file_hashes", [])),
                }
            )

            if not current:  # Empty string means no parent
                break

        return ordered_commits


class DatasetError(Exception):
    """Base class for exceptions in this module."""

    pass


class DatasetNoCommitsError(DatasetError):
    """Exception raised when there are no commits in the dataset."""

    pass
