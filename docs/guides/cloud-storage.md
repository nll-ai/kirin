# Cloud Storage

Set up and use Kirin with cloud storage backends like S3, GCS, and Azure.

## Overview

Kirin supports multiple cloud storage backends through the fsspec library. You can
use the same API whether you're working with local files or cloud storage.

**Supported Backends:**

- **AWS S3**: `s3://bucket/path`
- **Google Cloud Storage**: `gs://bucket/path`
- **Azure Blob Storage**: `az://container/path`
- **And many more**: Dropbox, Google Drive, etc.

## Authentication Methods

### AWS/S3 Authentication

#### Using AWS Profile (Recommended)

```python
from kirin import Catalog, Dataset

# Using AWS profile
catalog = Catalog(
    root_dir="s3://{{ bucket_name }}/data",
    aws_profile="{{ aws_profile }}"
)

# Using Dataset with AWS profile
dataset = Dataset(
    root_dir="s3://my-bucket/data",
    name="{{ dataset_name }}",
    aws_profile="my-profile"
)
```

#### Using Environment Variables

Set environment variables in your shell or system:

```bash
# Set AWS credentials
export AWS_ACCESS_KEY_ID={{ access_key_id }}
export AWS_SECRET_ACCESS_KEY={{ secret_access_key }}
export AWS_DEFAULT_REGION={{ region }}

# Set Azure credentials
export AZURE_CONNECTION_STRING={{ azure_connection_string }}
```

Then use without explicit credentials:

```python
# Environment variables are automatically detected
catalog = Catalog(root_dir="s3://{{ bucket_name }}/data")
```

#### Using IAM Roles (EC2/ECS/Lambda)

```python
# No explicit credentials needed - uses IAM role automatically
catalog = Catalog(root_dir="s3://my-bucket/data")
```

#### Using AWS SSO

```python
# After running: aws sso login
catalog = Catalog(
    root_dir="s3://{{ bucket_name }}/data",
    aws_profile="{{ sso_profile_name }}"
)
```

### GCP/GCS Authentication

#### Using Service Account Key File

```python
from kirin import Catalog, Dataset

# Using service account key file
catalog = Catalog(
    root_dir="gs://{{ bucket_name }}/data",
    gcs_token="/path/to/service-account.json",
    gcs_project="{{ project_id }}"
)

# Using Dataset with GCS credentials
dataset = Dataset(
    root_dir="gs://{{ bucket_name }}/data",
    name="{{ dataset_name }}",
    gcs_token="/path/to/service-account.json",
    gcs_project="{{ project_id }}"
)
```

#### Using Application Default Credentials

```python
# Set up ADC (one-time setup)
# gcloud auth application-default login

# Use without explicit credentials (automatically detects ADC)
catalog = Catalog(root_dir="gs://my-bucket/data")
```

#### Using Environment Variables (GCS)

```python
import os

# Set environment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/path/to/service-account.json"

# Use without explicit credentials (automatically detects environment)
catalog = Catalog(root_dir="gs://my-bucket/data")
```

#### Using Workload Identity (GKE/Kubernetes)

```python
# No explicit credentials needed - uses workload identity
catalog = Catalog(root_dir="gs://my-bucket/data")
```

### Azure Blob Storage Authentication

#### Using Connection String

```python
from kirin import Catalog, Dataset

# Using connection string
catalog = Catalog(
    root_dir="az://{{ container_name }}/data",
    azure_connection_string=os.getenv("AZURE_CONNECTION_STRING")
)

# Using Dataset with connection string
dataset = Dataset(
    root_dir="az://{{ container_name }}/data",
    name="{{ dataset_name }}",
    azure_connection_string=os.getenv("AZURE_CONNECTION_STRING")
)
```

#### Using Account Name and Key

```python
catalog = Catalog(
    root_dir="az://{{ container_name }}/data",
    azure_account_name="myaccount",
    azure_account_key="mykey"
)
```

#### Using Environment Variables (Azure)

```python
import os

# Set environment variables
os.environ["AZURE_STORAGE_ACCOUNT_NAME"] = "myaccount"
os.environ["AZURE_STORAGE_ACCOUNT_KEY"] = "mykey"

# Use without explicit credentials (automatically detects environment)
catalog = Catalog(root_dir="az://my-container/data")
```

#### Using Azure CLI Authentication

```python
# After running: az login
# No explicit credentials needed - uses Azure CLI authentication
catalog = Catalog(root_dir="az://my-container/data")
```

#### Using Managed Identity (Azure VMs/App Service)

```python
# No explicit credentials needed - uses managed identity
catalog = Catalog(root_dir="az://my-container/data")
```

## Working with Cloud Storage

### Basic Operations

```python
# Create catalog with cloud storage
catalog = Catalog(root_dir="s3://my-bucket/data")

# Create dataset
dataset = catalog.create_dataset("cloud_dataset")

# Add files (same API as local storage)
commit_hash = dataset.commit(
    message="Add data to cloud",
    add_files=["data.csv", "config.json"]
)

# Work with files (same API as local storage)
with dataset.local_files() as local_files:
    for filename, local_path in local_files.items():
        print(f"{filename} -> {local_path}")
        # Process files normally
```

