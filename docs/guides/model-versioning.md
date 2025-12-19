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

#### Option A: Committing Model Objects Directly (Recommended for scikit-learn)

Kirin can automatically handle scikit-learn model objects, serializing them and
extracting hyperparameters and metrics:

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

# Load and prepare data
iris = load_iris()
X, y = iris.data, iris.target
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train model
model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Commit model object directly - everything is automatic!
commit_hash = model_registry.commit(
    message="Initial baseline model",
    add_files=[model],  # Just pass the model object
    metadata={
        "accuracy": model.score(X_test, y_test),  # Data-dependent metrics
        "dataset": "iris",
    },
    tags=["baseline", "v1.0"]
)

# Hyperparameters and metrics are automatically extracted:
# - model.get_params() → metadata["models"]["model"]["hyperparameters"]
# - model.feature_importances_ → metadata["models"]["model"]["metrics"]
# - Source file linking → metadata["models"]["model"]["source_file"]
```

#### Option B: Manual Serialization (For PyTorch, TensorFlow, etc.)

For frameworks that don't have automatic support yet, manually serialize:

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

**With scikit-learn (automatic):**

```python
# Train an improved model
improved_model = RandomForestClassifier(
    n_estimators=200,  # More trees
    max_depth=10,  # Deeper trees
    random_state=42
)
improved_model.fit(X_train, y_train)

# Commit improved model - hyperparameters auto-extracted
commit_hash = model_registry.commit(
    message="Improved model with more trees",
    add_files=[improved_model],
    metadata={
        "accuracy": improved_model.score(X_test, y_test),
        "improvements": ["More trees", "Deeper trees"]
    },
    tags=["improved", "v2.0"]
)
```

**With PyTorch (manual):**

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

## Committing Model Objects Directly

Kirin supports committing scikit-learn model objects directly, automatically
handling serialization, hyperparameter extraction, and metrics extraction. This
simplifies your workflow significantly.

### Basic Usage

Simply pass the model object to `commit()`:

```python
from sklearn.ensemble import RandomForestClassifier

# Train your model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Commit directly - no manual serialization needed!
commit_hash = dataset.commit(
    message="Initial model",
    add_files=[model],  # Model object, not file path
    metadata={"accuracy": model.score(X_test, y_test)}
)
```

Kirin automatically:

- Serializes the model using joblib (saves as `model.pkl`)
- Extracts hyperparameters via `model.get_params()`
- Extracts available metrics (feature_importances_, coef_, etc.)
- Links the source script that created the model
- Structures metadata in `metadata["models"]["model"]`

### Model-Specific Metadata

When you have multiple models with different metrics, use the `metadata["models"]`
structure to provide model-specific metadata:

**Important:** The keys under `metadata["models"]` must match the model variable
names exactly. Kirin auto-detects variable names (e.g., `rf_model`, `lr_model`)
and uses them as keys in the metadata structure. If your metadata keys don't
match the variable names, the metadata won't be properly merged with
auto-extracted metadata. Always use the same variable names in both your code
and your metadata structure for consistency.

```python
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

# Train multiple models
rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
rf_model.fit(X_train, y_train)
rf_accuracy = rf_model.score(X_test, y_test)

lr_model = LogisticRegression(random_state=42)
lr_model.fit(X_train, y_train)
lr_accuracy = lr_model.score(X_test, y_test)

