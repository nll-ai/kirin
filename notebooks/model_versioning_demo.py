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
#     "pyzmq",
# ]
#
# [tool.uv.sources]
# kirin = { path = "../", editable = true }
# ///

import marimo

__generated_with = "0.17.8"
app = marimo.App(width="medium")


@app.cell
def _():
    """Setup imports and create model registry."""
    import tempfile
    from pathlib import Path
    import torch
    import torch.nn as nn
    import numpy as np
    import matplotlib.pyplot as plt
    import pandas as pd
    from loguru import logger

    from kirin import Dataset

    # Create a temporary directory for our model registry
    temp_dir = tempfile.mkdtemp(prefix="kirin_model_demo_")
    model_registry = Dataset(root_dir=temp_dir, name="sentiment_classifier")

    print(f"Model registry created at: {temp_dir}")
    print(f"Registry: {model_registry}")
    return Path, model_registry, nn, pd, plt, temp_dir, torch


@app.cell
def _(nn):
    """Create a simple PyTorch model for demonstration."""
    class SimpleSentimentClassifier(nn.Module):
        def __init__(self, vocab_size=1000, embedding_dim=128, hidden_dim=64):
            super().__init__()
            self.embedding = nn.Embedding(vocab_size, embedding_dim)
            self.lstm = nn.LSTM(embedding_dim, hidden_dim, batch_first=True)
            self.classifier = nn.Linear(hidden_dim, 2)  # binary classification
            self.dropout = nn.Dropout(0.2)

        def forward(self, x):
            embedded = self.embedding(x)
            lstm_out, _ = self.lstm(embedded)
            # Use the last output
            last_output = lstm_out[:, -1, :]
            dropped = self.dropout(last_output)
            return self.classifier(dropped)

    # Create model instance
    model = SimpleSentimentClassifier()

    print("Created PyTorch model:")
    print(f"  - Vocab size: 1000")
    print(f"  - Embedding dim: 128")
    print(f"  - Hidden dim: 64")
    print(f"  - Parameters: {sum(p.numel() for p in model.parameters()):,}")
    return SimpleSentimentClassifier, model


@app.cell
def _(Path, model, temp_dir, torch):
    """Save initial model version with metadata."""
    # Create model directory
    model_dir = Path(temp_dir) / "models"
    model_dir.mkdir(exist_ok=True)

    # Save model weights
    model_path = model_dir / "model_weights.pt"
    torch.save(model.state_dict(), model_path)

    # Create config file
    config_path = model_dir / "config.json"
    config_path.write_text('''{
    "model_type": "SimpleSentimentClassifier",
    "vocab_size": 1000,
    "embedding_dim": 128,
    "hidden_dim": 64,
    "num_classes": 2
    }''')

    # Create training info
    training_info_path = model_dir / "training_info.json"
    training_info_path.write_text('''{
    "dataset": "sentiment_analysis_v1",
    "train_samples": 10000,
    "val_samples": 2000,
    "test_samples": 2000,
    "batch_size": 32,
    "learning_rate": 0.001,
    "epochs": 10
    }''')

    print("Created model files:")
    print(f"  - {model_path.name} ({model_path.stat().st_size} bytes)")
    print(f"  - {config_path.name} ({config_path.stat().st_size} bytes)")
    print(f"  - {training_info_path.name} ({training_info_path.stat().st_size} bytes)")
    return config_path, model_path, training_info_path


@app.cell
def _(config_path, model_path, model_registry, training_info_path):
    """Commit initial model version with comprehensive metadata."""
    # Define metadata for the initial model
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

    # Commit the initial model
    commit_hash = model_registry.commit(
        message="Initial baseline model - SimpleSentimentClassifier v1.0",
        add_files=[str(model_path), str(config_path), str(training_info_path)],
        metadata=metadata,
        tags=tags,
    )

    print(f"✅ Committed initial model version")
    print(f"   Commit hash: {commit_hash[:8]}")
    print(f"   Tags: {tags}")
    print(f"   Accuracy: {metadata['accuracy']}")
    return


