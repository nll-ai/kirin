"""Tests for commit analytics helpers."""

from pathlib import Path

from kirin.commit_query import (
    commits_to_records,
    metadata_all,
    metadata_any,
    metadata_equals,
    metadata_exists,
    metadata_greater_than,
    metadata_startswith,
)
from kirin.dataset import Dataset


def test_metadata_predicates_support_nested_paths():
    """Test metadata predicates support dotted nested paths."""
    metadata = {
        "accuracy": 0.92,
        "version": "2.0.0",
        "training": {"samples": 15000},
    }

    assert metadata_greater_than("accuracy", 0.9)(metadata)
    assert metadata_startswith("version", "2.")(metadata)
    assert metadata_equals("training.samples", 15000)(metadata)
    assert metadata_exists("training.samples")(metadata)
    assert not metadata_exists("training.missing")(metadata)


def test_metadata_combinators_all_and_any():
    """Test metadata combinators for all/any behavior."""
    metadata = {"accuracy": 0.88, "domain": "medical", "version": "2.1.0"}

    high_accuracy = metadata_greater_than("accuracy", 0.9)
    is_medical = metadata_equals("domain", "medical")
    is_v2 = metadata_startswith("version", "2.")

    assert not metadata_all([high_accuracy, is_medical, is_v2])(metadata)
    assert metadata_any([high_accuracy, is_medical])(metadata)


def test_commits_to_records_projects_metadata_fields(tmp_path):
    """Test commit projections generate tabular records."""
    dataset = Dataset(root_dir=tmp_path, name="analytics-test")
    tracked_file = Path(tmp_path) / "artifact.txt"

    tracked_file.write_text("version-1")
    dataset.commit(
        message="baseline",
        add_files=[tracked_file],
        metadata={"accuracy": 0.87, "version": "1.0.0"},
        tags=["baseline"],
    )

    tracked_file.write_text("version-2")
    dataset.commit(
        message="improved",
        add_files=[tracked_file],
        metadata={"accuracy": 0.92, "version": "2.0.0"},
        tags=["production", "v2.0"],
    )

    rows = commits_to_records(
        dataset.history(),
        metadata_keys=["accuracy", "version"],
    )

    assert len(rows) == 2
    assert rows[0]["message"] == "improved"
    assert rows[0]["accuracy"] == 0.92
    assert rows[0]["version"] == "2.0.0"
    assert "production" in rows[0]["tags"]
    assert rows[1]["message"] == "baseline"