# Commit with model-specific metadata
commit_hash = dataset.commit(
    message="Compare RandomForest vs LogisticRegression",
    add_files=[rf_model, lr_model],
    metadata={
        "models": {
            "rf_model": {
                "accuracy": rf_accuracy,  # Model-specific
                "f1_score": 0.93
            },
            "lr_model": {
                "accuracy": lr_accuracy,  # Different accuracy
                "f1_score": 0.85
            }
        },
        "dataset": "iris",  # Shared metadata (top-level)
        "test_size": 0.2
    }
)
```

**Metadata Structure:**

The final metadata will be structured as:

```python
{
    "models": {
        "rf_model": {
            "model_type": "RandomForestClassifier",  # Auto-extracted
            "hyperparameters": {...},  # Auto-extracted
            "metrics": {...},  # Auto-extracted
            "sklearn_version": "1.3.0",  # Auto-extracted
            "accuracy": 0.95,  # User-provided
            "f1_score": 0.93,  # User-provided
            "source_file": "ml-workflow.py",  # Auto-detected
            "source_hash": "..."
        },
        "lr_model": {
            "model_type": "LogisticRegression",  # Auto-extracted
            "hyperparameters": {...},  # Auto-extracted
            "metrics": {...},  # Auto-extracted
            "sklearn_version": "1.3.0",  # Auto-extracted
            "accuracy": 0.87,  # User-provided
            "f1_score": 0.85,  # User-provided
            "source_file": "ml-workflow.py",  # Auto-detected
            "source_hash": "..."
        }
    },
    "dataset": "iris",  # Top-level (shared)
    "test_size": 0.2
}
```

### Metadata Merging

Kirin automatically merges auto-extracted metadata with your provided metadata:

1. **Auto-extracted first**: Hyperparameters, metrics, sklearn_version, and
   source info are extracted and added to each model's entry
2. **User-provided merges in**: Your model-specific metadata (via
   `metadata["models"][var_name]`) is merged, overriding auto-extracted values
   on conflicts
3. **Top-level metadata**: Metadata outside the `models` dict applies to the
   entire commit (shared context)

**Example:**

```python
from sklearn.ensemble import RandomForestClassifier

# Train a model
model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Commit with both auto-extracted and user-provided metadata
commit_hash = dataset.commit(
    message="Model with custom metadata",
    add_files=[model],
    metadata={
        "models": {
            "model": {
                "accuracy": 0.95,  # User-provided metric
                "f1_score": 0.93,  # User-provided metric
                "custom_note": "Trained on v2 dataset",  # Custom field
            }
        },
        "dataset": "iris",  # Top-level metadata
    }
)

# The final metadata structure will be:
# {
#     "models": {
#         "model": {
#             "model_type": "RandomForestClassifier",  # Auto-extracted
#             "hyperparameters": {  # Auto-extracted
#                 "n_estimators": 100,
#                 "max_depth": 5,
#                 "random_state": 42,
#                 # ... all other hyperparameters
#             },
#             "metrics": {  # Auto-extracted
#                 "feature_importances": [...],
#                 "n_features_in": 4,
#                 # ... other available metrics
#             },
#             "sklearn_version": "1.3.0",  # Auto-extracted
#             "accuracy": 0.95,  # User-provided (merged in)
#             "f1_score": 0.93,  # User-provided (merged in)
#             "custom_note": "Trained on v2 dataset",  # User-provided (merged in)
#             "source_file": "ml-workflow.py",  # Auto-extracted
#             "source_hash": "..."  # Auto-extracted
#         }
#     },
#     "dataset": "iris"  # Top-level metadata
# }
```

### Mixed Files and Models

You can mix model objects with regular file paths:

```python
dataset.commit(
    message="Model with plots and config",
    add_files=[
        model,  # Model object (auto-serialized)
        "plot1.svg",  # Regular file path
        "config.json",  # Regular file path
    ],
    metadata={"accuracy": 0.95}
)
```

### When to Use Model Objects vs File Paths

**Use model objects when:**

- Working with scikit-learn models
- You want automatic hyperparameter/metrics extraction
- You want source file linking
- You want simplified workflow

**Use file paths when:**

- Working with PyTorch, TensorFlow, or other frameworks (not yet supported)
- Models are already serialized
- You need explicit control over serialization format
- You're migrating existing workflows

## Querying and Discovery

### Find Models by Tags

```python
# Find all production models
production_models = model_registry.find_commits(tags=["production"])

