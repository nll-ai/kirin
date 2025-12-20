"""Plot saving functionality for Kirin.

This module provides functions to save plots from various plotting libraries
(matplotlib, plotly, seaborn, etc.) in optimal formats (SVG for vectors,
WebP for bitmaps) with automatic format detection.
"""

import io
import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union

from loguru import logger

from .utils import detect_source_file, is_kirin_internal_file

if TYPE_CHECKING:
    from .storage import ContentStore

try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    plt = None
    HAS_MATPLOTLIB = False

try:
    import plotly.graph_objects as go

    HAS_PLOTLY = True
except ImportError:
    go = None
    HAS_PLOTLY = False

try:
    from PIL import Image

    HAS_PILLOW = True
except ImportError:
    Image = None
    HAS_PILLOW = False


def is_matplotlib_figure(obj: Any) -> bool:
    """Check if object is a matplotlib Figure.

    Args:
        obj: Object to check

    Returns:
        True if object is a matplotlib Figure
    """
    if not HAS_MATPLOTLIB or plt is None:
        return False
    return isinstance(obj, plt.Figure)


def is_plotly_figure(obj: Any) -> bool:
    """Check if object is a plotly Figure.

    Args:
        obj: Object to check

    Returns:
        True if object is a plotly Figure
    """
    if not HAS_PLOTLY or go is None:
        return False
    return isinstance(obj, go.Figure)


def detect_plot_variable_name(plot: Any) -> Optional[str]:
    """Detect the variable name of a plot object from calling scope.

    Uses sys._getframe() to walk up the call stack and find where the plot
    object was passed to commit(). Skips kirin-internal frames and looks for
    the plot in frame.f_locals.

    Args:
        plot: Plot object to find variable name for

    Returns:
        Variable name if detected, None otherwise
    """
    try:
        frame = sys._getframe(1)  # Skip this function's frame

        while frame is not None:
            try:
                # Skip Kirin internal files
                filename = getattr(getattr(frame, "f_code", None), "co_filename", None)
                if filename and is_kirin_internal_file(filename):
                    frame = frame.f_back
                    continue

                # Look for the plot object in frame locals
                locals_dict = frame.f_locals
                if locals_dict:
                    for var_name, var_value in list(locals_dict.items()):
                        if var_value is plot:
                            return var_name

            except (AttributeError, RuntimeError, TypeError):
                # Frame might be invalidated, skip it
                pass

            # Move to parent frame
            frame = getattr(frame, "f_back", None)

        return None

    except Exception as e:
        logger.warning(f"Failed to detect plot variable name: {e}")
        return None


