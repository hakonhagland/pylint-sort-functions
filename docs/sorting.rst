Function and Method Sorting Algorithm
=====================================

This document describes the comprehensive sorting algorithm used by pylint-sort-functions
to organize Python code for improved readability and maintainability.

Overview
--------

The plugin enforces a consistent organizational pattern for both module-level functions
and class methods. This creates predictable code structure that improves navigation
and reduces cognitive overhead when reading code.

Sorting Rules
-------------

Module-Level Functions
~~~~~~~~~~~~~~~~~~~~~~

Functions within a module are organized using the following hierarchy:

1. **Public functions** (no underscore prefix) - sorted alphabetically
2. **Private functions** (single underscore prefix) - sorted alphabetically

**Example:**

.. code-block:: python

   # Public functions (alphabetically sorted)
   def calculate_total(items):
       return sum(item.price for item in items)

   def format_currency(amount):
       return f"${amount:.2f}"

   def validate_input(data):
       return data and isinstance(data, dict)

   # Private functions (alphabetically sorted)
   def _format_error_message(error):
       return f"Error: {error}"

   def _log_operation(operation):
       logger.debug(f"Performing: {operation}")

Class Methods
~~~~~~~~~~~~~

Methods within classes follow the same organizational pattern:

1. **Public methods** (including dunder methods) - sorted alphabetically
2. **Private methods** (single underscore prefix) - sorted alphabetically

**Example:**

.. code-block:: python

   class ShoppingCart:
       def __init__(self, customer_id):
           self.customer_id = customer_id
           self.items = []

       def __str__(self):
           return f"Cart for {self.customer_id} with {len(self.items)} items"

       def add_item(self, item):
           self.items.append(item)

       def calculate_total(self):
           return sum(item.price for item in self.items)

       def remove_item(self, item_id):
           self.items = [item for item in self.items if item.id != item_id]

       # Private methods
       def _apply_discount(self, amount):
           return amount * 0.9

       def _log_transaction(self, transaction):
           logger.info(f"Transaction: {transaction}")

Special Method Handling
-----------------------

Dunder Methods
~~~~~~~~~~~~~~

Dunder methods (``__init__``, ``__str__``, ``__call__``, etc.) are treated as public methods
and are sorted alphabetically with other public methods. Due to their ``__`` prefix, they
naturally appear at the top of the public methods section.

**Rationale:** Dunder methods are part of Python's special method protocol and are considered
public API. Their alphabetical ordering ensures consistency while their double-underscore prefix
provides natural grouping at the top of classes.

Private vs Public Classification
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Public:** No underscore prefix (``method_name``)
- **Public:** Dunder methods (``__method_name__``)
- **Private:** Single underscore prefix (``_method_name``)

Framework Integration
---------------------

Decorator Exclusions
~~~~~~~~~~~~~~~~~~~~

The plugin supports excluding functions/methods with specific decorators from sorting requirements.
This is essential for framework compatibility where decorator order matters.

**Common exclusion patterns:**

.. code-block:: python

   # Click commands - order may matter for help display
   @click.command()
   def init():
       pass

   @click.command()
   def deploy():
       pass

   # Flask routes - order may affect route matching
   @app.route('/api/users')
   def list_users():
       pass

   @app.route('/api/users/<int:id>')
   def get_user(id):
       pass

**Configuration example:**

.. code-block:: ini

   [tool.pylint.plugins]
   load-plugins = ["pylint_sort_functions"]

   [tool.pylint."messages control"]
   # Enable all sorting checks
   enable = ["unsorted-functions", "unsorted-methods", "mixed-function-visibility"]

   # Configure decorator exclusions
   ignore-decorators = ["@app.route", "@*.command", "@pytest.fixture"]

Privacy Detection
-----------------

The plugin includes intelligent bidirectional privacy detection to suggest functions that have incorrect privacy levels.

**Bidirectional Analysis:**

- **W9004 Detection**: Identifies public functions that should be private
- **W9005 Detection**: Identifies private functions that should be public

Detection Algorithm
~~~~~~~~~~~~~~~~~~~

1. **Skip already private functions** (start with ``_``)
2. **Skip dunder methods** (``__method__``)
3. **Skip common public API patterns:**

   - Entry points: ``main``, ``run``, ``execute``
   - Lifecycle: ``start``, ``stop``, ``setup``, ``teardown``