# Find models with multiple tags
v2_models = model_registry.find_commits(tags=["v2.0", "production"])
```

### Find Models by Performance Metrics

When models are committed as objects, their metadata is nested under
`metadata["models"][var_name]`. Here's how to query them:

```python
# Find high-accuracy models (checking nested model metadata)
def has_high_accuracy(metadata):
    """Check if any model in commit has high accuracy."""
    if "models" in metadata:
        for model_name, model_meta in metadata["models"].items():
            if model_meta.get("accuracy", 0) > 0.9:
                return True
    # Also check top-level accuracy (for backward compatibility)
    return metadata.get("accuracy", 0) > 0.9

high_accuracy = model_registry.find_commits(
    metadata_filter=has_high_accuracy
)

# Find models by specific model type
def is_sklearn_model(metadata):
    """Check if commit contains scikit-learn models."""
    if "models" in metadata:
        for model_name, model_meta in metadata["models"].items():
            if model_meta.get("model_type", "").startswith("RandomForest"):
                return True
    return False

rf_models = model_registry.find_commits(metadata_filter=is_sklearn_model)

# Complex queries: find best models with multiple criteria
def is_best_model(metadata):
    """Find models with high accuracy and f1_score."""
    if "models" in metadata:
        for model_name, model_meta in metadata["models"].items():
            accuracy = model_meta.get("accuracy", 0)
            f1_score = model_meta.get("f1_score", 0)
            if accuracy > 0.9 and f1_score > 0.85:
                return True
    return False

best_models = model_registry.find_commits(
    tags=["production"],
    metadata_filter=is_best_model
)

# For top-level metadata (backward compatibility or non-model commits)
high_accuracy_simple = model_registry.find_commits(
    metadata_filter=lambda m: m.get("accuracy", 0) > 0.9
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
print(f"Tags: {current_commit.tags}")

# Access model metadata (nested structure)
if "models" in current_commit.metadata:
    for model_name, model_meta in current_commit.metadata["models"].items():
        print(f"\nModel: {model_name}")
        print(f"  Type: {model_meta.get('model_type')}")
        print(f"  scikit-learn version: {model_meta.get('sklearn_version', 'N/A')}")
        print(f"  Accuracy: {model_meta.get('accuracy', 'N/A')}")
        print(f"  Hyperparameters: {model_meta.get('hyperparameters', {})}")
        print(f"  Metrics: {model_meta.get('metrics', {})}")
        print(f"  Source: {model_meta.get('source_file', 'N/A')}")

# For top-level metadata (backward compatibility)
if "accuracy" in current_commit.metadata:
    print(f"Accuracy: {current_commit.metadata['accuracy']}")

# List all files in current version
for filename in model_registry.list_files():
    file_obj = model_registry.get_file(filename)
    print(f"{filename}: {file_obj.size} bytes")
```

## Metadata Schema Conventions

While Kirin doesn't enforce a specific schema, here are recommended conventions:

### Core Model Information

**For model objects (recommended):**

When committing model objects, metadata is automatically structured under
`metadata["models"][var_name]`:

```python
# When committing model objects, structure is automatic
metadata = {
    "models": {
        "model": {  # Key matches variable name
            # Auto-extracted (for scikit-learn)
            "model_type": "RandomForestClassifier",
            "hyperparameters": {
                "n_estimators": 100,
                "max_depth": 5,
                # ... all hyperparameters auto-extracted
            },
            "metrics": {
                "feature_importances": [...],
                "n_features_in": 4,
                # ... available metrics auto-extracted
            },
            "sklearn_version": "1.3.0",  # Auto-extracted
            "source_file": "ml-workflow.py",  # Auto-detected
            "source_hash": "...",  # Auto-detected

            # User-provided
            "accuracy": 0.92,
            "f1_score": 0.90,
            "precision": 0.91,
            "recall": 0.89,
            "training_data": "dataset_v2",
            "training_time_seconds": 1200,
        }
    },
    # Top-level metadata (shared across all models in commit)
    "dataset": "iris",
    "test_size": 0.2,
}
```

**For manual serialization (backward compatibility):**

For frameworks not yet supported or when manually serializing:

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