def save_plot(
    plot_object: Union[  # noqa: F821
        "matplotlib.figure.Figure", "plotly.graph_objects.Figure", object  # noqa: F821
    ],
    filename: str,
    storage: "ContentStore",
    format: Optional[str] = None,
) -> Tuple[str, str, Optional[str], Optional[str]]:
    """Save a plot to content-addressed storage with automatic format detection.

    Automatically detects the plot type (matplotlib, plotly, etc.) and chooses
    the optimal format (SVG for vector graphics, WebP for bitmap/raster plots).

    **Important: Strict Content Hashing for SVG Plots**

    Kirin uses **strict content-addressed hashing** - files are identified by
    their exact byte content. This means:

    - **SVG plots will produce different hashes** even when the plot content
      is identical, because matplotlib embeds creation timestamps in the SVG
      metadata (`<dc:date>` elements). This is the strictest form of hashing
      and ensures complete content integrity.

    - **Identical plots = different commits**: If you save the same plot twice
      (same data, same code), you'll get different hashes and thus different
      commits, because the SVG files differ by their timestamps.

    - **This is by design**: Content-addressed storage requires exact byte
      matching. The timestamp metadata is part of the file content, so it
      affects the hash.

    - **For deterministic hashing**: If you need identical plots to produce
      identical hashes, you would need to strip metadata before saving, but
      this is not currently implemented as it would modify the original file
      content.

    Args:
        plot_object: The plot object to save (matplotlib Figure, plotly Figure, etc.)
        filename: Desired filename for the plot (extension may be adjusted)
        storage: ContentStore instance to use for storage
        format: Optional format override ('svg' or 'webp'). If None, auto-detects.

    Returns:
        Tuple of (content_hash, actual_filename, source_file_path, source_file_hash)
        where:
        - content_hash: Hash of the stored plot file
        - actual_filename: Filename used (may have extension adjusted based on format)
        - source_file_path: Path to source notebook/script, or None if not detected
        - source_file_hash: Hash of stored source file, or None if not detected

    Raises:
        ValueError: If plot type is not supported or format detection fails
        ImportError: If required libraries are not available
    """
    # Detect source file
    source_file_path = detect_source_file()
    source_file_hash = None

    # If source file detected, read and store it
    if source_file_path and os.path.exists(source_file_path):
        try:
            with open(source_file_path, "rb") as f:
                source_content = f.read()

            # Get just the filename from the path for storage
            source_filename = os.path.basename(source_file_path)

            # Store source file in content-addressed storage
            source_file_hash = storage.store_content(source_content, source_filename)
            logger.info(
                f"Detected and stored source file: {source_filename} "
                f"(hash: {source_file_hash[:8]})"
            )
        except Exception as e:
            logger.warning(
                f"Failed to store source file {source_file_path}: {e}. "
                "Plot will be saved without source linking."
            )
            source_file_path = None
            source_file_hash = None

    # Detect plot type and determine format
    if format is None:
        format = _detect_plot_format(plot_object, filename)

    # Save based on plot type
    if HAS_MATPLOTLIB and plt is not None and isinstance(plot_object, plt.Figure):
        content_hash, actual_filename = _save_matplotlib_plot(
            plot_object, filename, storage, format
        )
    elif HAS_PLOTLY and go is not None and isinstance(plot_object, go.Figure):
        content_hash, actual_filename = _save_plotly_plot(
            plot_object, filename, storage, format
        )
    else:
        raise ValueError(
            f"Unsupported plot type: {type(plot_object)}. "
            "Supported types: matplotlib.Figure, plotly.graph_objects.Figure"
        )

    return (content_hash, actual_filename, source_file_path, source_file_hash)


