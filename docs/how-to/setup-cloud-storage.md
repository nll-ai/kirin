# Setup Cloud Storage for Kirin

This guide shows you how to configure Kirin to work with AWS S3, Google
Cloud Storage, and Azure Blob Storage. Each section covers authentication
setup and creating your first catalog with cloud storage.

## Prerequisites

- AWS account with S3 access (for S3 setup)
- Google Cloud project with GCS access (for GCS setup)
- Azure account with Blob Storage access (for Azure setup)
- Basic familiarity with Kirin datasets and catalogs

## AWS S3 Setup

Configure Kirin to use AWS S3 as your storage backend.

### Step 1: Configure AWS Credentials

Set up AWS credentials using one of these methods:

#### Option A: AWS CLI Configuration (Recommended)

```bash
aws configure --profile {{ aws_profile }}
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
```

#### Option B: Environment Variables

```bash
export AWS_ACCESS_KEY_ID="{{ access_key_id }}"
export AWS_SECRET_ACCESS_KEY="{{ secret_access_key }}"
export AWS_DEFAULT_REGION="{{ region }}"
```

#### Option C: IAM Role (for EC2/ECS/Lambda)

If running on AWS infrastructure, IAM roles are automatically used.

### Step 2: Create S3 Bucket

Create an S3 bucket for your Kirin data:

```bash
aws s3 mb s3://{{ bucket_name }} --region {{ region }}
```

Or use the AWS Console to create a bucket with appropriate permissions.

### Step 3: Create Catalog with S3

Use the S3 URL as your `root_dir`:

```python
from kirin import Catalog

# Using AWS profile
catalog = Catalog(
    root_dir="s3://{{ bucket_name }}/data",
    aws_profile="{{ aws_profile }}"
)

# Using environment variables (no profile needed)
catalog = Catalog(root_dir="s3://{{ bucket_name }}/data")

# Create a dataset
dataset = catalog.create_dataset(
    name="{{ dataset_name }}",
    description="My cloud dataset"
)
```

### Step 4: Verify S3 Setup

Test that your setup works by creating a commit:

```python
from pathlib import Path

# Create a test file
test_file = Path("test.txt")
test_file.write_text("Hello from S3!")

# Commit to dataset
commit_hash = dataset.commit(
    message="Test commit",
    add_files=[str(test_file)]
)

print(f"✅ Successfully committed to S3: {commit_hash}")
```

#### What just happened? (S3)

- Kirin authenticated with AWS using your credentials
- Created dataset metadata in S3
- Stored your file using content-addressed storage in S3
- All future operations will use S3 as the backend

## Google Cloud Storage Setup

Configure Kirin to use Google Cloud Storage as your storage backend.

### Step 1: Create Service Account

Create a service account with Storage Object Admin permissions:

```bash
# Create service account
gcloud iam service-accounts create {{ service_account_name }} \
    --display-name="Kirin Storage Service Account"

# Grant Storage Object Admin role
gcloud projects add-iam-policy-binding {{ project_id }} \
    --member="serviceAccount:{{ service_account_name }}@{{ project_id }}.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"

# Create and download key
gcloud iam service-accounts keys create {{ service_account_name }}-key.json \
    --iam-account={{ service_account_name }}@{{ project_id }}.iam.gserviceaccount.com
```

### Step 2: Create GCS Bucket

Create a GCS bucket for your Kirin data:

```bash
gsutil mb -p {{ project_id }} -l {{ region }} gs://{{ bucket_name }}
```

Or use the Google Cloud Console to create a bucket.

### Step 3: Create Catalog with GCS

Use the GCS URL as your `root_dir` and provide the service account key:

```python
from kirin import Catalog

catalog = Catalog(
    root_dir="gs://{{ bucket_name }}/data",
    gcs_token="/path/to/{{ service_account_name }}-key.json",
    gcs_project="{{ project_id }}"
)

# Create a dataset
dataset = catalog.create_dataset(
    name="{{ dataset_name }}",
    description="My cloud dataset"
)
```

#### Alternative: Application Default Credentials

If you're running on Google Cloud infrastructure (Compute Engine, Cloud
Run, etc.), you can use Application Default Credentials:

```python
# No token needed - uses default credentials
catalog = Catalog(
    root_dir="gs://{{ bucket_name }}/data",
    gcs_project="{{ project_id }}"
)
```

### Step 4: Verify GCS Setup

Test that your setup works:

```python
from pathlib import Path

# Create a test file
test_file = Path("test.txt")
test_file.write_text("Hello from GCS!")

# Commit to dataset
commit_hash = dataset.commit(
    message="Test commit",
    add_files=[str(test_file)]
)

print(f"✅ Successfully committed to GCS: {commit_hash}")
```

#### What just happened? (GCS)

- Kirin authenticated with GCS using your service account
- Created dataset metadata in GCS
- Stored your file using content-addressed storage in GCS
- All future operations will use GCS as the backend

## Azure Blob Storage Setup

Configure Kirin to use Azure Blob Storage as your storage backend.

### Step 1: Create Storage Account

Create an Azure Storage Account and container:

```bash
# Create resource group
az group create --name {{ resource_group }} --location {{ location }}

# Create storage account
az storage account create \
    --name {{ storage_account_name }} \
    --resource-group {{ resource_group }} \
    --location {{ location }} \
    --sku Standard_LRS

# Create container
az storage container create \
    --name {{ container_name }} \
    --account-name {{ storage_account_name }} \
    --auth-mode login
```

### Step 2: Get Connection String

Retrieve the connection string for authentication:

```bash
az storage account show-connection-string \
    --name {{ storage_account_name }} \
    --resource-group {{ resource_group }} \
    --output tsv
```

The connection string looks like:
`DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net`

### Step 3: Create Catalog with Azure

Use the Azure URL as your `root_dir` and provide the connection string:

```python
from kirin import Catalog

catalog = Catalog(
    root_dir="az://{{ container_name }}/data",
    azure_connection_string="{{ connection_string }}"
)

# Create a dataset
dataset = catalog.create_dataset(
    name="{{ dataset_name }}",
    description="My cloud dataset"
)
```

#### Alternative: Environment Variable

You can also set the connection string as an environment variable:

```bash
export AZURE_STORAGE_CONNECTION_STRING="{{ connection_string }}"
```

Then create the catalog without the connection string parameter:

```python
catalog = Catalog(root_dir="az://{{ container_name }}/data")
```

### Step 4: Verify Azure Setup

Test that your setup works:

```python
from pathlib import Path

# Create a test file
test_file = Path("test.txt")
test_file.write_text("Hello from Azure!")

# Commit to dataset
commit_hash = dataset.commit(
    message="Test commit",
    add_files=[str(test_file)]
)

print(f"✅ Successfully committed to Azure: {commit_hash}")
```

#### What just happened? (Azure)

- Kirin authenticated with Azure using your connection string
- Created dataset metadata in Azure Blob Storage
- Stored your file using content-addressed storage in Azure
- All future operations will use Azure as the backend

## Next Steps

Now that you have cloud storage configured, you can:

- Create multiple datasets in your catalog
- Commit files to version control your data
- Access files from anywhere using the same API
- Use cloud storage for production workflows

See the [Cloud Storage Overview](../tutorials/cloud-storage.md) tutorial
for more details on working with remote files.