4. **Analyze cross-module usage** via import analysis
5. **Flag functions only used internally** as privacy candidates

**Example:**

.. code-block:: python

   # This function would be flagged for privacy
   def calculate_tax_rate(income):  # Not imported by other modules
       return income * 0.15

   # This function would NOT be flagged
   def main():  # Entry point pattern
       pass

   # This function would NOT be flagged
   def get_user_data():  # Imported by user_service.py
       pass

Advanced AST-Based Boundary Detection
--------------------------------------

The auto-fix tool uses sophisticated AST (Abstract Syntax Tree) analysis to accurately detect boundaries between functions and other module constructs. This ensures proper handling of complex Python patterns.

**Accurate Boundary Detection:**

The system correctly handles various Python constructs:

.. code-block:: python

    # Module-level constructs are properly preserved
    import os

    CONSTANT = "value"

    def function_a():
        pass

    # Comments and docstrings preserved
    """Module docstring after functions."""

    def function_b():
        pass

    class MyClass:
        pass

    # Main blocks preserved at end of file
    if __name__ == "__main__":
        main()

**Key Improvements:**

- **AST-Based Analysis**: Uses Python's AST to understand code structure instead of pattern matching
- **Accurate End Detection**: Finds actual function boundaries using AST node information
- **Main Block Preservation**: Correctly handles ``if __name__ == "__main__":`` blocks
- **Complex Constructs**: Properly sorts around classes, global variables, and imports
- **Docstring Handling**: Preserves module-level docstrings and comments in correct positions

Comment Preservation
--------------------

The auto-fix tool preserves comments associated with functions during reordering:

**Before sorting:**

.. code-block:: python

   def zebra_function():
       pass

   # Important comment about alpha function
   # This explains the algorithm
   def alpha_function():
       pass

**After sorting:**

.. code-block:: python

   # Important comment about alpha function
   # This explains the algorithm
   def alpha_function():
       pass

   def zebra_function():
       pass

Automatic Section Headers
--------------------------

The auto-fix tool can automatically insert section header comments to improve code organization
and make the visibility separation more explicit.

Configuration
~~~~~~~~~~~~~

Section headers are configured through the ``AutoFixConfig`` class or CLI arguments:

**Programmatic Configuration:**

.. code-block:: python

   from pylint_sort_functions.auto_fix import AutoFixConfig, FunctionSorter

   config = AutoFixConfig(
       add_section_headers=True,                    # Enable section headers
       public_header="# Public functions",         # Header for public functions
       private_header="# Private functions",       # Header for private functions
       public_method_header="# Public methods",    # Header for public methods
       private_method_header="# Private methods"   # Header for private methods
   )

   sorter = FunctionSorter(config)
   sorter.sort_file(Path("myfile.py"))

**CLI Configuration:**

.. code-block:: bash

   # Enable section headers with default text
   pylint-sort-functions --fix --add-section-headers myfile.py

   # Customize header text
   pylint-sort-functions --fix --add-section-headers \
       --public-header "=== PUBLIC API ===" \
       --private-header "=== INTERNAL HELPERS ===" \
       myfile.py

   # Separate headers for functions vs methods
   pylint-sort-functions --fix --add-section-headers \
       --public-method-header ">>> Public Methods <<<" \
       --private-method-header ">>> Private Methods <<<" \
       myfile.py

Custom Section Header Detection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The auto-fix tool can detect and preserve existing section headers using configurable patterns.
This prevents duplication when section headers are already present and allows integration with
existing code organization styles.

**Configuration Options:**

.. code-block:: python

   config = AutoFixConfig(
       add_section_headers=True,
       # Detection patterns for custom organizational styles
       additional_section_patterns=[
           "=== API ===",                    # Custom delimiter style
           "--- Helpers ---",                # Different delimiter
           "## Core Functions ##",           # Markdown-style headers
           "*** Private Implementation ***"  # Alternative marker
       ],
       # Case sensitivity control (default: case-insensitive)
       section_header_case_sensitive=True
   )

**CLI Usage:**

.. code-block:: bash

   # Add custom detection patterns
   pylint-sort-functions --fix --add-section-headers \
       --additional-section-patterns "=== API ===" \
       --additional-section-patterns "--- Helpers ---" \
       myfile.py

   # Enable case-sensitive detection
   pylint-sort-functions --fix --add-section-headers \
       --section-headers-case-sensitive \
       myfile.py

**Detection Logic:**