def serialize_plot(
    plot_object: Any,
    variable_name: Optional[str] = None,
    temp_dir: Optional[Path] = None,
    storage: Optional["ContentStore"] = None,
    format: Optional[str] = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    """Serialize a plot to a file with automatic format detection.

    Uses _detect_plot_format() to choose SVG (vector) or WebP (raster).
    Saves to a temporary file that can be read by commit().

    Args:
        plot_object: The plot object to save (matplotlib Figure, plotly Figure, etc.)
        variable_name: Optional variable name (auto-detected if None)
        temp_dir: Optional temporary directory (creates one if None)
        storage: ContentStore instance for storing source file
        format: Optional format override ('svg' or 'webp'). If None, auto-detects.

    Returns:
        Tuple of (file_path, source_file_path, source_file_hash)
        - file_path: Path to serialized plot file (e.g., "plot.svg")
        - source_file_path: Path to source script (if detected)
        - source_file_hash: Hash of source file (if detected and stored)

    Raises:
        ValueError: If plot type is not supported or variable name cannot be detected
    """
    import tempfile

    # Detect variable name if not provided
    if variable_name is None:
        variable_name = detect_plot_variable_name(plot_object)
        if not variable_name:
            raise ValueError(
                f"Could not detect variable name for plot object of type "
                f"{plot_object.__class__.__name__}. "
                "Variable name detection is required for plot objects. "
                "Either provide variable_name explicitly or ensure the plot is "
                "assigned to a variable before passing it to serialize_plot()."
            )

    # Detect format if not provided
    if format is None:
        # Generate a default filename based on variable name
        default_filename = f"{variable_name}.svg"
        format = _detect_plot_format(plot_object, default_filename)
    else:
        # Validate format
        if format not in ("svg", "webp"):
            raise ValueError(f"Unsupported format: {format}. Must be 'svg' or 'webp'")

    # Generate filename from variable name and format
    filename = f"{variable_name}.{format}"

    # Create temporary directory if not provided
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="kirin_plot_"))
    else:
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

    # Save plot to temp file
    plot_path = temp_dir / filename

    # Save based on plot type
    if HAS_MATPLOTLIB and plt is not None and isinstance(plot_object, plt.Figure):
        # Save matplotlib plot to temp file
        if format == "svg":
            plot_object.savefig(plot_path, format="svg", bbox_inches="tight")
        elif format == "webp":
            if HAS_PILLOW and Image is not None:
                # Save to PNG first, then convert to WebP
                png_path = temp_dir / f"{variable_name}.png"
                plot_object.savefig(png_path, format="png", bbox_inches="tight")
                # Convert PNG to WebP
                img = Image.open(png_path)
                img.save(plot_path, format="webp")
                png_path.unlink()  # Remove temporary PNG
            else:
                # Fallback to PNG if Pillow not available
                plot_object.savefig(plot_path, format="png", bbox_inches="tight")
                filename = f"{variable_name}.png"
                plot_path = temp_dir / filename
    elif HAS_PLOTLY and go is not None and isinstance(plot_object, go.Figure):
        # Save plotly plot to temp file
        if format == "svg":
            content_bytes = plot_object.to_image(format="svg")
            plot_path.write_bytes(content_bytes)
        elif format == "webp":
            # Export to PNG first, then convert to WebP
            png_bytes = plot_object.to_image(format="png")
            if HAS_PILLOW and Image is not None:
                img = Image.open(io.BytesIO(png_bytes))
                img.save(plot_path, format="webp")
            else:
                # Fallback to PNG if Pillow not available
                plot_path.write_bytes(png_bytes)
                filename = f"{variable_name}.png"
                plot_path = temp_dir / filename
    else:
        raise ValueError(
            f"Unsupported plot type: {type(plot_object)}. "
            "Supported types: matplotlib.Figure, plotly.graph_objects.Figure"
        )

    # Detect and store source file
    source_file_path = None
    source_file_hash = None

    if storage is not None:
        detected_source = detect_source_file()
        if detected_source and os.path.exists(detected_source):
            try:
                with open(detected_source, "rb") as f:
                    source_content = f.read()

                # Get just the filename from the path for storage
                source_filename = os.path.basename(detected_source)

                # Store source file in content-addressed storage
                source_file_hash = storage.store_content(source_content, source_filename)
                source_file_path = detected_source

                logger.info(
                    f"Detected and stored source file: {source_filename} "
                    f"(hash: {source_file_hash[:8]})"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to store source file {detected_source}: {e}. "
                    "Plot will be saved without source linking."
                )

    return (str(plot_path), source_file_path, source_file_hash)


def _detect_plot_format(plot_object: object, filename: str) -> str:
    """Detect optimal format for a plot.

    Args:
        plot_object: The plot object
        filename: Original filename (for extension hints)

    Returns:
        Format string: 'svg' or 'webp'
    """
    # Default format detection based on plot type (prioritize plot type over filename)
    if HAS_MATPLOTLIB and plt is not None and isinstance(plot_object, plt.Figure):
        # For matplotlib, default to SVG (most plots are vector-based)
        # Could be enhanced to check if plot contains raster elements
        return "svg"
    elif HAS_PLOTLY and go is not None and isinstance(plot_object, go.Figure):
        # Plotly figures are inherently vector-based
        return "svg"
    else:
        # Check filename extension for hints if plot type unknown
        filename_lower = filename.lower()
        if filename_lower.endswith(".svg"):
            return "svg"
        if filename_lower.endswith((".webp", ".png", ".jpg", ".jpeg")):
            return "webp"
        # Default to SVG for unknown types
        return "svg"


