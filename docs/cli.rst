Auto-Fix Tool Reference
========================

The ``pylint-sort-functions`` command-line tool provides auto-fix functionality for function
and method sorting independent of PyLint integration.

Installation
------------

The CLI tool is automatically available after installing the ``pylint-sort-functions`` package.

Development Dependency (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you're already using the PyLint plugin in your project (see :doc:`usage`), the CLI tool is automatically available:

.. code-block:: bash

   # Tool is available after plugin installation
   uv sync  # or poetry install, pip install -r requirements-dev.txt
   pylint-sort-functions --help

Global Installation
~~~~~~~~~~~~~~~~~~~

For standalone use without the PyLint plugin integration:

.. code-block:: bash

   # Install globally or in a virtual environment
   pip install pylint-sort-functions
   pylint-sort-functions --help

.. note::
   This CLI tool complements the PyLint plugin integration. For comprehensive code quality workflows, see :doc:`usage` for PyLint plugin setup, configuration options, and team integration patterns.

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

``--add-section-headers``
  Add section header comments (e.g., '# Public functions') during sorting to improve code organization.

``--public-header TEXT``
  Header text for public functions (default: '# Public functions').

``--private-header TEXT``
  Header text for private functions (default: '# Private functions').

``--public-method-header TEXT``
  Header text for public methods (default: '# Public methods').

``--private-method-header TEXT``
  Header text for private methods (default: '# Private methods').

``--additional-section-patterns PATTERN``
  Additional patterns to detect as section headers (e.g., '=== API ===' or '--- Helpers ---'). Can be used multiple times.

``--section-headers-case-sensitive``
  Make section header detection case-sensitive (default: case-insensitive).

**Privacy Fixer Options**

``--fix-privacy``
  Apply automatic function renaming for privacy fixes (functions that should be private). Uses conservative safety validation before making changes.

``--privacy-dry-run``
  Analyze and preview privacy fixes without applying changes (standalone option). Shows which functions can be safely renamed and which cannot. This option works independently and should not be combined with ``--fix-privacy``.

``--auto-sort``
  Automatically apply function sorting after privacy fixes. Only takes effect when used with ``--fix-privacy`` or ``--privacy-dry-run``.

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

.. note::
   The ``--ignore-decorators`` feature is available in both the CLI tool and the PyLint plugin. For PyLint plugin configuration, see :doc:`pylintrc` for details on setting up decorator exclusions in your project configuration.

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

Section Header Examples
~~~~~~~~~~~~~~~~~~~~~~~

**Basic Section Headers:**

.. code-block:: bash

   # Add default section headers
   pylint-sort-functions --fix --add-section-headers src/

**Custom Header Text:**

.. code-block:: bash

   # Use custom organizational style
   pylint-sort-functions --fix --add-section-headers \
       --public-header "=== PUBLIC API ===" \
       --private-header "=== INTERNAL ===" \
       src/

**Detect Existing Custom Headers:**

.. code-block:: bash

   # Preserve existing organizational patterns
   pylint-sort-functions --fix --add-section-headers \
       --additional-section-patterns "--- API ---" \
       --additional-section-patterns "*** Helpers ***" \
       src/

**Case-Sensitive Detection:**

.. code-block:: bash

   # Enable case-sensitive header detection
   pylint-sort-functions --fix --add-section-headers \
       --section-headers-case-sensitive \
       --additional-section-patterns "Public API" \
       src/

Privacy Fixer
~~~~~~~~~~~~~~

The CLI tool includes automatic privacy fixing functionality with bidirectional analysis:

- **W9004 Detection**: Rename public functions that should be private (add underscore prefix)
- **W9005 Detection**: Rename private functions that should be public (remove underscore prefix)

**Usage Examples:**

.. code-block:: bash

   # Preview privacy fixes (dry-run mode)
   pylint-sort-functions --privacy-dry-run src/

   # Apply privacy fixes with safety checks
   pylint-sort-functions --fix-privacy src/

   # Privacy fixes with automatic sorting
   pylint-sort-functions --fix-privacy --auto-sort src/

   # Preview privacy fixes AND sorting changes
   pylint-sort-functions --privacy-dry-run --auto-sort src/

**Key Features**:

- **Conservative safety validation**: Multiple validation layers ensure safe renaming
- **Comprehensive reference detection**: Finds function calls, assignments, decorators
- **Dry-run preview**: Review changes before applying them
- **Automatic backups**: Creates ``.bak`` files before modifying originals
- **Integrated sorting**: Use ``--auto-sort`` to automatically apply function sorting after privacy fixes
- **Flexible workflow**: Use privacy fixes alone or combined with automatic sorting

**Safety Checks**:

- Validates no name conflicts with existing private functions
- Ensures all references can be safely renamed
- Detects dynamic references (``getattr``, ``hasattr``) that prevent safe renaming
- Prevents renaming functions used in string literals

**Example Output:**

.. code-block:: text

   Privacy Fix Analysis:

   ✅ Can safely rename 4 functions:
     • validate_input → _validate_input (2 references) [W9004]
     • helper_function → _helper_function (1 reference) [W9004]
     • format_data → _format_data (3 references) [W9004]
     • _shared_util → shared_util (3 external references) [W9005]

   ⚠️  Cannot safely rename 1 function:
     • process_item: Contains dynamic references (getattr, hasattr, etc.)

**Integrated Workflow Example with --auto-sort:**

.. code-block:: text

   $ pylint-sort-functions --fix-privacy --auto-sort --no-backup src/utils.py

   Privacy Fix Analysis:

   ✅ Can safely rename 2 functions:
     • helper_function → _helper_function (1 reference)
     • validate_data → _validate_data (2 references)

   Renamed 2 functions.

   === Applying Automatic Sorting ===
   Sorted 1 of 1 files

This workflow first applies privacy fixes (renaming functions to be private), then automatically sorts all functions alphabetically within their visibility groups (public functions first, then private functions).

For technical implementation details, see the developer documentation.

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

.. note::
   **Section Header Support:** The auto-fix tool now fully supports automatic section header insertion and detection. Use ``--add-section-headers`` to enable organizational headers, and ``--additional-section-patterns`` to detect existing custom organizational patterns. Function-specific comments are preserved during reordering.

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
