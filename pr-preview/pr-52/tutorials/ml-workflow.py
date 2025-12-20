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
    import tempfile
    from pathlib import Path

    import joblib
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns
    from sklearn.datasets import load_iris
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        accuracy_score,
        classification_report,
        confusion_matrix,
    )
    from sklearn.model_selection import train_test_split

    from kirin import Dataset

    # Set style for plots
    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)

    # Create temporary directory for our workflow
    temp_dir = Path(tempfile.mkdtemp(prefix="kirin_ml_workflow_"))

    # Create a dataset to serve as our model registry
    model_registry = Dataset(root_dir=temp_dir, name="iris_classifier")
    model_registry
    return (
        RandomForestClassifier,
        accuracy_score,
        classification_report,
        confusion_matrix,
        joblib,
        load_iris,
        model_registry,
        np,
        plt,
        sns,
        temp_dir,
        train_test_split,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 1: Load and Prepare the Data

    We'll use the classic Iris dataset from scikit-learn, which contains
    measurements of iris flowers for three different species. This is a
    classification problem where we predict the species based on flower
    measurements.
    """)
    return


@app.cell
def _(load_iris, train_test_split):
    # Load the Iris dataset
    iris_data = load_iris()
    X = iris_data.data
    y = iris_data.target
    feature_names = iris_data.feature_names
    target_names = iris_data.target_names

    # Split into training and testing sets
    # Using a smaller test set to show more variation between models
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    print("✅ Dataset loaded and split")
    print(f"   Training samples: {len(X_train)}")
    print(f"   Test samples: {len(X_test)}")
    print(f"   Features: {', '.join(feature_names)}")
    print(f"   Classes: {', '.join(target_names)}")
    return X_test, X_train, feature_names, target_names, y_test, y_train


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 2: Train the Initial Model

    We'll train a Random Forest classifier as our initial model. We'll start
    with a simple configuration to establish a baseline, then improve it in
    the next version.
    """)
    return


@app.cell
def _(RandomForestClassifier, X_train, y_train):
    # Train initial model with very simple hyperparameters (baseline)
    # Using very few trees and very shallow depth for a simple baseline
    initial_model = RandomForestClassifier(
        n_estimators=3,
        max_depth=1,
        random_state=1,  # Different random state
    )
    initial_model.fit(X_train, y_train)

    print("✅ Initial model trained")
    print("   Model type: RandomForestClassifier")
    print(f"   Number of trees: {initial_model.n_estimators}")
    print(f"   Max depth: {initial_model.max_depth}")
    return (initial_model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 3: Evaluate the Model

    Before archiving, we need to evaluate our model's performance. We'll
    calculate metrics and create diagnostic plots that help us understand how
    well the model performs.
    """)
    return


@app.cell
def _(X_test, accuracy_score, initial_model, y_test):
    # Make predictions
    y_pred = initial_model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)

    print("✅ Model evaluated")
    print(f"   Test accuracy: {accuracy:.4f}")
    return accuracy, y_pred


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 4: Create Diagnostic Plots

    Diagnostic plots help visualize model performance and behavior. We'll
    create:

    - **Confusion Matrix**: Shows how well the model classifies each class
    - **Feature Importance**: Shows which features the model considers most
      important
    - **Classification Report Visualization**: Displays precision, recall, and
      F1-score for each class
    """)
    return


