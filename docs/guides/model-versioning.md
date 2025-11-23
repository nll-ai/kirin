# Model Versioning with Kirin

Kirin provides powerful model versioning capabilities that make it easy to
track, compare, and manage machine learning models throughout their lifecycle.
This guide shows you how to use Kirin for model versioning workflows.

## Overview

Model versioning with Kirin enables you to:

- **Track model artifacts** alongside rich metadata (hyperparameters, metrics,
  training info)
- **Tag models** for different stages (dev, staging, production) or versions
- **Query and discover** models by performance metrics, tags, or custom criteria
- **Compare model versions** to understand what changed between iterations
- **Maintain linear history** with simple, git-like semantics
- **Store models anywhere** - local filesystem, S3, GCS, Azure, etc.

## Basic Model Versioning Workflow

### 1. Initialize a Model Registry

```python
from kirin import Dataset

# Create a model registry (works with any storage backend)
model_registry = Dataset(
    root_dir="s3://my-bucket/models",  # or local path, GCS, Azure, etc.
    name="sentiment_classifier"
)
```

### 2. Save Your First Model

```python
import torch

# Save your model files
torch.save(model.state_dict(), "model_weights.pt")

# Commit with metadata and tags
commit_hash = model_registry.commit(
    message="Initial baseline model",
    add_files=["model_weights.pt", "config.json"],
    metadata={
        "framework": "pytorch",
        "accuracy": 0.87,
        "f1_score": 0.85,
        "hyperparameters": {
            "learning_rate": 0.001,
            "epochs": 10,
            "batch_size": 32
        },
        "training_data": "sentiment_v1",
        "model_size_mb": 0.5
    },
    tags=["baseline", "v1.0"]
)
```

### 3. Save Improved Models

```python
# Train an improved model
# ... training code ...

# Save improved model
torch.save(improved_model.state_dict(), "model_weights_v2.pt")

# Commit with updated metadata
commit_hash = model_registry.commit(
    message="Improved model with better regularization",
    add_files=["model_weights_v2.pt"],
    metadata={
        "framework": "pytorch",
        "accuracy": 0.92,  # Improved!
        "f1_score": 0.90,
        "hyperparameters": {
            "learning_rate": 0.0005,
            "epochs": 15,
            "batch_size": 32,
            "weight_decay": 0.01  # Added regularization
        },
        "training_data": "sentiment_v2",
        "improvements": ["Better regularization", "More epochs"]
    },
    tags=["improved", "v2.0", "production"]
)
```

## Querying and Discovery

### Find Models by Tags

```python
# Find all production models
production_models = model_registry.find_commits(tags=["production"])

# Find models with multiple tags
v2_models = model_registry.find_commits(tags=["v2.0", "production"])
```

### Find Models by Performance Metrics

```python
# Find high-accuracy models
high_accuracy = model_registry.find_commits(
    metadata_filter=lambda m: m.get("accuracy", 0) > 0.9
)

# Find models by framework
pytorch_models = model_registry.find_commits(
    metadata_filter=lambda m: m.get("framework") == "pytorch"
)

# Complex queries
best_models = model_registry.find_commits(
    tags=["production"],
    metadata_filter=lambda m: (
        m.get("accuracy", 0) > 0.9 and
        m.get("f1_score", 0) > 0.85
    )
)
```

### Compare Model Versions

```python
# Compare two model versions
comparison = model_registry.compare_commits(
    "abc123def",  # First model hash
    "xyz789ghi"   # Second model hash
)

print("Metadata changes:")
print(comparison["metadata_diff"]["changed"])
print("Tag changes:")
print(comparison["tags_diff"])
```

## Loading and Using Models

### Checkout Specific Model Version

```python
# Checkout a specific model version
model_registry.checkout("abc123def")

# Access files from that version
with model_registry.local_files() as files:
    # Files are lazily downloaded when accessed
    model_path = files["model_weights.pt"]
    config_path = files["config.json"]

    # Load your model
    model = torch.load(model_path)
```

