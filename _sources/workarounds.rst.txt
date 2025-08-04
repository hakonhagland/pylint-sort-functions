Known Issues & Workarounds
===========================

This page provides temporary solutions for known limitations while we work on permanent fixes.

.. note::
   These are temporary solutions. Permanent fixes are tracked in our `GitHub issues <https://github.com/hakonhagland/pylint-sort-functions/issues>`_.
   Check the :doc:`roadmap` for implementation timeline.

Framework Decorator Issues
--------------------------

**Issue**: `#1 <https://github.com/hakonhagland/pylint-sort-functions/issues/1>`_ - Functions with decorators that depend on other functions trigger false positives.

**Affected Frameworks**: Click, Flask, FastAPI, Celery

**Problem Example**::

    # This code works but violates sorting
    def main():
        pass

    @main.command()  # Depends on main() being defined first
    def create():
        pass

Workaround Options
~~~~~~~~~~~~~~~~~~

**1. File-level disable (recommended for now)**::

    # pylint: disable=unsorted-functions
    def main():
        pass

    @main.command()
    def create():
        pass

**2. Per-function disable**::

    def main():
        pass

    def create():  # pylint: disable=unsorted-functions
        pass

**3. Global configuration** (in ``.pylintrc``)::

    [MESSAGES CONTROL]
    disable=unsorted-functions,unsorted-methods

Test Method Ordering
--------------------

**Issue**: `#5 <https://github.com/hakonhagland/pylint-sort-functions/issues/5>`_ - Test classes with setUp/tearDown methods trigger violations.

**Problem**: Test frameworks expect conventional ordering (setUp, tearDown, then test methods), not alphabetical.

**Workaround**::

    class TestExample:  # pylint: disable=unsorted-methods
        def setUp(self):
            pass

        def tearDown(self):
            pass

        def test_create(self):
            pass

Magic Methods (__init__, __str__, etc.)
---------------------------------------

**Issue**: Magic methods should follow conventional ordering, not alphabetical.

**Problem**: Classes with magic methods get flagged incorrectly.

**Workaround**::

    class MyClass:  # pylint: disable=unsorted-methods
        def __init__(self):
            pass

        def __str__(self):
            pass

        def my_method(self):
            pass

Bulk Violations
---------------

**Issue**: `#4 <https://github.com/hakonhagland/pylint-sort-functions/issues/4>`_ - Many files need manual reordering.

**Problem**: Manually fixing 30+ files is time-consuming and error-prone.

Temporary Strategy
~~~~~~~~~~~~~~~~~~

1. **Prioritize by impact**: Fix public API modules first
2. **Use selective disabling**: Disable on complex files, enable on simple ones
3. **Gradual adoption**: Enable on new files only

**Configuration Example**::

    # In .pylintrc - disable by default, enable selectively
    [MESSAGES CONTROL]
    disable=unsorted-functions,unsorted-methods

    # Then in specific files where you want enforcement:
    # pylint: enable=unsorted-functions,unsorted-methods

Getting Better Error Messages
------------------------------

**Issue**: `#2 <https://github.com/hakonhagland/pylint-sort-functions/issues/2>`_ - Current messages don't show expected order.

**Problem**: Messages like "Functions are not sorted alphabetically" aren't actionable.

Manual Debugging
~~~~~~~~~~~~~~~~~

Until enhanced error messages are implemented::

    # Get function names in current order
    grep -n "^def " myfile.py

    # Sort them to see expected order
    grep "^def " myfile.py | sort

Project-Wide Configuration
--------------------------

**Issue**: `#3 <https://github.com/hakonhagland/pylint-sort-functions/issues/3>`_ - No pyproject.toml support yet.

**Current Solution**: Use ``.pylintrc`` for now::

    [MESSAGES CONTROL]
    # Disable where not suitable
    disable=unsorted-functions,unsorted-methods

    [TOOL:pylint-sort-functions]
    # Future configuration will go here

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

Configuration Templates
-----------------------

**For Click Applications**::

    # At top of main CLI file
    # pylint: disable=unsorted-functions

    import click

    @click.group()
    def main():
        pass

    @main.command()
    def create():
        pass

**For Flask Applications**::

    # At top of app.py
    # pylint: disable=unsorted-functions

    from flask import Flask
    app = Flask(__name__)

    @app.route('/')
    def index():
        return 'Hello World'

**For Test Files**::

    # At top of test files
    # pylint: disable=unsorted-methods

    import unittest

    class TestMyClass(unittest.TestCase):
        def setUp(self):
            pass

        def test_something(self):
            pass

Getting Help
------------

If you encounter issues not covered here:

1. Check our `GitHub issues <https://github.com/hakonhagland/pylint-sort-functions/issues>`_
2. Create a new issue with a minimal reproduction case
3. Include your configuration files and Python version
4. Mention which frameworks you're using

The plugin is actively developed and we prioritize fixes based on user feedback!
