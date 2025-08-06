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

The plugin includes intelligent privacy detection to suggest functions that should be made private.

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

Section Headers (Future Enhancement)
------------------------------------

A future enhancement may add support for automatic section header comments:

.. code-block:: python

   # Public functions

   def calculate_total(items):
       pass

   def validate_input(data):
       pass

   # Private functions

   def _format_error(error):
       pass

   def _log_operation(op):
       pass

Message Types
-------------

The plugin reports three types of sorting violations:

W9001: unsorted-functions
~~~~~~~~~~~~~~~~~~~~~~~~~
Functions in a module are not sorted alphabetically within their visibility scope.

W9002: unsorted-methods
~~~~~~~~~~~~~~~~~~~~~~~
Methods in a class are not sorted alphabetically within their visibility scope.

W9003: mixed-function-visibility
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Public and private functions are not properly separated (public must come before private).

Configuration
-------------

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
