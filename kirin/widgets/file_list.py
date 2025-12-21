"""Interactive file list widget using anywidget.

This widget displays a list of files with clickable items that expand to show
code snippets for accessing files via dataset.local_files().
"""

from pathlib import Path

import anywidget
import traitlets


class FileListWidget(anywidget.AnyWidget):
    """Interactive file list widget with expandable code snippets.

    Displays a list of files with icons, names, and sizes. Clicking a file
    item toggles the visibility of a code snippet showing how to access that
    file using dataset.local_files().

    Attributes:
        files: List of file dictionaries with name, size, and icon_html
        dataset_name: Name of the dataset (used in code snippet)
        expanded_files: List of file indices that are currently expanded
    """

    _esm = Path(__file__).parent / "assets" / "file_list.js"

    _css = Path(__file__).parent / "assets" / "shared.css"

    # Python state synchronized with JavaScript
    files = traitlets.List(default_value=[]).tag(sync=True)
    dataset_name = traitlets.Unicode(default_value="").tag(sync=True)
    expanded_files = traitlets.List(default_value=[]).tag(sync=True)
