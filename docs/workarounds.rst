Configuration & Limitations Guide
====================================

This page covers modern configuration options and current limitations with their workarounds.

.. note::
   Many previously documented issues have been resolved! This guide now focuses on current configuration best practices and remaining limitations.
   Active issues are tracked in our `GitHub issues <https://github.com/hakonhagland/pylint-sort-functions/issues>`_.

Current Status Summary
-----------------------

✅ **RESOLVED (Modern Solutions Available)**:

- Framework decorator conflicts (Click, Flask, FastAPI) - Use ``ignore-decorators`` configuration
- pyproject.toml configuration support - Fully supported via ``[tool.pylint.function-sort]``
- Bulk fixing automation - Comprehensive CLI auto-fix tool available
- Privacy detection and fixing - Built-in ``--fix-privacy`` feature

🟡 **ACTIVE LIMITATIONS (Workarounds Available)**:

- Enhanced error messages - CLI tool provides better analysis, plugin improvements planned
- Test method conventional ordering - Use class-level disables or ignore decorators
- Magic method conventional ordering - Use class-level disables

🔧 **RECOMMENDED APPROACH**: Use modern pyproject.toml configuration with selective workarounds for remaining limitations.

Framework Decorator Support
----------------------------

**Status**: ✅ **RESOLVED** - The plugin now supports decorator exclusions.

**Supported Frameworks**: Click, Flask, FastAPI, Celery, pytest, and more.

**Modern Solution**: Use ``ignore-decorators`` configuration instead of disabling the plugin.

**pyproject.toml Configuration**::

    [tool.pylint.function-sort]
    ignore-decorators = [
        "@app.route",      # Flask routes
        "@*.command",      # Click commands (wildcard support)
        "@celery.task",    # Celery tasks
        "@pytest.fixture", # pytest fixtures
    ]

**CLI Tool Integration**::

    # Auto-fix with decorator exclusions
    pylint-sort-functions --fix --ignore-decorators "@app.route" --ignore-decorators "@*.command" src/

**Example - Click Application**::

    # pyproject.toml: ignore-decorators = ["@*.command"]

    # This now works without violations:
    def main():
        pass

    @main.command()  # Excluded from sorting requirements
    def create():
        pass

Test Method Ordering
--------------------

**Status**: 🟡 **PLANNED** - `Issue #5 <https://github.com/hakonhagland/pylint-sort-functions/issues/5>`_ is still open.

**Problem**: Test frameworks expect conventional ordering (setUp, tearDown, then test methods), not alphabetical.

**Current Workarounds**:

**1. Class-level disable (recommended)**::

    class TestExample:  # pylint: disable=unsorted-methods
        def setUp(self):
            pass

        def tearDown(self):
            pass

        def test_create(self):
            pass

**2. Configure exclusions for test files**::

    # pyproject.toml
    [tool.pylint.function-sort]
    ignore-decorators = ["@pytest.fixture"]

    # Or disable in test files only:
    # At top of test_*.py files:
    # pylint: disable=unsorted-methods

**Planned Enhancement**: Future configuration option for conventional test ordering::

    [tool.pylint.function-sort]
    test-method-ordering = "conventional"  # setUp, tearDown, then alphabetical

Magic Methods (__init__, __str__, etc.)
---------------------------------------

**Status**: 🟡 **ACTIVE LIMITATION** - Magic methods currently trigger sorting violations.

**Problem**: Magic methods should follow conventional Python ordering, not alphabetical (e.g., ``__init__`` first), but the plugin currently enforces alphabetical sorting.

**Current Workaround**::

    class MyClass:  # pylint: disable=unsorted-methods
        def __init__(self):  # Convention: __init__ comes first
            pass

        def __str__(self):   # Then other magic methods
            pass

        def my_method(self):  # Then regular methods
            pass

**Alternative**: Selective class-level configuration (future enhancement)::

    # Planned feature
    [tool.pylint.function-sort]
    respect-magic-method-conventions = true

Automated Bulk Fixing
----------------------

**Status**: ✅ **RESOLVED** - Comprehensive CLI auto-fix tool available.

**Modern Solution**: Use the ``pylint-sort-functions`` CLI tool for automated bulk fixing.

**Basic Usage**::

    # Preview changes without modifying files
    pylint-sort-functions --dry-run src/

    # Apply fixes with automatic backups
    pylint-sort-functions --fix src/

    # Fix with decorator exclusions and section headers
    pylint-sort-functions --fix --ignore-decorators "@app.route" --add-section-headers src/

