Release Management
==================

This document describes the automated release workflow for pylint-sort-functions.

Overview
--------

The project includes comprehensive automation for:

* **Continuous changelog management** - Update CHANGELOG.md as you develop
* **Automated releases** - Single command handles version bumping, PyPI publishing, and GitHub releases
* **Safe commit workflow** - Prevents losing commit messages due to pre-commit hook modifications

Changelog Management
--------------------

During Development
~~~~~~~~~~~~~~~~~~

Add changelog entries continuously as you work, not just at release time:

.. code-block:: bash

   # Add a bug fix entry
   make changelog-add TYPE='fixed' MESSAGE='Memory leak in parser'

   # Add a feature with PR reference
   make changelog-add TYPE='added' MESSAGE='Dark mode support' PR=45 ISSUE=12

   # Add a breaking change
   make changelog-add TYPE='changed' MESSAGE='API redesign' BREAKING=1

Valid entry types follow Keep a Changelog standard:

* ``added`` - New features
* ``changed`` - Changes in existing functionality
* ``deprecated`` - Soon-to-be removed features
* ``removed`` - Now removed features
* ``fixed`` - Bug fixes
* ``security`` - Security vulnerabilities

Scripts
~~~~~~~

The changelog management system includes three scripts:

**add-changelog-entry.py**
   Adds entries to the ``[Unreleased]`` section of CHANGELOG.md

**prepare-release-changelog.py**
   Moves ``[Unreleased]`` entries to a versioned section during release

**validate-changelog.py**
   Validates CHANGELOG.md format according to Keep a Changelog standards

Release Process
---------------

Local Release (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use the integrated Makefile targets for releases:

.. code-block:: bash

   # Patch release (1.0.0 → 1.0.1) for bug fixes
   make publish-to-pypi

   # Minor release (1.0.0 → 1.1.0) for new features
   make publish-to-pypi-minor

   # Major release (1.0.0 → 2.0.0) for breaking changes
   make publish-to-pypi-major

These commands automatically:

1. **Prepare changelog** - Move ``[Unreleased]`` entries to versioned section
2. **Bump version** - Update version in ``pyproject.toml``
3. **Build package** - Create distribution artifacts
4. **Upload to PyPI** - Publish the new version
5. **Create git tag** - Tag the release and push to GitHub
6. **Trigger GitHub release** - Tag push triggers GitHub Actions

GitHub Actions Automation
~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``.github/workflows/release.yml`` workflow provides multiple trigger methods:

**Tag Push (Primary)**
   When local release creates and pushes a tag, GitHub Actions automatically creates a GitHub release with artifacts

**Manual Dispatch**
   Use GitHub Actions UI to trigger test releases to Test PyPI

**GitHub Release UI**
   Creating a release through GitHub web interface can trigger PyPI publication

Token Configuration
~~~~~~~~~~~~~~~~~~~~

For GitHub Actions to publish to PyPI, configure repository secrets:

1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Add ``PYPI_API_TOKEN`` with your PyPI API token
3. Optionally add ``TEST_PYPI_API_TOKEN`` for testing

Version Management
------------------

Manual Version Bumping
~~~~~~~~~~~~~~~~~~~~~~~

For testing version changes without releasing:

.. code-block:: bash

   # Test version bump (dry run)
   python scripts/bump-version.py --dry-run patch

   # Actual version bump with git commit
   python scripts/bump-version.py patch

   # Version bump without git commit
   python scripts/bump-version.py --no-commit patch


Best Practices
--------------

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Make changes** to code
2. **Add changelog entry** for user-facing changes:

   .. code-block:: bash

      make changelog-add TYPE='fixed' MESSAGE='Your fix description'

3. **Commit** with detailed message:

   .. code-block:: bash

      git commit -m 'feat: your feature description'

4. **Release when ready**:

   .. code-block:: bash

      make publish-to-pypi

Release Checklist
~~~~~~~~~~~~~~~~~

Before releasing:

* ✅ All tests pass: ``make test``
* ✅ Code quality checks pass: ``make pre-commit``
* ✅ Changelog has unreleased entries
* ✅ Version bump is appropriate (patch/minor/major)

The release automation handles:

* ✅ Moving changelog entries to versioned section
* ✅ Version bumping in ``pyproject.toml``
* ✅ Building and uploading to PyPI
* ✅ Creating and pushing git tags
* ✅ Triggering GitHub release creation

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**"Pre-commit checks made changes"**
   Pre-commit hooks modified files. Stage the changes and commit:

   .. code-block:: bash

      git add -A
      git commit -m 'Your message'

**"Version mismatch between tag and project"**
   GitHub Actions detected that the git tag doesn't match pyproject.toml version. Ensure you're using the automated release process.

**"PyPI upload failed - version already exists"**
   The version already exists on PyPI. You cannot re-upload the same version. Bump to a new version.

Manual Recovery
~~~~~~~~~~~~~~~

If the automated process fails partway through:

.. code-block:: bash

   # Check current state
   git status
   git log --oneline -5

   # If version was bumped but not tagged:
   VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
   git tag -a "v$VERSION" -m "Release v$VERSION"
   git push origin "v$VERSION"

   # If PyPI upload failed but tag exists, manual upload:
   uv build
   twine upload dist/*
