Developer Guide
===============

This guide explains the internal architecture of the ``pylint-sort-functions`` plugin and how it integrates with PyLint to enforce function and method sorting.

Overview
--------

The ``pylint-sort-functions`` plugin is a PyLint checker that enforces alphabetical sorting of functions and methods within Python modules and classes. It consists of two main components:

1. **PyLint Plugin**: Integrates with PyLint's checking framework to report sorting violations
2. **Auto-fix Tool**: Standalone tool that can automatically reorder functions to fix violations

PyLint Plugin Architecture
--------------------------

PyLint Plugin System
~~~~~~~~~~~~~~~~~~~~

PyLint uses a plugin system where external checkers can be loaded and integrated into the linting process. The plugin system works as follows:

1. **Plugin Discovery**: PyLint discovers plugins through entry points defined in ``pyproject.toml``
2. **Registration**: PyLint calls the plugin's ``register()`` function to register checkers
3. **AST Traversal**: PyLint parses Python code into an Abstract Syntax Tree (AST) using ``astroid``
4. **Visitor Pattern**: PyLint calls ``visit_*`` methods on registered checkers for each AST node
5. **Message Reporting**: Checkers call ``self.add_message()`` to report violations

Plugin Entry Point
~~~~~~~~~~~~~~~~~~~

The plugin entry point is defined in ``pyproject.toml``:

.. code-block:: toml

    [project.entry-points."pylint.plugins"]
    pylint_sort_functions = "pylint_sort_functions"

When PyLint loads the plugin, it imports the package and calls the ``register()`` function from ``__init__.py``.

Core Components
---------------

