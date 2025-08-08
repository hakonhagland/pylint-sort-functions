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

Use the included CLI tool to automatically reorder functions:

```bash
pylint-sort-functions path/to/file.py  # Fix single file
pylint-sort-functions src/            # Fix entire directory
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

## Advanced Configuration

### Framework Integration

Exclude framework decorators from sorting requirements:

```ini
[tool.pylint-sort-functions]
ignore-decorators = ["@app.route", "@*.command", "@pytest.fixture"]
```

### Privacy Detection

Configure which functions are always considered public API:

```ini
[tool.pylint-sort-functions]
public-api-patterns = ["main", "run", "setup", "teardown", "handler"]
enable-privacy-detection = true
```

## Documentation

For comprehensive documentation, including:
- **CLI Reference**: Complete command-line tool documentation
- **Configuration Guide**: PyLint integration and advanced options
- **Algorithm Details**: How function sorting and privacy detection work
- **Framework Integration**: Flask, Django, FastAPI, Click examples

See [hakonhagland.github.io/pylint-sort-functions](https://hakonhagland.github.io/pylint-sort-functions)

## Links

- **PyPI Package**: [pylint-sort-functions](https://pypi.org/project/pylint-sort-functions/)
- **GitHub Repository**: [pylint-sort-functions](https://github.com/hakonhagland/pylint-sort-functions)
- **Issue Tracker**: [GitHub Issues](https://github.com/hakonhagland/pylint-sort-functions/issues)
# Test change
