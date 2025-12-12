# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "torch",
#     "kirin",
#     "loguru",
#     "numpy",
#     "matplotlib",
#     "pandas",
#     "marimo>=0.17.0",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../../", editable = true }
# ///

import marimo

__generated_with = "0.17.8"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Track Model Training Data

    This guide shows you how to version control your machine learning models
    and training data using Kirin. You'll learn to create a model registry,
    commit models with metadata, query models by performance metrics, and
    compare different versions.
    """)
    return


@app.cell
def _():
    import tempfile
    from pathlib import Path

    import matplotlib.pyplot as plt
    import numpy as np
    import pandas as pd
    import torch
    from loguru import logger

    from kirin import Dataset

    temp_dir = tempfile.mkdtemp(prefix="kirin_model_demo_")
    model_registry = Dataset(root_dir=temp_dir, name="sentiment_classifier")

    print(f"✅ Model registry created at: {temp_dir}")
    return Dataset, Path, logger, model_registry, np, pd, plt, temp_dir, torch


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Create a Model Registry

    Start by creating a Dataset to serve as your model registry. In production,
    use cloud storage like `s3://my-bucket/models` instead of a temporary
    directory.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Create a Model for Demonstration

    We'll create a simple sentiment classifier model to demonstrate the
    workflow.
    """)
    return


@app.cell
def _(torch):
    class SimpleSentimentClassifier(torch.nn.Module):
        def __init__(self, vocab_size=1000, embedding_dim=128, hidden_dim=64):
            super().__init__()
            self.embedding = torch.nn.Embedding(vocab_size, embedding_dim)
            self.lstm = torch.nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
            self.classifier = torch.nn.Linear(hidden_dim, 2)
            self.dropout = torch.nn.Dropout(0.2)

        def forward(self, x):
            embedded = self.embedding(x)
            lstm_out, _ = self.lstm(embedded)
            last_output = lstm_out[:, -1, :]
            dropped = self.dropout(last_output)
            return self.classifier(dropped)

    model = SimpleSentimentClassifier()
    param_count = sum(p.numel() for p in model.parameters())
    print(f"✅ Created model with {param_count:,} parameters")
    return SimpleSentimentClassifier, model


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Save Model Files

    Save your model weights, configuration, and training information as
    separate files that will be versioned together.
    """)
    return


@app.cell
def _(Path, model, temp_dir, torch):
    model_dir = Path(temp_dir) / "models"
    model_dir.mkdir(exist_ok=True)

    model_path = model_dir / "model_weights.pt"
    torch.save(model.state_dict(), model_path)

    config_path = model_dir / "config.json"
    config_path.write_text("""{
    "model_type": "SimpleSentimentClassifier",
    "vocab_size": 1000,
    "embedding_dim": 128,
    "hidden_dim": 64,
    "num_classes": 2
    }""")

    training_info_path = model_dir / "training_info.json"
    training_info_path.write_text("""{
    "dataset": "sentiment_analysis_v1",
    "train_samples": 10000,
    "val_samples": 2000,
    "test_samples": 2000,
    "batch_size": 32,
    "learning_rate": 0.001,
    "epochs": 10
    }""")

    print("✅ Created model files:")
    print(f"   - {model_path.name}")
    print(f"   - {config_path.name}")
    print(f"   - {training_info_path.name}")
    return config_path, model_path, training_info_path


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Commit Your First Model

    Commit your model with comprehensive metadata including performance
    metrics, hyperparameters, and tags for easy discovery.
    """)
    return


@app.cell
def _(config_path, model_path, model_registry, training_info_path):
    metadata = {
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
        "training_data": {
            "dataset": "sentiment_analysis_v1",
            "train_samples": 10000,
            "val_samples": 2000,
            "test_samples": 2000,
        },
        "training_time_seconds": 1200,
        "model_size_mb": 0.5,
    }

    tags = ["baseline", "v1.0"]

    commit_hash = model_registry.commit(
        message="Initial baseline model - SimpleSentimentClassifier v1.0",
        add_files=[str(model_path), str(config_path), str(training_info_path)],
        metadata=metadata,
        tags=tags,
    )

    print("✅ Committed initial model version")
    print(f"   Commit: {commit_hash[:8]}")
    print(f"   Tags: {tags}")
    print(f"   Accuracy: {metadata['accuracy']}")
    return commit_hash, metadata, tags


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Create an Improved Model Version

    Train or create an improved version of your model with better
    performance.
    """)
    return


@app.cell
def _(Path, SimpleSentimentClassifier, temp_dir, torch):
    improved_model = SimpleSentimentClassifier()
    with torch.no_grad():
        for param in improved_model.parameters():
            param.add_(torch.randn_like(param) * 0.01)

    improved_model_path = Path(temp_dir) / "models" / "model_weights.pt"
    torch.save(improved_model.state_dict(), improved_model_path)

    improved_config_path = Path(temp_dir) / "models" / "config.json"
    improved_config_path.write_text("""{
    "model_type": "SimpleSentimentClassifier",
    "vocab_size": 1000,
    "embedding_dim": 128,
    "hidden_dim": 64,
    "num_classes": 2,
    "improvements": ["better_regularization", "learning_rate_schedule"]
    }""")

    print(
        "✅ Created improved model files "
        "(same filenames - versioning handled by commits)"
    )
    return improved_config_path, improved_model_path


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Commit the Improved Model

    Commit the improved model with updated metadata reflecting the better
    performance and new hyperparameters.
    """)
    return


