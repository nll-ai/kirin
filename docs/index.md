# Kirin Documentation

Welcome to the Kirin documentation! Kirin is a simplified content-addressed storage
system
for data versioning that provides linear commit history for datasets.

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

- **Linear Data Versioning**: Track changes to datasets with simple, linear commits
- **Content-Addressed Storage**: Ensure data integrity and enable deduplication
- **Multi-Backend Support**: Work with S3, GCS, Azure, local filesystem, and more
- **Serverless Architecture**: No dedicated servers required
- **Ergonomic Python API**: Focus on ease of use and developer experience
- **File Versioning**: Track changes to individual files over time

## Key Benefits

- **Simplified workflows**: Linear commit history without branching complexity
- **Backend-agnostic**: Works with any storage backend via fsspec
- **Automatic deduplication**: Identical files stored once, saving space
- **Content integrity**: Files stored by content hash for data integrity
- **Performance optimized**: Streaming operations for large files
- **Extensible**: Easy to add new backends and features
