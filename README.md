# pylint-sort-functions

A PyLint plugin that enforces alphabetical sorting of functions and methods within Python classes and modules.

## Features

- **Function Organization**: Enforces alphabetical sorting of functions within modules
- **Method Organization**: Enforces alphabetical sorting of methods within classes
- **Public/Private Separation**: Ensures public functions/methods come before private ones (underscore prefix)
- **Configurable Rules**: Customizable message codes (W9001-W9003) for different violations
- **Clear Error Messages**: Helpful messages indicating exactly what needs to be reordered

## Installation

```bash
pip install pylint-sort-functions
```

## Usage

### Enable the Plugin

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

## Warning

⚠️ **This project is currently under active development and not ready for production use.**

Key limitations:
- Many core features are still being implemented
- More unit tests need to be added
- Documentation is incomplete
- APIs and functionality may change significantly

Please check back later for a stable release.

## Documentation

See [hakonhagland.github.io/pylint-sort-functions](https://hakonhagland.github.io/pylint-sort-functions)

## PyPI

See [pylint-sort-functions](https://pypi.org/project/pylint-sort-functions/)