@app.cell
def _(improved_config_path, improved_model_path, model_registry):
    improved_metadata = {
        "framework": "pytorch",
        "model_type": "SimpleSentimentClassifier",
        "version": "2.0.0",
        "accuracy": 0.92,
        "f1_score": 0.90,
        "precision": 0.91,
        "recall": 0.89,
        "hyperparameters": {
            "vocab_size": 1000,
            "embedding_dim": 128,
            "hidden_dim": 64,
            "learning_rate": 0.0005,
            "epochs": 15,
            "batch_size": 32,
            "weight_decay": 0.01,
        },
        "training_data": {
            "dataset": "sentiment_analysis_v2",
            "train_samples": 15000,
            "val_samples": 3000,
            "test_samples": 3000,
        },
        "training_time_seconds": 1800,
        "model_size_mb": 0.5,
        "improvements": [
            "Better regularization",
            "Learning rate scheduling",
            "More training data",
            "Longer training time",
        ],
    }

    improved_tags = ["improved", "v2.0", "production"]

    improved_commit_hash = model_registry.commit(
        message="Improved model v2.0 - Better regularization and more data",
        add_files=[str(improved_model_path), str(improved_config_path)],
        metadata=improved_metadata,
        tags=improved_tags,
    )

    print("✅ Committed improved model version")
    print(f"   Commit: {improved_commit_hash[:8]}")
    print(f"   Tags: {improved_tags}")
    print(f"   Accuracy: {improved_metadata['accuracy']} (↑ from 0.87)")
    return improved_commit_hash, improved_metadata, improved_tags


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Discover Models by Tags and Metadata

    Use `find_commits()` to discover models by tags, metadata filters, or
    custom filter functions.
    """)
    return


@app.cell
def _(model_registry):
    print("🔍 Model Discovery Examples")
    print("=" * 50)

    production_models = model_registry.find_commits(tags=["production"])
    print(f"\n📦 Production models: {len(production_models)}")
    for prod_commit in production_models:
        print(f"   {prod_commit.short_hash}: {prod_commit.message}")
        print(f"      Accuracy: {prod_commit.metadata.get('accuracy', 'N/A')}")

    high_accuracy_models = model_registry.find_commits(
        metadata_filter=lambda m: m.get("accuracy", 0) > 0.9
    )
    print(f"\n🎯 High accuracy models (>0.9): {len(high_accuracy_models)}")
    for acc_commit in high_accuracy_models:
        print(f"   {acc_commit.short_hash}: {acc_commit.message}")
        print(f"      Accuracy: {acc_commit.metadata.get('accuracy', 'N/A')}")

    return high_accuracy_models, production_models


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Compare Model Versions

    Use `compare_commits()` to see what changed between versions including
    metadata differences, tag changes, and file changes.
    """)
    return