The tool automatically detects section headers using a comprehensive pattern matching system:

1. **Configured Headers**: Patterns from your ``public_header``, ``private_header``, etc. are automatically included
2. **Default Patterns**: Backward-compatible patterns like "public functions", "private methods", etc.
3. **Additional Patterns**: Your custom patterns via ``additional_section_patterns``
4. **Case Sensitivity**: Configurable case-sensitive or case-insensitive matching

**Example - Preserving Existing Headers:**

.. code-block:: python

   # Before: Existing file with custom headers
   """=== PUBLIC API ==="""

   def zebra_function():
       return "zebra"

   def alpha_function():
       return "alpha"

   """=== INTERNAL ==="""

   def _private_helper():
       return "helper"

   # Configuration to detect these headers
   config = AutoFixConfig(
       add_section_headers=True,
       public_header="=== PUBLIC API ===",
       private_header="=== INTERNAL ==="
   )

   # After auto-fix: Headers preserved, functions sorted
   """=== PUBLIC API ==="""

   def alpha_function():
       return "alpha"

   def zebra_function():
       return "zebra"

   """=== INTERNAL ==="""

   def _private_helper():
       return "helper"

When Headers Are Added
~~~~~~~~~~~~~~~~~~~~~~~

Section headers are automatically inserted **only when both public and private functions/methods
exist in the same scope**. This smart behavior ensures headers add value by clearly separating
different visibility levels, while avoiding unnecessary headers for single-visibility scopes.

**Headers added:**
- Module with both public and private functions ✓
- Class with both public and private methods ✓

**Headers NOT added:**
- Module with only public functions ✗
- Module with only private functions ✗
- Class with only public methods ✗
- Class with only private methods ✗

Examples
~~~~~~~~

**Before auto-fix (unsorted mixed functions):**

.. code-block:: python

   """User management module."""

   def zebra_function():
       """A public function."""
       return "zebra"

   def alpha_function():
       """Another public function."""
       return "alpha"

   def _zebra_private():
       """A private helper function."""
       return "_zebra"

   def _alpha_private():
       """Another private helper."""
       return "_alpha"

**After auto-fix with section headers enabled:**

.. code-block:: python

   """User management module."""

   # Public functions

   def alpha_function():
       """Another public function."""
       return "alpha"

   def zebra_function():
       """A public function."""
       return "zebra"


   # Private functions

   def _alpha_private():
       """Another private helper."""
       return "_alpha"

   def _zebra_private():
       """A private helper function."""
       return "_zebra"

**Class method example:**

.. code-block:: python

   class UserService:
       """Service for user management."""

       # Public methods

       def create_user(self, data):
           return self._validate_user_data(data)

       def get_user(self, user_id):
           return self._fetch_from_db(user_id)


       # Private methods

       def _fetch_from_db(self, user_id):
           # Database access logic
           pass

       def _validate_user_data(self, data):
           # Validation logic
           pass

Message Types
-------------

The plugin reports five types of violations:

**Sorting Violations:**

W9001: unsorted-functions
~~~~~~~~~~~~~~~~~~~~~~~~~
Functions in a module are not sorted alphabetically within their visibility scope.

W9002: unsorted-methods
~~~~~~~~~~~~~~~~~~~~~~~
Methods in a class are not sorted alphabetically within their visibility scope.

W9003: mixed-function-visibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Public and private functions are not properly separated (public must come before private).

**Privacy Violations:**

W9004: function-should-be-private
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A public function should be marked as private (add underscore prefix) because it's only used within its own module.

**Example:**

.. code-block:: python

    # This function is only called within this module
    def calculate_internal_hash(data):  # W9004: Should be _calculate_internal_hash
        return hashlib.md5(data.encode()).hexdigest()

W9005: function-should-be-public
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A private function should be made public (remove underscore prefix) because it's imported and used by other modules.

**Example:**

.. code-block:: python

    # utils.py
    def _format_currency(amount):  # W9005: Should be format_currency
        return f"${amount:.2f}"

    # main.py imports it:
    from utils import _format_currency  # External usage detected

PyLint Integration
------------------

See :doc:`pylintrc` for complete configuration options including:

- Enabling/disabling specific message types
- Configuring decorator exclusion patterns
- Setting up auto-fix integration

CLI Tool
--------

See :doc:`cli` for information about the standalone ``pylint-sort-functions`` command-line tool
that provides auto-fix functionality independent of PyLint.

