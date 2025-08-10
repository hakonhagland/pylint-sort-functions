User Guide
==========

This guide explains how to use the ``pylint-sort-functions`` plugin to enforce function and method sorting in your Python code.

Installation
------------

Add ``pylint-sort-functions`` as a development dependency to enable function sorting enforcement in your PyLint workflow.

Project Development Dependencies (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The most common approach is adding the plugin to your project's development dependencies, ensuring consistent code quality checks across your team and CI/CD pipeline.

**Using pyproject.toml** (Modern Python projects):

.. code-block:: toml

    [tool.uv.dev-dependencies]
    # or [project.optional-dependencies.dev]
    pylint-sort-functions = ">=1.0.0"
    pylint = ">=3.3.0"  # Required for the plugin

**Using Poetry**:

.. code-block:: toml

    [tool.poetry.group.dev.dependencies]
    pylint-sort-functions = "^1.0.0"
    pylint = "^3.3.0"

**Using requirements-dev.txt**:

.. code-block:: text

    # requirements-dev.txt
    pylint-sort-functions>=1.0.0
    pylint>=3.3.0

Then install with your preferred dependency manager:

.. code-block:: bash

    # uv (recommended)
    uv sync

    # Poetry
    poetry install

    # pip
    pip install -r requirements-dev.txt

Virtual Environment Installation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For project-specific virtual environments without modern dependency management:

.. code-block:: bash

    # Create and activate virtual environment
    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    # .venv\Scripts\activate   # Windows

    # Install the plugin
    pip install pylint-sort-functions pylint

CI/CD Integration
~~~~~~~~~~~~~~~~~

With development dependencies, your continuous integration automatically includes the plugin:

.. code-block:: yaml

    # GitHub Actions example
    - name: Install dependencies
      run: uv sync

    - name: Run PyLint with sorting checks
      run: uv run pylint --load-plugins=pylint_sort_functions src/

Standalone Auto-Fix Tool
~~~~~~~~~~~~~~~~~~~~~~~~~

The package also includes a standalone command-line tool for automatically fixing function order. For installation and usage details, see :doc:`cli`.

.. note::
   Most users should start with the PyLint plugin integration described in this guide. The standalone CLI tool is useful for one-time fixes or integration with other tools.

Quick Start
-----------

Run PyLint with the plugin enabled:

.. code-block:: bash

    pylint --load-plugins=pylint_sort_functions your_module.py

Configuration
-------------

There are several ways to enable the plugin permanently in your project:

Using .pylintrc
~~~~~~~~~~~~~~~

Add to your ``.pylintrc`` file:

.. code-block:: ini

    [MASTER]
    load-plugins = pylint_sort_functions

Using pyproject.toml
~~~~~~~~~~~~~~~~~~~~

Add to your ``pyproject.toml``:

.. code-block:: toml

    [tool.pylint.MASTER]
    load-plugins = ["pylint_sort_functions"]

Using setup.cfg
~~~~~~~~~~~~~~~

Add to your ``setup.cfg``:

.. code-block:: ini

    [pylint]
    load-plugins = pylint_sort_functions

Plugin Configuration Options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plugin supports several configuration options to customize its behavior:

**Using pyproject.toml** (Recommended):

.. code-block:: toml

    [tool.pylint.MASTER]
    load-plugins = ["pylint_sort_functions"]

    [tool.pylint.function-sort]
    public-api-patterns = ["main", "run", "execute", "start", "stop", "setup", "teardown"]
    enable-privacy-detection = true

**Using .pylintrc**:

.. code-block:: ini

    [MASTER]
    load-plugins = pylint_sort_functions

    [function-sort]
    public-api-patterns = main,run,execute,start,stop,setup,teardown
    enable-privacy-detection = yes

Configuration Options Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**public-api-patterns**
    List of function names to always treat as public API. These functions will not be flagged for privacy even if only used internally. Useful for entry points and framework callbacks.

    *Default*: ``["main", "run", "execute", "start", "stop", "setup", "teardown"]``

**enable-privacy-detection**
    Enable detection of functions that should be made private based on usage analysis. When enabled, the plugin analyzes cross-module imports to identify functions only used within their defining module.

    *Default*: ``true``

Test File Exclusion
~~~~~~~~~~~~~~~~~~~

The privacy detection system automatically excludes test files from analysis to prevent functions used only by tests from being incorrectly marked as private. This ensures that functions validating the public API (via tests) remain accessible.

**Automatically detected test files:**

- Files in ``tests/`` or ``test/`` directories
- Files starting with ``test_`` (e.g., ``test_utils.py``)
- Files ending with ``_test`` (e.g., ``module_test.py``)
- ``conftest.py`` files (pytest configuration)

**Example excluded files:**

.. code-block:: text

    tests/test_module.py          ✓ Excluded (in tests/ directory)
    test_integration.py           ✓ Excluded (starts with test_)
    utils_test.py                 ✓ Excluded (ends with _test)
    conftest.py                   ✓ Excluded (pytest configuration)
    src/tests/helpers.py          ✓ Excluded (in tests/ subdirectory)

.. note::
   Test file exclusion patterns are currently built-in and not configurable. Future versions may add configuration options for custom test patterns.

Automatic Directory Exclusion
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plugin automatically skips common directories that should not be analyzed for performance and accuracy:

**Build and Distribution:**
    ``build/``, ``dist/``, ``*.egg-info/``

**Version Control:**
    ``.git/``

**Python Caches:**
    ``__pycache__/``, ``.pytest_cache/``, ``.mypy_cache/``, ``.tox/``

**Virtual Environments:**
    ``venv/``, ``.venv/``, ``env/``, ``.env/``

**Node.js Dependencies:**
    ``node_modules/``

.. note::
   Directory exclusion patterns are currently built-in and not configurable. For custom directory exclusions, see `GitHub issue #7 <https://github.com/hakonhagland/pylint-sort-functions/issues/7>`_.

Message Types
-------------

The plugin reports four types of violations:

W9001: unsorted-functions
~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Functions are not sorted alphabetically in module scope

**When triggered**: Module-level functions are not in alphabetical order within their visibility scope

**Example violation**:

.. code-block:: python

    # Bad: Functions out of order
    def zebra_function():
        pass

    def alpha_function():  # Should come before zebra_function
        pass

**How to fix**: Reorder functions alphabetically:

.. code-block:: python

    # Good: Functions sorted alphabetically
    def alpha_function():
        pass

    def zebra_function():
        pass

**Auto-fix available**: Use ``pylint-sort-functions --fix`` to automatically reorder functions. See :doc:`cli` for details.

W9002: unsorted-methods
~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Methods are not sorted alphabetically in class

**When triggered**: Class methods are not in alphabetical order within their visibility scope

**Example violation**:

.. code-block:: python

    class MyClass:
        def method_z(self):
            pass

        def method_a(self):  # Should come before method_z
            pass

**How to fix**: Reorder methods alphabetically:

.. code-block:: python

    class MyClass:
        def method_a(self):
            pass

        def method_z(self):
            pass

**Auto-fix available**: Use ``pylint-sort-functions --fix`` to automatically reorder methods. See :doc:`cli` for details.

W9003: mixed-function-visibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Public and private functions are not properly separated

**When triggered**: Private functions (with underscore prefix) appear before public functions

**Example violation**:

.. code-block:: python

    # Bad: Private function before public function
    def _private_helper():
        pass

    def public_function():  # Public functions should come first
        pass

**How to fix**: Place all public functions before private functions:

.. code-block:: python

    # Good: Public functions first, then private
    def public_function():
        pass

    def _private_helper():
        pass

**Auto-fix available**: Use ``pylint-sort-functions --fix`` to automatically reorder functions. See :doc:`cli` for details.

W9004: function-should-be-private
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Function should be private (prefix with underscore)

**When triggered**: A function is only used within its defining module based on sophisticated import analysis

**Example violation**:

.. code-block:: python

    # Bad: Internal helper not marked as private
    def validate_internal_state(data):  # Only used in this module
        return data.is_valid()

    def public_api():
        if validate_internal_state(data):
            process(data)

**How to fix**: Add underscore prefix to make it private:

.. code-block:: python

    # Good: Internal function marked as private
    def _validate_internal_state(data):
        return data.is_valid()

    def public_api():
        if _validate_internal_state(data):
            process(data)

**Detection Method**: Uses comprehensive import analysis that scans the entire project to identify actual usage patterns:

- **Cross-module analysis**: Analyzes all Python files to detect function imports and calls
- **Usage tracking**: Maps which functions are accessed by other modules via ``from module import function`` or ``module.function()``
- **Smart exclusions**: Skips common public API patterns (``main``, ``run``, ``setup``) and automatically excludes test files from analysis
- **Test file exclusion**: Automatically excludes ``tests/``, ``test_*.py``, ``*_test.py``, and ``conftest.py`` files to prevent functions used only by tests from being marked private
- **False positive prevention**: Only flags functions with zero external usage (excluding tests), ensuring accuracy

**Auto-fix availability**:
- **Manual renaming**: Functions can be manually renamed following PyLint suggestions
- **Automatic renaming**: Available via the bidirectional privacy fixer feature

  See privacy fixer documentation for comprehensive privacy analysis capabilities.

W9005: function-should-be-public
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Private function should be public (remove underscore prefix)

**When triggered**: A private function (with underscore prefix) is imported and used by other modules based on cross-module usage analysis

**Example violation**:

.. code-block:: python

    # Bad: Private function used externally
    # utils.py contains:
    def _helper_function():  # Used by other modules
        return "help"

    # main.py imports it:
    from utils import _helper_function  # External usage detected

**How to fix**: Remove underscore prefix to make it public:

.. code-block:: python

    # Good: Function correctly marked as public
    def helper_function():
        return "help"

**Detection Method**: Uses comprehensive import analysis to identify private functions with external usage:

- **Cross-module import detection**: Scans all Python files to identify imports of private functions
- **Usage pattern analysis**: Detects ``from module import _function`` and ``module._function()`` patterns
- **Conservative approach**: Only flags private functions with clear external usage evidence
- **Test file exclusion**: Automatically ignores usage within ``tests/``, ``test_*.py``, ``*_test.py``, and ``conftest.py`` files to avoid false positives from test code

**Auto-fix availability**:
- **Manual renaming**: Functions can be manually renamed following PyLint suggestions
- **Automatic renaming**: Available via the bidirectional privacy fixer feature

  See privacy fixer documentation for comprehensive privacy analysis capabilities.

Sorting Rules
-------------

The plugin enforces these sorting rules:

1. **Visibility Separation**: Public functions/methods (no underscore) must come before private ones (underscore prefix)
2. **Alphabetical Order**: Within each visibility group, items must be sorted alphabetically
3. **Case Sensitive**: Sorting is case-sensitive (uppercase comes before lowercase)
4. **Dunder Method Handling**: Special methods (``__init__``, ``__str__``) are treated as public and sorted alphabetically
5. **Public API Pattern Recognition**: Configurable patterns (``main``, ``run``, ``setup``) are preserved as public regardless of usage
6. **Decorator Exclusions**: Functions with specified decorators can be excluded from sorting requirements (CLI tool only)

Complete Example
~~~~~~~~~~~~~~~~

Here's a properly organized module:

.. code-block:: python

    """Example module with proper function organization."""

    # Public functions (alphabetically sorted)

    def calculate_total(items):
        """Calculate the total of all items."""
        return sum(item.value for item in items)

    def process_data(data):
        """Process the input data."""
        validated = _validate_data(data)
        return _transform_data(validated)

    def save_results(results):
        """Save results to storage."""
        formatted = _format_results(results)
        _write_to_disk(formatted)

    # Private functions (alphabetically sorted)

    def _format_results(results):
        """Format results for storage."""
        return json.dumps(results)

    def _transform_data(data):
        """Transform validated data."""
        return [d.upper() for d in data]

    def _validate_data(data):
        """Validate input data."""
        return [d for d in data if d]

    def _write_to_disk(data):
        """Write data to disk."""
        with open("output.json", "w") as f:
            f.write(data)

Disabling Messages
------------------

You can disable specific messages for a file, class, or function:

File Level
~~~~~~~~~~

.. code-block:: python

    # pylint: disable=unsorted-functions
    """This module intentionally has unsorted functions."""

Function Level
~~~~~~~~~~~~~~

.. code-block:: python

    def zebra():  # pylint: disable=unsorted-functions
        pass

    def alpha():  # Order required by framework
        pass

Inline Comments
~~~~~~~~~~~~~~~

.. code-block:: python

    class MyClass:
        def z_method(self):
            pass

        def a_method(self):  # pylint: disable=unsorted-methods
            pass

Configuration in .pylintrc
~~~~~~~~~~~~~~~~~~~~~~~~~~

Disable specific messages project-wide:

.. code-block:: ini

    [MESSAGES CONTROL]
    disable = unsorted-functions,
              unsorted-methods

Or enable only specific messages:

.. code-block:: ini

    [MESSAGES CONTROL]
    enable = unsorted-functions,
             unsorted-methods,
             mixed-function-visibility,
             function-should-be-private,
             function-should-be-public

Command Line Options
--------------------

Run with specific messages enabled:

.. code-block:: bash

    # Check only function sorting
    pylint --load-plugins=pylint_sort_functions \
           --disable=all \
           --enable=unsorted-functions,unsorted-methods \
           mymodule.py

Run with increased verbosity:

.. code-block:: bash

    # See which files are being checked
    pylint --load-plugins=pylint_sort_functions --verbose mymodule.py

Generate a full report:

.. code-block:: bash

    # Get detailed statistics
    pylint --load-plugins=pylint_sort_functions --reports=yes mymodule.py

Command-Line Plugin Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Configure plugin behavior through PyLint command-line options:

.. code-block:: bash

    # Configure public API patterns
    pylint --load-plugins=pylint_sort_functions \
           --public-api-patterns=main,run,custom_entry \
           mymodule.py

    # Disable privacy detection
    pylint --load-plugins=pylint_sort_functions \
           --disable-privacy-detection \
           mymodule.py

Self-Check Pattern
~~~~~~~~~~~~~~~~~~

Focus exclusively on sorting violations for clean output:

.. code-block:: bash

    # Check only plugin-specific violations
    pylint --load-plugins=pylint_sort_functions \
           --disable=all \
           --enable=unsorted-functions,unsorted-methods,mixed-function-visibility,function-should-be-private,function-should-be-public \
           src/

    # Make target equivalent (if available)
    make self-check

Integration with IDEs
---------------------

VS Code
~~~~~~~

Add to ``.vscode/settings.json``:

.. code-block:: json

    {
        "pylint.args": [
            "--load-plugins=pylint_sort_functions"
        ]
    }

PyCharm
~~~~~~~

1. Go to Settings → Tools → External Tools
2. Add PyLint with arguments: ``--load-plugins=pylint_sort_functions``

Vim (with ALE)
~~~~~~~~~~~~~~

Add to your ``.vimrc``:

.. code-block:: vim

    let g:ale_python_pylint_options = '--load-plugins=pylint_sort_functions'

Best Practices
--------------

1. **Use Section Comments**: Clearly separate public and private sections:

   .. code-block:: python

       # Public functions

       def public_one():
           pass

       # Private functions

       def _private_one():
           pass

2. **Framework Exceptions**: Some frameworks require specific ordering. In these cases:

   - Document why the order is required
   - Configure decorator exclusions in your project (see :doc:`pylintrc`)
   - Use the CLI auto-fix tool with decorator exclusions: ``pylint-sort-functions --fix --ignore-decorators "@app.route"`` (see :doc:`cli`)
   - **Note**: Decorator exclusions are available in both PyLint plugin and CLI tool for consistent behavior.


3. **Test Organization**: Apply the same principles to test files for consistency:

   .. code-block:: python

       class TestMyClass:
           # Test methods (alphabetically sorted)

           def test_feature_a(self):
               pass

           def test_feature_b(self):
               pass

           # Helper methods

           def _create_fixture(self):
               pass

4. **Gradual Adoption**: When adding to an existing project:

   - Start by enabling only in new modules
   - Gradually fix existing modules
   - Use file-level disables during transition

Troubleshooting
---------------

Plugin Not Loading
~~~~~~~~~~~~~~~~~~

If the plugin isn't loading, verify:

1. Installation: ``pip show pylint-sort-functions``
2. Python path: ``python -c "import pylint_sort_functions"``
3. PyLint version: ``pylint --version`` (requires PyLint >=3.3.0)
4. Python version: ``python --version`` (requires Python >=3.11)

Configuration Issues
~~~~~~~~~~~~~~~~~~~~

If plugin configuration options aren't being recognized:

1. Verify configuration section name: ``[tool.pylint.function-sort]``
2. Check option names: ``public-api-patterns``, ``enable-privacy-detection``
3. Restart your IDE/editor after configuration changes
4. Test configuration: ``pylint --help`` should show plugin options

Privacy Detection Issues
~~~~~~~~~~~~~~~~~~~~~~~~~

If ``function-should-be-private`` (W9004) or ``function-should-be-public`` (W9005) messages aren't appearing:

1. Verify privacy detection is enabled: ``enable-privacy-detection=y``
2. Check that files are part of a Python project with project markers (pyproject.toml, setup.py, etc.)
3. Ensure functions aren't in test files (automatically excluded)
4. For W9004: Verify functions aren't matching public API patterns
5. For W9005: Confirm the private function is actually imported by other modules

False Positives
~~~~~~~~~~~~~~~

If you get false positives for privacy detection:

**For W9004 (function-should-be-private)**:

1. Ensure your ``__init__.py`` files properly export public APIs
2. The detection is conservative and won't flag functions used across modules
3. Configure public API patterns if you have custom entry points:

   .. code-block:: ini

       [tool.pylint.function-sort]
       public-api-patterns = ["main", "run", "setup", "custom_entry"]

4. Use inline disables for legitimate cases: ``# pylint: disable=function-should-be-private``

**For W9005 (function-should-be-public)**:

1. Verify the function is genuinely used externally (not just in tests)
2. Check if the external usage is intentional API design
3. Use inline disables if the private usage is intentional: ``# pylint: disable=function-should-be-public``

Performance Issues
~~~~~~~~~~~~~~~~~~

For large codebases:

1. The import analysis feature may add overhead
2. Consider running the plugin separately from other checks
3. Use file/directory exclusions for generated code

Output Format
-------------

The plugin produces standard PyLint output:

.. code-block:: text

    ************* Module mymodule
    mymodule.py:10:0: W9001: Functions are not sorted alphabetically in module scope (unsorted-functions)
    mymodule.py:25:0: W9002: Methods are not sorted alphabetically in class MyClass (unsorted-methods)
    mymodule.py:30:0: W9003: Public and private functions are not properly separated in module (mixed-function-visibility)
    mymodule.py:35:0: W9004: Function 'helper_function' should be private (prefix with underscore) (function-should-be-private)
    mymodule.py:40:0: W9005: Function '_shared_util' should be public (remove underscore prefix) (function-should-be-public)

Exit Codes
~~~~~~~~~~

The plugin follows PyLint's exit code convention:

- 0: No issues found
- 1: Fatal error occurred
- 2: Error messages issued
- 4: Warning messages issued
- 8: Refactor messages issued
- 16: Convention messages issued

Since this plugin issues warnings (W codes), expect exit code 4 when violations are found.

Summary
-------

The ``pylint-sort-functions`` plugin helps maintain consistent code organization by enforcing:

- Alphabetical sorting of functions and methods
- Proper separation of public and private functions
- Clear identification of internal helper functions and externally-used private functions

This leads to more maintainable and navigable codebases where developers can quickly locate functions and understand the public API surface.

See Also
--------

- :doc:`cli` - Command-line auto-fix tool with ``pylint-sort-functions`` command
- :doc:`pylintrc` - Complete PyLint configuration reference
- :doc:`sorting` - Detailed sorting algorithm and rules documentation