@app.cell
def _(model_registry, production_models):
    if len(production_models) >= 2:
        print("🔄 Model Comparison")
        print("=" * 30)

        commit1 = production_models[0]
        commit2 = production_models[1]

        comparison = model_registry.compare_commits(commit1.hash, commit2.hash)

        print("Comparing:")
        print(f"  {comparison['commit1']['hash']}: {comparison['commit1']['message']}")
        print(f"  {comparison['commit2']['hash']}: {comparison['commit2']['message']}")

        print("\n📊 Metadata Changes:")
        metadata_diff = comparison["metadata_diff"]

        if metadata_diff["changed"]:
            print("  🔄 Changed:")
            for diff_key, change in metadata_diff["changed"].items():
                print(f"     {diff_key}: {change['old']} → {change['new']}")

        print("\n🏷️  Tag Changes:")
        tags_diff = comparison["tags_diff"]
        if tags_diff["added"]:
            print(f"  ➕ Added tags: {tags_diff['added']}")
    else:
        print("Not enough models to compare")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Visualize Model Performance Over Time

    Track how your models improve over time by plotting metrics from commit
    history.
    """)
    return


@app.cell
def _(model_registry, pd, plt):
    print("📈 Model Performance Over Time")
    print("=" * 40)

    commits = model_registry.history()
    metrics_data = []

    for hist_commit in commits:
        if hist_commit.metadata:
            metrics_data.append(
                {
                    "commit": hist_commit.short_hash,
                    "message": hist_commit.message[:30] + "..."
                    if len(hist_commit.message) > 30
                    else hist_commit.message,
                    "accuracy": hist_commit.metadata.get("accuracy", 0),
                    "f1_score": hist_commit.metadata.get("f1_score", 0),
                    "version": hist_commit.metadata.get("version", "unknown"),
                }
            )

    if metrics_data:
        df = pd.DataFrame(metrics_data)

        print("\nModel Performance Summary:")
        print(df[["commit", "version", "accuracy", "f1_score"]].to_string(index=False))

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

        ax1.plot(range(len(df)), df["accuracy"], "o-", linewidth=2, markersize=8)
        ax1.set_title("Model Accuracy Over Time")
        ax1.set_xlabel("Commit Order")
        ax1.set_ylabel("Accuracy")
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim(0.8, 1.0)

        ax2.plot(
            range(len(df)),
            df["f1_score"],
            "s-",
            color="orange",
            linewidth=2,
            markersize=8,
        )
        ax2.set_title("Model F1 Score Over Time")
        ax2.set_xlabel("Commit Order")
        ax2.set_ylabel("F1 Score")
        ax2.grid(True, alpha=0.3)
        ax2.set_ylim(0.8, 1.0)

        plt.tight_layout()
        plt.show()
    else:
        print("No metrics data found")
        df = None
        fig = None
        ax1 = None
        ax2 = None

    return ax1, ax2, commits, df, fig, metrics_data


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Load Specific Model Versions

    Checkout a specific commit to access files from that version. Files are
    lazily downloaded when accessed.
    """)
    return


@app.cell
def _(Path, model_registry):
    print("🚀 Loading Specific Model Versions")
    print("=" * 40)

    prod_models = model_registry.find_commits(tags=["production"])

    if prod_models:
        latest_model = prod_models[0]
        print(f"Loading latest production model: {latest_model.short_hash}")

        model_registry.checkout(latest_model.hash)

        print("\n📁 Files in this commit:")
        for filename in model_registry.list_files():
            file_obj = model_registry.get_file(filename)
            print(f"   {filename}: {file_obj.size} bytes")

        print("\n💾 Accessing files (lazy loading):")
        with model_registry.local_files() as local_files:
            for filename in local_files.keys():
                local_path = local_files[filename]
                print(f"   {filename} → {local_path}")
                print(f"      Exists: {Path(local_path).exists()}")

        print("\n📋 Model metadata:")
        for key, value in latest_model.metadata.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
    else:
        print("No production models found")
        latest_model = None
        local_files = None
        local_path = None

    return latest_model, local_files, local_path


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Summary

    Your model registry now tracks:

    - ✅ Content-addressed storage (automatic deduplication)
    - ✅ Lazy loading (files only downloaded when needed)
    - ✅ Rich metadata tracking (hyperparameters, metrics, etc.)
    - ✅ Flexible tagging system (staging, versions, domains)
    - ✅ Powerful querying (by metadata, tags, or custom filters)
    - ✅ Model comparison and diffing
    - ✅ Linear history (simple, no branching complexity)
    - ✅ Cloud storage support (works with S3, GCS, Azure)

    **Use Cases:**
    - Model experiment tracking
    - A/B testing different model versions
    - Model deployment staging (dev → staging → production)
    - Reproducible ML workflows
    """)
    return


@app.cell
def _(model_registry):
    all_commits = model_registry.history()

    print("🎯 Summary")
    print("=" * 50)
    print("\n📊 Registry Statistics:")
    print(f"   Total commits: {len(all_commits)}")
    print(f"   Total files: {sum(len(c.files) for c in all_commits)}")

    tag_counts = {}
    for summary_commit in all_commits:
        for tag in summary_commit.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    print("\n🏷️  Tag Distribution:")
    for tag, count in sorted(tag_counts.items()):
        print(f"   {tag}: {count}")

    return all_commits, tag_counts


if __name__ == "__main__":
    app.run()