**Advanced Features**::

    # Privacy analysis and fixing
    pylint-sort-functions --fix-privacy --auto-sort src/

    # Custom section headers
    pylint-sort-functions --fix --add-section-headers \
        --public-header "=== Public API ===" \
        --private-header "=== Internal ===" src/

**Safety Features**:

- Automatic backup creation (disable with ``--no-backup``)
- Dry-run mode for safe previewing
- AST-based parsing preserves comments and formatting
- Integration with existing formatters (ruff, black)

Enhanced Error Messages
------------------------

**Status**: 🟡 **PLANNED** - `Issue #2 <https://github.com/hakonhagland/pylint-sort-functions/issues/2>`_ is still open.

**Current Limitation**: Messages like "Functions are not sorted alphabetically" don't show the expected order.

**Temporary Solutions**:

**1. Use CLI tool for detailed analysis**::

    # Get detailed analysis with CLI tool
    pylint-sort-functions --dry-run --verbose src/myfile.py

**2. Manual debugging**::

    # Get function names in current order
    grep -n "^def " myfile.py

    # Sort them to see expected order
    grep "^def " myfile.py | sort

**Planned Enhancement**: Future versions will show both expected and actual order::

    W9001: Functions are not sorted alphabetically in module scope
    Expected order: create, edit_config, main
    Current order: main, create, edit_config

Modern Configuration
---------------------

**pyproject.toml Support**: The plugin now supports modern configuration via ``pyproject.toml``::

    [tool.pylint.function-sort]
    ignore-decorators = ["@app.route", "@*.command", "@pytest.fixture"]
    public-api-patterns = ["^[a-zA-Z][a-zA-Z0-9_]*$"]

**Legacy .pylintrc Support**: Still supported for existing projects::

    [function-sort]
    ignore-decorators = @app.route,@*.command,@pytest.fixture
    public-api-patterns = ^[a-zA-Z][a-zA-Z0-9_]*$

Selective Enforcement Strategy
------------------------------

For large projects, consider this phased approach:

**Phase 1**: Disable globally, enable on new code::

    # .pylintrc
    [MESSAGES CONTROL]
    disable=unsorted-functions,unsorted-methods

**Phase 2**: Enable on specific modules::

    # In well-structured modules
    # pylint: enable=unsorted-functions,unsorted-methods

**Phase 3**: Gradually expand as violations are fixed

Modern Configuration Examples
-------------------------------

**pyproject.toml - Comprehensive Setup**::

    [tool.pylint.function-sort]
    # Framework support
    ignore-decorators = [
        "@app.route",         # Flask routes
        "@*.command",         # Click commands
        "@pytest.fixture",    # pytest fixtures
        "@celery.task",       # Celery tasks
        "@api.route",         # FastAPI routes
    ]

    # Privacy detection patterns
    public-api-patterns = [
        "^[a-zA-Z][a-zA-Z0-9_]*$"  # Public functions (no leading underscore)
    ]

**For Click Applications**::

    # pyproject.toml
    [tool.pylint.function-sort]
    ignore-decorators = ["@*.command", "@*.group"]

    # Now this works without violations:
    import click

    @click.group()
    def main():
        pass

    @main.command()  # Excluded from sorting
    def create():
        pass

**For Flask Applications**::

    # pyproject.toml
    [tool.pylint.function-sort]
    ignore-decorators = ["@app.route", "@app.before_request", "@app.errorhandler"]

    # Now this works without violations:
    from flask import Flask
    app = Flask(__name__)

    @app.route('/')  # Excluded from sorting
    def index():
        return 'Hello World'

**For pytest Test Files**::

    # pyproject.toml
    [tool.pylint.function-sort]
    ignore-decorators = ["@pytest.fixture", "@pytest.mark.*"]

    # Then disable methods sorting in test files:
    # At top of test_*.py:
    # pylint: disable=unsorted-methods

    import pytest

    @pytest.fixture  # Excluded from sorting
    def sample_data():
        return {"key": "value"}

    class TestExample:  # pylint: disable=unsorted-methods
        def setUp(self):
            pass

        def test_something(self):
            pass

**Legacy .pylintrc Support**::

    # Still supported for existing projects
    [function-sort]
    ignore-decorators = @app.route,@*.command,@pytest.fixture
    public-api-patterns = ^[a-zA-Z][a-zA-Z0-9_]*$

Getting Help
------------

If you encounter issues not covered here:

1. Check our `GitHub issues <https://github.com/hakonhagland/pylint-sort-functions/issues>`_
2. Create a new issue with a minimal reproduction case
3. Include your configuration files and Python version
4. Mention which frameworks you're using

The plugin is actively developed and we prioritize fixes based on user feedback!