1. Plugin Registration (``__init__.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Entry point for PyLint plugin system

**Key Function**:
- ``register(linter: PyLinter) -> None``: Required by PyLint, registers the ``FunctionSortChecker``

**Integration Point**: This is where PyLint discovers and loads our checker.

2. Message Definitions (``messages.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Defines all warning messages that the plugin can report

**Structure**: Each message is a tuple containing:
- ``message_template``: Text shown to users (supports ``%s`` formatting)
- ``message_symbol``: Human-readable name for disabling (e.g., ``unsorted-functions``)
- ``message_description``: Detailed explanation

**Message IDs**:
- ``W9001``: ``unsorted-functions`` - Functions not sorted alphabetically
- ``W9002``: ``unsorted-methods`` - Class methods not sorted alphabetically
- ``W9003``: ``mixed-function-visibility`` - Public/private functions not properly separated
- ``W9004``: ``function-should-be-private`` - Function should be marked private

**Usage in Checker**: The checker calls ``self.add_message("unsorted-functions", node=node, args=("module",))``

3. Main Checker (``checker.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: The core PyLint checker that performs sorting validation

**Class**: ``FunctionSortChecker(BaseChecker)``

**PyLint Integration**:
- Inherits from ``pylint.checkers.BaseChecker``
- Defines ``name = "function-sort"`` for PyLint identification
- Uses ``msgs = messages.MESSAGES`` to register available messages

**Visitor Methods**:
- ``visit_module(node: nodes.Module)``: Called for each module, checks function sorting
- ``visit_classdef(node: nodes.ClassDef)``: Called for each class, checks method sorting

**AST Analysis Flow**:

1. PyLint parses Python code using ``astroid`` (enhanced AST library)
2. PyLint walks the AST and calls visitor methods on our checker
3. Checker extracts functions/methods from AST nodes
4. Checker validates sorting using utility functions
5. Checker reports violations using ``self.add_message()``

4. Utility Functions (``utils.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Core logic for AST analysis and sorting validation

**Key Functions**:

**Function Extraction**:
- ``get_functions_from_node(node: nodes.Module)``: Extract module-level functions
- ``get_methods_from_class(node: nodes.ClassDef)``: Extract class methods

**Sorting Validation**:
- ``are_functions_sorted(functions)``: Check alphabetical sorting within visibility scopes
- ``are_methods_sorted(methods)``: Check method sorting (same logic as functions)
- ``are_functions_properly_separated(functions)``: Check public/private separation

**Advanced Features**:
- ``are_functions_sorted_with_exclusions()``: Framework-aware sorting with decorator exclusions
- ``should_function_be_private_with_import_analysis()``: Detect functions that should be private

**Privacy Detection**:
The plugin includes heuristic analysis to suggest when public functions should be marked private:
- Analyzes function naming patterns
- Checks cross-module usage via import analysis
- Conservative approach to minimize false positives

5. Auto-fix Tool (``auto_fix.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Standalone tool for automatically reordering functions

**Key Classes**:
- ``AutoFixConfig``: Configuration for auto-fix behavior
- ``FunctionSorter``: Main auto-fix implementation
- ``FunctionSpan``: Represents a function with its text span in source

**Process**:
1. Parse file content with ``astroid`` (same as checker)
2. Extract function text spans from source
3. Sort functions according to plugin rules
4. Reconstruct file content with sorted functions

**Integration with Checker**: Uses the same utility functions as the checker for consistency.

6. Command-line Interface (``cli.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Provides CLI for the auto-fix tool

**Features**:
- File/directory processing
- Dry-run mode
- Backup creation
- Decorator exclusion patterns
- Integration with the auto-fix functionality

AST and PyLint Integration Details
----------------------------------

Abstract Syntax Tree (AST)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plugin works with ``astroid`` nodes, which are enhanced AST nodes:

**Key Node Types**:
- ``nodes.Module``: Represents a Python module
- ``nodes.ClassDef``: Represents a class definition
- ``nodes.FunctionDef``: Represents a function/method definition

**Node Properties**:
- ``node.name``: Function/class name
- ``node.lineno``: Line number in source
- ``node.body``: List of child nodes
- ``node.decorators``: Decorator information

Visitor Pattern
~~~~~~~~~~~~~~~

PyLint uses the visitor pattern to traverse AST nodes:

.. code-block:: python

    class FunctionSortChecker(BaseChecker):
        def visit_module(self, node: nodes.Module) -> None:
            # Called once per module
            functions = utils.get_functions_from_node(node)
            # Analyze and report violations

        def visit_classdef(self, node: nodes.ClassDef) -> None:
            # Called once per class definition
            methods = utils.get_methods_from_class(node)
            # Analyze and report violations

Message Reporting
~~~~~~~~~~~~~~~~~

When violations are found, the checker reports them to PyLint:

.. code-block:: python

    self.add_message(
        "unsorted-functions",    # Message ID (from messages.py)
        node=node,               # AST node where violation occurs
        args=("module",)         # Arguments for message template
    )

This creates output like:
``W9001: Functions are not sorted alphabetically in module scope (unsorted-functions)``

Sorting Logic
-------------

Function Organization Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The plugin enforces these rules:

1. **Visibility Separation**: Public functions (no underscore) before private functions (underscore prefix)
2. **Alphabetical Sorting**: Within each visibility scope, functions are sorted alphabetically
3. **Decorator Awareness**: Functions with certain decorators can be excluded from sorting

Example of correct organization:

.. code-block:: python

    # Public functions (alphabetically sorted)
    def calculate_total():
        pass

    def process_data():
        pass

    def validate_input():
        pass

    # Private functions (alphabetically sorted)
    def _format_output():
        pass

    def _helper_function():
        pass

Framework Integration
~~~~~~~~~~~~~~~~~~~~~

The plugin supports framework-aware sorting through decorator exclusions:

.. code-block:: python

    # These might need to stay in specific order due to framework requirements
    @app.route("/")
    def home():
        pass

    @app.route("/users")
    def users():
        pass

    # Regular functions still get sorted
    def calculate():
        pass

    def validate():
        pass

Advanced Features
-----------------

Import Analysis
~~~~~~~~~~~~~~~

The plugin can analyze cross-module imports to detect functions that should be private:

1. **Project Scanning**: Scans all Python files in the project
2. **Import Extraction**: Extracts ``import`` and ``from module import function`` statements
3. **Usage Detection**: Determines which functions are used outside their defining module
4. **Privacy Suggestions**: Suggests making functions private if they're only used internally

This is more accurate than simple heuristics and reduces false positives.

Testing Strategy
~~~~~~~~~~~~~~~~

The plugin uses PyLint's testing framework:

.. code-block:: python

    class TestFunctionSortChecker(CheckerTestCase):
        CHECKER_CLASS = FunctionSortChecker

        def test_unsorted_functions(self):
            node = astroid.extract_node("""
            def zebra(): pass
            def alpha(): pass
            """)
            # Test that violation is reported

Extending the Plugin
--------------------

Adding New Messages
~~~~~~~~~~~~~~~~~~~

1. Add message definition to ``messages.py``
2. Use it in checker with ``self.add_message()``
3. Add tests for the new message

Adding New Validation Rules
~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Add validation logic to ``utils.py``
2. Call from appropriate visitor method in ``checker.py``
3. Consider auto-fix support in ``auto_fix.py``

Framework Support
~~~~~~~~~~~~~~~~~

To add support for new frameworks:

1. Extend decorator pattern matching in ``utils.py``
2. Add framework-specific decorator patterns
3. Update configuration options
4. Add tests with framework-specific code

Development Workflow
--------------------

Setting Up Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # or .venv-linux/bin/activate in WSL

    # Install in development mode
    pip install -e .

    # Install development dependencies
    pip install pytest mypy ruff coverage

    # Install pre-commit hooks
    pre-commit install

Testing the Plugin
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Run unit tests
    pytest tests/

    # Test plugin with PyLint
    pylint --load-plugins=pylint_sort_functions src/

    # Test auto-fix tool
    python -m pylint_sort_functions.cli --dry-run src/

Code Quality Checks
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Type checking
    mypy src/ tests/

    # Linting and formatting
    ruff check src tests
    ruff format src tests

    # Coverage (must be 100%)
    coverage run -m pytest tests
    coverage report -m

Debugging Tips
--------------

AST Inspection
~~~~~~~~~~~~~~

To understand AST structure:

.. code-block:: python

    import astroid
    code = """
    def function_name():
        pass
    """
    tree = astroid.parse(code)
    print(tree.repr_tree())  # Shows AST structure

PyLint Integration Debug
~~~~~~~~~~~~~~~~~~~~~~~~

To debug PyLint integration:

.. code-block:: bash

    # Run with verbose output
    pylint --load-plugins=pylint_sort_functions --verbose src/

    # Enable specific message types
    pylint --enable=unsorted-functions src/

    # Disable other checkers to focus on sorting
    pylint --load-plugins=pylint_sort_functions --disable=all --enable=unsorted-functions src/

Performance Considerations
--------------------------

The plugin is designed for good performance:

**AST Parsing**: PyLint handles AST parsing, plugin only analyzes existing nodes
**Single Pass**: Each file is processed once during PyLint's normal operation
**Import Analysis**: Only performed when necessary, with caching opportunities
**Memory Usage**: Minimal additional memory usage beyond PyLint's normal operation

For large projects, the import analysis feature may add some overhead, but it can be disabled if needed.

Conclusion
----------

The ``pylint-sort-functions`` plugin demonstrates a complete PyLint plugin implementation with:

- Proper integration with PyLint's plugin system
- AST-based code analysis using ``astroid``
- Comprehensive message definitions and error reporting
- Advanced features like import analysis and auto-fixing
- Framework-aware sorting with decorator exclusions
- Thorough testing using PyLint's testing framework

The modular architecture makes it easy to extend and maintain while providing a solid foundation for enforcing code organization standards.