@app.cell
def _(Path, SimpleSentimentClassifier, temp_dir, torch):
    """Simulate training an improved model version."""
    # Simulate training by modifying the model slightly
    # In real training, this would be done through actual training loops

    # Create a "trained" version with slightly different weights
    improved_model = SimpleSentimentClassifier()

    # Simulate training by adding small random changes to weights
    with torch.no_grad():
        for improved_param in improved_model.parameters():
            improved_param.add_(torch.randn_like(improved_param) * 0.01)

    # Save improved model
    improved_model_path = Path(temp_dir) / "models" / "model_weights_v2.pt"
    torch.save(improved_model.state_dict(), improved_model_path)

    # Create updated config
    improved_config_path = Path(temp_dir) / "models" / "config_v2.json"
    improved_config_path.write_text('''{
    "model_type": "SimpleSentimentClassifier",
    "vocab_size": 1000,
    "embedding_dim": 128,
    "hidden_dim": 64,
    "num_classes": 2,
    "improvements": ["better_regularization", "learning_rate_schedule"]
    }''')

    print("Created improved model files:")
    print(f"  - {improved_model_path.name}")
    print(f"  - {improved_config_path.name}")
    return improved_config_path, improved_model_path


@app.cell
def _(improved_config_path, improved_model_path, model_registry):
    """Commit improved model version with updated metadata."""
    # Define metadata for the improved model
    improved_metadata = {
        "framework": "pytorch",
        "model_type": "SimpleSentimentClassifier",
        "version": "2.0.0",
        "accuracy": 0.92,  # Improved accuracy
        "f1_score": 0.90,  # Improved F1
        "precision": 0.91,
        "recall": 0.89,
        "hyperparameters": {
            "vocab_size": 1000,
            "embedding_dim": 128,
            "hidden_dim": 64,
            "learning_rate": 0.0005,  # Lower learning rate
            "epochs": 15,  # More epochs
            "batch_size": 32,
            "weight_decay": 0.01,  # Added regularization
        },
        "training_data": {
            "dataset": "sentiment_analysis_v2",  # Updated dataset
            "train_samples": 15000,  # More training data
            "val_samples": 3000,
            "test_samples": 3000,
        },
        "training_time_seconds": 1800,  # Longer training
        "model_size_mb": 0.5,
        "improvements": [
            "Better regularization",
            "Learning rate scheduling",
            "More training data",
            "Longer training time"
        ],
    }

    improved_tags = ["improved", "v2.0", "production"]

    # Commit the improved model
    improved_commit_hash = model_registry.commit(
        message="Improved model v2.0 - Better regularization and more data",
        add_files=[str(improved_model_path), str(improved_config_path)],
        metadata=improved_metadata,
        tags=improved_tags,
    )

    print(f"✅ Committed improved model version")
    print(f"   Commit hash: {improved_commit_hash[:8]}")
    print(f"   Tags: {improved_tags}")
    print(f"   Accuracy: {improved_metadata['accuracy']} (↑ from 0.87)")
    return


@app.cell
def _(Path, SimpleSentimentClassifier, temp_dir, torch):
    """Create a specialized model for a specific domain."""
    # Create a domain-specific model (e.g., for medical sentiment)
    domain_model = SimpleSentimentClassifier()

    # Simulate domain-specific training
    with torch.no_grad():
        for domain_param in domain_model.parameters():
            domain_param.add_(torch.randn_like(domain_param) * 0.02)  # Larger changes for domain adaptation

    # Save domain-specific model
    domain_model_path = Path(temp_dir) / "models" / "model_medical.pt"
    torch.save(domain_model.state_dict(), domain_model_path)

    # Create domain-specific config
    domain_config_path = Path(temp_dir) / "models" / "config_medical.json"
    domain_config_path.write_text('''{
    "model_type": "SimpleSentimentClassifier",
    "vocab_size": 1000,
    "embedding_dim": 128,
    "hidden_dim": 64,
    "num_classes": 2,
    "domain": "medical",
    "specialization": "medical_sentiment_analysis"
    }''')

    print("Created domain-specific model files:")
    print(f"  - {domain_model_path.name}")
    print(f"  - {domain_config_path.name}")
    return domain_config_path, domain_model_path


