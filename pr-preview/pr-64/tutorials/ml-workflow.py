# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
#     "scikit-learn",
#     "matplotlib",
#     "seaborn",
#     "pandas",
#     "numpy",
#     "joblib",
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../../", editable = true }
# ///

import marimo

__generated_with = "0.18.4"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Machine Learning Workflow with Kirin

    This tutorial will guide you through a complete machine learning workflow
    using Kirin for version control. You'll learn how to train a model, create
    diagnostic plots, archive everything together, and track different model
    versions over time.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## What You'll Learn

    - How to train a machine learning model with scikit-learn
    - How to create diagnostic plots for model evaluation
    - How to archive model artifacts, metrics, and plots together in Kirin
    - How to version control your ML workflow with commits
    - How to track improvements across different model versions
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Prerequisites

    - Python 3.13 or higher
    - Kirin installed (see [Installation Guide](../getting-started/installation.md))
    - Basic familiarity with machine learning concepts
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Understanding ML Workflow Versioning

    When working with machine learning models, you need to track multiple
    artifacts together:

    - **Model artifacts**: The trained model files (weights, parameters)
    - **Metrics**: Performance measurements (accuracy, precision, recall)
    - **Diagnostic plots**: Visualizations that help understand model behavior
    - **Metadata**: Hyperparameters, training configuration, dataset info

    Kirin lets you commit all of these together, creating a complete snapshot
    of your model at a point in time. When you improve your model, you create
    a new commit with updated artifacts, showing the evolution of your work.
    """)
    return


@app.cell
def _():
    import subprocess
    import tempfile
    from pathlib import Path

    from kirin import Dataset

    # Create temporary directory for our workflow
    temp_dir = Path(tempfile.mkdtemp(prefix="kirin_ml_workflow_"))
    print(f"Created dataset directory: {temp_dir}")
    return Dataset, Path, subprocess, temp_dir


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Train and Commit Initial Model

    We'll use the classic Iris dataset from scikit-learn, which contains
    measurements of iris flowers for three different species. This is a
    classification problem where we predict the species based on flower
    measurements.

    We'll train an initial Random Forest model with simple hyperparameters
    to establish a baseline, then commit it along with diagnostic plots.
    """)
    return


@app.cell
def _(Path):
    # Get the script path (same directory as this notebook)
    script_path = Path(__file__).parent / "ml-workflow-script.py"
    return (script_path,)


@app.cell
def _(script_path, subprocess, temp_dir):
    # Run the script to train initial model
    _result = subprocess.run(
        ["uv", "run", str(script_path), str(temp_dir), "--step", "initial"],
        capture_output=True,
        text=True,
    )

    print(_result.stdout)
    if _result.stderr:
        print("STDERR:", _result.stderr)
    if _result.returncode != 0:
        print(f"Error: Script exited with code {_result.returncode}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What just happened?**

    We've created our first model version commit! All the artifacts are now
    stored together in Kirin:

    - The trained model was automatically serialized (no manual joblib.dump needed!)
    - Hyperparameters were automatically extracted from the model
    - Metrics were automatically extracted (feature_importances_, etc.)
    - The plots were automatically converted to SVG files
    - Source file linking connects the model to the script that created it
    - Everything is versioned together, so you can always see what went into
      this model version

    Notice how much simpler this is compared to the traditional workflow where you'd
    need to manually: save the model with `joblib.dump()`, extract hyperparameters
    with `model.get_params()`, save plots with `plt.savefig()`, and manually track
    all these files. Here, we just passed the model and plot objects directly, and
    Kirin handled serialization, metadata extraction, and file conversion automatically!

    Now let's see how to create an improved version.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Train and Commit Improved Model

    Now let's train an improved version with better hyperparameters. We'll
    increase the number of trees, allow deeper trees, and tune other
    parameters to improve performance.
    """)
    return


@app.cell
def _(script_path, subprocess, temp_dir):
    # Run the script to train improved model
    _result = subprocess.run(
        ["uv", "run", str(script_path), str(temp_dir), "--step", "improved"],
        capture_output=True,
        text=True,
    )

    print(_result.stdout)
    if _result.stderr:
        print("STDERR:", _result.stderr)
    if _result.returncode != 0:
        print(f"Error: Script exited with code {_result.returncode}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    **What just happened?**

    We've successfully created two model versions in Kirin:

    1. **Initial Model (v1.0)**: Random Forest with 3 trees, max depth 1
    2. **Improved Model (v2.0)**: Random Forest with 100 trees, unlimited depth

    Each commit contains:
    - The complete model artifact (auto-serialized)
    - Hyperparameters (auto-extracted via get_params())
    - Metrics (auto-extracted: feature_importances_, n_features_in_, etc.)
    - All diagnostic plots (auto-converted to SVG)
    - Source file linking (connects model to script)

    This workflow is much simpler than manually managing files: instead of saving
    models with `joblib.dump()`, extracting metadata manually, and saving plots
    with `plt.savefig()`, we just passed the model and plot objects directly.
    Kirin handled all the serialization, metadata extraction, and file conversion
    automatically!

    The commit history shows the linear progression of your model development,
    making it easy to track improvements and understand what changed between
    versions.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: View the Commit History

    Let's look at the commit history to see how our model has evolved. This
    shows the linear progression of our model versions.
    """)
    return


