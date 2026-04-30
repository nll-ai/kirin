"""Generic commit query helpers for filtering and projection."""

from collections.abc import Callable, Iterable
from datetime import datetime
from typing import Any

from .commit import Commit

MetadataFilter = Callable[[dict[str, Any]], bool]


def get_metadata_value(
    metadata: dict[str, Any], key_path: str, default: Any = None
) -> Any:
    """Get a nested metadata value via dotted key path.

    :param metadata: Metadata dictionary.
    :param key_path: Dotted key path like ``training.samples``.
    :param default: Value to return when path is missing.
    :return: Resolved value or default.
    """
    current_value: Any = metadata
    for part in key_path.split("."):
        if not isinstance(current_value, dict) or part not in current_value:
            return default
        current_value = current_value[part]
    return current_value


def metadata_equals(key_path: str, expected_value: Any) -> MetadataFilter:
    """Build a metadata filter that checks equality.

    :param key_path: Dotted metadata key path.
    :param expected_value: Expected value.
    :return: Predicate function for metadata filtering.
    """

    def matches(metadata: dict[str, Any]) -> bool:
        """Check equality for one metadata payload.

        :param metadata: Metadata dictionary.
        :return: True if metadata value equals expected value.
        """
        return get_metadata_value(metadata, key_path) == expected_value

    return matches


def metadata_greater_than(key_path: str, threshold: float) -> MetadataFilter:
    """Build a metadata filter that checks numeric threshold.

    :param key_path: Dotted metadata key path.
    :param threshold: Numeric threshold.
    :return: Predicate function for metadata filtering.
    """

    def matches(metadata: dict[str, Any]) -> bool:
        """Check threshold for one metadata payload.

        :param metadata: Metadata dictionary.
        :return: True if metadata value exceeds threshold.
        """
        value = get_metadata_value(metadata, key_path)
        return isinstance(value, (int, float)) and value > threshold

    return matches


def metadata_startswith(key_path: str, prefix: str) -> MetadataFilter:
    """Build a metadata filter for string prefixes.

    :param key_path: Dotted metadata key path.
    :param prefix: String prefix to match.
    :return: Predicate function for metadata filtering.
    """

    def matches(metadata: dict[str, Any]) -> bool:
        """Check prefix for one metadata payload.

        :param metadata: Metadata dictionary.
        :return: True if metadata value starts with prefix.
        """
        value = get_metadata_value(metadata, key_path)
        return isinstance(value, str) and value.startswith(prefix)

    return matches


def metadata_exists(key_path: str) -> MetadataFilter:
    """Build a metadata filter that checks presence.

    :param key_path: Dotted metadata key path.
    :return: Predicate function for metadata filtering.
    """

    def matches(metadata: dict[str, Any]) -> bool:
        """Check existence for one metadata payload.

        :param metadata: Metadata dictionary.
        :return: True if dotted key path exists.
        """
        marker = object()
        return get_metadata_value(metadata, key_path, default=marker) is not marker

    return matches


def metadata_all(filters: Iterable[MetadataFilter]) -> MetadataFilter:
    """Combine metadata filters using logical AND.

    :param filters: Iterable of metadata predicate functions.
    :return: Combined predicate.
    """
    filter_list = list(filters)

    def matches(metadata: dict[str, Any]) -> bool:
        """Evaluate all predicates for one metadata payload.

        :param metadata: Metadata dictionary.
        :return: True if all filters match.
        """
        return all(filter_fn(metadata) for filter_fn in filter_list)

    return matches


def metadata_any(filters: Iterable[MetadataFilter]) -> MetadataFilter:
    """Combine metadata filters using logical OR.

    :param filters: Iterable of metadata predicate functions.
    :return: Combined predicate.
    """
    filter_list = list(filters)

    def matches(metadata: dict[str, Any]) -> bool:
        """Evaluate any predicate for one metadata payload.

        :param metadata: Metadata dictionary.
        :return: True if any filter matches.
        """
        return any(filter_fn(metadata) for filter_fn in filter_list)

    return matches


def commits_to_records(
    commits: Iterable[Commit],
    metadata_keys: Iterable[str] = (),
    *,
    include_tags: bool = True,
    tags_separator: str = ", ",
    include_timestamp: bool = True,
) -> list[dict[str, Any]]:
    """Project commits into row dictionaries for tables/dataframes.

    :param commits: Commit iterable.
    :param metadata_keys: Metadata fields to project.
    :param include_tags: Whether to include serialized tags.
    :param tags_separator: Tag join separator.
    :param include_timestamp: Whether to include commit timestamp.
    :return: List of row dictionaries.
    """
    keys = list(metadata_keys)
    rows: list[dict[str, Any]] = []

    for commit in commits:
        row: dict[str, Any] = {
            "commit": commit.short_hash,
            "message": commit.message,
        }
        if include_timestamp:
            timestamp: datetime = commit.timestamp
            row["timestamp"] = timestamp.isoformat()
        if include_tags:
            row["tags"] = tags_separator.join(commit.tags) if commit.tags else "none"

        for key in keys:
            row[key] = get_metadata_value(commit.metadata, key)

        rows.append(row)

    return rows
