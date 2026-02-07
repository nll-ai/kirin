# Catalog Management

Configuration and management of data catalogs in the web UI.

## Catalog Configuration

### Local Storage Catalogs

For local filesystem storage:

**Benefits:**

- **Simple setup**: No authentication required
- **Fast access**: Direct filesystem access
- **Easy backup**: Standard file operations
- **No costs**: No cloud storage fees

### Cloud Storage Catalogs

#### AWS S3 Configuration

**Setup Steps:**

1. **Configure AWS credentials** in your environment
2. **Create S3 bucket** with appropriate permissions
3. **Set up IAM policies** for bucket access
4. **Test connection** in the web UI

**Web UI Configuration:**

- **Root Directory**: S3 URL (e.g., `s3://my-bucket/data`). The catalog is identified
  and shown by this path (no separate name field).
- **AWS Profile**: Optional AWS profile name (auto-detected from environment)
- **Authentication Command**: Optional CLI command for automatic authentication

#### Google Cloud Storage Configuration

**Setup Steps:**

1. **Authenticate with GCP** using `gcloud auth application-default login`
2. **Create bucket** in GCP console
3. **Set up bucket permissions**
4. **Test connection** in the web UI

**Web UI Configuration:**

- **Root Directory**: GCS URL (e.g., `gs://my-bucket/data`). The catalog is identified
  and shown by this path.
- **Authentication Command**: Optional CLI command for automatic authentication

#### Azure Blob Storage Configuration

**Setup Steps:**

1. **Authenticate with Azure** using `az login`
2. **Create storage account** in Azure portal
3. **Create container** for data storage
4. **Test connection** in the web UI

**Web UI Configuration:**

- **Root Directory**: Azure URL (e.g., `az://my-container/data`). The catalog is
  identified and shown by this path.
- **Authentication Command**: Optional CLI command for automatic authentication

### Authentication Command Auto-Execution

**NEW**: Kirin's web UI can automatically execute authentication commands
when accessing catalogs, eliminating the need for manual CLI authentication.

**How It Works:**

1. Store your authentication command in the catalog configuration (e.g.,
   `aws sso login --profile my-profile`)
2. When authentication fails, Kirin automatically executes the command
3. If successful, Kirin retries the operation and shows your datasets
4. If it fails, you'll see clear error messages with manual instructions

**Setup:**

When adding or editing a catalog, fill in the "Authentication Command
(Optional)" field:

- **AWS S3**: `aws sso login --profile {{ aws_profile }}`
- **GCP GCS**: `gcloud auth login`
- **Azure**: `az login`

**Benefits:**

- **Automatic retry**: No manual intervention needed
- **Seamless UX**: Authentication happens in the background
- **Clear feedback**: Success/failure messages shown in UI
- **Manual fallback**: You can still authenticate manually if auto-auth fails

**Example:**

```text
Root Directory: s3://my-production-bucket/data
AWS Profile: production
Auth Command: aws sso login --profile production

Result: The catalog is shown as s3://my-production-bucket/data. When you
click on it, Kirin will automatically run the auth command if needed.
```

## Multi-Catalog Workflows

### Organizing Catalogs

Structure your catalogs by purpose (each is identified by its root path):

```text
s3://production-bucket/data
gs://production-bucket/data
gs://analytics-bucket/data
az://ml-container/data
```

### Working with Multiple Catalogs

The web UI allows you to manage multiple catalogs from a single interface:

1. **Add multiple catalogs** using the "Add Catalog" button (enter root directory
   only; the catalog is identified and named by that path)
2. **Switch between catalogs** by clicking on catalog cards
3. **View datasets** in each catalog separately
4. **Edit or remove** catalogs as needed

Each catalog maintains its own datasets and commit history independently.
**Removing a catalog** from the list only removes it from your local config; it
does not delete any data on S3, GCS, or other remote storage.

## Authentication Management

### AWS Authentication

#### Using AWS Profiles

