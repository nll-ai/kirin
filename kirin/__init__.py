"""Top-level API for kirin.

This is the file from which you can do:

    from kirin import some_function

Use it to control the top-level API of your Python data science project.
"""

from kirin.catalog import Catalog
from kirin.cloud_auth import (
    get_azure_filesystem,
    get_gcs_filesystem,
    get_s3_compatible_filesystem,
    get_s3_filesystem,
)
from kirin.dataset import Dataset, DatasetCommit

__all__ = [
    "Catalog",
    "Dataset",
    "DatasetCommit",
    "get_s3_filesystem",
    "get_gcs_filesystem",
    "get_azure_filesystem",
    "get_s3_compatible_filesystem",
]