@app.cell
def _(domain_config_path, domain_model_path, model_registry):
    """Commit domain-specific model with specialized metadata."""
    # Define metadata for the domain-specific model
    domain_metadata = {
        "framework": "pytorch",
        "model_type": "SimpleSentimentClassifier",
        "version": "2.1.0",
        "domain": "medical",
        "accuracy": 0.89,  # Slightly lower on general data
        "f1_score": 0.87,
        "precision": 0.90,
        "recall": 0.84,
        "domain_accuracy": 0.94,  # Higher on medical data
        "domain_f1": 0.92,
        "hyperparameters": {
            "vocab_size": 1000,
            "embedding_dim": 128,
            "hidden_dim": 64,
            "learning_rate": 0.0003,
            "epochs": 20,
            "batch_size": 16,  # Smaller batch for domain adaptation
            "domain_adaptation": True,
        },
        "training_data": {
            "dataset": "medical_sentiment_v1",
            "train_samples": 5000,  # Smaller medical dataset
            "val_samples": 1000,
            "test_samples": 1000,
            "domain_specific": True,
        },
        "training_time_seconds": 2400,
        "model_size_mb": 0.5,
        "specialization": "Medical sentiment analysis",
        "use_cases": ["patient_feedback", "medical_reviews", "clinical_notes"],
    }

    domain_tags = ["domain-specific", "medical", "v2.1", "specialized"]

    # Commit the domain-specific model
    domain_commit_hash = model_registry.commit(
        message="Domain-specific model for medical sentiment analysis",
        add_files=[str(domain_model_path), str(domain_config_path)],
        metadata=domain_metadata,
        tags=domain_tags,
    )

    print(f"✅ Committed domain-specific model")
    print(f"   Commit hash: {domain_commit_hash[:8]}")
    print(f"   Tags: {domain_tags}")
    print(f"   General accuracy: {domain_metadata['accuracy']}")
    print(f"   Medical accuracy: {domain_metadata['domain_accuracy']}")
    return


@app.cell
def _(model_registry):
    """Query and discover models using metadata and tags."""
    print("🔍 Model Discovery and Querying")
    print("=" * 50)

    # Find all production models
    production_models = model_registry.find_commits(tags=["production"])
    print(f"\n📦 Production models: {len(production_models)}")
    for prod_commit in production_models:
        print(f"   {prod_commit.short_hash}: {prod_commit.message}")
        print(f"      Tags: {prod_commit.tags}")
        print(f"      Accuracy: {prod_commit.metadata.get('accuracy', 'N/A')}")

    # Find high-accuracy models (>0.9)
    high_accuracy_models = model_registry.find_commits(
        metadata_filter=lambda m: m.get("accuracy", 0) > 0.9
    )
    print(f"\n🎯 High accuracy models (>0.9): {len(high_accuracy_models)}")
    for high_acc_commit in high_accuracy_models:
        print(f"   {high_acc_commit.short_hash}: {high_acc_commit.message}")
        print(f"      Accuracy: {high_acc_commit.metadata.get('accuracy', 'N/A')}")

    # Find domain-specific models
    domain_models = model_registry.find_commits(
        metadata_filter=lambda m: m.get("domain") is not None
    )
    print(f"\n🏥 Domain-specific models: {len(domain_models)}")
    for domain_commit in domain_models:
        print(f"   {domain_commit.short_hash}: {domain_commit.message}")
        print(f"      Domain: {domain_commit.metadata.get('domain', 'N/A')}")
        print(f"      Specialization: {domain_commit.metadata.get('specialization', 'N/A')}")

    # Find models by version
    v2_models = model_registry.find_commits(
        metadata_filter=lambda m: m.get("version", "").startswith("2.")
    )
    print(f"\n🔢 Version 2.x models: {len(v2_models)}")
    for v2_commit in v2_models:
        print(f"   {v2_commit.short_hash}: {v2_commit.message}")
        print(f"      Version: {v2_commit.metadata.get('version', 'N/A')}")
    return high_accuracy_models, production_models


