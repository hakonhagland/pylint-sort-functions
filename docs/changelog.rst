Changelog
=========

This file tracks all notable changes to the pylint-sort-functions project.

The format follows `Keep a Changelog <https://keepachangelog.com/en/1.0.0/>`_
and adheres to `Semantic Versioning <https://semver.org/spec/v2.0.0.html>`_.

.. note::

   The canonical changelog is maintained in the repository root as ``CHANGELOG.md``.
   For the most up-to-date version and contribution instructions, see:

   * `CHANGELOG.md on GitHub <https://github.com/hakonhagland/pylint-sort-functions/blob/main/CHANGELOG.md>`_
   * :doc:`release` for information on adding changelog entries

Recent Releases
---------------

Unreleased Changes
~~~~~~~~~~~~~~~~~~

The following changes are in development:

* Automated changelog management with Make targets
* GitHub Actions workflow for automated PyPI releases on tag push

Version 1.0.0 (2025-01-06)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Initial stable release with complete functionality:

**Added**

* **Complete PyLint plugin** for enforcing alphabetical function and method sorting
* **Auto-fix CLI tool** (``pylint-sort-functions``) for automatically reordering code
* **Comment preservation** - comments move with their associated functions during sorting
* **Class method sorting** in addition to module-level function sorting
* **Framework integration** with decorator exclusions for Flask, Click, FastAPI, Django
* **Configurable privacy detection** with customizable public API patterns
* **Performance optimizations** with intelligent caching (146x speedup for import analysis)
* **Cross-platform support** for Linux, macOS, and Windows
* **Comprehensive documentation** including CLI reference, configuration guide, and algorithm details
* **100% test coverage** across all functionality
* **Enterprise-ready features** including error handling, verbose output, and backup creation

**Features**

Message Types:
  * ``W9001``: ``unsorted-functions`` - Functions not sorted alphabetically
  * ``W9002``: ``unsorted-methods`` - Class methods not sorted alphabetically
  * ``W9003``: ``mixed-function-visibility`` - Public/private functions not properly separated
  * ``W9004``: ``function-should-be-private`` - Function should be marked private based on usage analysis

Configuration Options:
  * ``public-api-patterns`` - Customize which functions are always treated as public API
  * ``enable-privacy-detection`` - Toggle privacy detection feature

CLI Tool Features:
  * Check-only mode (default) - shows help and guidance
  * Dry-run mode (``--dry-run``) - preview changes without modification
  * Fix mode (``--fix``) - actually modify files with optional backup
  * Verbose output (``--verbose``) - detailed processing information
  * Decorator exclusions (``--ignore-decorators``) - framework-aware sorting
  * Backup control (``--no-backup``) - disable automatic backup creation

**Technical**

* **Python 3.11+ support** with type hints throughout
* **Zero external dependencies** beyond PyLint and astroid
* **AST-based analysis** using astroid enhanced syntax trees
* **Import analysis** with real cross-module usage detection
* **File modification caching** for performance optimization
* **Modular architecture** designed for extensibility

**Quality Assurance**

* **Perfect 10.00/10 PyLint score** across all source code
* **100% test coverage** with 112+ comprehensive tests
* **Pre-commit hooks** for code quality enforcement
* **Cross-platform CI/CD** testing on Linux, macOS, Windows
* **Multiple Python version support** (3.11, 3.12, 3.13)

**Performance**

* **Smart caching** prevents redundant AST parsing and import analysis
* **File modification time tracking** for cache invalidation
* **Minimal memory footprint** with efficient data structures
* **Large project optimization** tested on 100+ file codebases

For complete details, see the `full changelog <https://github.com/hakonhagland/pylint-sort-functions/blob/main/CHANGELOG.md>`_.