@app.cell
def _(
    classification_report,
    confusion_matrix,
    feature_names,
    initial_model,
    np,
    plt,
    sns,
    target_names,
    temp_dir,
    y_pred,
    y_test,
):
    # Create directory for plots
    plots_dir = temp_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    # Plot 1: Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=target_names,
        yticklabels=target_names,
    )
    plt.title("Confusion Matrix - Initial Model")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    confusion_matrix_path = plots_dir / "confusion_matrix.png"
    plt.savefig(confusion_matrix_path, dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 2: Feature Importance
    feature_importance = initial_model.feature_importances_
    plt.figure(figsize=(10, 6))
    indices = np.argsort(feature_importance)[::-1]
    plt.bar(range(len(feature_importance)), feature_importance[indices])
    plt.xticks(range(len(feature_importance)), [feature_names[i] for i in indices])
    plt.title("Feature Importance - Initial Model")
    plt.xlabel("Features")
    plt.ylabel("Importance")
    plt.xticks(rotation=45, ha="right")
    feature_importance_path = plots_dir / "feature_importance.png"
    plt.savefig(feature_importance_path, dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 3: Classification Report (as text, saved to file)
    report = classification_report(y_test, y_pred, target_names=target_names)
    report_path = plots_dir / "classification_report.txt"
    report_path.write_text(report)

    print("✅ Diagnostic plots created")
    print(f"   - Confusion matrix: {confusion_matrix_path.name}")
    print(f"   - Feature importance: {feature_importance_path.name}")
    print(f"   - Classification report: {report_path.name}")
    return (
        confusion_matrix_path,
        feature_importance_path,
        plots_dir,
        report_path,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 5: Commit Everything to Kirin

    Now we'll commit all our artifacts together: the model, plots, and
    metadata. Kirin automatically handles model serialization and extracts
    hyperparameters and metrics, so we can just pass the model object directly!
    This creates a complete snapshot of our model version that we can reference
    later.
    """)
    return


@app.cell
def _(
    accuracy,
    confusion_matrix_path,
    feature_importance_path,
    initial_model,
    model_registry,
    report_path,
):
    # Commit all artifacts together
    # Model object is passed directly - auto-serialized and metadata extracted!
    commit_hash = model_registry.commit(
        message="Initial model v1.0 - Simple Random Forest baseline (3 trees, depth 1)",
        add_files=[
            initial_model,  # Model object - auto-serialized as "initial_model.pkl"
            str(confusion_matrix_path),
            str(feature_importance_path),
            str(report_path),
        ],
        metadata={
            "accuracy": accuracy,  # Data-dependent metric
            "model_version": "1.0.0",
        },
    )

    print("✅ Initial model version committed")
    print(f"   Commit hash: {commit_hash[:8]}")
    print("   Files committed:")
    print("     - Model artifact (auto-serialized)")
    print("     - Hyperparameters (auto-extracted)")
    print("     - Metrics (auto-extracted)")
    print("     - Confusion matrix plot")
    print("     - Feature importance plot")
    print("     - Classification report")
    return (commit_hash,)


@app.cell
def _(commit_hash, model_registry):
    if commit_hash:
        pass

    model_registry
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
    - The plots help visualize model performance
    - Source file linking connects the model to the script that created it
    - Everything is versioned together, so you can always see what went into
      this model version

    Notice how much simpler this is - we just passed the model object, and
    Kirin handled the rest!

    Now let's see how to create an improved version.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 6: Train an Improved Model

    Now let's train an improved version with better hyperparameters. We'll
    increase the number of trees, allow deeper trees, and tune other
    parameters to improve performance.
    """)
    return


@app.cell
def _(RandomForestClassifier, X_train, y_train):
    # Train improved model with better hyperparameters
    improved_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,  # No limit on depth
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",  # Better feature sampling
        random_state=42,
    )
    improved_model.fit(X_train, y_train)

    print("✅ Improved model trained")
    print("   Model type: RandomForestClassifier")
    print(f"   Number of trees: {improved_model.n_estimators} (increased from 10)")
    print(f"   Max depth: {improved_model.max_depth} (unlimited, was 3)")
    print("   Max features: sqrt (better feature sampling)")
    return (improved_model,)


@app.cell
def _(X_test, accuracy, accuracy_score, improved_model, y_test):
    # Evaluate improved model
    y_pred_improved = improved_model.predict(X_test)
    improved_accuracy = accuracy_score(y_test, y_pred_improved)

    print("✅ Improved model evaluated")
    print(f"   Test accuracy: {improved_accuracy:.4f}")
    print(f"   Improvement: {improved_accuracy - accuracy:.4f}")
    return improved_accuracy, y_pred_improved


@app.cell(hide_code=True)
def _(
    classification_report,
    confusion_matrix,
    feature_names,
    improved_model,
    np,
    plots_dir,
    plt,
    sns,
    target_names,
    y_pred_improved,
    y_test,
):
    # Create new diagnostic plots for improved model

    # Plot 1: Confusion Matrix
    cm_improved = confusion_matrix(y_test, y_pred_improved)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm_improved,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=target_names,
        yticklabels=target_names,
    )
    plt.title("Confusion Matrix - Improved Model")
    plt.ylabel("True Label")
    plt.xlabel("Predicted Label")
    confusion_matrix_improved_path = plots_dir / "confusion_matrix.png"
    plt.savefig(confusion_matrix_improved_path, dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 2: Feature Importance
    feature_importance_improved = improved_model.feature_importances_
    plt.figure(figsize=(10, 6))
    indices_improved = np.argsort(feature_importance_improved)[::-1]
    plt.bar(
        range(len(feature_importance_improved)),
        feature_importance_improved[indices_improved],
    )
    plt.xticks(
        range(len(feature_importance_improved)),
        [feature_names[i] for i in indices_improved],
    )
    plt.title("Feature Importance - Improved Model")
    plt.xlabel("Features")
    plt.ylabel("Importance")
    plt.xticks(rotation=45, ha="right")
    feature_importance_improved_path = plots_dir / "feature_importance.png"
    plt.savefig(feature_importance_improved_path, dpi=150, bbox_inches="tight")
    plt.close()

    # Plot 3: Classification Report
    report_improved = classification_report(
        y_test, y_pred_improved, target_names=target_names
    )
    report_improved_path = plots_dir / "classification_report.txt"
    report_improved_path.write_text(report_improved)

    print("✅ Improved diagnostic plots created")
    print(f"   - Confusion matrix: {confusion_matrix_improved_path.name}")
    print(f"   - Feature importance: {feature_importance_improved_path.name}")
    print(f"   - Classification report: {report_improved_path.name}")
    return (
        confusion_matrix_improved_path,
        feature_importance_improved_path,
        report_improved_path,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 7: Commit the Improved Version

    Now we'll commit the improved model version. We'll use the same simplified
    approach - just pass the model object directly. Kirin automatically handles
    serialization, hyperparameter extraction, and metrics extraction.
    """)
    return


@app.cell
def _(
    confusion_matrix_improved_path,
    feature_importance_improved_path,
    improved_accuracy,
    improved_model,
    model_registry,
    report_improved_path,
):
    # Commit improved version
    # Model object passed directly - hyperparameters and metrics auto-extracted!
    improved_commit_hash = model_registry.commit(
        message=(
            "Improved model v2.0 - Better hyperparameters (100 trees, unlimited depth)"
        ),
        add_files=[
            improved_model,  # Model object - auto-serialized as "improved_model.pkl"
            str(confusion_matrix_improved_path),
            str(feature_importance_improved_path),
            str(report_improved_path),
        ],
        metadata={
            "accuracy": improved_accuracy,  # Data-dependent metric
            "model_version": "2.0.0",
        },
    )

    print("✅ Improved model version committed")
    print(f"   Commit hash: {improved_commit_hash[:8]}")
    print("   Files committed:")
    print("     - Model artifact (auto-serialized)")
    print("     - Hyperparameters (auto-extracted)")
    print("     - Metrics (auto-extracted)")
    print("     - Confusion matrix plot (updated)")
    print("     - Feature importance plot (updated)")
    print("     - Classification report (updated)")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 8: View the Commit History

    Let's look at the commit history to see how our model has evolved. This
    shows the linear progression of our model versions.
    """)
    return


@app.cell
def _(model_registry):
    # Get commit history
    history = model_registry.history()

    print("✅ Commit history retrieved")
    print(f"\n📊 Model Version History ({len(history)} commits):\n")
    for i, commit in enumerate(history, 1):
        print(f"{i}. {commit.message}")
        print(f"   Hash: {commit.hash[:8]}")
        if commit.metadata and "accuracy" in commit.metadata:
            print(f"   Accuracy: {commit.metadata['accuracy']:.4f}")
        print()
    return (history,)


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
    - All diagnostic plots
    - Source file linking (connects model to script)

    Notice how much simpler the workflow is now - we just passed model objects
    and Kirin handled serialization and metadata extraction automatically!

    The commit history shows the linear progression of your model development,
    making it easy to track improvements and understand what changed between
    versions.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Step 9: Access Files from Different Versions

    One of the powerful features of Kirin is the ability to access files from
    any commit in the history. We'll use `checkout()` to switch to a specific
    commit, then use the `local_files()` context manager to access files as
    local paths. This is the recommended pattern for working with files from
    historical commits.
    """)
    return


@app.cell
def _(history, joblib, model_registry):
    # Get the first commit (initial model)
    initial_commit = history[-1]  # History is in reverse chronological order

    # Checkout the initial commit
    model_registry.checkout(initial_commit.hash)

    # Access files as local paths using the context manager
    with model_registry.local_files() as local_files:
        initial_model_path = local_files["iris_classifier.pkl"]
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
    - **Archive complete model snapshots** in Kirin, including:
      - Model artifacts (auto-serialized)
      - Hyperparameters (auto-extracted)
      - Metrics (auto-extracted)
      - Diagnostic plots
      - Source file linking
    - **Version control your ML workflow** by committing different model
      versions
    - **Track improvements** across model versions using commit history
    - **Access historical versions** of your models and artifacts

    **Key Takeaways**:

    - Kirin lets you commit model objects directly - no manual serialization
      needed!
    - Hyperparameters and metrics are automatically extracted from scikit-learn
      models
    - Source file linking connects models to the scripts that created them
    - Using the same variable names across commits lets Kirin handle versioning
      automatically
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
