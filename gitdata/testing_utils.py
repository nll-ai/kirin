"""Utilities for testing."""
import random
import string
import tempfile
from pathlib import Path


def dummy_file() -> Path:
    """Create a dummy text file in a temporary directory.

    :return: The path to the dummy text file.
    """
    content = "".join(random.choice(string.ascii_letters) for _ in range(1000))
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
        # Write the content to the temporary file
        temp_file.write(content)
    return Path(temp_file.name)
