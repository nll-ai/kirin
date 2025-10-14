# Cloud Storage Authentication Guide

When using `kirin` with cloud storage backends (S3, GCS, Azure, etc.), you need
to provide authentication credentials. This guide shows you how to authenticate
with different cloud providers using the new cloud-agnostic authentication parameters.

## New Cloud-Agnostic Authentication (Recommended)

Kirin now supports cloud-agnostic authentication parameters that work across all cloud providers:

### AWS/S3 Authentication

```python
from kirin import Catalog, Dataset

# Using AWS profile
catalog = Catalog(
    root_dir="s3://my-bucket/data",
    aws_profile="my-profile"
)

# Using Dataset with AWS profile
dataset = Dataset(
    root_dir="s3://my-bucket/data",
    name="my-dataset",
    aws_profile="my-profile"
)
```

### GCP/GCS Authentication

```python
from kirin import Catalog, Dataset

# Using service account key file
catalog = Catalog(
    root_dir="gs://my-bucket/data",
    gcs_token="/path/to/service-account.json",
    gcs_project="my-project"
)

# Using Dataset with GCS credentials
dataset = Dataset(
    root_dir="gs://my-bucket/data",
    name="my-dataset",
    gcs_token="/path/to/service-account.json",
    gcs_project="my-project"
)
```

### Azure Blob Storage Authentication

```python
from kirin import Catalog, Dataset

# Using connection string
catalog = Catalog(
    root_dir="az://my-container/data",
    azure_connection_string=os.getenv("AZURE_CONNECTION_STRING")
)

# Using account name and key
dataset = Dataset(
    root_dir="az://my-container/data",
    name="my-dataset",
    azure_account_name="my-account",
    azure_account_key="my-key"
)
```

### Web UI Integration

The web UI also supports cloud authentication through the `CatalogConfig.to_catalog()` method:

```python
from kirin.web.config import CatalogConfig

# Create catalog config with cloud auth
config = CatalogConfig(
    id="my-catalog",
    name="My Catalog",
    root_dir="s3://my-bucket/data",
    aws_profile="my-profile"
)

# Convert to runtime catalog
catalog = config.to_catalog()
```

## Legacy Authentication Methods

The following sections show the legacy authentication methods that still work but are less convenient than the new cloud-agnostic approach.

## Google Cloud Storage (GCS)

### Error You Might See

```text
gcsfs.retry.HttpError: Anonymous caller does not have storage.objects.list access
to the Google Cloud Storage bucket. Permission 'storage.objects.list' denied on
resource (or it may not exist)., 401
```

### Solutions

#### Option 1: Application Default Credentials (Recommended)

Use `gcloud` CLI to set up credentials:

```bash
# Install gcloud CLI first, then:
gcloud auth application-default login
```

Then use kirin normally:

```python
from kirin.dataset import Dataset

# Will automatically use your gcloud credentials
ds = Dataset(root_dir="gs://my-bucket/datasets", dataset_name="my_data")
```

#### Option 2: Service Account Key File

```python
from kirin.dataset import Dataset
import fsspec

# Create filesystem with service account
fs = fsspec.filesystem(
    'gs',
    token='/path/to/service-account-key.json'
)

# Pass it to Dataset
ds = Dataset(
    root_dir="gs://my-bucket/datasets",
    dataset_name="my_data",
    fs=fs  # Use authenticated filesystem
)
```

#### Option 3: Environment Variable

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

```python
from kirin.dataset import Dataset

# Will automatically use the credentials from environment variable
ds = Dataset(root_dir="gs://my-bucket/datasets", dataset_name="my_data")
```

#### Option 4: Pass Credentials Directly

```python
import fsspec
from kirin.dataset import Dataset

fs = fsspec.filesystem(
    'gs',
    project='my-project-id',
    token='cloud'  # Uses gcloud credentials
)

ds = Dataset(root_dir="gs://my-bucket/datasets", dataset_name="my_data", fs=fs)
```

## Amazon S3

### Option 1: AWS CLI Credentials (Recommended)

```bash
# Configure AWS credentials
aws configure
```

Then use normally:

```python
from kirin.dataset import Dataset

ds = Dataset(root_dir="s3://my-bucket/datasets", dataset_name="my_data")
```

### Option 2: Environment Variables

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Option 3: Pass Credentials Explicitly

```python
import fsspec
from kirin.dataset import Dataset

fs = fsspec.filesystem(
    's3',
    key='your-access-key',
    secret='your-secret-key',
    client_kwargs={'region_name': 'us-east-1'}
)

ds = Dataset(root_dir="s3://my-bucket/datasets", dataset_name="my_data", fs=fs)
```