### Performance Considerations

#### Processing Large Files

```python
# For large files, use chunked processing
with dataset.local_files() as local_files:
    if "large_data.csv" in local_files:
        local_path = local_files["large_data.csv"]
        # Use pandas chunking for large files
        for chunk in pd.read_csv(local_path, chunksize=10000):
            print(f"Processing chunk with {len(chunk)} rows")
            process_chunk(chunk)
```

#### Batch Operations

```python
# Batch multiple operations for better performance
files_to_add = ["file1.csv", "file2.csv", "file3.csv"]
dataset.commit(
    message="Add multiple files",
    add_files=files_to_add
)
```

### Error Handling

```python
import boto3
from botocore.exceptions import ClientError

try:
    catalog = Catalog(root_dir="s3://my-bucket/data")
    dataset = catalog.get_dataset("my-dataset")
except ClientError as e:
    if e.response['Error']['Code'] == 'NoSuchBucket':
        print("Bucket does not exist")
    elif e.response['Error']['Code'] == 'AccessDenied':
        print("Access denied - check your credentials")
    else:
        print(f"AWS error: {e}")
except Exception as e:
    print(f"General error: {e}")
```

## Web UI Cloud Integration

### Setting Up Cloud Catalogs

The web UI supports cloud storage through a simple interface:

1. **Authenticate with your cloud provider** using their CLI tools:

   ```bash
   # AWS
   aws configure

   # GCP
   gcloud auth login

   # Azure
   az login
   ```

2. **Create catalog in web UI**:
   - Click "Add Catalog" in the web interface
   - Enter catalog details (ID, name, root directory)
   - For S3: Select AWS profile from dropdown
   - For GCS/Azure: Ensure credentials are configured via environment variables
     or CLI

3. **Authentication handling**:
   - **S3**: Web UI provides profile selection
   - **GCS/Azure**: Requires pre-configured credentials (environment variables,
     CLI auth, etc.)

### Cloud Authentication in Web UI

1. **Create catalog with cloud URL**: Use `s3://`, `gs://`, or `az://` URLs
2. **AWS Profile Selection**: Web UI provides AWS profile dropdown for S3
   authentication
3. **Other Cloud Providers**: For GCS and Azure, authentication must be
   configured programmatically or via environment variables
4. **Credentials stored securely**: AWS profiles saved in catalog configuration
5. **Automatic authentication**: Subsequent uses authenticate automatically

## Troubleshooting

### Common Issues

#### SSL Certificate Errors

```bash
# Set up SSL certificates for isolated Python environments
python -m kirin.setup_ssl
```

#### Authentication Failures

```python
# Check your credentials
import boto3

# Test AWS credentials
session = boto3.Session(profile_name="my-profile")
s3 = session.client('s3')
s3.list_buckets()  # Should work without errors
```

#### Permission Issues

```python
# Check bucket permissions
import boto3

s3 = boto3.client('s3')
try:
    s3.head_bucket(Bucket='my-bucket')
    print("Bucket accessible")
except ClientError as e:
    print(f"Bucket not accessible: {e}")
```

### Performance Optimization

#### Use Appropriate Regions

```python
# Use same region as your compute resources
catalog = Catalog(
    root_dir="s3://{{ bucket_name }}/data",
    aws_profile="{{ aws_profile }}"
)
# Ensure bucket is in same region as your compute
```

#### Optimize File Sizes

```python
# For very large files, consider chunking
# Split large files into smaller chunks
dataset.commit(
    message="Add chunked data",
    add_files=["chunk_001.csv", "chunk_002.csv", "chunk_003.csv"]
)
```

#### Use Compression

```python
# Compress files before adding to reduce storage costs
import gzip
import shutil

# Compress file
with open("data.csv", "rb") as f_in:
    with gzip.open("data.csv.gz", "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

# Add compressed file
dataset.commit(
    message="Add compressed data",
    add_files=["data.csv.gz"]
)
```

## Best Practices

### Security

- **Use IAM roles** when possible instead of access keys
- **Rotate credentials** regularly
- **Use least privilege** - only grant necessary permissions
- **Monitor access** through cloud provider audit logs

### Cost Optimization

- **Use appropriate storage classes** (S3 Standard, IA, Glacier)
- **Enable lifecycle policies** for automatic archival
- **Monitor usage** through cloud provider dashboards
- **Use compression** for text files

### Performance

- **Use same region** as your compute resources
- **Batch operations** when possible
- **Use chunked processing** for large files
- **Consider CDN** for frequently accessed data

## Next Steps

- **[Working with Files](working-with-files.md)** - Advanced file operations
- **[Web UI Overview](../web-ui/overview.md)** - Using the web interface
- **[Basic Usage](basic-usage.md)** - Core dataset operations
