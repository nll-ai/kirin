"""ML artifact handling utilities for Kirin.

This module provides utilities for automatically handling machine learning
artifacts, particularly scikit-learn models, when committing to Kirin datasets.
"""

import inspect
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

from loguru import logger

from .utils import detect_source_file, is_kirin_internal_file

if TYPE_CHECKING:
    from .storage import ContentStore

# Optional Dependencies Pattern
#
# This module uses optional dependencies (joblib and numpy) that are not required
# for the core Kirin package. This pattern allows:
# - Core Kirin to remain lightweight without heavy ML dependencies
# - ML functionality to work when these dependencies are available
# - Clear error messages when dependencies are missing
#
# Functions that require these dependencies check HAS_JOBLIB/HAS_NUMPY flags
# and raise informative errors if dependencies are not available.

try:
    import joblib

    HAS_JOBLIB = True
except ImportError:
    joblib = None
    HAS_JOBLIB = False

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    np = None
    HAS_NUMPY = False

try:
    import sklearn

    HAS_SKLEARN = True
except ImportError:
    sklearn = None
    HAS_SKLEARN = False


def is_sklearn_model(obj: Any) -> bool:
    """Check if an object is a scikit-learn model.

    Checks for:
    - Has `get_params()` method (scikit-learn BaseEstimator interface)
    - Has `fit()` method (all scikit-learn models have this)

    Args:
        obj: Object to check

    Returns:
        True if object appears to be a scikit-learn model
    """
    if not hasattr(obj, "get_params") or not callable(getattr(obj, "get_params")):
        return False

    if not hasattr(obj, "fit") or not callable(getattr(obj, "fit")):
        return False

    return True


def detect_model_variable_name(model: Any) -> Optional[str]:
    """Detect the variable name of a model object from calling scope.

    Uses inspect.stack() to walk up call stack and find where the model
    object was passed to commit(). Looks for variable assignments in the
    calling frame.

    This function is more robust in CI environments by:
    - Checking more frames in the stack
    - Using try/except around frame access (frames can be invalidated)
    - Checking both locals and globals more carefully

    Args:
        model: Model object to find variable name for

    Returns:
        Variable name if detected, None otherwise
    """
    try:
        # Walk up the call stack to find the calling frame
        # Use context=0 to avoid loading source lines (faster, more reliable)
        stack = inspect.stack(context=0)

        # Skip frames that are inside the kirin package itself
        # Frame 0: detect_model_variable_name() itself
        # Frame 1+: Callers (may include kirin internal functions)
        for frame_info in stack[1:]:
            try:
                frame = frame_info.frame

                # Skip Kirin internal files
                if hasattr(frame, "f_code") and hasattr(frame.f_code, "co_filename"):
                    filename = frame.f_code.co_filename
                    if filename and is_kirin_internal_file(filename):
                        continue

                # Look for the model object in frame locals
                # Use getattr with default to handle cases where f_locals
                # might not be accessible
                try:
                    locals_dict = frame.f_locals
                    if locals_dict:
                        for var_name, var_value in locals_dict.items():
                            # Use 'is' for identity check (same object)
                            if var_value is model:
                                return var_name
                except (AttributeError, RuntimeError):
                    # Frame might be invalidated or locals not accessible
                    pass

                # Also check globals
                try:
                    globals_dict = frame.f_globals
                    if globals_dict:
                        for var_name, var_value in globals_dict.items():
                            if var_value is model:
                                return var_name
                except (AttributeError, RuntimeError):
                    # Frame might be invalidated or globals not accessible
                    pass

            except (AttributeError, RuntimeError):
                # Frame might be invalidated, skip it
                continue

        # If we couldn't determine the variable name, return None
        return None

    except Exception as e:
        logger.warning(f"Failed to detect model variable name: {e}")
        return None