## S3-Compatible Services (Minio, Backblaze B2, DigitalOcean Spaces)

### Minio Example

```python
import fsspec
from kirin.dataset import Dataset

fs = fsspec.filesystem(
    's3',
    key='your-access-key',
    secret='your-secret-key',
    client_kwargs={
        'endpoint_url': 'http://localhost:9000'  # Your Minio endpoint
    }
)

ds = Dataset(root_dir="s3://my-bucket/datasets", dataset_name="my_data", fs=fs)
```

### Backblaze B2 Example

```python
import fsspec
from kirin.dataset import Dataset

fs = fsspec.filesystem(
    's3',
    key='your-application-key-id',
    secret='your-application-key',
    client_kwargs={
        'endpoint_url': 'https://s3.us-west-002.backblazeb2.com'
    }
)

ds = Dataset(root_dir="s3://my-bucket/datasets", dataset_name="my_data", fs=fs)
```

## Azure Blob Storage

### Option 1: Azure CLI Credentials

```bash
az login
```

### Option 2: Connection String

```python
import fsspec
from kirin.dataset import Dataset

fs = fsspec.filesystem(
    'az',
    connection_string='your-connection-string'
)

ds = Dataset(root_dir="az://container/path", dataset_name="my_data", fs=fs)
```

### Option 3: Account Key

```python
import fsspec
from kirin.dataset import Dataset

fs = fsspec.filesystem(
    'az',
    account_name='your-account-name',
    account_key='your-account-key'
)

ds = Dataset(root_dir="az://container/path", dataset_name="my_data", fs=fs)
```

## General Pattern

For any cloud provider, the recommended pattern is:

1. **New Cloud-Agnostic Approach (Recommended)**:

   ```python
   from kirin import Catalog, Dataset

   # For AWS/S3
   catalog = Catalog(root_dir="s3://bucket/path", aws_profile="my-profile")
   dataset = Dataset(root_dir="s3://bucket/path", name="my_data", aws_profile="my-profile")

   # For GCS
   catalog = Catalog(root_dir="gs://bucket/path", gcs_token="/path/to/key.json", gcs_project="my-project")
   dataset = Dataset(root_dir="gs://bucket/path", name="my_data", gcs_token="/path/to/key.json", gcs_project="my-project")

   # For Azure
   catalog = Catalog(root_dir="az://container/path", azure_connection_string="...")
   dataset = Dataset(root_dir="az://container/path", name="my_data", azure_connection_string="...")
   ```

2. **Auto-detect (works if credentials are already configured)**:

   ```python
   ds = Dataset(root_dir="protocol://bucket/path", name="my_data")
   ```

3. **Legacy explicit authentication (still supported)**:

   ```python
   import fsspec
   from kirin.dataset import Dataset

   # Create authenticated filesystem
   fs = fsspec.filesystem('protocol', **auth_kwargs)

   # Pass to Dataset
   ds = Dataset(root_dir="protocol://bucket/path", name="my_data", fs=fs)
   ```

## Testing Without Credentials

For local development/testing without cloud access, you can use:

```python
# In-memory filesystem (no cloud needed)
from kirin.dataset import Dataset

ds = Dataset(root_dir="memory://test-data", dataset_name="my_data")
```

## Troubleshooting

### Issue: "Anonymous caller" or "Access Denied"

- **Cause**: No credentials provided
- **Solution**: Set up credentials using one of the methods above

### Issue: "Permission denied"

- **Cause**: Credentials don't have required permissions
- **Solution**: Ensure your IAM role/service account has read/write permissions
  on the bucket

### Issue: "Bucket does not exist"

- **Cause**: Bucket name is incorrect or doesn't exist
- **Solution**: Create the bucket first or check the bucket name

### Issue: Import errors like "No module named 's3fs'"

- **Cause**: Cloud storage package not installed
- **Solution**: Install required package:

  ```bash
  pip install s3fs      # For S3
  pip install gcsfs     # For GCS
  pip install adlfs     # For Azure
  ```

## Known Issues

### macOS Python 3.13 SSL Certificate Verification

On macOS with Python 3.13, you may encounter SSL certificate verification errors when using cloud storage backends. This is a known Python/macOS issue.

**Workaround**: The web UI skips connection testing during backend creation. Backends are validated when actually used. If you encounter SSL errors during actual usage, install certificates:

```bash
/Applications/Python\ 3.13/Install\ Certificates.command
```

Or use `certifi`:

```bash
pip install --upgrade certifi
```
