# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "torch==2.11.0",
#     "kirin==0.0.15",
#     "loguru==0.7.3",
#     "numpy==2.4.4",
#     "matplotlib==3.10.9",
#     "pandas==3.0.2",
#     "marimo>=0.17.0",
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.23.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Kirin Model Versioning Demo

    This notebook showcases model artifact versioning with Kirin.

    We will:
    1. initialize a local model registry
    2. create and commit a baseline model snapshot
    3. overwrite the same model filenames with improved snapshots
    4. query, compare, and visualize model performance history
    5. load the latest production model via lazy file access
    """)
    return


@app.cell
def _():
    from pathlib import Path
    import tempfile

    import marimo as mo
    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import torch
    import torch.nn as nn

    from kirin import Dataset
    from kirin.commit_query import (
        commits_to_records,
        metadata_exists,
        metadata_greater_than,
        metadata_startswith,
    )

    return (
        Dataset,
        Path,
        commits_to_records,
        metadata_exists,
        metadata_greater_than,
        metadata_startswith,
        mo,
        nn,
        pd,
        plt,
        tempfile,
        torch,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1) Initialize model registry

    Create an ephemeral local root with `mkdtemp` and open a dataset.
    """)
    return


@app.cell
def _(Dataset, Path, tempfile):
    registry_root = Path(tempfile.mkdtemp(prefix="kirin_model_demo_"))
    model_registry = Dataset(root_dir=str(registry_root), name="sentiment_classifier")

    model_registry
    return model_registry, registry_root


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2) Define model architecture
    """)
    return


@app.cell
def _(nn, torch):
    class SimpleSentimentClassifier(nn.Module):
        def __init__(self, vocab_size: int = 1000, embedding_dim: int = 128, hidden_dim: int = 64):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, embedding_dim)
            self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
            self.classifier = nn.Linear(hidden_dim, 2)
            self.dropout = nn.Dropout(0.2)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            embedded = self.embedding(x)
            lstm_out, _ = self.lstm(embedded)
            last_output = lstm_out[:, -1, :]
            dropped = self.dropout(last_output)
            return self.classifier(dropped)

    return (SimpleSentimentClassifier,)


@app.cell
def _(SimpleSentimentClassifier):
    baseline_model = SimpleSentimentClassifier()
    parameter_count = sum(parameter.numel() for parameter in baseline_model.parameters())
    parameter_count
    return (baseline_model,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3) Create baseline model artifacts

    Use stable filenames so commit history, not filenames, encodes versions.
    """)
    return


@app.cell
def _(registry_root):
    model_dir = registry_root / "models"
    model_dir.mkdir(exist_ok=True)

    weights_path = model_dir / "model_weights.pt"
    config_path = model_dir / "config.json"
    training_info_path = model_dir / "training_info.json"
    return config_path, training_info_path, weights_path


@app.cell
def _(baseline_model, config_path, torch, training_info_path, weights_path):
    torch.save(baseline_model.state_dict(), weights_path)
    config_path.write_text(
        """{
      "model_type": "SimpleSentimentClassifier",
      "vocab_size": 1000,
      "embedding_dim": 128,
      "hidden_dim": 64,
      "num_classes": 2
    }"""
    )
    training_info_path.write_text(
        """{
      "dataset": "sentiment_analysis_v1",
      "train_samples": 10000,
      "val_samples": 2000,
      "test_samples": 2000,
      "batch_size": 32,
      "learning_rate": 0.001,
      "epochs": 10
    }"""
    )

    [str(path.name) for path in [weights_path, config_path, training_info_path]]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 4) Commit baseline snapshot

    Use `skip_if_no_changes=True` to make reruns idempotent.
    """)
    return


@app.cell
def _():
    baseline_metadata = {
        "framework": "pytorch",
        "model_type": "SimpleSentimentClassifier",
        "version": "1.0.0",
        "accuracy": 0.87,
        "f1_score": 0.85,
        "precision": 0.88,
        "recall": 0.82,
        "hyperparameters": {
            "vocab_size": 1000,
            "embedding_dim": 128,
            "hidden_dim": 64,
            "learning_rate": 0.001,
            "epochs": 10,
            "batch_size": 32,
        },
    }
    baseline_tags = ["baseline", "v1.0"]
    return baseline_metadata, baseline_tags


@app.cell
def _(
    baseline_metadata,
    baseline_tags,
    config_path,
    model_registry,
    training_info_path,
    weights_path,
):
    baseline_commit_hash = model_registry.commit(
        message="Initial baseline model - SimpleSentimentClassifier v1.0",
        add_files=[str(weights_path), str(config_path), str(training_info_path)],
        metadata=baseline_metadata,
        tags=baseline_tags,
        skip_if_no_changes=True,
    )

    baseline_commit_hash
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 5) Update artifacts for improved model

    Overwrite the same files with improved model content.
    """)
    return


