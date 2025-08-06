Command Line Interface
======================

The ``pylint-sort-functions`` command-line tool provides auto-fix functionality for function
and method sorting independent of PyLint integration.

Installation
------------

The CLI tool is automatically available after installing the package:

.. code-block:: bash

   pip install pylint-sort-functions

Usage
-----

Basic Syntax
~~~~~~~~~~~~~

.. code-block:: bash

   pylint-sort-functions [options] PATHS

The tool operates on Python files or directories containing Python files.

Command Examples
~~~~~~~~~~~~~~~~

**Check files (dry-run mode):**

.. code-block:: bash

   pylint-sort-functions --dry-run src/
   pylint-sort-functions --dry-run myfile.py

**Fix files in-place:**

.. code-block:: bash

   pylint-sort-functions --fix src/
   pylint-sort-functions --fix myfile.py another_file.py

**Fix without creating backups:**

.. code-block:: bash

   pylint-sort-functions --fix --no-backup src/

**Exclude decorator patterns:**

.. code-block:: bash

   pylint-sort-functions --fix --ignore-decorators "@app.route" src/
   pylint-sort-functions --fix --ignore-decorators "@*.command" --ignore-decorators "@pytest.fixture" src/

Command-Line Options
---------------------

Positional Arguments
~~~~~~~~~~~~~~~~~~~~

``PATHS``
  One or more Python files or directories to process. Directories are searched recursively for ``.py`` files.

Optional Arguments
~~~~~~~~~~~~~~~~~~

``--fix``
  Apply auto-fix to sort functions and methods. Without this flag, the tool runs in check-only mode.

``--dry-run``
  Show what would be changed without modifying files. Useful for previewing changes.

``--no-backup``
  Do not create backup files (``.bak``) when fixing files. By default, backups are created for safety.

``--ignore-decorators PATTERN``
  Decorator patterns to ignore during sorting. Can be used multiple times. Supports wildcards.

  Examples:

  - ``@app.route`` - Exact match
  - ``@*.command`` - Wildcard match (``@main.command``, ``@cli.command``, etc.)
  - ``@pytest.fixture`` - Framework decorators

``--verbose, -v``
  Enable verbose output showing processing details.

``--help, -h``
  Show help message and exit.

Operating Modes
---------------

