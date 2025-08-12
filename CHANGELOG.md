# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.0] - 2025-08-12

### Added

- Complete Phase 1 implementation with dogfooding success - enhanced privacy analysis and detection system
- Complete Phase 2 Test File Update System - automatic test file import and mock pattern updates for privacy fixes ([#28](https://github.com/hakonhagland/pylint-sort-functions/issues/28))
- Flexible method categorization system supporting multi-category organization beyond simple public/private separation
- Comprehensive TOML validation system for RST documentation code blocks
- Fast test targets for optimized development workflow with coverage exclusions

### Changed

- Complete modularization of privacy_fixer.py - transform monolithic 1119-line file into focused single-responsibility modules ([#32](https://github.com/hakonhagland/pylint-sort-functions/issues/32))
- Break down complex _handle_privacy_fixing() function into focused helper methods for better maintainability ([#31](https://github.com/hakonhagland/pylint-sort-functions/issues/31))
- Centralized coverage configuration with single source of truth for consistent testing
- Split utils.py and test modules into focused single-responsibility modules for better maintainability ([#37](https://github.com/hakonhagland/pylint-sort-functions/pull/37))
- Optimized pre-commit hooks for faster development workflow with improved performance

### Fixed

- Resolve all pylint warnings to achieve perfect 10.00/10 code quality scores for both source and test files
- Integration test failures and method categorization test issues ([#47](https://github.com/hakonhagland/pylint-sort-functions/pull/47))
## [1.3.2] - 2025-08-10

### Fixed

- Improved test file detection in privacy analysis to properly exclude test files (issue #26) ([#26](https://github.com/hakonhagland/pylint-sort-functions/issues/26))
## [1.3.1] - 2025-08-09

### Fixed

- **CRITICAL:** Auto-sort syntax corruption on complex class hierarchies (GitHub issue #25)
  - Fixed multi-class processing that caused class definitions to be lost
  - Added mandatory syntax validation with automatic rollback to prevent data loss
  - Enhanced method extraction to preserve class boundaries
  - Added comprehensive test coverage for complex class scenarios
- Auto-sort now processes classes in reverse order to preserve line number integrity
- Syntax errors during auto-sort transformation now trigger automatic rollback to original content

## [1.3.0] - 2025-08-09

### Added

- Cross-module import analysis for enhanced privacy detection accuracy
- PrivacyFixer.detect_privacy_violations() API method for programmatic privacy analysis
- W9005 message type for detecting private functions that should be public

### Changed

- Standardize testing infrastructure from unittest to pytest format
- Update all testing documentation to reflect new test structure and integration tests
- Integration test suite achieves 100% success rate with all 19 tests passing

### Fixed

- Test coverage now focuses on source code only, excluding test files from coverage measurement for more meaningful metrics ([#18](https://github.com/hakonhagland/pylint-sort-functions/issues/18))

## [1.2.1] - 2025-08-08

### Added

- **Privacy Fixer System** - Comprehensive automatic function renaming for privacy violations
  - **W9004 Detection**: Identifies public functions that should be private (add underscore prefix)
  - **W9005 Detection**: Identifies private functions that should be public (remove underscore prefix)
  - **Bidirectional Analysis**: Complete privacy analysis in both directions with mutually exclusive detection
  - **Conservative Safety Validation**: Multiple validation layers ensure safe renaming operations
  - **Comprehensive Reference Detection**: Finds function calls, assignments, decorators using AST traversal
  - **Dynamic Reference Detection**: Prevents unsafe renaming of functions used with getattr, eval, exec
  - **String Literal Scanning**: Detects function names in string literals to prevent breaking references
  - **Name Conflict Prevention**: Validates no conflicts with existing function names
  - **Automatic Backup Creation**: Creates .bak files before applying changes for safety

- **CLI Integration** - Complete command-line interface for privacy fixing
  - `--fix-privacy` - Apply automatic privacy fixes with safety validation
  - `--privacy-dry-run` - Preview privacy fixes without applying changes
  - `--auto-sort` - Automatically resort functions after privacy fixes for integrated workflow

- **Advanced AST-Based Sorting** - Improved function sorting with proper boundary detection
  - **AST Boundary Detection**: Accurate detection of function boundaries using Abstract Syntax Tree analysis
  - **Main Block Preservation**: Correctly handles `if __name__ == "__main__":` blocks at end of files
  - **Complex Construct Support**: Proper sorting around classes, global variables, imports, and docstrings
  - **Module Structure Preservation**: Maintains proper Python module organization during sorting

- **Integration Test Infrastructure** - End-to-end validation of privacy fixing workflows
  - **Docker-based Testing**: Complete validation environment for privacy fixer functionality
  - **CLI Integration Tests**: Validates command-line interface with real file processing
  - **Multi-framework Compatibility**: Tests privacy detection with Flask, Django, FastAPI, Click patterns

### Enhanced

- **PyLint Plugin** - Extended with bidirectional privacy detection
  - Added W9005 message type for private functions that should be public
  - Mutually exclusive W9004/W9005 detection prevents conflicting suggestions
  - Enhanced configuration options for privacy detection patterns
  - Improved error handling and edge case coverage

- **Documentation System** - Comprehensive updates across all documentation files
  - **Privacy Fixer Architecture** (docs/privacy.rst) - Complete technical implementation details
  - **Bidirectional Detection Examples** - W9004 and W9005 usage patterns and troubleshooting
  - **Advanced Sorting Algorithm** (docs/sorting.rst) - AST-based boundary detection documentation
  - **CLI Reference** (docs/cli.rst) - Complete privacy fixer command-line documentation
  - **User Guide** (docs/usage.rst) - Enhanced with bidirectional privacy detection guidance

- **Test Coverage** - Expanded to maintain 100% coverage with new features
  - **22+ Privacy Fixer Tests** - Comprehensive unit and integration test coverage
  - **W9005 Detection Tests** - Complete validation of bidirectional privacy analysis
  - **Integration Workflow Tests** - End-to-end privacy fixing + sorting workflow validation
  - **Safety Validation Tests** - Extensive coverage of all safety check scenarios

### Fixed

- **Function Boundary Detection** - Resolved auto-sort issues with complex Python constructs
  - Fixed `if __name__ == "__main__":` block displacement during function sorting
  - Eliminated hardcoded pattern matching in favor of AST-based boundary analysis
  - Improved handling of module-level docstrings, comments, and complex syntax

- **Reference Detection Edge Cases** - Enhanced AST traversal for comprehensive reference finding
  - Prevents double-counting of decorator nodes during AST traversal
  - Handles complex nested scopes and function definitions correctly
  - Improved detection of assignment references and function call patterns

### Technical Improvements

- **Architecture Enhancement** - Modular privacy fixer system with extensible design
  - FunctionReference, RenameCandidate, and PrivacyFixer classes for clean separation of concerns
  - Comprehensive error handling with graceful degradation for edge cases
  - Performance optimizations for large project analysis with intelligent caching

- **Safety-First Design** - Multiple validation layers prioritize correctness over completeness
  - Conservative approach: skips functions rather than risk incorrect renaming
  - Atomic operations with rollback support for failed rename attempts
  - Extensive logging and reporting for transparency in automated decisions

### Performance

- **Enhanced Import Analysis** - Improved cross-module usage detection for privacy analysis
  - Optimized AST parsing with caching to prevent redundant analysis
  - Intelligent file filtering to skip test files and generated code
  - Memory-efficient data structures for large project processing

### Workflow Integration

- **Integrated Privacy + Sorting** - Seamless workflow combining privacy fixes with function sorting
  - Privacy fixes applied first, followed by automatic alphabetical sorting
  - Consistent backup creation across all automated operations
  - Unified CLI interface for streamlined developer experience

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

[1.4.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.4.0
[1.3.2]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.3.2
[1.3.1]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.3.1
[1.3.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.3.0
[1.2.1]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.2.1
[1.2.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.2.0
[1.1.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.1.0
[1.0.0]: https://github.com/hakonhagland/pylint-sort-functions/releases/tag/v1.0.0
