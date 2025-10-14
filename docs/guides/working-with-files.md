# Working with Files

Advanced file operations and integration patterns for data science workflows.

## File Access Patterns

### Local Files Context Manager (Recommended)

The `local_files()` context manager is the recommended way to work with files:

```python
from pathlib import Path
import pandas as pd
import polars as pl

# Work with files locally
with dataset.local_files() as local_files:
    for filename, local_path in local_files.items():
        print(f"{filename} -> {local_path}")

        # Process files with standard Python libraries
        if filename.endswith('.csv'):
            # Use pandas
            df = pd.read_csv(local_path)
            print(f"CSV shape: {df.shape}")

            # Or use polars
            df_polars = pl.read_csv(local_path)
            print(f"Polars shape: {df_polars.shape}")

        elif filename.endswith('.parquet'):
            # Read parquet files
            df = pd.read_parquet(local_path)
            print(f"Parquet shape: {df.shape}")

        elif filename.endswith('.json'):
            import json
            data = json.loads(Path(local_path).read_text())
            print(f"JSON keys: {list(data.keys())}")
```

**Benefits:**
- **Library compatibility**: Works with pandas, polars, numpy, etc.
- **Automatic cleanup**: Files cleaned up when done
- **Standard paths**: Use normal Python file operations
- **Memory efficient**: No need to load entire files into memory



## Working with Data Science Libraries

### Pandas Examples

```python
import pandas as pd

with dataset.local_files() as local_files:
    # Read CSV files
    if "data.csv" in local_files:
        df = pd.read_csv(local_files["data.csv"])
        print(f"DataFrame shape: {df.shape}")

        # Process data
        df_processed = df.dropna().reset_index(drop=True)

        # Save processed data
        df_processed.to_csv("processed_data.csv")

        # Commit processed data
        dataset.commit(
            message="Add processed data",
            add_files=["processed_data.csv"]
        )
```

### Polars Examples

```python
import polars as pl

with dataset.local_files() as local_files:
    # Read CSV files with Polars
    if "data.csv" in local_files:
        df = pl.read_csv(local_files["data.csv"])
        print(f"Polars DataFrame shape: {df.shape}")

        # Process data with Polars
        df_processed = df.filter(pl.col("value").is_not_null())

        # Save processed data
        df_processed.write_csv("processed_data.csv")

        # Commit processed data
        dataset.commit(
            message="Add processed data",
            add_files=["processed_data.csv"]
        )
```

### NumPy Examples

```python
import numpy as np

with dataset.local_files() as local_files:
    # Read CSV files as NumPy arrays
    if "data.csv" in local_files:
        df = pd.read_csv(local_files["data.csv"])
        array = df.values
        print(f"NumPy array shape: {array.shape}")

        # Process with NumPy
        processed_array = np.nan_to_num(array)

        # Save processed array
        np.savetxt("processed_data.csv", processed_array, delimiter=",")

        # Commit processed data
        dataset.commit(
            message="Add processed array",
            add_files=["processed_data.csv"]
        )
```

### Scikit-learn Examples

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

with dataset.local_files() as local_files:
    # Load training data
    if "train.csv" in local_files:
        df = pd.read_csv(local_files["train.csv"])
        X = df.drop("target", axis=1)
        y = df["target"]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

        # Train model
        model = RandomForestClassifier(n_estimators=100)
        model.fit(X_train, y_train)

        # Save model
        joblib.dump(model, "model.pkl")

        # Save test data
        X_test.to_csv("X_test.csv", index=False)
        y_test.to_csv("y_test.csv", index=False)

        # Commit model and test data
        dataset.commit(
            message="Add trained model and test data",
            add_files=["model.pkl", "X_test.csv", "y_test.csv"]
        )
```





## Best Practices

### File Naming

Use descriptive, consistent file names:

```python
# Good naming
dataset.commit("Add Q1 sales data", add_files=["sales_q1_2024.csv"])
dataset.commit("Add processed data", add_files=["sales_q1_2024_processed.csv"])
dataset.commit("Add model results", add_files=["model_results_q1_2024.json"])

# Avoid vague names
dataset.commit("Add data", add_files=["data.csv"])
dataset.commit("Update", add_files=["file1.csv", "file2.csv"])
```

### File Organization

Organize files in logical directories:

```python
# Good organization
dataset.commit("Add raw data", add_files=["raw/sales.csv", "raw/customers.csv"])
dataset.commit("Add processed data", add_files=["processed/sales_clean.csv"])
dataset.commit("Add analysis", add_files=["analysis/results.csv", "analysis/plots.png"])

# Avoid flat structure
dataset.commit("Add files", add_files=["sales.csv", "customers.csv", "results.csv", "plots.png"])
```


## Next Steps

- **[Commit Management](commit-management.md)** - Understanding commit history
- **[Cloud Storage](cloud-storage.md)** - Working with cloud backends
- **[Basic Usage](basic-usage.md)** - Core dataset operations
