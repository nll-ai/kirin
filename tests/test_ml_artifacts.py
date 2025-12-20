"""Tests for ML artifact handling in Kirin."""

from pathlib import Path

import pytest

from kirin import Dataset
from kirin.ml_artifacts import (
    detect_model_variable_name,
    extract_sklearn_hyperparameters,
    extract_sklearn_metrics,
    get_sklearn_version,
    is_sklearn_model,
    serialize_sklearn_model,
)

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.tree import DecisionTreeClassifier

    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    RandomForestClassifier = None
    LogisticRegression = None
    DecisionTreeClassifier = None

pytestmark = pytest.mark.skipif(
    not HAS_SKLEARN, reason="scikit-learn not available"
)


def test_is_sklearn_model_with_rf():
    """Test that RandomForestClassifier is detected as sklearn model."""
    model = RandomForestClassifier(n_estimators=10)
    assert is_sklearn_model(model) is True


def test_is_sklearn_model_with_lr():
    """Test that LogisticRegression is detected as sklearn model."""
    model = LogisticRegression()
    assert is_sklearn_model(model) is True


def test_is_sklearn_model_with_regular_object():
    """Test that regular objects are not detected as sklearn models."""
    assert is_sklearn_model("not a model") is False
    assert is_sklearn_model(42) is False
    assert is_sklearn_model({"key": "value"}) is False


def test_extract_sklearn_hyperparameters():
    """Test hyperparameter extraction from sklearn model."""
    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    hyperparams = extract_sklearn_hyperparameters(model)

    assert "n_estimators" in hyperparams
    assert hyperparams["n_estimators"] == 100
    assert "max_depth" in hyperparams
    assert hyperparams["max_depth"] == 5
    assert "random_state" in hyperparams
    assert hyperparams["random_state"] == 42


def test_extract_sklearn_hyperparameters_nested():
    """Test hyperparameter extraction with nested parameters."""
    model = RandomForestClassifier(
        n_estimators=50, max_depth=3, random_state=42, max_features="sqrt"
    )
    hyperparams = extract_sklearn_hyperparameters(model)

    assert hyperparams["n_estimators"] == 50
    assert hyperparams["max_depth"] == 3
    assert hyperparams["max_features"] == "sqrt"


def test_extract_sklearn_metrics_unfitted():
    """Test metrics extraction from unfitted model returns empty dict."""
    model = RandomForestClassifier()
    metrics = extract_sklearn_metrics(model)

    assert isinstance(metrics, dict)
    assert len(metrics) == 0


def test_extract_sklearn_metrics_fitted_rf():
    """Test metrics extraction from fitted RandomForest."""
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=4, random_state=42)
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    metrics = extract_sklearn_metrics(model)

    assert "feature_importances" in metrics
    assert isinstance(metrics["feature_importances"], list)
    assert len(metrics["feature_importances"]) == 4
    assert "n_features_in" in metrics
    assert metrics["n_features_in"] == 4
    assert "n_outputs" in metrics


def test_extract_sklearn_metrics_fitted_lr():
    """Test metrics extraction from fitted LogisticRegression."""
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=4, random_state=42)
    model = LogisticRegression(random_state=42)
    model.fit(X, y)

    metrics = extract_sklearn_metrics(model)

    assert "coef" in metrics
    assert isinstance(metrics["coef"], list)
    assert "intercept" in metrics
    assert isinstance(metrics["intercept"], list)
    assert "n_features_in" in metrics
    assert metrics["n_features_in"] == 4


def test_get_sklearn_version():
    """Test getting scikit-learn version."""
    version = get_sklearn_version()
    assert version is not None
    assert isinstance(version, str)
    # Version should be in format like "1.3.0" or "1.3.0.dev0"
    assert len(version) > 0


def test_serialize_sklearn_model(tmp_path):
    """Test model serialization."""
    import fsspec

    from kirin.storage import ContentStore

    model = RandomForestClassifier(n_estimators=10, random_state=42)
    storage = ContentStore(str(tmp_path), fsspec.filesystem("file"))

    model_path, source_path, source_hash = serialize_sklearn_model(
        model, variable_name="test_model", temp_dir=tmp_path, storage=storage
    )

    assert Path(model_path).exists()
    assert Path(model_path).name == "test_model.pkl"
    # Source detection may or may not work in test environment
    # Just check that function returns without error


def test_serialize_sklearn_model_without_storage(tmp_path):
    """Test model serialization without storage (no source linking)."""
    model = RandomForestClassifier(n_estimators=10, random_state=42)

    model_path, source_path, source_hash = serialize_sklearn_model(
        model, variable_name="test_model", temp_dir=tmp_path, storage=None
    )

    assert Path(model_path).exists()
    assert Path(model_path).name == "test_model.pkl"
    assert source_path is None
    assert source_hash is None


def test_serialize_sklearn_model_with_explicit_name(tmp_path):
    """Test model serialization with explicit variable name."""
    model = RandomForestClassifier(n_estimators=10, random_state=42)

    # When variable_name is provided explicitly, should work
    model_path, _, _ = serialize_sklearn_model(
        model, variable_name="my_model", temp_dir=tmp_path, storage=None
    )

    assert Path(model_path).name == "my_model.pkl"


def test_detect_model_variable_name():
    """Test variable name detection."""
    model = RandomForestClassifier()

    # In this test context, we can't easily test variable name detection
    # because the model is created in the test function itself
    # But we can test that it doesn't crash
    var_name = detect_model_variable_name(model)
    # May return None if detection fails, which is acceptable
    assert var_name is None or isinstance(var_name, str)