def convert_to_python_type(value: Any) -> Any:
    """Convert numpy types and other non-serializable types to Python types.

    This function handles conversion of numpy types (integers, floats, arrays,
    booleans) to native Python types for JSON serialization. It works
    recursively on lists and dictionaries.

    Args:
        value: Value to convert (may be numpy type, list, dict, or Python type)

    Returns:
        Python-serializable value (numpy types converted to Python equivalents)
    """
    if HAS_NUMPY and np is not None:
        if isinstance(value, np.integer):
            return int(value)
        elif isinstance(value, np.floating):
            return float(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        elif isinstance(value, np.bool_):
            return bool(value)

    # Handle lists and dicts recursively
    if isinstance(value, list):
        return [convert_to_python_type(item) for item in value]
    elif isinstance(value, dict):
        return {k: convert_to_python_type(v) for k, v in value.items()}

    return value


def extract_sklearn_hyperparameters(model: Any) -> Dict[str, Any]:
    """Extract hyperparameters from a scikit-learn model.

    Uses model.get_params() which returns all hyperparameters.
    Converts non-serializable values (like numpy types) to Python types.

    Args:
        model: scikit-learn model object

    Returns:
        Dictionary of hyperparameters
    """
    if not is_sklearn_model(model):
        raise ValueError(f"Object is not a scikit-learn model: {type(model)}")

    params = model.get_params()
    # Convert numpy types to Python types for JSON serialization
    converted_params = convert_to_python_type(params)

    return converted_params


def get_sklearn_version() -> Optional[str]:
    """Get the version of scikit-learn if available.

    Returns:
        Version string (e.g., "1.3.0") if scikit-learn is installed, None otherwise
    """
    if HAS_SKLEARN and sklearn is not None:
        try:
            return sklearn.__version__
        except AttributeError:
            return None
    return None


def extract_sklearn_metrics(model: Any) -> Dict[str, Any]:
    """Extract available metrics from a fitted scikit-learn model.

    Extracts metrics that don't require data:
    - feature_importances_ (tree-based models)
    - coef_ (linear models)
    - intercept_ (linear models)
    - n_features_in_ (all fitted models)
    - n_outputs_ (all fitted models)

    Note: Data-dependent metrics like score() should be passed
    explicitly in metadata.

    Args:
        model: scikit-learn model object (must be fitted)

    Returns:
        Dictionary of available metrics (empty dict if none available)
    """
    metrics = {}

    # Check for feature_importances_ (tree-based models)
    if hasattr(model, "feature_importances_"):
        try:
            metrics["feature_importances"] = convert_to_python_type(
                model.feature_importances_
            )
        except Exception:
            pass

    # Check for coef_ (linear models)
    if hasattr(model, "coef_"):
        try:
            metrics["coef"] = convert_to_python_type(model.coef_)
        except Exception:
            pass

    # Check for intercept_ (linear models)
    if hasattr(model, "intercept_"):
        try:
            metrics["intercept"] = convert_to_python_type(model.intercept_)
        except Exception:
            pass

    # Check for n_features_in_ (all fitted models)
    if hasattr(model, "n_features_in_"):
        try:
            metrics["n_features_in"] = int(model.n_features_in_)
        except Exception:
            pass

    # Check for n_outputs_ (all fitted models)
    if hasattr(model, "n_outputs_"):
        try:
            metrics["n_outputs"] = int(model.n_outputs_)
        except Exception:
            pass

    return metrics


def serialize_sklearn_model(
    model: Any,
    variable_name: Optional[str] = None,
    temp_dir: Optional[Path] = None,
    storage: Optional["ContentStore"] = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    """Serialize a scikit-learn model to a file using joblib.

    Args:
        model: scikit-learn model object
        variable_name: Optional variable name (auto-detected if None via
        detect_model_variable_name)
        temp_dir: Optional temporary directory (creates one if None)
        storage: ContentStore instance for storing source file

    Returns:
        Tuple of (file_path, source_file_path, source_file_hash)
        - file_path: Path to serialized model file (e.g., "model.pkl")
        - source_file_path: Path to source script (if detected)
        - source_file_hash: Hash of source file (if detected and stored)

    Raises:
        ValueError: If joblib is not available
        Exception: If serialization fails (no error handling - let joblib raise)
    """
    if not HAS_JOBLIB or joblib is None:
        raise ValueError(
            "joblib is required for model serialization. "
            "Install with: pip install joblib"
        )

    if not is_sklearn_model(model):
        raise ValueError(f"Object is not a scikit-learn model: {type(model)}")

    # Detect variable name if not provided
    if variable_name is None:
        variable_name = detect_model_variable_name(model)
        if not variable_name:
            raise ValueError(
                f"Could not detect variable name for model object of type "
                f"{model.__class__.__name__}. "
                "Variable name detection is required for model objects. "
                "Either provide variable_name explicitly or ensure the model is "
                "assigned to a variable before passing it to serialize_sklearn_model()."
            )

    # Generate filename from variable name
    filename = f"{variable_name}.pkl"

    # Create temporary directory if not provided
    if temp_dir is None:
        temp_dir = Path(tempfile.mkdtemp(prefix="kirin_model_"))
    else:
        temp_dir = Path(temp_dir)
        temp_dir.mkdir(parents=True, exist_ok=True)

    # Serialize model to file
    model_path = temp_dir / filename
    joblib.dump(model, model_path)

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
                source_file_hash = storage.store_content(
                    source_content, source_filename
                )
                source_file_path = detected_source

                logger.info(
                    f"Detected and stored source file: {source_filename} "
                    f"(hash: {source_file_hash[:8]})"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to store source file {detected_source}: {e}. "
                    "Model will be saved without source linking."
                )

    return (str(model_path), source_file_path, source_file_hash)
