# Temporary Workarounds

This document provides temporary solutions for known limitations while we work on permanent fixes.

## Framework Decorator Issues (Click, Flask, etc.)

**Issue**: [#1](https://github.com/hakonhagland/pylint-sort-functions/issues/1)
Functions with decorators that depend on other functions trigger false positives.

### Workaround Options:

1. **File-level disable** (recommended for now):
   ```python
   # pylint: disable=unsorted-functions
   def main():
       pass

   @main.command()
   def create():
       pass
   ```

2. **Per-function disable**:
   ```python
   def main():
       pass

   def create():  # pylint: disable=unsorted-functions
       pass
   ```

3. **Global configuration** (in `.pylintrc`):
   ```ini
   [MESSAGES CONTROL]
   disable=unsorted-functions,unsorted-methods
   ```

## Test Method Ordering

**Issue**: [#5](https://github.com/hakonhagland/pylint-sort-functions/issues/5)
Test classes with setUp/tearDown methods trigger violations.

### Workaround:
```python
class TestExample:  # pylint: disable=unsorted-methods
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_create(self):
        pass
```

## Magic Methods (__init__, __str__, etc.)

**Issue**: Magic methods should follow conventional ordering, not alphabetical.

### Workaround:
```python
class MyClass:  # pylint: disable=unsorted-methods
    def __init__(self):
        pass

    def __str__(self):
        pass

    def my_method(self):
        pass
```

## Bulk Violations

**Issue**: [#4](https://github.com/hakonhagland/pylint-sort-functions/issues/4)
Many files need manual reordering.

### Temporary Strategy:
1. **Prioritize by impact**: Fix public API modules first
2. **Use selective disabling**: Disable on complex files, enable on simple ones
3. **Gradual adoption**: Enable on new files only

### Configuration Example:
```ini
# In .pylintrc - disable by default, enable selectively
[MESSAGES CONTROL]
disable=unsorted-functions,unsorted-methods

# Then in specific files where you want enforcement:
# pylint: enable=unsorted-functions,unsorted-methods
```

## Getting Better Error Messages

**Issue**: [#2](https://github.com/hakonhagland/pylint-sort-functions/issues/2)
Current messages don't show expected order.

### Manual Debugging:
```bash
# Get function names in current order
grep -n "^def " myfile.py

# Sort them to see expected order
grep "^def " myfile.py | sort
```

## Project-Wide Configuration

Until pyproject.toml support ([#3](https://github.com/hakonhagland/pylint-sort-functions/issues/3)) is available:

```ini
# .pylintrc
[MESSAGES CONTROL]
# Disable where not suitable
disable=unsorted-functions,unsorted-methods

[TOOL:pylint-sort-functions]
# Future configuration will go here
```

---

**Note**: These are temporary solutions. Permanent fixes are tracked in the GitHub issues linked above. Check the [ROADMAP.md](ROADMAP.md) for implementation timeline.
