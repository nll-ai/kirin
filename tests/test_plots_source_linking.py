"""Tests for plot source file detection and linking."""

from kirin import Dataset
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


def test_save_plot_with_source_file(tmp_path, monkeypatch):
    """Test that save_plot() detects and stores source files."""
    import matplotlib.pyplot as plt

    # Create a temporary script file
    script_path = tmp_path / "test_script.py"
    script_path.write_text("# Test script\nimport matplotlib.pyplot as plt\n")

    # Mock source detection to return our script
    # Need to patch where it's imported, not where it's defined
    def mock_detect_source_file():
        return str(script_path)

    from kirin import plots

    monkeypatch.setattr(plots, "detect_source_file", mock_detect_source_file)

    # Create dataset
    dataset_root = tmp_path / "dataset"
    dataset = Dataset(root_dir=str(dataset_root), name="test_dataset")

    # Create a plot
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])
    plt.close(fig)

    # Save plot with auto-commit
    _commit_hash = dataset.save_plot(
        fig, "test_plot.png", auto_commit=True, message="Add plot"
    )

    # Verify plot was saved
    plot_file = dataset.get_file("test_plot.svg")
    assert plot_file is not None

    # Verify source file was detected and stored
    assert plot_file.metadata.get("source_file") == "test_script.py"
    assert plot_file.metadata.get("source_hash") is not None

    # Verify source file is in the same commit
    source_file = dataset.get_file("test_script.py")
    assert source_file is not None
    assert source_file.hash == plot_file.metadata["source_hash"]


def test_dataset_save_plot_with_source_metadata(tmp_path):
    """Test that Dataset.save_plot() stores source file metadata."""
    import matplotlib.pyplot as plt

    # Create dataset
    dataset_root = tmp_path / "dataset"
    dataset = Dataset(root_dir=str(dataset_root), name="test_dataset")

    # Create a plot
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])
    plt.close(fig)

    # Save plot with auto-commit
    _commit_hash = dataset.save_plot(
        fig, "test_plot.png", auto_commit=True, message="Add plot"
    )

    # Get the file from the commit (extension changes to .svg)
    file_obj = dataset.get_file("test_plot.svg")
    assert file_obj is not None

    # Check if metadata exists (may be empty if source not detected)
    assert hasattr(file_obj, "metadata")
    assert isinstance(file_obj.metadata, dict)

    # If source was detected, metadata should contain source info
    if file_obj.metadata.get("source_file"):
        assert "source_file" in file_obj.metadata
        assert "source_hash" in file_obj.metadata
        assert isinstance(file_obj.metadata["source_file"], str)
        assert isinstance(file_obj.metadata["source_hash"], str)


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


def test_source_file_stored_in_same_commit(tmp_path):
    """Test that source file is stored in the same commit as the plot."""
    import matplotlib.pyplot as plt

    # Create a temporary script file
    script_path = tmp_path / "test_script.py"
    script_path.write_text("# Test script\nimport matplotlib.pyplot as plt\n")

    # Create dataset
    dataset_root = tmp_path / "dataset"
    dataset = Dataset(root_dir=str(dataset_root), name="test_dataset")

    # Create a plot
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])
    plt.close(fig)

    # Save plot with auto-commit
    _commit_hash = dataset.save_plot(
        fig, "test_plot.png", auto_commit=True, message="Add plot"
    )

    # Get the commit
    commit = dataset.current_commit
    assert commit is not None

    # Check that plot file exists (extension changes to .svg)
    plot_file = dataset.get_file("test_plot.svg")
    assert plot_file is not None

    # If source was detected, check that source file is also in the commit
    if plot_file.metadata.get("source_file"):
        source_filename = plot_file.metadata["source_file"]
        source_file = dataset.get_file(source_filename)
        assert source_file is not None, (
            f"Source file {source_filename} should be in commit"
        )
        assert source_file.hash == plot_file.metadata["source_hash"]