def _save_matplotlib_plot(
    fig: "matplotlib.figure.Figure",  # noqa: F821
    filename: str,
    storage: "ContentStore",
    format: str,
) -> tuple[str, str]:
    """Save a matplotlib figure to storage.

    Args:
        fig: Matplotlib figure object
        filename: Desired filename
        storage: ContentStore instance
        format: Format to use ('svg' or 'webp')

    Returns:
        Content hash of stored file
    """
    # Adjust filename extension based on format
    if format == "svg":
        if not filename.lower().endswith(".svg"):
            filename = filename.rsplit(".", 1)[0] + ".svg"
    elif format == "webp":
        if not filename.lower().endswith(".webp"):
            filename = filename.rsplit(".", 1)[0] + ".webp"
    else:
        raise ValueError(f"Unsupported format for matplotlib: {format}")

    # Save to bytes buffer
    buffer = io.BytesIO()
    if format == "svg":
        fig.savefig(buffer, format="svg", bbox_inches="tight")
    elif format == "webp":
        if not HAS_PILLOW:
            logger.warning(
                "Pillow not available, falling back to PNG for matplotlib WebP export"
            )
            fig.savefig(buffer, format="png", bbox_inches="tight")
            # Convert PNG to WebP if Pillow is available
            if HAS_PILLOW and Image is not None:
                buffer.seek(0)
                img = Image.open(buffer)
                buffer = io.BytesIO()
                img.save(buffer, format="webp")
        else:
            fig.savefig(buffer, format="png", bbox_inches="tight")
            buffer.seek(0)
            if Image is not None:
                img = Image.open(buffer)
                buffer = io.BytesIO()
                img.save(buffer, format="webp")
    else:
        raise ValueError(f"Unsupported format: {format}")

    buffer.seek(0)
    content = buffer.read()
    buffer.close()

    # Store in content-addressed storage
    content_hash = storage.store_content(content, filename)

    logger.info(
        f"Saved matplotlib plot as {format.upper()} with hash {content_hash[:8]}"
    )

    return (content_hash, filename)


def _save_plotly_plot(
    fig: "plotly.graph_objects.Figure",  # noqa: F821
    filename: str,
    storage: "ContentStore",
    format: str,
) -> tuple[str, str]:
    """Save a plotly figure to storage.

    Args:
        fig: Plotly figure object
        filename: Desired filename
        storage: ContentStore instance
        format: Format to use ('svg' or 'webp')

    Returns:
        Content hash of stored file
    """
    # Adjust filename extension based on format
    if format == "svg":
        if not filename.lower().endswith(".svg"):
            filename = filename.rsplit(".", 1)[0] + ".svg"
        # Plotly's to_image returns bytes for SVG
        content_bytes = fig.to_image(format="svg")
    elif format == "webp":
        if not filename.lower().endswith(".webp"):
            filename = filename.rsplit(".", 1)[0] + ".webp"
        # Plotly can export to PNG, then convert to WebP
        png_bytes = fig.to_image(format="png")
        if HAS_PILLOW and Image is not None:
            img = Image.open(io.BytesIO(png_bytes))
            buffer = io.BytesIO()
            img.save(buffer, format="webp")
            content_bytes = buffer.getvalue()
        else:
            logger.warning(
                "Pillow not available, using PNG instead of WebP for plotly export"
            )
            content_bytes = png_bytes
            filename = filename.rsplit(".", 1)[0] + ".png"
    else:
        raise ValueError(f"Unsupported format for plotly: {format}")

    # Store in content-addressed storage
    content_hash = storage.store_content(content_bytes, filename)

    logger.info(f"Saved plotly plot as {format.upper()} with hash {content_hash[:8]}")

    return (content_hash, filename)