@app.cell
def _(model_registry, production_models):
    """Compare different model versions."""
    if len(production_models) >= 2:
        print("🔄 Model Comparison")
        print("=" * 30)

        # Compare the two production models
        commit1 = production_models[0]  # Most recent
        commit2 = production_models[1]  # Previous

        comparison = model_registry.compare_commits(commit1.hash, commit2.hash)

        print(f"Comparing:")
        print(f"  {comparison['commit1']['hash']}: {comparison['commit1']['message']}")
        print(f"  {comparison['commit2']['hash']}: {comparison['commit2']['message']}")

        print(f"\n📊 Metadata Changes:")
        metadata_diff = comparison['metadata_diff']

        if metadata_diff['added']:
            print(f"  ➕ Added: {metadata_diff['added']}")
        if metadata_diff['removed']:
            print(f"  ➖ Removed: {metadata_diff['removed']}")
        if metadata_diff['changed']:
            print(f"  🔄 Changed:")
            for changed_key, change in metadata_diff['changed'].items():
                print(f"     {changed_key}: {change['old']} → {change['new']}")

        print(f"\n🏷️  Tag Changes:")
        tags_diff = comparison['tags_diff']
        if tags_diff['added']:
            print(f"  ➕ Added tags: {tags_diff['added']}")
        if tags_diff['removed']:
            print(f"  ➖ Removed tags: {tags_diff['removed']}")
    else:
        print("Not enough production models to compare")
    return


@app.cell
def _(high_accuracy_models, model_registry, pd, plt):
    """Visualize model performance metrics."""
    if high_accuracy_models:
        print("📈 Model Performance Visualization")
        print("=" * 40)

        # Extract metrics for visualization
        commits = model_registry.history()
        metrics_data = []

        for metrics_commit in commits:
            if metrics_commit.metadata:
                metrics_data.append({
                    'commit': metrics_commit.short_hash,
                    'message': metrics_commit.message[:30] + "..." if len(metrics_commit.message) > 30 else metrics_commit.message,
                    'accuracy': metrics_commit.metadata.get('accuracy', 0),
                    'f1_score': metrics_commit.metadata.get('f1_score', 0),
                    'version': metrics_commit.metadata.get('version', 'unknown'),
                    'tags': ', '.join(metrics_commit.tags) if metrics_commit.tags else 'none',
                })

        if metrics_data:
            # Create DataFrame for easier handling
            df = pd.DataFrame(metrics_data)

            print("\nModel Performance Summary:")
            print(df[['commit', 'version', 'accuracy', 'f1_score', 'tags']].to_string(index=False))

            # Create a simple visualization
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

            # Accuracy over time
            ax1.plot(range(len(df)), df['accuracy'], 'o-', linewidth=2, markersize=8)
            ax1.set_title('Model Accuracy Over Time')
            ax1.set_xlabel('Commit Order')
            ax1.set_ylabel('Accuracy')
            ax1.grid(True, alpha=0.3)
            ax1.set_ylim(0.8, 1.0)

            # F1 Score over time
            ax2.plot(range(len(df)), df['f1_score'], 's-', color='orange', linewidth=2, markersize=8)
            ax2.set_title('Model F1 Score Over Time')
            ax2.set_xlabel('Commit Order')
            ax2.set_ylabel('F1 Score')
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0.8, 1.0)

            plt.tight_layout()
            plt.show()

        # Return variables for reactive dependencies
        ax1, ax2, commits, df, fig, metrics_data
    else:
        print("No high-accuracy models found for visualization")
        # Return None values for reactive dependencies
        ax1, ax2, commits, df, fig, metrics_data = None, None, None, None, None, None
    return


