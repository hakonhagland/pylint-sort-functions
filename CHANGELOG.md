# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.1] - 2025-08-08

### Changed

- Consolidated publish-to-pypi Makefile targets with robust safe-commit workflow
## [1.2.0] - 2025-08-08

### Changed

- README.md comprehensive documentation alignment with current feature set
## [1.1.0] - 2025-08-08

### Added

- Automated changelog management with Make targets for continuous updates
- GitHub Actions workflow for automated PyPI releases on tag push
- Decorator exclusion support for framework-specific sorting (Flask, Click, FastAPI, Django)
- Configurable section header detection patterns for function organization
- Automatic section header insertion during auto-fix (adds # Public/Private comments)
- Safe commit workflow to prevent commit message loss from pre-commit hooks
- Docker-based documentation validation system for quality assurance
- Comprehensive release management documentation (docs/release.rst)
- Claude Code specific guidelines documentation (docs/claude.rst)
- Auto-syncing CHANGELOG.md content in Sphinx documentation

### Fixed

- Section header displacement during function sorting
- GitHub Actions integration test exit code failures
- Pre-commit hook failures in CI/CD pipeline
- Tox configuration for proper package installation
- Documentation accuracy issues in pylintrc.rst

### Changed

- Enhanced auto-fix tool with section header detection and preservation
- Improved tox.ini with quality checks and proper uv integration
- Modernized installation and configuration documentation

## [1.0.0] - 2025-08-06

### Added
- **Complete PyLint plugin** for enforcing alphabetical function and method sorting
- **Auto-fix CLI tool** (`pylint-sort-functions`) for automatically reordering code
- **Comment preservation** - comments move with their associated functions during sorting
- **Class method sorting** in addition to module-level function sorting
- **Framework integration** with decorator exclusions for Flask, Click, FastAPI, Django
- **Configurable privacy detection** with customizable public API patterns
- **Performance optimizations** with intelligent caching (146x speedup for import analysis)
- **Cross-platform support** for Linux, macOS, and Windows
- **Comprehensive documentation** including CLI reference, configuration guide, and algorithm details
- **100% test coverage** across all functionality
- **Enterprise-ready features** including error handling, verbose output, and backup creation

### Features
- **Message Types**:
  - `W9001`: `unsorted-functions` - Functions not sorted alphabetically
  - `W9002`: `unsorted-methods` - Class methods not sorted alphabetically
  - `W9003`: `mixed-function-visibility` - Public/private functions not properly separated
  - `W9004`: `function-should-be-private` - Function should be marked private based on usage analysis

- **Configuration Options**:
  - `public-api-patterns` - Customize which functions are always treated as public API
  - `enable-privacy-detection` - Toggle privacy detection feature

- **CLI Tool Features**:
  - Check-only mode (default) - shows help and guidance
  - Dry-run mode (`--dry-run`) - preview changes without modification
  - Fix mode (`--fix`) - actually modify files with optional backup
  - Verbose output (`--verbose`) - detailed processing information
  - Decorator exclusions (`--ignore-decorators`) - framework-aware sorting
  - Backup control (`--no-backup`) - disable automatic backup creation

### Technical
- **Python 3.11+ support** with type hints throughout
- **Zero external dependencies** beyond PyLint and astroid
- **AST-based analysis** using astroid enhanced syntax trees
- **Import analysis** with real cross-module usage detection
- **File modification caching** for performance optimization
- **Modular architecture** designed for extensibility

### Documentation
- **Complete developer guide** (`docs/developer.rst`)
- **CLI tool reference** (`docs/cli.rst`)
- **Configuration guide** (`docs/pylintrc.rst`)
- **Sorting algorithm documentation** (`docs/sorting.rst`)
- **Usage examples** for all major frameworks
- **API reference** for plugin developers

### Quality Assurance
- **Perfect 10.00/10 PyLint score** across all source code
- **100% test coverage** with 112+ comprehensive tests
- **Pre-commit hooks** for code quality enforcement
- **Cross-platform CI/CD** testing on Linux, macOS, Windows
- **Multiple Python version support** (3.11, 3.12, 3.13)

### Performance
- **Smart caching** prevents redundant AST parsing and import analysis
- **File modification time tracking** for cache invalidation
- **Minimal memory footprint** with efficient data structures
- **Large project optimization** tested on 100+ file codebases

[1.2.1]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.2.1
[1.2.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.2.0
[1.1.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.1.0
[1.0.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.0.0
