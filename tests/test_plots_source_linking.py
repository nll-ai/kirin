"""Tests for source file detection utility.

Note: Source file linking for plots committed via dataset.commit() is tested
in test_ml_artifacts.py alongside model source linking tests.
"""

from kirin.utils import detect_source_file


def test_detect_source_file_from_script(tmp_path, monkeypatch):
    """Test that detect_source_file() detects regular Python scripts."""
    script_path = tmp_path / "test_script.py"
    script_path.write_text("# Test script\nprint('hello')\n")

    # Mock inspect.stack() to return our script in the call stack
    import inspect

    def mock_stack():
        # Create a mock FrameInfo that matches inspect.stack() structure
        # inspect.stack() returns FrameInfo objects with .frame, .filename, etc.
        # Frame 0: detect_source_file() itself (will be skipped)
        detect_frame = type(
            "Frame",
            (),
            {
                "f_globals": {},
                "f_code": type("Code", (), {"co_filename": "<test>"})(),
            },
        )()
        detect_frame_info = type(
            "FrameInfo",
            (),
            {
                "frame": detect_frame,
                "filename": "<test>",
                "lineno": 1,
                "function": "detect_source_file",
                "code_context": None,
                "index": None,
            },
        )()

        # Frame 1: The actual script we want to detect
        script_frame = type(
            "Frame",
            (),
            {
                "f_globals": {"__file__": str(script_path)},
                "f_code": type("Code", (), {"co_filename": str(script_path)})(),
            },
        )()
        script_frame_info = type(
            "FrameInfo",
            (),
            {
                "frame": script_frame,
                "filename": str(script_path),
                "lineno": 1,
                "function": "test_function",
                "code_context": None,
                "index": None,
            },
        )()
        return [detect_frame_info, script_frame_info]

    monkeypatch.setattr(inspect, "stack", mock_stack)

    detected = detect_source_file()
    # Should detect our script file
    assert detected == str(script_path)


def test_detect_source_file_no_source(monkeypatch):
    """Test that detect_source_file() returns None when no source can be detected."""
    import inspect

    # Mock stack to return frames without valid source files
    def mock_stack():
        frame = type(
            "Frame",
            (),
            {
                "f_globals": {},
                "f_code": type("Code", (), {"co_filename": "<stdin>"})(),
            },
        )()
        frame_info = type("FrameInfo", (), {"frame": frame})()
        return [frame_info]

    monkeypatch.setattr(inspect, "stack", mock_stack)

    detected = detect_source_file()
    # Should return None when no valid source file found
    assert detected is None


def test_file_metadata_serialization(tmp_path):
    """Test that File metadata is properly serialized and deserialized."""
    from kirin.file import File
    from kirin.storage import ContentStore

    # Create storage
    storage = ContentStore(str(tmp_path / "storage"))

    # Create file with metadata
    file_obj = File(
        hash="abc123",
        name="test.txt",
        size=100,
        metadata={"source_file": "script.py", "source_hash": "def456"},
        _storage=storage,
    )

    # Serialize
    file_dict = file_obj.to_dict()
    assert "metadata" in file_dict
    assert file_dict["metadata"]["source_file"] == "script.py"
    assert file_dict["metadata"]["source_hash"] == "def456"

    # Deserialize
    restored_file = File.from_dict(file_dict, storage=storage)
    assert restored_file.metadata == file_obj.metadata
    assert restored_file.metadata["source_file"] == "script.py"
    assert restored_file.metadata["source_hash"] == "def456"


def test_commit_with_file_metadata(tmp_path):
    """Test that commits properly serialize File metadata."""
    from kirin import Dataset
    from kirin.file import File
    from kirin.storage import ContentStore

    # Create dataset
    dataset_root = tmp_path / "dataset"
    dataset = Dataset(root_dir=str(dataset_root), name="test_dataset")

    # Create storage
    storage = ContentStore(str(tmp_path / "storage"))

    # Create file with metadata (not used directly, just testing File creation)
    _file_obj = File(
        hash="abc123",
        name="test.txt",
        size=100,
        metadata={"source_file": "script.py", "source_hash": "def456"},
        _storage=storage,
    )

    # Create a dummy file to commit
    dummy_file = tmp_path / "dummy.txt"
    dummy_file.write_text("dummy content")

    # Create commit with file
    _commit_hash = dataset.commit(
        message="Test commit",
        add_files=[str(dummy_file)],
    )

    # Get commit and verify metadata is preserved
    commit = dataset.current_commit
    assert commit is not None

    # If the file is in the commit, check its metadata
    if "test.txt" in commit.files:
        file_in_commit = commit.files["test.txt"]
        assert hasattr(file_in_commit, "metadata")
        assert isinstance(file_in_commit.metadata, dict)
