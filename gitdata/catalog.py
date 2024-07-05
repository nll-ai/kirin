"""Lightweight implementation of a Data Catalog, which is a collection of Datasets."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from .dataset import Dataset


@dataclass
class Catalog:
    """A class for storing a collection of datasets."""
    root_dir: Path

    def __post_init__(self):
        """Post-initialization function for the Catalog class."""
        self.datasets_dir = self.root_dir / "datasets"

    def datasets(self) -> List[str]:
        """Return a list of the names of the datasets in the catalog.

        :return: A list of the names of the datasets in the catalog.
        """
        return [d.name for d in (self.datasets_dir).iterdir() if d.is_dir()]

    def get_dataset(self, dataset_name: str) -> Dataset:
        """Get a dataset from the catalog.

        :param dataset_name: The name of the dataset to get.
        :return: The Dataset object with the given name.
        """
        return Dataset(root_dir=self.root_dir, dataset_name=dataset_name)

    def create_dataset(self, dataset_name, description: str) -> Dataset:
        """Create a dataset in the catalog.

        :param dataset_name: The name of the dataset to create.
        :description: The description of the dataset.
        :return: The Dataset object with the given name.
        """
        dataset_dir = self.datasets_dir / dataset_name
        dataset_dir.mkdir(parents=True, exist_ok=True)
        return Dataset(
            root_dir=self.root_dir, dataset_name=dataset_name, description=description
        )