Benefits
--------

Consistency
~~~~~~~~~~~
- Predictable function/method location
- Reduced time searching for specific functions
- Easier code reviews and maintenance

Readability
~~~~~~~~~~~
- Public API clearly separated from internal implementation
- Alphabetical ordering eliminates arbitrary placement decisions
- Natural grouping of related functionality

Maintainability
~~~~~~~~~~~~~~~
- New functions have obvious placement location
- Refactoring becomes more systematic
- Codebase-wide organizational standards

Algorithm Safety and Robustness
===============================

Critical Issue Resolution (v1.3.1+)
------------------------------------

**GitHub Issue #25 Resolution**

Version 1.3.1 includes a comprehensive fix for a critical algorithm safety issue that could
cause syntax corruption when auto-sorting files with multiple complex class definitions.

The Problem
~~~~~~~~~~~

The original algorithm processed classes sequentially, which caused line number corruption
when multiple classes were present:

.. code-block:: python

    # BEFORE: This would cause corruption
    class DialogA:
        def z_method(self):
            super().__init__()
            pass
        def a_method(self):
            pass

    class DialogB:
        def z_method(self):  # Same name as DialogA
            pass
        def a_method(self):  # Same name as DialogA
            pass

**Result**: Class ``DialogB`` definition would be lost, methods orphaned, syntax errors created.

The Solution
~~~~~~~~~~~~

**Multi-Class Safe Processing Algorithm:**

1. **Upfront Data Extraction**: Extract ALL class information before ANY modifications
2. **Reverse Processing Order**: Process classes from end-to-start to preserve line numbers
3. **Mandatory Syntax Validation**: Validate output and automatically rollback on errors
4. **Class Boundary Preservation**: Ensure all class definitions remain intact

.. code-block:: python

    # NEW ALGORITHM (simplified pseudocode):

    def _sort_class_methods(self, content, module, lines):
        # PHASE 1: Extract all class data upfront (NO modifications yet)
        class_info = []
        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                method_spans = self._extract_method_spans(methods, lines, node)
                sorted_spans = self._sort_function_spans(method_spans)
                class_info.append((node, method_spans, sorted_spans))

        # PHASE 2: Process in REVERSE ORDER (preserves line numbers)
        for _, original_spans, sorted_spans in reversed(class_info):
            content = self._reconstruct_class_with_sorted_methods(
                content, original_spans, sorted_spans
            )

        return content

**Syntax Validation with Auto-Rollback:**

Every auto-sort operation now includes mandatory validation:

.. code-block:: python

    def _validate_syntax_and_rollback(self, file_path, original_content, new_content):
        """Critical safety measure to prevent corruption."""
        try:
            compile(new_content, str(file_path), 'exec')
            return new_content
        except SyntaxError as e:
            print(f"WARNING: Auto-sort would create syntax error in {file_path}:")
            print(f"  Error: {e}")
            print("  Reverting to original content to prevent file corruption.")
            return original_content

Safety Guarantees
~~~~~~~~~~~~~~~~~

The enhanced algorithm provides multiple safety layers:

**1. Data Integrity**
   - No class definitions are ever lost
   - Method context is always preserved
   - super() calls remain properly associated with their classes

**2. Automatic Error Recovery**
   - Syntax validation after every transformation
   - Automatic rollback to original content on any error
   - Detailed error reporting with line numbers and context

**3. Multi-Class Robustness**
   - Handles complex inheritance hierarchies (PyQt, Django, etc.)
   - Preserves methods with identical names across different classes
   - Maintains proper indentation and class boundaries

**4. Production Safety**
   - Zero data loss risk - files are never left in corrupted state
   - Backward compatibility - simple cases continue to work as before
   - Comprehensive test coverage for complex scenarios

Example: Safe Complex Class Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Input (Complex Class Hierarchy):**

.. code-block:: python

    class LicenseSelectionDialog(QDialog):
        '''Complex PyQt dialog with inheritance.'''

        def setup_ui(self):
            '''Setup the user interface.'''
            pass

        def __init__(self, task, parent=None):
            '''Initialize dialog.'''
            super().__init__(parent)  # CRITICAL: Must preserve class context
            self.task = task

        def accept(self):
            '''Accept dialog.'''
            self.result_value = "accepted"

        def _validate_input(self):
            '''Private validation method.'''
            return True

    class AnotherDialog(QDialog):
        '''Another dialog with same method names.'''

        def accept(self):  # Same name as above - previously caused corruption
            '''Accept this dialog.'''
            pass

        def __init__(self, parent=None):
            '''Initialize this dialog.'''
            super().__init__(parent)  # This also would break

        def _helper_method(self):
            '''Private helper.'''
            pass

