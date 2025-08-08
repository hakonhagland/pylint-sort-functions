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

## Links

- **PyPI Package**: [pylint-sort-functions](https://pypi.org/project/pylint-sort-functions/)
- **GitHub Repository**: [pylint-sort-functions](https://github.com/hakonhagland/pylint-sort-functions)
- **Issue Tracker**: [GitHub Issues](https://github.com/hakonhagland/pylint-sort-functions/issues)
