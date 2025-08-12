# pylint-sort-functions

A PyLint plugin that enforces alphabetical sorting of functions and methods within Python classes and modules, helping maintain consistent and predictable code organization.

## Features

- **Function Organization**: Enforces alphabetical sorting of functions within modules
- **Method Organization**: Enforces alphabetical sorting of methods within classes
- **Public/Private Separation**: Ensures public functions/methods come before private ones (underscore prefix)
- **Auto-fix Capability**: Automatically reorder functions and methods with the included CLI tool
- **Comment Preservation**: Comments move with their associated functions during sorting
- **Framework Integration**: Supports decorator exclusions for Flask, Click, FastAPI, Django
- **Performance Optimized**: Intelligent caching for large projects (100+ files)
- **Configurable Privacy Detection**: Customizable patterns for public API identification
- **Enterprise Ready**: 100% test coverage, comprehensive documentation

## Installation

### For Modern Python Projects (Recommended)

Add as a development dependency:

**Using pyproject.toml**:
```toml
[tool.uv.dev-dependencies]
pylint-sort-functions = ">=1.0.0"
pylint = ">=3.3.0"
```

**Using Poetry**:
```toml
[tool.poetry.group.dev.dependencies]
pylint-sort-functions = "^1.0.0"
pylint = "^3.3.0"
```

Then install:
```bash
uv sync          # or poetry install
```

### Traditional Installation
```bash
pip install pylint-sort-functions
```

## Quick Start

### 1. Enable the Plugin

Add the plugin to your pylint configuration:

```bash
pylint --load-plugins=pylint_sort_functions your_module.py
```

Or add to your `.pylintrc` file:

```ini
[MASTER]
load-plugins = pylint_sort_functions
```

Or in `pyproject.toml`:

```toml
[tool.pylint.MASTER]
load-plugins = ["pylint_sort_functions"]
```

### 2. Auto-fix Violations

The CLI tool offers multiple modes for function reordering:

```bash
# Check what would be changed (dry-run)
pylint-sort-functions --dry-run path/to/file.py

# Fix single file with backup
pylint-sort-functions --fix path/to/file.py

# Fix directory without backup
pylint-sort-functions --fix --no-backup src/

# Add section headers for better organization
pylint-sort-functions --fix --add-section-headers src/

# Exclude framework decorators from sorting
pylint-sort-functions --fix --ignore-decorators "@app.route" src/
```

### Example

**❌ Bad (will trigger warnings):**
```python
class MyClass:
    def public_method_b(self):
        pass

    def _private_method_a(self):
        pass

    def public_method_a(self):  # Out of order!
        pass
```

**✅ Good (follows sorting rules):**
```python
class MyClass:
    # Public methods
    def public_method_a(self):
        pass

    def public_method_b(self):
        pass

    # Private methods
    def _private_method_a(self):
        pass
```

## Message Codes

- **W9001**: `unsorted-functions` - Functions not sorted alphabetically within their scope
- **W9002**: `unsorted-methods` - Class methods not sorted alphabetically within their scope
- **W9003**: `mixed-function-visibility` - Public and private functions not properly separated
- **W9004**: `function-should-be-private` - Function should be private (prefix with underscore)

## Advanced Configuration

### Plugin Configuration

Configure the plugin through PyLint configuration:

**Using pyproject.toml** (Recommended):
```toml
[tool.pylint.MASTER]
load-plugins = ["pylint_sort_functions"]

[tool.pylint.function-sort]
public-api-patterns = ["main", "run", "execute", "start", "stop", "setup", "teardown"]
enable-privacy-detection = true
```

**Using .pylintrc**:
```ini
[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
public-api-patterns = main,run,execute,start,stop,setup,teardown
enable-privacy-detection = yes
```

### CLI Tool Options

The CLI tool supports decorator exclusions and section headers:

```bash
# Exclude framework decorators from sorting
pylint-sort-functions --fix --ignore-decorators "@app.route" --ignore-decorators "@*.command" src/

# Add custom section headers
pylint-sort-functions --fix --add-section-headers --public-header "=== PUBLIC API ===" src/
```

## Documentation

For comprehensive documentation, including:
- **CLI Reference**: Complete command-line tool documentation
- **Configuration Guide**: PyLint integration and advanced options
- **Algorithm Details**: How function sorting and privacy detection work
- **Framework Integration**: Flask, Django, FastAPI, Click examples

See [hakonhagland.github.io/pylint-sort-functions](https://hakonhagland.github.io/pylint-sort-functions)

## Development and Testing

### Running Tests

The project uses a comprehensive testing framework with both unit tests and fixture-based integration tests:

```bash
# Run all tests (unit + integration)
make test-all

# Run unit tests only (fast)
make test

# Run integration tests only  
make test-integration

# Run with coverage (enforces 100%)
make coverage

# Run specific integration test
pytest tests/integration/test_method_categorization_integration.py -v
```

### Integration Testing with Fixtures

The project includes a robust fixture-based integration testing system for end-to-end validation:

```python
# Example integration test using fixtures
def test_framework_preset_integration(
    pylint_runner, file_creator, config_writer, sample_test_class
):
    """Test pytest framework preset with proper configuration."""
    # Create test file using sample data
    file_creator("src/test_example.py", sample_test_class["pytest"])
    
    # Create configuration with required settings
    config_writer("pylintrc", """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
category-sorting = declaration
""")
    
    # Run PyLint and validate results
    returncode, stdout, stderr = pylint_runner(
        ["src/test_example.py"], 
        extra_args=["--enable=unsorted-methods"]
    )
    
    assert "unsorted-methods" not in stdout
```

### Available Testing Fixtures

- `test_project`: Creates temporary Python project structure
- `file_creator`: Factory for creating test files with content
- `config_writer`: Factory for PyLint configuration files (.pylintrc, pyproject.toml)
- `pylint_runner`: Factory for running PyLint with plugin loaded
- `cli_runner`: Factory for CLI command execution
- `sample_test_class`: Framework-specific test class templates

### Framework Preset Testing

When testing framework presets, always include the `category-sorting = declaration` setting:

```python
# Correct framework preset configuration for testing
config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest  # or unittest, pyqt
category-sorting = declaration  # Required!
"""
```

For complete development documentation, see the [Testing Guide](https://hakonhagland.github.io/pylint-sort-functions/testing.html) and [Developer Guide](https://hakonhagland.github.io/pylint-sort-functions/developer.html).

## Links

- **PyPI Package**: [pylint-sort-functions](https://pypi.org/project/pylint-sort-functions/)
- **GitHub Repository**: [pylint-sort-functions](https://github.com/hakonhagland/pylint-sort-functions)
- **Issue Tracker**: [GitHub Issues](https://github.com/hakonhagland/pylint-sort-functions/issues)
