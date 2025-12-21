# Migrate build system from setuptools to hatchling

## Goal

Migrate the project's build system from setuptools to hatchling for
modernization and improved maintainability.

## Current State

The project currently uses setuptools as the build backend:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

Package configuration is defined in `[tool.setuptools]` sections.

## Proposed Changes

1. **Update build system configuration**:
   - Change `build-backend` from `setuptools.build_meta` to `hatchling.build`
   - Update `requires` to include `hatchling`

2. **Migrate package configuration**:
   - Convert `[tool.setuptools]` configuration to
     `[tool.hatch.build.targets.wheel]` format
   - Migrate package data configuration (`kirin.widgets` and `kirin.web` static assets)
   - Ensure all package discovery and data inclusion works correctly

3. **Update documentation**:
   - Remove setuptools references from comments/docs
   - Update any build-related documentation

## Benefits

- **Modern build system**: Hatchling is the recommended modern build backend
- **Simpler configuration**: More intuitive `pyproject.toml` structure
- **Better tooling**: Improved integration with modern Python packaging tools
- **Future-proof**: Aligns with Python packaging best practices

## Acceptance Criteria

- [ ] Build system migrated to hatchling
- [ ] All package data (widgets assets, web templates/static files) properly included
- [ ] Package builds successfully with `pip install -e .`
- [ ] Package builds successfully for distribution (`pip build` or equivalent)
- [ ] All existing functionality works (no regressions)
- [ ] Documentation updated to reflect new build system
- [ ] Tests pass with new build system

## Notes

- This is a modernization effort - no functional changes expected
- Should maintain backward compatibility with existing package structure
- May need to verify pixi integration still works correctly after migration
