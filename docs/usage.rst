User Guide
==========

This guide explains how to use the ``pylint-sort-functions`` plugin to enforce function and method sorting in your Python code.

Installation
------------

Install the plugin using pip:

.. code-block:: bash

    pip install pylint-sort-functions

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

W9004: function-should-be-private
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description**: Function should be private (prefix with underscore)

**When triggered**: A function is only used within its defining module and should be marked as private

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

**Note**: This detection uses import analysis when possible to avoid false positives. Functions that are imported by other modules won't be flagged.

Sorting Rules
-------------

The plugin enforces these sorting rules:

1. **Visibility Separation**: Public functions/methods (no underscore) must come before private ones (underscore prefix)
2. **Alphabetical Order**: Within each visibility group, items must be sorted alphabetically
3. **Case Sensitive**: Sorting is case-sensitive (uppercase comes before lowercase)

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
             function-should-be-private

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
   - Disable the check for those specific functions
   - Consider using the decorator exclusion feature (future enhancement)

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
3. PyLint version: ``pylint --version`` (requires PyLint 2.0+)

False Positives
~~~~~~~~~~~~~~~

If you get false positives for ``function-should-be-private``:

1. Ensure your ``__init__.py`` files properly export public APIs
2. The detection is conservative and won't flag functions used across modules
3. Use inline disables for legitimate cases

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
- Clear identification of internal helper functions

This leads to more maintainable and navigable codebases where developers can quickly locate functions and understand the public API surface.