Check-Only Mode (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~

When run without ``--fix`` or ``--dry-run``, the tool displays usage information:

.. code-block:: bash

   $ pylint-sort-functions src/
   Note: Running in check-only mode. Use --fix or --dry-run to make changes.
   Use 'pylint-sort-functions --help' for more options.

Dry-Run Mode
~~~~~~~~~~~~

Preview changes without modifying files:

.. code-block:: bash

   $ pylint-sort-functions --dry-run src/
   Would modify: src/utils.py
   Would modify: src/models.py
   Would modify 2 of 15 files

Fix Mode
~~~~~~~~

Modify files in-place with optional backup creation:

.. code-block:: bash

   $ pylint-sort-functions --fix src/
   Modified 3 of 15 files
   Backup files created with .bak extension

Decorator Pattern Matching
---------------------------

Pattern Syntax
~~~~~~~~~~~~~~~

The ``--ignore-decorators`` option supports flexible pattern matching:

**Exact Matches:**

- ``@app.route`` matches ``@app.route`` and ``@app.route("/path")``
- ``@pytest.fixture`` matches ``@pytest.fixture`` and ``@pytest.fixture(scope="session")``

**Wildcard Patterns:**

- ``@*.command`` matches ``@main.command``, ``@cli.command``, ``@app.command``
- ``@app.*`` matches ``@app.route``, ``@app.before_request``, ``@app.errorhandler``

**Pattern Normalization:**

- Patterns are automatically prefixed with ``@`` if not present
- Parentheses are ignored for matching (``@fixture()`` matches ``@fixture``)

Common Framework Examples
~~~~~~~~~~~~~~~~~~~~~~~~~

**Flask Applications:**

.. code-block:: bash

   pylint-sort-functions --fix --ignore-decorators "@app.route" --ignore-decorators "@app.before_request" src/

**Click CLI Applications:**

.. code-block:: bash

   pylint-sort-functions --fix --ignore-decorators "@*.command" --ignore-decorators "@*.group" src/

**Django Applications:**

.. code-block:: bash

   pylint-sort-functions --fix --ignore-decorators "@login_required" --ignore-decorators "@csrf_exempt" src/

**Pytest Test Files:**

.. code-block:: bash

   pylint-sort-functions --fix --ignore-decorators "@pytest.*" tests/

Exit Codes
-----------

The tool returns standard exit codes:

- ``0`` - Success (files processed successfully, or check-only mode)
- ``1`` - Error (invalid paths, processing failures, user interruption)

Error Handling
--------------

The CLI tool provides user-friendly error handling:

**File System Errors:**

.. code-block:: bash

   $ pylint-sort-functions --fix nonexistent_file.py
   Error: Path does not exist: /path/to/nonexistent_file.py

**Permission Errors:**

.. code-block:: bash

   $ pylint-sort-functions --fix readonly_file.py
   Error processing readonly_file.py: [Errno 13] Permission denied

**Keyboard Interruption:**

.. code-block:: bash

   $ pylint-sort-functions --fix large_project/
   Processing 1000 Python files...
   ^C
   Operation cancelled by user.

Integration with Build Systems
------------------------------

Makefile Integration
~~~~~~~~~~~~~~~~~~~~

.. code-block:: makefile

   .PHONY: format-functions
   format-functions:
   	pylint-sort-functions --fix --ignore-decorators "@app.route" src/

   .PHONY: check-functions
   check-functions:
   	pylint-sort-functions --dry-run src/

Pre-commit Integration
~~~~~~~~~~~~~~~~~~~~~~

Add to ``.pre-commit-config.yaml``:

.. code-block:: yaml

   repos:
     - repo: local
       hooks:
         - id: pylint-sort-functions
           name: Sort functions and methods
           entry: pylint-sort-functions
           args: [--fix, --ignore-decorators, "@app.route"]
           language: system
           files: \\.py$

GitHub Actions Integration
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: yaml

   name: Code Quality
   on: [push, pull_request]

   jobs:
     lint:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Set up Python
           uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - name: Install dependencies
           run: |
             pip install pylint-sort-functions
         - name: Check function sorting
           run: |
             pylint-sort-functions --dry-run src/

Performance Considerations
--------------------------

File Discovery
~~~~~~~~~~~~~~

The tool recursively searches directories for Python files while skipping common
directories that should not be processed:

- Build artifacts: ``build/``, ``dist/``, ``*.egg-info/``
- Version control: ``.git/``
- Virtual environments: ``venv/``, ``.venv/``, ``env/``, ``.env/``
- Caches: ``__pycache__/``, ``.pytest_cache/``, ``.mypy_cache/``, ``.tox/``

Processing Speed
~~~~~~~~~~~~~~~~

- **Small projects (<100 files):** Near-instantaneous processing
- **Medium projects (100-1000 files):** 1-5 seconds typical
- **Large projects (1000+ files):** May take longer due to import analysis

The import analysis feature scans the project to determine function privacy suggestions,
which scales with project size.

Backup Files
~~~~~~~~~~~~

When using ``--fix`` (default behavior), the tool creates ``.bak`` backup files:

- ``myfile.py`` → ``myfile.py.bak``
- Backups preserve original timestamps and permissions
- Use ``--no-backup`` to skip backup creation
- Clean up with: ``find . -name "*.py.bak" -delete``

Related Tools
-------------

- **PyLint Plugin:** Use ``pylint --load-plugins=pylint_sort_functions`` for linting integration
- **Configuration:** See :doc:`pylintrc` for PyLint configuration options
- **Algorithm Details:** See :doc:`sorting` for complete sorting algorithm documentation

Troubleshooting
---------------

Tool Not Found
~~~~~~~~~~~~~~~

If ``pylint-sort-functions`` command is not found after installation:

.. code-block:: bash

   # Verify installation
   pip show pylint-sort-functions

   # Check if script directory is in PATH
   python -m pip show pylint-sort-functions

   # Alternative: run as module
   python -m pylint_sort_functions.cli --help

Permission Issues
~~~~~~~~~~~~~~~~~

For files with restrictive permissions:

.. code-block:: bash

   # Make files writable
   chmod u+w src/*.py

   # Run the tool
   pylint-sort-functions --fix src/

   # Optionally restore permissions
   chmod u-w src/*.py

Large Project Performance
~~~~~~~~~~~~~~~~~~~~~~~~~

For very large projects, consider:

- Processing subdirectories individually
- Using ``--dry-run`` first to preview changes
- Running during off-peak hours for large codebases
