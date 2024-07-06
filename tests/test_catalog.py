"""Tests for lightweight data catalogs."""
import pytest

from gitdata.cataog import Catalog


@pytest.fixture
def empty_catalog(tmp_dir) -> Catalog:
    """Create an empty catalog.

    :return: The empty catalog.
    """
    return Catalog(root_dir=tmp_dir)