@app.cell
def _(Dataset, temp_dir):
    # Load the dataset and view commit history
    dataset = Dataset(root_dir=temp_dir, name="iris_classifier")
    history = dataset.history()

    print("✅ Commit history retrieved")
    print(f"\n📊 Model Version History ({len(history)} commits):\n")
    for i, commit in enumerate(history, 1):
        print(f"{i}. {commit.message}")
        print(f"   Hash: {commit.hash[:8]}")
        if commit.metadata and "accuracy" in commit.metadata:
            print(f"   Accuracy: {commit.metadata['accuracy']:.4f}")
        print()
    return dataset, history


@app.cell
def _(dataset):
    # Display the dataset
    dataset
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Access Files from Different Versions

    One of the powerful features of Kirin is the ability to access files from
    any commit in the history. We'll use `checkout()` to switch to a specific
    commit, then use the `local_files()` context manager to access files as
    local paths.
    """)
    return


@app.cell
def _(dataset, history):
    import joblib

    # Get the first commit (initial model)
    initial_commit = history[-1]  # History is in reverse chronological order

    # Checkout the initial commit
    dataset.checkout(initial_commit.hash)

    # Access files as local paths using the context manager
    with dataset.local_files() as local_files:
        # Find the model file
        model_files = [f for f in local_files.keys() if f.endswith(".pkl")]
        if model_files:
            initial_model_path = local_files[model_files[0]]
            initial_model_loaded = joblib.load(initial_model_path)

            print("✅ Model loaded from initial commit")
            print(f"   Commit: {initial_commit.hash[:8]}")
            print(f"   Message: {initial_commit.message}")
            print(f"   Model type: {type(initial_model_loaded).__name__}")
            print(f"   Number of trees: {initial_model_loaded.n_estimators}")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    In this tutorial, you've learned how to:

    - **Train machine learning models** using scikit-learn
    - **Create diagnostic plots** to visualize model performance
    - **Commit model objects directly** - Kirin automatically handles
      serialization, hyperparameter extraction, and metrics extraction
    - **Commit plot objects directly** - Kirin automatically converts them to
      SVG files with format auto-detection
    - **Archive complete model snapshots** in Kirin, including:
      - Model artifacts (auto-serialized)
      - Hyperparameters (auto-extracted)
      - Metrics (auto-extracted)
      - Diagnostic plots (auto-converted to SVG)
      - Source file linking
    - **Version control your ML workflow** by committing different model
      versions
    - **Track improvements** across model versions using commit history
    - **Access historical versions** of your models and artifacts

    **Key Takeaways**:

    - Kirin lets you commit model objects directly - no manual serialization
      needed!
    - Kirin lets you commit plot objects directly - no manual file saving needed!
    - Hyperparameters and metrics are automatically extracted from scikit-learn
      models
    - Plots are automatically converted to SVG with format auto-detection
    - Source file linking connects models to the scripts that created them
    - The linear commit history makes it easy to track model evolution
    - You can always access any version of your models and artifacts from the
      commit history

    **Next Steps**:

    - Try this workflow with your own models and datasets
    - Explore the [Model Versioning Guide](../guides/model-versioning.md) for
      more advanced features
    - Check out the [How-To Guide](../how-to/track-model-data.py) for
      additional ML workflow patterns
    """)
    return


if __name__ == "__main__":
    app.run()
