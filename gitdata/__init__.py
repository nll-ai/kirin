"""Top-level API for gitdata.

This is the file from which you can do:

    from gitdata import some_function

Use it to control the top-level API of your Python data science project.
"""

from gitdata.catalog import Catalog
from gitdata.cloud_auth import (
    get_azure_filesystem,
    get_gcs_filesystem,
    get_s3_compatible_filesystem,
    get_s3_filesystem,
)
from gitdata.dataset import Dataset, DatasetCommit

__all__ = [
    "Catalog",
    "Dataset",
    "DatasetCommit",
    "get_s3_filesystem",
    "get_gcs_filesystem",
    "get_azure_filesystem",
    "get_s3_compatible_filesystem",
]