@app.cell
def _(SimpleSentimentClassifier, torch):
    improved_model = SimpleSentimentClassifier()
    with torch.no_grad():
        for improved_parameter in improved_model.parameters():
            improved_parameter.add_(torch.randn_like(improved_parameter) * 0.01)
    return (improved_model,)


@app.cell
def _(config_path, improved_model, torch, training_info_path, weights_path):
    torch.save(improved_model.state_dict(), weights_path)
    config_path.write_text(
        """{
      "model_type": "SimpleSentimentClassifier",
      "vocab_size": 1000,
      "embedding_dim": 128,
      "hidden_dim": 64,
      "num_classes": 2,
      "improvements": ["better_regularization", "learning_rate_schedule"]
    }"""
    )
    training_info_path.write_text(
        """{
      "dataset": "sentiment_analysis_v2",
      "train_samples": 15000,
      "val_samples": 3000,
      "test_samples": 3000,
      "batch_size": 32,
      "learning_rate": 0.0005,
      "epochs": 15
    }"""
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 6) Commit improved snapshot
    """)
    return


@app.cell
def _():
    improved_metadata = {
        "framework": "pytorch",
        "model_type": "SimpleSentimentClassifier",
        "version": "2.0.0",
        "accuracy": 0.92,
        "f1_score": 0.90,
        "precision": 0.91,
        "recall": 0.89,
        "training_time_seconds": 1800,
        "improvements": [
            "Better regularization",
            "Learning rate scheduling",
            "More training data",
        ],
    }
    improved_tags = ["improved", "v2.0", "production"]
    return improved_metadata, improved_tags


@app.cell
def _(
    config_path,
    improved_metadata,
    improved_tags,
    model_registry,
    training_info_path,
    weights_path,
):
    improved_commit_hash = model_registry.commit(
        message="Improved model v2.0 - Better regularization and more data",
        add_files=[str(weights_path), str(config_path), str(training_info_path)],
        metadata=improved_metadata,
        tags=improved_tags,
        skip_if_no_changes=True,
    )

    improved_commit_hash
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 7) Commit domain-specialized snapshot

    Again, overwrite the same artifact filenames with specialized weights/config.
    """)
    return


@app.cell
def _(
    SimpleSentimentClassifier,
    config_path,
    torch,
    training_info_path,
    weights_path,
):
    domain_model = SimpleSentimentClassifier()
    with torch.no_grad():
        for domain_parameter in domain_model.parameters():
            domain_parameter.add_(torch.randn_like(domain_parameter) * 0.02)

    torch.save(domain_model.state_dict(), weights_path)
    config_path.write_text(
        """{
      "model_type": "SimpleSentimentClassifier",
      "vocab_size": 1000,
      "embedding_dim": 128,
      "hidden_dim": 64,
      "num_classes": 2,
      "domain": "medical",
      "specialization": "medical_sentiment_analysis"
    }"""
    )
    training_info_path.write_text(
        """{
      "dataset": "medical_sentiment_v1",
      "train_samples": 5000,
      "val_samples": 1000,
      "test_samples": 1000,
      "batch_size": 16,
      "learning_rate": 0.0003,
      "epochs": 20,
      "domain_specific": true
    }"""
    )
    return