@app.cell
def _(Path, model_registry):
    """Demonstrate model loading and usage patterns."""
    print("🚀 Model Loading and Usage Patterns")
    print("=" * 40)

    # Get the latest production model
    prod_models_for_loading = model_registry.find_commits(tags=["production"])

    if prod_models_for_loading:
        latest_model = prod_models_for_loading[0]
        print(f"Loading latest production model: {latest_model.short_hash}")

        # Checkout the model
        model_registry.checkout(latest_model.hash)

        # Demonstrate lazy loading
        print(f"\n📁 Files in this commit:")
        for filename in model_registry.list_files():
            file_obj = model_registry.get_file(filename)
            print(f"   {filename}: {file_obj.size} bytes")

        # Demonstrate lazy file access
        print(f"\n💾 Lazy file loading (files only downloaded when accessed):")
        with model_registry.local_files() as local_files:
            print(f"   Available files: {list(local_files.keys())}")

            # Files are only downloaded when accessed
            for filename in local_files.keys():
                local_path = local_files[filename]
                print(f"   {filename} → {local_path}")
                print(f"      File exists: {Path(local_path).exists()}")
                print(f"      File size: {Path(local_path).stat().st_size} bytes")

        print(f"\n📋 Model metadata:")
        for metadata_key, value in latest_model.metadata.items():
            if isinstance(value, dict):
                print(f"   {metadata_key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   {metadata_key}: {value}")

        # Return variables for reactive dependencies
        latest_model, local_files, local_path
    else:
        print("No production models found")
        # Return None values for reactive dependencies
        latest_model, local_files, local_path = None, None, None
    return


@app.cell
def _(model_registry):
    """Summary and key takeaways."""
    print("🎯 Model Versioning with Kirin - Summary")
    print("=" * 50)

    # Get all commits
    all_commits = model_registry.history()

    print(f"\n📊 Registry Statistics:")
    print(f"   Total commits: {len(all_commits)}")
    print(f"   Total files: {sum(len(c.files) for c in all_commits)}")

    # Count by tags
    tag_counts = {}
    for summary_commit in all_commits:
        for tag in summary_commit.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    print(f"\n🏷️  Tag Distribution:")
    for tag, count in sorted(tag_counts.items()):
        print(f"   {tag}: {count}")

    # Count by framework
    framework_counts = {}
    for framework_commit in all_commits:
        framework = framework_commit.metadata.get('framework', 'unknown')
        framework_counts[framework] = framework_counts.get(framework, 0) + 1

    print(f"\n🔧 Framework Distribution:")
    for framework, count in sorted(framework_counts.items()):
        print(f"   {framework}: {count}")

    print(f"\n✨ Key Benefits Demonstrated:")
    print(f"   ✅ Content-addressed storage (automatic deduplication)")
    print(f"   ✅ Lazy loading (files only downloaded when needed)")
    print(f"   ✅ Rich metadata tracking (hyperparameters, metrics, etc.)")
    print(f"   ✅ Flexible tagging system (staging, versions, domains)")
    print(f"   ✅ Powerful querying (by metadata, tags, or custom filters)")
    print(f"   ✅ Model comparison and diffing")
    print(f"   ✅ Linear history (simple, no branching complexity)")
    print(f"   ✅ Cloud storage support (works with S3, GCS, Azure)")

    print(f"\n🚀 Use Cases:")
    print(f"   • Model experiment tracking")
    print(f"   • A/B testing different model versions")
    print(f"   • Model deployment staging (dev → staging → production)")
    print(f"   • Domain-specific model specialization")
    print(f"   • Model performance monitoring over time")
    print(f"   • Reproducible ML workflows")
    return


if __name__ == "__main__":
    app.run()
