# Installation

Choose the installation method that best fits your use case.

## Option 1: Pixi (Recommended for Development)

Best for contributors and developers who want the full development environment.

```bash
# Clone and install
git clone git@github.com:nll-ai/kirin
cd kirin
pixi install

# Set up SSL certificates for cloud storage (one-time setup)
pixi run setup-ssl

# Start the web UI
pixi run kirin ui
```

**Benefits:**

- Full development environment with all dependencies
- Easy to contribute to the project
- Includes testing and development tools

## Option 2: UV Tool (Recommended for Production)

Best for users who want a clean, isolated installation.

```bash
# Install with uv
uv tool install kirin

# Set up SSL certificates (one-time setup)
uv run python -m kirin.setup_ssl

# Start the web UI
uv run kirin ui
```

**Benefits:**

- Clean, isolated installation
- Easy to update and manage
- No system Python conflicts

## Option 3: UVX (One-time Use)

Best for trying out Kirin without permanent installation.

```bash
# Run directly with uvx
uvx kirin ui

# If SSL issues occur, set up certificates
uvx python -m kirin.setup_ssl
```

**Benefits:**

- No permanent installation
- Always uses latest version
- Good for experimentation

## SSL Certificate Setup

When using isolated Python environments (pixi, uv, conda), SSL certificates
are not automatically available. This affects HTTPS connections to cloud
storage providers.

### Automatic Setup (Recommended)

```bash
# Works with any Python environment - detects automatically
python -m kirin.setup_ssl
```

### Manual Setup (if automatic setup fails)

```bash
# The automatic setup script handles this automatically
# But if you need to do it manually, use the Python executable path:
python -c "import sys; print('Python path:', sys.executable)"
# Then create ssl directory next to that path and copy certificates
```

## Verification

Test your installation:

```bash
# Check if Kirin is installed
python -c "import kirin; print('Kirin version:', kirin.__version__)"

# Test HTTPS connection
python -c "import requests; r = requests.get('https://storage.googleapis.com'); \
print('HTTPS works:', r.status_code)"

# Or use the automatic setup
python -m kirin.setup_ssl
```

## Troubleshooting

### SSL Certificate Issues

If you get SSL errors when connecting to cloud storage:

1. **Run the SSL setup**: `python -m kirin.setup_ssl`
2. **Check your Python environment**: Make sure you're using the right Python
3. **Verify cloud credentials**: Ensure your cloud authentication is set up correctly

### Import Errors

If you get import errors:

1. **Check your Python environment**: Make sure you're using the right Python
2. **Verify installation**: Run `python -c "import kirin"`
3. **Check dependencies**: Ensure all required packages are installed

### Cloud Authentication Issues

If you have trouble with cloud storage:

1. **See the [Cloud Storage Guide](../guides/cloud-storage.md)** for detailed setup
2. **Check your credentials**: Verify AWS profiles, GCS tokens, etc.
3. **Test connectivity**: Try a simple cloud operation first

## Development Setup

If you want to contribute to Kirin:

```bash
# Clone the repository
git clone git@github.com:nll-ai/kirin
cd kirin

# Install with pixi
pixi install

# Set up SSL certificates
pixi run setup-ssl

# Run tests
pixi run -e tests pytest

# Start development server
pixi run kirin ui
```

## Next Steps

- **[Core Concepts](core-concepts.md)** - Understanding how Kirin works
- **[Quickstart](quickstart.md)** - Get started with your first dataset
- **[Cloud Storage Guide](../guides/cloud-storage.md)** - Set up cloud storage