@app.cell
def _(config_path, model_registry, training_info_path, weights_path):
    domain_metadata = {
        "framework": "pytorch",
        "model_type": "SimpleSentimentClassifier",
        "version": "2.1.0",
        "domain": "medical",
        "accuracy": 0.89,
        "f1_score": 0.87,
        "domain_accuracy": 0.94,
        "domain_f1": 0.92,
        "specialization": "Medical sentiment analysis",
    }
    domain_tags = ["domain-specific", "medical", "v2.1", "specialized"]

    domain_commit_hash = model_registry.commit(
        message="Domain-specific model for medical sentiment analysis",
        add_files=[str(weights_path), str(config_path), str(training_info_path)],
        metadata=domain_metadata,
        tags=domain_tags,
        skip_if_no_changes=True,
    )

    domain_commit_hash
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 8) Query models by tags and metadata
    """)
    return


@app.cell
def _(
    metadata_exists,
    metadata_greater_than,
    metadata_startswith,
    mo,
    model_registry,
):
    production_models = model_registry.find_commits(tags=["production"])
    high_accuracy_models = model_registry.find_commits(
        metadata_filter=metadata_greater_than("accuracy", 0.9)
    )
    domain_models = model_registry.find_commits(
        metadata_filter=metadata_exists("domain")
    )
    v2_models = model_registry.find_commits(
        metadata_filter=metadata_startswith("version", "2.")
    )

    mo.md(
        f"""
    ### Discovery summary

    - Production models: **{len(production_models)}**
    - High accuracy models (>0.9): **{len(high_accuracy_models)}**
    - Domain-specific models: **{len(domain_models)}**
    - Version 2.x models: **{len(v2_models)}**
    """
    )
    return (production_models,)


@app.cell
def _(production_models):
    production_models[0]
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 9) Compare recent commits
    """)
    return


@app.cell
def _(model_registry):
    recent_commits = model_registry.history(limit=2)
    comparison = None
    if len(recent_commits) == 2:
        comparison = model_registry.compare_commits(recent_commits[0].hash, recent_commits[1].hash)

    comparison
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 10) Visualize performance over commits
    """)
    return


@app.cell
def _(commits_to_records, model_registry, pd):
    history = model_registry.history()
    metrics_rows = commits_to_records(
        history,
        metadata_keys=["version", "accuracy", "f1_score"],
    )

    metrics_dataframe = pd.DataFrame(metrics_rows)
    metrics_dataframe
    return (metrics_dataframe,)


@app.cell
def _(metrics_dataframe, mo, plt):
    if not metrics_dataframe.empty:
        fig, (axis1, axis2) = plt.subplots(1, 2, figsize=(12, 4))
        commit_positions = list(range(len(metrics_dataframe)))

        axis1.plot(commit_positions, metrics_dataframe["accuracy"], "o-", linewidth=2)
        axis1.set_title("Accuracy over commits")
        axis1.set_xlabel("Commit order")
        axis1.set_ylabel("Accuracy")
        axis1.set_xticks(commit_positions)
        axis1.grid(True, alpha=0.3)

        axis2.plot(
            commit_positions,
            metrics_dataframe["f1_score"],
            "s-",
            color="orange",
            linewidth=2,
        )
        axis2.set_title("F1 score over commits")
        axis2.set_xlabel("Commit order")
        axis2.set_ylabel("F1 score")
        axis2.set_xticks(commit_positions)
        axis2.grid(True, alpha=0.3)

        plt.tight_layout()
        plot_output = fig
    else:
        plot_output = mo.md("No metrics available yet.")

    plot_output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 11) Load latest production model snapshot

    Demonstrate checkout + lazy local file access.
    """)
    return


@app.cell
def _(Path, mo, model_registry, production_models):
    latest_production = production_models[0] if production_models else None

    if latest_production is not None:
        model_registry.checkout(latest_production.hash)
        files = model_registry.list_files()
        with model_registry.local_files() as local_files:
            file_sizes = {
                file_name: Path(local_files[file_name]).stat().st_size
                for file_name in local_files
            }
        load_output = mo.md(
            f"""
    ### Loaded production commit

    - Commit: `{latest_production.short_hash}`
    - Message: {latest_production.message}
    - Files: {', '.join(files)}
    - File sizes: {file_sizes}
    """
        )
    else:
        load_output = mo.md("No production model found.")

    load_output
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 12) Summary

    Kirin model versioning patterns demonstrated here:
    - stable artifact filenames across commits
    - metadata-rich commits for search/discovery
    - tags for deployment/status grouping
    - commit comparison and performance trend tracking
    - lazy loading of files from checked-out commits
    """)
    return


if __name__ == "__main__":
    app.run()