```bash
# Configure AWS profile
aws configure --profile production
aws configure --profile development

# Use in web UI: Select profile from dropdown when creating S3 catalog
```

#### Using Environment Variables

```bash
# Set environment variables
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-west-2"

# Use in web UI: Leave AWS Profile empty to use environment variables
```

#### Using IAM Roles

For AWS EC2, ECS, or Lambda instances that have an associated IAM role, no
explicit credentials are required. The web UI will automatically use the IAM
role provided to the instance for authentication.

### GCP Authentication

#### Application Default Credentials (Recommended)

```bash
# Set up ADC (one-time setup)
gcloud auth application-default login

# Use in web UI: No additional configuration needed
# Root Directory: gs://my-bucket/data
```

#### Service Account Keys (Advanced)

```bash
# Create service account
gcloud iam service-accounts create kirin-service

# Download key file
gcloud iam service-accounts keys create key.json \
  --iam-account=kirin-service@project.iam.gserviceaccount.com

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"

# Use in web UI: No additional configuration needed
```

### Azure Authentication

#### Azure CLI (Recommended)

```bash
# Authenticate with Azure
az login

# Use in web UI: No additional configuration needed
# Root Directory: az://my-container/data
```

#### Connection String (Advanced)

```bash
# Set environment variable
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=mykey"

# Use in web UI: No additional configuration needed
```

## Security Best Practices

### Credential Management

#### Secure Storage

- **Use IAM roles** when possible instead of access keys
- **Rotate credentials** regularly
- **Use least privilege** - only grant necessary permissions
- **Monitor access** through cloud provider audit logs

#### Environment Variables

```bash
# Set environment variables for sensitive data
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
export AZURE_STORAGE_ACCOUNT_NAME="myaccount"
export AZURE_STORAGE_ACCOUNT_KEY="mykey"
```

### Access Control

#### AWS S3 Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::{{ account_id }}:user/{{ username }}"
      },
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::{{ bucket_name }}",
        "arn:aws:s3:::{{ bucket_name }}/*"
      ]
    }
  ]
}
```

#### GCP IAM Permissions

For Google Cloud Storage, ensure your service account or user has the
following roles:

- **Storage Object Admin**: For full read/write access to objects
- **Storage Legacy Bucket Reader**: For listing bucket contents

## Troubleshooting

### Common Issues

#### Authentication Failures

```bash
# Test AWS credentials
aws s3 ls s3://{{ bucket_name }}

# Test GCS credentials
gsutil ls gs://{{ bucket_name }}

# Test Azure credentials
az storage blob list --container-name {{ container_name }}
```

#### Permission Errors

```bash
# Check S3 bucket permissions
aws s3api get-bucket-policy --bucket my-bucket

# Check GCS bucket permissions
gsutil iam get gs://my-bucket

# Check Azure container permissions
az storage container show --name my-container
```

#### Connection Issues

```bash
# Test network connectivity
ping s3.amazonaws.com
ping storage.googleapis.com
ping blob.core.windows.net

# Check DNS resolution
nslookup s3.amazonaws.com
nslookup storage.googleapis.com
```

### Performance Issues

#### Slow Operations

```python
# Use appropriate file sizes
# Split large files into chunks
dataset.commit(
    message="Add chunked data",
    add_files=["chunk_001.csv", "chunk_002.csv", "chunk_003.csv"]
)

# Use compression for text files
dataset.commit(
    message="Add compressed data",
    add_files=["data.csv.gz"]
)
```

#### Memory Issues

```python
# Use chunked processing for large files
with dataset.local_files() as local_files:
    for filename, local_path in local_files.items():
        if filename.endswith('.csv'):
            # Process in chunks
            for chunk in pd.read_csv(local_path, chunksize=10000):
                process_chunk(chunk)
```

## Next Steps

- **[Web UI Overview](overview.md)** - Getting started with the web interface
- **[Cloud Storage Guide](../guides/cloud-storage.md)** - Detailed cloud setup
- **[Basic Usage Guide](../guides/basic-usage.md)** - Core dataset operations
