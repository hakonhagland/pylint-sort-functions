# Scripts Directory

This directory contains automation scripts for the pylint-sort-functions project.

## Scripts

### `add-changelog-entry.py`
Adds entries to the `[Unreleased]` section of CHANGELOG.md.

Usage via Make:
```bash
make changelog-add TYPE='fixed' MESSAGE='Bug fix description'
make changelog-add TYPE='added' MESSAGE='New feature' PR=123
make changelog-add TYPE='changed' MESSAGE='Breaking change' BREAKING=1
```

### `prepare-release-changelog.py`
Prepares CHANGELOG.md for a release by moving `[Unreleased]` entries to a versioned section.
Called automatically by `make publish-to-pypi*` commands.

### `validate-changelog.py`
Validates CHANGELOG.md format according to Keep a Changelog standards.

Usage:
```bash
make changelog-validate
```

### `bump-version.py`
Increments version in pyproject.toml and creates a git commit.

Usage:
```bash
python scripts/bump-version.py patch    # 1.0.0 → 1.0.1
python scripts/bump-version.py minor    # 1.0.0 → 1.1.0
python scripts/bump-version.py major    # 1.0.0 → 2.0.0
```

### `pylint-config.sh`
Centralized PyLint configuration for consistent checking across Makefile, pre-commit, and CI.

## Release Workflow

The complete release workflow is automated:

1. **During development**: Add changelog entries as you work
   ```bash
   make changelog-add TYPE='fixed' MESSAGE='Description'
   ```

2. **To release**: Run the appropriate publish command
   ```bash
   make publish-to-pypi        # Patch release
   make publish-to-pypi-minor  # Minor release
   make publish-to-pypi-major  # Major release
   ```

   This will:
   - Move `[Unreleased]` to versioned section in CHANGELOG.md
   - Bump version in pyproject.toml
   - Build and upload to PyPI
   - Create and push git tag
   - Trigger GitHub Action for GitHub release

## GitHub Actions

The tag push triggers `.github/workflows/release.yml` which:
- Verifies the version matches the tag
- Creates a GitHub release with artifacts
- Can also be triggered manually for test releases
