Introduction
============

``pylint-sort-functions`` is a PyLint plugin that enforces organized sorting of functions and methods within Python classes and modules. It supports both traditional binary public/private sorting and advanced multi-category organization with framework-specific presets for pytest, unittest, and PyQt applications.

Features
--------

* **Multi-Category Method Organization**: Framework-aware method categorization beyond binary public/private (Phase 1)
* **Framework Presets**: Built-in configurations for pytest, unittest, and PyQt frameworks
* **Custom Categorization**: JSON-configurable method categories with pattern matching and priority resolution
* **Functional Section Headers**: Validated section headers that enforce organizational structure (Phase 2)
* **Traditional Binary Sorting**: Classic public/private alphabetical organization (backward compatible)
* **Privacy Detection**: Identifies functions that should be private/public based on cross-module usage analysis
* **Automatic Fixing**: CLI tool for automatically fixing function order and privacy violations
* **Comprehensive Message Codes**: Eight message types (W9001-W9008) covering all organizational violations
* **Advanced Configuration**: Public API patterns, privacy detection settings, and decorator exclusions
* **Clear Error Messages**: Detailed messages with line numbers indicating exactly what needs to be reorganized

Installation
------------

**Development Dependencies (Recommended)**

Add to your project's development dependencies for consistent team usage:

.. code-block:: toml

    # pyproject.toml
    [tool.uv.dev-dependencies]
    pylint-sort-functions = ">=1.0.0"
    pylint = ">=3.3.0"

.. code-block:: toml

    # Poetry
    [tool.poetry.group.dev.dependencies]
    pylint-sort-functions = "^1.0.0"

**Direct Installation**

Install from PyPI:

.. code-block:: bash

   pip install pylint-sort-functions

Quick Start
-----------

Enable the plugin in your pylint configuration:

.. code-block:: bash

   pylint --load-plugins=pylint_sort_functions your_module.py

Or add to your ``.pylintrc`` file:

.. code-block:: ini

   [MASTER]
   load-plugins = pylint_sort_functions

Message Codes
-------------

The plugin defines these message types:

* **W9001**: ``unsorted-functions`` - Functions not sorted alphabetically within their scope
* **W9002**: ``unsorted-methods`` - Class methods not sorted alphabetically within their scope
* **W9003**: ``mixed-function-visibility`` - Public and private functions not properly separated
* **W9004**: ``function-should-be-private`` - Function should be private (prefix with underscore)
* **W9005**: ``function-should-be-public`` - Private function should be public (remove underscore prefix)

Advanced Configuration
----------------------

The plugin supports advanced configuration options:

**Using pyproject.toml**:

.. code-block:: toml

    [tool.pylint.function-sort]
    public-api-patterns = ["main", "run", "setup", "teardown"]
    enable-privacy-detection = true

**Using .pylintrc**:

.. code-block:: ini

    [function-sort]
    public-api-patterns = main,run,setup,teardown
    enable-privacy-detection = yes

**Configuration Options**:

* ``public-api-patterns``: Function names to always treat as public API
* ``enable-privacy-detection``: Enable cross-module usage analysis for privacy detection
