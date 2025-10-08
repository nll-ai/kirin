# Kirin Documentation

Welcome to the Kirin documentation! Kirin is a content-addressed storage system
for data versioning that provides Git-like workflows for datasets.

## Quickstart

### Install from source

```bash
pip install git@github.com:ericmjl/kirin
```

### Build and preview docs

```bash
mkdocs serve
```

## Documentation

### Architecture & Design

- [Design Document](./design.md) - Overall system architecture and design goals
- [API Documentation](./api.md) - Programmatic API reference
- [Branching Guide](./branching.md) - Git-like branching and merging workflows

### Technical Decisions

- [HashFS Evaluation](./hashfs-evaluation.md) - Detailed analysis of HashFS
  integration
- [Ecosystem Due Diligence](./ecosystem-diligence.md) - Evaluation of
  third-party libraries
- [ADR: HashFS Integration](./adr-hashfs-evaluation.md) - Architectural decision
  record

### Cloud Storage

- [Cloud Storage Authentication](./cloud-storage-auth.md) - Setting up cloud backends

## Why Kirin Exists

Kirin addresses critical needs in machine learning and data science workflows:

- **Data Versioning**: Track changes to datasets with Git-like commits and branches
- **Content-Addressed Storage**: Ensure data integrity and enable deduplication
- **Multi-Backend Support**: Work with S3, GCS, Azure, local filesystem, and more
- **Serverless Architecture**: No dedicated servers required
- **Usage Tracking**: Monitor data access and lineage
- **Clean API**: Both programmatic and CLI interfaces

## Key Benefits

- **Git-like workflows for data**: Familiar version control concepts for datasets
- **Backend-agnostic**: Works with any storage backend via fsspec
- **Automatic deduplication**: Identical files stored once, saving space
- **Metadata tracking**: Complete audit trail of data usage and changes
- **Performance optimized**: Streaming operations for large files
- **Extensible**: Easy to add new backends and features