def test_commit_with_model_object(tmp_path):
    """Test committing a model object directly."""
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=4, random_state=42)
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    dataset = Dataset(root_dir=tmp_path, name="test_model_commit")
    commit_hash = dataset.commit(
        message="Test model commit",
        add_files=[model],
    )

    assert commit_hash is not None
    assert dataset.current_commit is not None

    # Check that model file was committed
    files = dataset.list_files()
    model_files = [f for f in files if f.endswith(".pkl")]
    assert len(model_files) > 0

    # Check metadata
    metadata = dataset.current_commit.metadata
    assert "models" in metadata
    assert len(metadata["models"]) > 0

    # Get first model metadata
    model_meta = list(metadata["models"].values())[0]
    assert "model_type" in model_meta
    assert "hyperparameters" in model_meta
    assert "metrics" in model_meta
    assert "sklearn_version" in model_meta
    assert model_meta["model_type"] == "RandomForestClassifier"
    assert "n_estimators" in model_meta["hyperparameters"]
    assert isinstance(model_meta["sklearn_version"], str)


def test_commit_with_model_and_file_path(tmp_path):
    """Test committing model object with regular file path."""
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=4, random_state=42)
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)

    # Create a regular file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    dataset = Dataset(root_dir=tmp_path, name="test_mixed_commit")
    commit_hash = dataset.commit(
        message="Test mixed commit",
        add_files=[model, str(test_file)],
    )

    assert commit_hash is not None
    files = dataset.list_files()
    assert len(files) == 2  # Model file + test.txt
    assert "test.txt" in files


def test_commit_with_multiple_models(tmp_path):
    """Test committing multiple models with model-specific metadata."""
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=4, random_state=42)

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X, y)
    rf_accuracy = rf_model.score(X, y)

    lr_model = LogisticRegression(random_state=42)
    lr_model.fit(X, y)
    lr_accuracy = lr_model.score(X, y)

    dataset = Dataset(root_dir=tmp_path, name="test_multiple_models")
    commit_hash = dataset.commit(
        message="Compare models",
        add_files=[rf_model, lr_model],
        metadata={
            "models": {
                "rf_model": {"accuracy": rf_accuracy},
                "lr_model": {"accuracy": lr_accuracy},
            },
            "dataset": "test",
        },
    )

    assert commit_hash is not None
    metadata = dataset.current_commit.metadata

    assert "models" in metadata
    assert "rf_model" in metadata["models"]
    assert "lr_model" in metadata["models"]

    # Check RF model metadata
    rf_meta = metadata["models"]["rf_model"]
    assert rf_meta["model_type"] == "RandomForestClassifier"
    assert "hyperparameters" in rf_meta
    assert "metrics" in rf_meta
    assert "sklearn_version" in rf_meta
    assert rf_meta["accuracy"] == rf_accuracy
    assert isinstance(rf_meta["sklearn_version"], str)

    # Check LR model metadata
    lr_meta = metadata["models"]["lr_model"]
    assert lr_meta["model_type"] == "LogisticRegression"
    assert "hyperparameters" in lr_meta
    assert "metrics" in lr_meta
    assert "sklearn_version" in lr_meta
    assert lr_meta["accuracy"] == lr_accuracy
    assert isinstance(lr_meta["sklearn_version"], str)

    # Check top-level metadata
    assert metadata["dataset"] == "test"


def test_commit_with_model_specific_metadata_merging(tmp_path):
    """Test that user-provided metadata merges with auto-extracted metadata."""
    from sklearn.datasets import make_classification

    X, y = make_classification(n_samples=100, n_features=4, random_state=42)
    model = RandomForestClassifier(n_estimators=50, max_depth=3, random_state=42)
    model.fit(X, y)

    dataset = Dataset(root_dir=tmp_path, name="test_metadata_merge")
    commit_hash = dataset.commit(
        message="Test metadata merge",
        add_files=[model],
        metadata={
            "models": {
                "model": {
                    "accuracy": 0.95,
                    "custom_metric": "test_value",
                }
            }
        },
    )

    assert commit_hash is not None
    metadata = dataset.current_commit.metadata

    model_meta = metadata["models"]["model"]
    # Auto-extracted should be present
    assert "hyperparameters" in model_meta
    assert "metrics" in model_meta
    assert "model_type" in model_meta
    assert "sklearn_version" in model_meta
    assert isinstance(model_meta["sklearn_version"], str)
    # User-provided should be present
    assert "accuracy" in model_meta
    assert model_meta["accuracy"] == 0.95
    assert "custom_metric" in model_meta
    assert model_meta["custom_metric"] == "test_value"


def test_commit_with_invalid_object_raises_error(tmp_path):
    """Test that committing invalid object raises error."""
    dataset = Dataset(root_dir=tmp_path, name="test_invalid")

    with pytest.raises(ValueError, match="Unsupported item type"):
        dataset.commit(
            message="Test invalid",
            add_files=[{"not": "a model"}],
        )


def test_commit_backward_compatibility_file_paths(tmp_path):
    """Test that existing file path usage still works."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")

    dataset = Dataset(root_dir=tmp_path, name="test_backward_compat")
    commit_hash = dataset.commit(
        message="Test backward compat",
        add_files=[str(test_file)],
    )

    assert commit_hash is not None
    assert "test.txt" in dataset.list_files()
