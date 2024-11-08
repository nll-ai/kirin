"""Implementation for the Dataset and DatasetCommit classes."""

import shutil
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import List

import json5 as json


def hash_file(filepath: Path) -> str:
    """Hash a file's contents using sha256 and return the hash hex digest.

    :param filepath: The path to the file to hash.
    :return: The hash hex digest, a hex string.
    """
    hash = sha256()
    with open(filepath, "rb") as f:
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
        if not self.json_path.parent.exists():
            self.json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.json_path, "w+") as f:
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

    root_dir: Path
    dataset_name: str
    version_hash: str = field(default="")
    commit_message: str = field(default="")
    file_hashes: list[str] = field(default_factory=list)
    parent_hash: str = field(default="")

    @autowrite_json
    def __post_init__(self):
        """Post-init function for the DatasetCommit class."""
        if self.version_hash == "":
            # generate a random hash from uuidv4
            self.version_hash = sha256(self.dataset_name.encode()).hexdigest()

        self.data_dir = self.root_dir / "data"
        self.dataset_dir = self.root_dir / "datasets" / self.dataset_name
        self.json_path = self.dataset_dir / self.version_hash / "commit.json"

    def _read_json(self) -> dict:
        """Read the commit.json file for this commit.

        The commit.json file is a json file
        that serves as the on-disk source of truth of information for the DatasetCommit.

        :return: A dictionary that follows the schema as specified in to_dict().
        """
        with open(self.json_path, "r+") as f:
            return json.loads(f.read())

    def _file_dict(self) -> dict:
        """Return a file dictionary associated with this commit.

        :return: A dictionary of the form {filename: file_hash_dir}
        """
        # Return a dictionary of the form {filename: file_hash_dir}
        file_dict = {}
        for file_hash in self.file_hashes:
            filepath = sorted((self.data_dir / file_hash).glob("*"))[0]
            file_dict[filepath.name] = filepath
        return file_dict

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
        # For each file, create the hash directory and copy the file to it
        if add_files is not None:
            if isinstance(add_files, Path):
                add_files = [add_files]
            for filepath in add_files:
                hash_hex = hash_file(Path(filepath))
                hash_hexes.append(hash_hex)
                file_hash_dir = self.data_dir / hash_hex
                file_hash_dir.mkdir(parents=True, exist_ok=True)
                # Copy the file, not move, to the hash directory.
                shutil.copy(filepath, file_hash_dir / filepath.name)

        hash_hexes.extend(self.file_hashes)

        # Finally, compute the hash of the removed files
        # and remove them from the hash_hexes
        if remove_files is not None:
            if isinstance(remove_files, (str, Path)):
                remove_files = [remove_files]

            for filename in remove_files:
                hash_hex = self._file_dict()[str(filename)].parent.name
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
        dataset_version_dir = self.dataset_dir / version_hash
        dataset_version_dir.mkdir(parents=True, exist_ok=True)

        return DatasetCommit(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=version_hash,
            commit_message=commit_message,
            file_hashes=hash_hexes,
            parent_hash=self.version_hash,
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
            "file_hashes": self.file_hashes,
        }
        return info

    @classmethod
    def from_json(
        cls, root_dir: Path, dataset_name: str, version_hash: str
    ) -> "DatasetCommit":
        """Create a DatasetCommit from a commit.json file.

        :param commit_json: The path to the commit.json file.
        :return: A DatasetCommit object.
        """
        with open(
            root_dir / "datasets" / dataset_name / version_hash / "commit.json", "r+"
        ) as f:
            commit_dict = json.loads(f.read())

        return DatasetCommit(
            root_dir=Path(commit_dict["root_dir"]),
            dataset_name=commit_dict["dataset_name"],
            version_hash=commit_dict["version_hash"],
            commit_message=commit_dict["commit_message"],
            file_hashes=commit_dict["file_hashes"],
            parent_hash=commit_dict["parent_hash"],
        )


@dataclass
class Dataset:
    """A class for storing data in a git-like structure.

    `dataset.json` defines the latest commit hash of the dataset.
    """

    root_dir: Path
    dataset_name: str
    description: str = field(default="")

    @autowrite_json
    def __post_init__(self) -> None:
        """Create the data and dataset directories."""
        self.data_dir = self.root_dir / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.dataset_dir = self.root_dir / "datasets" / self.dataset_name
        self.dataset_dir.mkdir(parents=True, exist_ok=True)

        self.json_path = self.dataset_dir / "dataset.json"

        # This is the only class attribute that we change
        # throughout the lifetime of the object!
        try:
            version_hash = self.latest_version_hash()
            self.current_commit = DatasetCommit.from_json(
                root_dir=self.root_dir,
                dataset_name=self.dataset_name,
                version_hash=version_hash,
            )
        except DatasetNoCommitsError:
            self.current_commit = DatasetCommit(
                root_dir=self.root_dir,
                dataset_name=self.dataset_name,
                version_hash=sha256(self.dataset_name.encode()).hexdigest(),
                commit_message="",
                file_hashes=[],
                parent_hash="",
            )

        self._file_dict = {}

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
        jsons = list(self.dataset_dir.glob("*/commit.json"))
        if not jsons:
            raise DatasetNoCommitsError(
                "No commit.json files found in "
                + str(self.dataset_dir)
                + ". It appears that the dataset has not yet had data committed to it."
            )
        commit_to_parent = dict()
        for json_file in jsons:
            with open(json_file, "r") as f:
                data = json.loads(f.read())
                commit_to_parent[data["version_hash"]] = data["parent_hash"]

        # Now, find the commit that is not a parent to any other commit.

        # If we are at the HEAD of a new dataset,
        # there should only be one commit
        # with no parents and no files that is automatically created.
        if len(commit_to_parent) == 1:
            return list(commit_to_parent.keys())[0]

        # Otherwise, find the commit that is not a parent to any other commit.
        commits = set(commit_to_parent.keys())
        parents = set(commit_to_parent.values())
        commit_set = parents.symmetric_difference(commits)
        return [c for c in commit_set if c][0]

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

    def metadata(self) -> dict:
        """Return the metadata for the dataset.

        :return: The metadata for the dataset.
        """
        with open(self.dataset_dir / "dataset.json", "r") as f:
            return json.loads(f.read())

    def checkout(self, version_hash: str = "") -> None:
        """Checkout a version of the dataset."""
        # Checkout the latest version of the dataset if it is not specified.
        if version_hash == "":
            version_hash = self.latest_version_hash()

        self.current_commit = DatasetCommit.from_json(
            root_dir=self.root_dir,
            dataset_name=self.dataset_name,
            version_hash=version_hash,
        )

    @property
    def file_dict(self) -> dict:
        """Return a dictionary of the files in the dataset.

        The dictionary maps the filename to the path to the file.

        :return: A dictionary of the files in the dataset.
        """
        return self.current_commit._file_dict()

    def to_dict(self) -> dict:
        """Return a dictionary representation of the dataset.

        :return: A dictionary representation of the dataset.
        """
        return {
            "dataset_name": self.dataset_name,
            "current_version_hash": self.current_version_hash(),
            "description": self.description,
        }


class DatasetError(Exception):
    """Base class for exceptions in this module."""

    pass


class DatasetNoCommitsError(DatasetError):
    """Exception raised when there are no commits in the dataset."""

    pass