### Get Model Information

```python
# Get current model info
current_commit = model_registry.current_commit
print(f"Model: {current_commit.message}")
print(f"Accuracy: {current_commit.metadata['accuracy']}")
print(f"Tags: {current_commit.tags}")

# List all files in current version
for filename in model_registry.list_files():
    file_obj = model_registry.get_file(filename)
    print(f"{filename}: {file_obj.size} bytes")
```

## Metadata Schema Conventions

While Kirin doesn't enforce a specific schema, here are recommended conventions:

### Core Model Information

```python
metadata = {
    # Required
    "framework": "pytorch",  # or "tensorflow", "sklearn", etc.
    "version": "2.1.0",      # Semantic versioning

    # Performance metrics
    "accuracy": 0.92,
    "f1_score": 0.90,
    "precision": 0.91,
    "recall": 0.89,

    # Model configuration
    "hyperparameters": {
        "learning_rate": 0.001,
        "epochs": 10,
        "batch_size": 32,
        "optimizer": "adam"
    },

    # Training information
    "training_data": "dataset_v2",
    "training_time_seconds": 1200,
    "model_size_mb": 0.5,

    # Optional: domain-specific info
    "domain": "medical",
    "use_cases": ["patient_feedback", "clinical_notes"]
}
```

### Tag Conventions

```python
# Staging tags
tags = ["dev", "staging", "production"]

# Version tags
tags = ["v1.0", "v2.0", "v2.1"]

# Domain tags
tags = ["medical", "financial", "general"]

# Status tags
tags = ["baseline", "improved", "experimental"]
```

## Advanced Patterns

### Model Staging Pipeline

```python
# Development model
dev_commit = model_registry.commit(
    message="Experimental model with new architecture",
    add_files=["model.pt"],
    metadata={"accuracy": 0.88, "framework": "pytorch"},
    tags=["dev", "experimental"]
)

# Promote to staging
staging_commit = model_registry.commit(
    message="Promote experimental model to staging",
    add_files=["model.pt"],  # Same model, different tags
    metadata={"accuracy": 0.88, "framework": "pytorch"},
    tags=["staging", "v2.1-beta"]
)

# Promote to production
prod_commit = model_registry.commit(
    message="Release v2.1 to production",
    add_files=["model.pt"],
    metadata={"accuracy": 0.88, "framework": "pytorch"},
    tags=["production", "v2.1"]
)
```

### A/B Testing Models

```python
# Model A
model_a = model_registry.commit(
    message="Model A - Original architecture",
    add_files=["model_a.pt"],
    metadata={"accuracy": 0.89, "architecture": "original"},
    tags=["ab-test", "model-a"]
)

# Model B
model_b = model_registry.commit(
    message="Model B - Improved architecture",
    add_files=["model_b.pt"],
    metadata={"accuracy": 0.92, "architecture": "improved"},
    tags=["ab-test", "model-b"]
)

# Find A/B test models
ab_models = model_registry.find_commits(tags=["ab-test"])
```

### Domain-Specific Models

```python
# General model
general_model = model_registry.commit(
    message="General sentiment classifier",
    add_files=["general_model.pt"],
    metadata={
        "accuracy": 0.90,
        "domain": "general",
        "training_data": "general_reviews"
    },
    tags=["general", "v1.0"]
)

# Medical domain model
medical_model = model_registry.commit(
    message="Medical sentiment classifier",
    add_files=["medical_model.pt"],
    metadata={
        "accuracy": 0.85,  # Lower on general data
        "domain_accuracy": 0.94,  # Higher on medical data
        "domain": "medical",
        "training_data": "medical_reviews"
    },
    tags=["medical", "domain-specific", "v1.1"]
)
```

## Best Practices

### 1. Consistent Metadata Schema

Define a standard metadata schema for your team:

