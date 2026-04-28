# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "kirin",
#     "scikit-learn",
#     "matplotlib",
#     "seaborn",
#     "numpy",
#     "joblib",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../../", editable = true }
# ///

"""ML workflow script for Kirin tutorial.

This script trains models, creates plots, and commits them to a Kirin dataset.
It accepts a directory path where the dataset should be stored.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split

from kirin import Dataset

# Set style for plots
sns.set_style("whitegrid")
plt.rcParams["figure.figsize"] = (10, 6)


def train_initial_model(dataset_dir: Path):
    """Train initial model and commit to dataset."""
    # Load data
    iris_data = load_iris()
    X = iris_data.data
    y = iris_data.target
    feature_names = iris_data.feature_names
    target_names = iris_data.target_names

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Train initial model
    initial_model = RandomForestClassifier(
        n_estimators=3,
        max_depth=1,
        random_state=1,
    )
    initial_model.fit(X_train, y_train)

    # Evaluate
    y_pred = initial_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    # Create plots
    # Plot 1: Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    confusion_matrix_fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=target_names,
        yticklabels=target_names,
        ax=ax,
    )
    ax.set_title("Confusion Matrix - Initial Model")
    ax.set_ylabel("True Label")
    ax.set_xlabel("Predicted Label")

    # Plot 2: Feature Importance
    feature_importance = initial_model.feature_importances_
    feature_importance_fig, ax = plt.subplots(figsize=(10, 6))
    indices = np.argsort(feature_importance)[::-1]
    ax.bar(range(len(feature_importance)), feature_importance[indices])
    ax.set_xticks(range(len(feature_importance)))
    ax.set_xticklabels([feature_names[i] for i in indices], rotation=45, ha="right")
    ax.set_title("Feature Importance - Initial Model")
    ax.set_xlabel("Features")
    ax.set_ylabel("Importance")

    # Classification Report
    report = classification_report(y_test, y_pred, target_names=target_names)
    reports_dir = dataset_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_path = reports_dir / "classification_report.txt"
    report_path.write_text(report)

    # Commit to dataset
    dataset = Dataset(root_dir=dataset_dir, name="iris_classifier")
    commit_hash = dataset.commit(
        message="Initial model v1.0 - Simple Random Forest baseline (3 trees, depth 1)",
        add_files=[
            initial_model,  # Model object - auto-serialized
            confusion_matrix_fig,  # Plot object - auto-converted to SVG
            feature_importance_fig,  # Plot object - auto-converted to SVG
            str(report_path),  # Text file
        ],
        metadata={
            "accuracy": accuracy,
            "model_version": "1.0.0",
        },
    )

    plt.close(confusion_matrix_fig)
    plt.close(feature_importance_fig)

    print(f"✅ Initial model committed: {commit_hash[:8]}")
    print(f"   Accuracy: {accuracy:.4f}")
    return commit_hash, accuracy


def train_improved_model(dataset_dir: Path):
    """Train improved model and commit to dataset."""
    # Load data
    iris_data = load_iris()
    X = iris_data.data
    y = iris_data.target
    feature_names = iris_data.feature_names
    target_names = iris_data.target_names

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    # Train improved model
    improved_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        max_features="sqrt",
        random_state=42,
    )
    improved_model.fit(X_train, y_train)

    # Evaluate
    y_pred_improved = improved_model.predict(X_test)
    improved_accuracy = accuracy_score(y_test, y_pred_improved)

    # Create plots
    # Plot 1: Confusion Matrix
    cm_improved = confusion_matrix(y_test, y_pred_improved)
    confusion_matrix_fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(
        cm_improved,
        annot=True,
        fmt="d",
        cmap="Greens",
        xticklabels=target_names,
        yticklabels=target_names,
        ax=ax,
    )
    ax.set_title("Confusion Matrix - Improved Model")
    ax.set_ylabel("True Label")
    ax.set_xlabel("Predicted Label")

    # Plot 2: Feature Importance
    feature_importance_improved = improved_model.feature_importances_
    feature_importance_fig, ax = plt.subplots(figsize=(10, 6))
    indices_improved = np.argsort(feature_importance_improved)[::-1]
    ax.bar(
        range(len(feature_importance_improved)),
        feature_importance_improved[indices_improved],
    )
    ax.set_xticks(range(len(feature_importance_improved)))
    ax.set_xticklabels(
        [feature_names[i] for i in indices_improved], rotation=45, ha="right"
    )
    ax.set_title("Feature Importance - Improved Model")
    ax.set_xlabel("Features")
    ax.set_ylabel("Importance")

    # Classification Report
    report_improved = classification_report(
        y_test, y_pred_improved, target_names=target_names
    )
    reports_dir = dataset_dir / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_improved_path = reports_dir / "classification_report.txt"
    report_improved_path.write_text(report_improved)

    # Commit to dataset
    dataset = Dataset(root_dir=dataset_dir, name="iris_classifier")
    commit_hash = dataset.commit(
        message=(
            "Improved model v2.0 - Better hyperparameters (100 trees, unlimited depth)"
        ),
        add_files=[
            improved_model,  # Model object - auto-serialized
            confusion_matrix_fig,  # Plot object - auto-converted to SVG
            feature_importance_fig,  # Plot object - auto-converted to SVG
            str(report_improved_path),  # Text file
        ],
        metadata={
            "accuracy": improved_accuracy,
            "model_version": "2.0.0",
        },
    )

    plt.close(confusion_matrix_fig)
    plt.close(feature_importance_fig)

    print(f"✅ Improved model committed: {commit_hash[:8]}")
    print(f"   Accuracy: {improved_accuracy:.4f}")
    return commit_hash, improved_accuracy


def main():
    parser = argparse.ArgumentParser(description="ML workflow script for Kirin")
    parser.add_argument(
        "dataset_dir",
        type=Path,
        help="Directory where the dataset should be stored",
    )
    parser.add_argument(
        "--step",
        choices=["initial", "improved", "both"],
        default="both",
        help="Which step to run (default: both)",
    )
    args = parser.parse_args()

    dataset_dir = args.dataset_dir
    dataset_dir.mkdir(parents=True, exist_ok=True)

    if args.step in ("initial", "both"):
        train_initial_model(dataset_dir)

    if args.step in ("improved", "both"):
        train_improved_model(dataset_dir)

    # Print summary
    if args.step == "both":
        dataset = Dataset(root_dir=dataset_dir, name="iris_classifier")
        history = dataset.history()
        print(f"\n📊 Commit History ({len(history)} commits):")
        for i, commit in enumerate(history, 1):
            print(f"{i}. {commit.message}")
            if commit.metadata and "accuracy" in commit.metadata:
                print(f"   Accuracy: {commit.metadata['accuracy']:.4f}")


if __name__ == "__main__":
    main()