**Output (Safely Sorted):**

.. code-block:: python

    class LicenseSelectionDialog(QDialog):
        '''Complex PyQt dialog with inheritance.'''

        def __init__(self, task, parent=None):
            '''Initialize dialog.'''
            super().__init__(parent)  # ✓ Preserved in correct class context
            self.task = task

        def accept(self):
            '''Accept dialog.'''
            self.result_value = "accepted"

        def setup_ui(self):
            '''Setup the user interface.'''
            pass

        def _validate_input(self):
            '''Private validation method.'''
            return True

    class AnotherDialog(QDialog):
        '''Another dialog with same method names.'''

        def __init__(self, parent=None):
            '''Initialize this dialog.'''
            super().__init__(parent)  # ✓ Preserved in correct class context

        def accept(self):  # ✓ No longer conflicts with LicenseSelectionDialog.accept
            '''Accept this dialog.'''
            pass

        def _helper_method(self):
            '''Private helper.'''
            pass

**Key Improvements Demonstrated:**

- ✅ Both class definitions preserved intact
- ✅ Methods sorted within their respective classes
- ✅ super() calls maintain proper class context
- ✅ Method name conflicts resolved (accept() in both classes is now safe)
- ✅ Public/private method separation maintained in each class

User Experience
~~~~~~~~~~~~~~~

**Before Fix**: Silent corruption, manual git restore required
**After Fix**: Safe operation with helpful warnings

.. code-block:: bash

    $ pylint-sort-functions --fix --auto-sort complex_file.py

If any issues occur (extremely rare), you will see output like::

    WARNING: Auto-sort would create syntax error in complex_file.py:
      Error: invalid syntax (complex_file.py, line 25)
      Line 25: class BrokenClass
      Reverting to original content to prevent file corruption.

The file remains unchanged and safe.

Compatibility
~~~~~~~~~~~~~

**Supported Complex Patterns:**

- ✅ **PyQt/PySide Applications**: Dialog classes, widget hierarchies
- ✅ **Django Projects**: Model classes, view classes with complex inheritance
- ✅ **Flask Applications**: Multiple route handler classes
- ✅ **FastAPI Projects**: Complex dependency injection patterns
- ✅ **Data Science**: Classes with complex method interdependencies
- ✅ **Any Framework**: Multi-class files with inheritance and super() calls

**Testing Coverage:**

The fix includes comprehensive test coverage for:

- Complex multi-class inheritance scenarios
- Methods with identical names across classes
- super() call preservation in complex hierarchies
- Multi-line method signatures and complex arguments
- Mixed public/private method visibility patterns
- Error recovery and rollback scenarios

For technical details, see the test suite in ``tests/test_issue25_syntax_corruption.py``.

Technical Implementation Details
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Root Cause Analysis:**

The original bug occurred because:

1. **Sequential Processing**: Classes were processed one-by-one in order
2. **Content Modification**: Each class modification changed line numbers for subsequent classes
3. **Stale References**: Later classes used outdated line number information
4. **Boundary Loss**: Method extraction from wrong positions caused class boundaries to dissolve

**Fix Implementation:**

1. **Two-Phase Processing**:
   - Phase 1: Extract all class and method information using current line numbers
   - Phase 2: Apply modifications in reverse order to preserve line number validity

2. **Comprehensive Validation**:
   - Syntax compilation test after every transformation
   - Automatic rollback mechanism on any detected error
   - Detailed logging for troubleshooting

3. **Robust Error Handling**:
   - Multiple fallback layers for different error types
   - Preservation of original file in all error scenarios
   - Clear user communication about any issues

**Performance Impact:**

The safety improvements have minimal performance impact:

- **Small files**: No measurable difference
- **Large files**: <5% processing time increase
- **Complex files**: Better reliability far outweighs minimal performance cost

**Future Maintenance:**

The enhanced algorithm is designed for long-term maintainability:

- **Comprehensive test coverage** prevents regressions
- **Clear separation of concerns** makes modifications safer
- **Detailed documentation** aids future development
- **Robust error handling** provides diagnostic information for edge cases