```python
def create_model_metadata(accuracy, f1_score, hyperparams, training_info):
    """Create standardized metadata for model commits."""
    return {
        "framework": "pytorch",
        "accuracy": accuracy,
        "f1_score": f1_score,
        "hyperparameters": hyperparams,
        "training_data": training_info["dataset"],
        "training_time_seconds": training_info["duration"],
        "model_size_mb": training_info["size_mb"],
        "timestamp": datetime.now().isoformat()
    }
```

### 2. Meaningful Commit Messages

```python
# Good commit messages
"Initial baseline model - BERT fine-tuned on customer reviews"
"Improved model v2.0 - Added regularization and more training data"
"Hotfix v2.0.1 - Fixed tokenization bug in production model"
"Domain adaptation - Medical sentiment classifier"

# Avoid vague messages
"Updated model"
"New version"
"Changes"
```

### 3. Tag Management

Use consistent tagging strategies:

```python
# Semantic versioning
tags = ["v1.0.0", "v1.1.0", "v2.0.0"]

# Staging pipeline
tags = ["dev", "staging", "production"]

# Feature flags
tags = ["feature-xyz", "experimental", "deprecated"]
```

### 4. Model Validation

Always validate model performance before committing:

```python
def validate_model(model, test_data):
    """Validate model before committing."""
    accuracy = evaluate_model(model, test_data)
    if accuracy < 0.8:
        raise ValueError(f"Model accuracy {accuracy} below threshold")
    return accuracy

# Use in commit workflow
accuracy = validate_model(model, test_data)
model_registry.commit(
    message="Validated model v2.0",
    add_files=["model.pt"],
    metadata={"accuracy": accuracy, "validated": True},
    tags=["validated", "v2.0"]
)
```

## Integration with ML Workflows

### With Experiment Tracking

```python
# Log to both Kirin and your experiment tracker
import wandb

# Start experiment
wandb.init(project="sentiment-classifier")

# Train model
model, metrics = train_model()

# Log to experiment tracker
wandb.log(metrics)

# Commit to Kirin
commit_hash = model_registry.commit(
    message=f"Experiment {wandb.run.name}",
    add_files=["model.pt"],
    metadata={
        **metrics,
        "experiment_id": wandb.run.id,
        "run_name": wandb.run.name
    },
    tags=["experiment", wandb.run.name]
)
```

### With Model Serving

```python
# Deploy model from Kirin
def deploy_model(commit_hash):
    model_registry.checkout(commit_hash)

    with model_registry.local_files() as files:
        model = torch.load(files["model.pt"])
        config = json.load(open(files["config.json"]))

    # Deploy to your serving infrastructure
    deploy_to_production(model, config)
    print(f"Deployed model {commit_hash[:8]}")
```

## Troubleshooting

### Common Issues

#### My metadata isn't being saved

Make sure you're passing the `metadata` parameter to `commit()`. Check
that your metadata is JSON-serializable.

#### Can't find my models with `find_commits()`

Verify your filter function returns a boolean. Use
`lambda m: m.get("key", default) > value` for safe access.

#### Files aren't downloading with `local_files()`

Files are lazily loaded. Access them through the dictionary:
`local_files["filename"]` to trigger download.

#### How do I migrate from other model versioning tools?

Kirin can work alongside other tools. You can import models from MLflow,
DVC, etc., by saving their artifacts and committing them to Kirin.

### Performance Tips

- Use `limit` parameter in `find_commits()` for large datasets
- Store large models in cloud storage (S3, GCS) for better performance
- Use `local_files()` context manager to ensure cleanup of temporary files
- Consider using tags for frequently queried model categories

## Next Steps

- Explore the [API Reference](../reference/api.md) for detailed method documentation
- Check out the [Model Versioning
  Demo](../../notebooks/model_versioning_demo.py) for a complete example
- Learn about [Cloud Storage Integration](cloud-storage.md) for production deployments
