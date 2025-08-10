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

Plugin Configuration
--------------------

The plugin supports configuration options that can be set in ``.pylintrc`` or ``pyproject.toml`` files to customize its behavior.

Configuration Options
~~~~~~~~~~~~~~~~~~~~~

**public-api-patterns**
    :Type: csv (comma-separated values)
    :Default: ``main,run,execute,start,stop,setup,teardown``
    :Description: List of function names to always treat as public API. These functions will not be flagged for privacy even if only used internally. Useful for entry points and framework callbacks.

    Example usage in ``.pylintrc``:

    .. code-block:: ini

        [function-sort]
        public-api-patterns = main,run,setup,teardown,app_factory

    Example usage in ``pyproject.toml``:

    .. code-block:: toml

        [tool.pylint."function-sort"]
        public-api-patterns = ["main", "run", "setup", "teardown", "app_factory"]

**enable-privacy-detection**
    :Type: yn (yes/no boolean)
    :Default: ``yes``
    :Description: Enable detection of functions that should be made private based on usage analysis. When enabled, the plugin performs cross-module import analysis to detect functions that are only used internally and suggests making them private.

    Example usage in ``.pylintrc``:

    .. code-block:: ini

        [function-sort]
        enable-privacy-detection = no

    Example usage in ``pyproject.toml``:

    .. code-block:: toml

        [tool.pylint."function-sort"]
        enable-privacy-detection = false

Configuration Integration
~~~~~~~~~~~~~~~~~~~~~~~~~

The plugin integrates with PyLint's configuration system through the ``options`` class attribute:

.. code-block:: python

    class FunctionSortChecker(BaseChecker):
        options = (
            ("public-api-patterns", {
                "default": ["main", "run", "execute", ...],
                "type": "csv",
                "help": "Function names to always treat as public API"
            }),
            ("enable-privacy-detection", {
                "default": True,
                "type": "yn",
                "help": "Enable privacy detection based on usage analysis"
            }),
        )

These options are accessible in checker methods via ``self.linter.config``, allowing the plugin to adapt its behavior based on project-specific requirements.

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

**Privacy Detection Methods**:

- ``_check_function_privacy(functions, node)``: Main privacy detection using import analysis
- ``_check_function_privacy_heuristic(functions, node)``: Fallback privacy detection (currently no-op)
- ``_get_module_path()``: Extract current module's file path from PyLint's linter
- ``_get_project_root(module_path)``: Find project root by searching for common markers

**Privacy Detection Process**:

1. **Configuration Check**: Verify ``enable-privacy-detection`` is enabled
2. **Path Resolution**: Get module path and determine project root directory
3. **Pattern Matching**: Collect ``public-api-patterns`` from configuration
4. **Import Analysis**: Use ``utils.should_function_be_private()`` to analyze cross-module usage
5. **Message Reporting**: Report ``W9004`` (function-should-be-private) for internal-only functions

The privacy detection gracefully falls back to heuristic mode when path information is unavailable (rare in normal PyLint usage).

**Automatic Privacy Fixing**: The plugin also includes an experimental privacy fixer system that can automatically rename functions identified by W9004 to be private. For complete technical details about the privacy fixer architecture, safety validation, and implementation status, see :doc:`privacy`.

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
- ``should_function_be_private(func, module_path, project_root, public_patterns=None)``: Detect functions that should be private based on cross-module import analysis

**Privacy Detection**:
The plugin includes sophisticated import analysis to suggest when public functions should be private:

**Function Signature**:

.. code-block:: python

    def should_function_be_private(
        func: nodes.FunctionDef,
        module_path: Path,
        project_root: Path,
        public_patterns: set[str] | None = None,
    ) -> bool:
        """Detect if a function should be private based on import analysis."""

**Detection Process**:

1. **Skip Already Private**: Functions with underscore prefix are ignored
2. **Skip Special Methods**: Dunder methods (``__init__``, ``__str__``) are ignored
3. **Apply Public Patterns**: Functions matching configurable patterns (``main``, ``run``, ``setup``) are treated as public API
4. **Cross-Module Analysis**: Uses ``_build_cross_module_usage_graph()`` to check if function is imported elsewhere
5. **Privacy Suggestion**: Returns ``True`` if function is only used internally

**Parameters**:

- ``func``: AST node of the function to analyze
- ``module_path``: File path of the current module (for relative path calculation)
- ``project_root``: Project root directory (for import scanning scope)
- ``public_patterns``: Custom public API patterns (defaults to ``main``, ``run``, ``execute``, etc.)

This real usage analysis provides accurate detection with minimal false positives.

**Helper Functions**:

- ``_is_dunder_method(func)``: Detects special methods like ``__init__``, ``__str__`` that should remain public
- ``_extract_attribute_accesses(tree, imported_modules, attribute_accesses)``: Analyzes AST for dot notation patterns (``module.function``) during import analysis
- ``_is_unittest_file(module_name)``: Identifies test files to exclude from API analysis (tests access internals without indicating public API)

These helper functions support the main import analysis workflow while maintaining code clarity and modularity.

5. Auto-fix Tool (``auto_fix.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Standalone tool for automatically reordering functions

**Key Classes**:

- ``AutoFixConfig``: Configuration for auto-fix behavior
- ``FunctionSorter``: Main auto-fix implementation
- ``FunctionSpan``: Represents a function with its text span in source

**Process**:

1. Parse file content with ``astroid`` (same as checker)
2. Extract function and method text spans from source **with comment preservation**
3. Sort functions/methods according to plugin rules (public first, then alphabetical within visibility scopes)
4. Reconstruct file content with sorted functions/methods and their associated comments

**Dual-Level Sorting Support**:

- **Module-Level Functions**: Sorts functions at the module level using ``_sort_module_functions()``
- **Class Method Sorting**: Sorts methods within each class using ``_sort_class_methods()``
- **Comment Preservation**: Both function and method sorting preserve associated comments
- **Mixed Content**: Handles files with both module functions and class methods simultaneously

**Comment Preservation Feature**:

The auto-fix tool preserves comments that belong to functions during reordering:

**Comment Detection Process**:

1. **Backward Scanning**: For each function, scan backwards from the function definition
2. **Comment Association**: Identify comment lines that precede the function (including decorators)
3. **Boundary Detection**: Determine where function-specific comments start vs. general file comments
4. **Span Calculation**: Include comment lines in the function's text span for movement

**Implementation Method**:

- ``_find_comments_above_function(lines, function_start_line)``: Scans backwards to find associated comments
- **Empty Line Handling**: Allows gaps between comments and function definitions
- **Decorator Support**: Comments above decorators are included with the function
- **Conservative Approach**: Only includes comments directly above functions to avoid misattribution

This ensures that functions retain their documentation and explanatory comments when reordered, maintaining code readability and intent.

**Key Auto-fix Methods**:

**Function/Method Extraction**:

- ``_extract_function_spans(functions, lines)``: Extract module-level function spans with comments
- ``_extract_method_spans(methods, lines, class_node)``: Extract class method spans with comments
- ``_find_comments_above_function(lines, function_start_line)``: Find and associate comments with functions

**Content Reconstruction**:

- ``_reconstruct_content_with_sorted_functions(content, original_spans, sorted_spans)``: Rebuild module with sorted functions
- ``_reconstruct_class_with_sorted_methods(content, original_spans, sorted_spans)``: Rebuild class with sorted methods

**Sorting Logic**:

- ``_sort_function_spans(spans)``: Apply sorting rules to function spans (public first, then alphabetical)
- ``_sort_module_functions(functions, content)``: Handle module-level function sorting workflow
- ``_sort_class_methods(methods, content, class_node)``: Handle class method sorting workflow

**Utility Methods**:

- ``_file_needs_sorting(content)``: Determine if file requires reordering (optimization)
- ``_sort_functions_in_content(content)``: Main entry point for content transformation

**Integration with Checker**: Uses the same utility functions as the checker for consistency.

6. Command-line Interface (``cli.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Purpose**: Provides CLI for the auto-fix tool

**CLI Operation Modes**:

1. **Check-Only Mode** (default): Shows recommendations without modifying files
2. **Dry-Run Mode** (``--dry-run``): Previews changes without modifying files
3. **Fix Mode** (``--fix``): Actually applies changes to files

**Key Features**:

- **File/Directory Processing**: Accepts single files, directories, or multiple paths
- **Path Validation**: Checks file/directory existence before processing
- **Backup Creation**: Automatically creates ``.bak`` files (can be disabled with ``--no-backup``)
- **Verbose Output** (``--verbose``, ``-v``): Detailed processing information and progress reporting
- **Decorator Exclusion Patterns**: Framework-aware sorting with ``--ignore-decorators`` (supports multiple patterns)
- **Exit Codes**: Standard exit codes for CI/CD integration (0=success, 1=error, 2=invalid usage)

**User Experience Features**:

- **Help Text**: Comprehensive usage instructions and examples
- **Error Handling**: Clear error messages with actionable guidance
- **Progress Reporting**: File-by-file processing status in verbose mode
- **Zero Dependencies**: Minimal installation footprint (only PyLint/astroid dependencies)

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

Sorting Algorithm
-----------------

The plugin implements a comprehensive sorting algorithm for organizing Python functions and methods. For complete details about sorting rules, examples, and configuration options, see :doc:`sorting`.

**Key Implementation Points:**

- **Dual-Level Processing**: Handles both module-level functions and class methods
- **AST-Based Analysis**: Uses ``astroid`` for consistent parsing with PyLint
- **Comment Preservation**: Maintains function-associated comments during reordering
- **Section Header Integration**: Optional automatic insertion of organizational headers
- **Framework Compatibility**: Supports decorator-based exclusions for frameworks

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

The plugin analyzes cross-module imports to detect functions that should be private:

1. **Project Scanning**: Scans all Python files in the project
2. **Import Extraction**: Extracts ``import`` and ``from module import function`` statements
3. **Usage Detection**: Determines which functions are used outside their defining module
4. **Privacy Suggestions**: Suggests making functions private if they're only used internally

This real usage analysis provides accurate detection with minimal false positives.

Testing Architecture
~~~~~~~~~~~~~~~~~~~~

The plugin uses a multi-layered testing strategy designed for comprehensive validation of plugin functionality.

**Test Organization**:

.. code-block:: text

   tests/
   ├── integration/              # End-to-end pytest tests
   │   ├── test_privacy_cli_integration.py    # CLI functionality
   │   ├── test_privacy_fixer_integration.py  # Privacy fixer API (all passing)
   │   └── test_privacy_fixer_simple.py       # Simplified CLI tests
   ├── files/                    # Test data and fixtures
   └── test_*.py                 # Unit tests (pytest + CheckerTestCase)

**Testing Frameworks**:

- **Unit Tests**: Use pytest with PyLint's ``CheckerTestCase`` for plugin-specific testing
- **Integration Tests**: Pure pytest for CLI and end-to-end functionality
- **Docker Validation**: Separate system for testing documentation examples

**Key Testing Patterns**:

**Plugin Testing with CheckerTestCase**:

.. code-block:: python

   from pylint.testutils import CheckerTestCase
   from pylint_sort_functions.checker import FunctionSortChecker

   class TestFunctionSortChecker(CheckerTestCase):
       CHECKER_CLASS = FunctionSortChecker

       def test_unsorted_functions(self):
           node = astroid.extract_node("""
           def zebra_function():  #@
               pass
           def alpha_function():
               pass
           """)
           with self.assertAddsMessages(
               pylint.testutils.MessageTest(msg_id="W9001", node=node)
           ):
               self.checker.visit_module(node)

**Integration Testing Approach**:

.. code-block:: python

   class TestCLIIntegration:
       def setup_method(self):
           self.test_dir = Path(tempfile.mkdtemp())

       def test_cli_functionality(self):
           # Create test files, run CLI, verify results
           result = subprocess.run([sys.executable, cli_script, args])
           assert result.returncode == 0

**Developer Testing Guidelines**:

1. **Unit Tests**: Add to ``tests/test_*.py`` for new utility functions or checker logic
2. **Integration Tests**: Add to ``tests/integration/`` for CLI or cross-module functionality
3. **Test Data**: Place fixtures in ``tests/files/`` organized by test type
4. **Coverage**: Maintain 100% coverage on source code (``src/`` directory)

**Running Tests During Development**:

.. code-block:: bash

   make test              # Unit tests only
   make test-integration  # Integration tests only
   make test-all         # All tests (unit + integration)
   make coverage         # Coverage report (must be 100%)

For complete testing documentation including Docker validation and framework testing, see :doc:`testing`.

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

Prerequisites
^^^^^^^^^^^^^

1. **Python Version Management** (recommended):

   Install `pyenv <https://github.com/pyenv/pyenv>`_ to manage multiple Python versions:

   - Install the Python versions listed in `.python-version <.python-version>`_
   - This ensures compatibility testing across supported versions

2. **Package Manager**:

   Install `uv <https://github.com/astral-sh/uv>`_ for fast, reliable dependency management:

   .. code-block:: bash

      # Linux and macOS
      curl -LsSf https://astral.sh/uv/install.sh | sh
      export PATH="$HOME/.cargo/bin:$PATH"

      # Windows (PowerShell)
      powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
      # Add %USERPROFILE%\.cargo\bin to your PATH

3. **Make command** (Windows only):

   - Install via `Chocolatey <https://chocolatey.org/install>`_: ``choco install make``
   - Or use `Git Bash <https://git-scm.com/download/win>`_ which includes ``make``

Environment Setup
^^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Create virtual environment (uses first Python version from .python-version)
    uv venv

    # Activate virtual environment
    source .venv/bin/activate      # Linux/macOS
    .venv\Scripts\activate          # Windows

    # Install dependencies
    uv sync                         # Uses default Python version
    # or specify version:
    uv sync --python=3.11

    # Install pre-commit hooks
    pre-commit install --hook-type pre-commit
    pre-commit install --hook-type commit-msg

    # Verify setup
    make pre-commit                 # Run all pre-commit checks
    make test                       # Run test suite
    make coverage                   # Generate coverage report

Alternative Setup (pip)
^^^^^^^^^^^^^^^^^^^^^^^

If you prefer traditional pip:

.. code-block:: bash

    # Create virtual environment
    python -m venv .venv
    source .venv/bin/activate  # or .venv\Scripts\activate on Windows

    # Install in development mode
    pip install -e .

    # Install development dependencies
    pip install pytest mypy ruff coverage pre-commit

Testing & Quality Assurance
~~~~~~~~~~~~~~~~~~~~~~~~~~~

See :doc:`testing` for complete testing documentation, including:

- Unit testing with PyLint's framework
- Plugin integration testing
- Docker validation system for documentation examples
- Framework-specific integration testing

Quick test commands:

.. code-block:: bash

    make test                    # Run unit tests
    make test-plugin             # Test plugin with PyLint
    make test-documentation      # Validate all documentation examples

Code Quality Checks
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Type checking
    mypy src/ tests/

    # Linting and formatting
    ruff check src tests
    ruff format src tests

    # Coverage (must be 100% on source code in src/)
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

The plugin is designed for good performance with intelligent caching optimizations:

Core Performance Features
~~~~~~~~~~~~~~~~~~~~~~~~~

- **AST Parsing**: PyLint handles AST parsing, plugin only analyzes existing nodes
- **Single Pass**: Each file is processed once during PyLint's normal operation
- **Lazy Evaluation**: Import analysis only performed when privacy detection is enabled
- **Memory Usage**: Minimal additional memory usage beyond PyLint's normal operation

Caching Optimizations
~~~~~~~~~~~~~~~~~~~~~

The plugin uses Python's ``@lru_cache`` decorator for significant performance improvements:

**File Import Analysis Caching** (``@lru_cache(maxsize=128)``):

- Function: ``_extract_imports_from_file()``
- **Performance Impact**: 50%+ improvement for projects with 100+ files
- **Cache Key**: File path + modification time (ensures cache invalidation on file changes)
- **Benefit**: Prevents redundant AST parsing of the same files during analysis

**Cross-Module Usage Graph Caching** (``@lru_cache(maxsize=1)``):

- Function: ``_build_cross_module_usage_graph()``
- **Performance Impact**: Up to 146x speedup for repeated import analysis
- **Cache Key**: Project root path
- **Benefit**: Entire project scan is cached during a single PyLint run

**File Modification Time Tracking**:

.. code-block:: python

    # Cache invalidation strategy
    file_mtime = file_path.stat().st_mtime
    imports = _extract_imports_from_file(file_path, file_mtime)

This ensures cache correctness when files change between analysis runs.

**Directory Filtering**:

The plugin automatically skips performance-impacting directories:

- ``__pycache__/``, ``.pytest_cache/``, ``.mypy_cache/``
- ``.git/``, ``.svn/``, ``.venv/``, ``node_modules/``
- ``dist/``, ``build/``, ``*.egg-info/``

Performance Benchmarks
~~~~~~~~~~~~~~~~~~~~~~

**Small Projects** (< 50 files):

- Negligible performance impact
- Import analysis adds ~50-100ms

**Medium Projects** (50-200 files):

- With caching: ~200-500ms additional overhead
- Without caching: ~2-5 seconds (4-10x slower)

**Large Projects** (200+ files):

- With caching: ~500ms-1s additional overhead
- Without caching: ~10+ seconds (20x+ slower)
- 146x speedup observed in real-world codebases

**Disabling Privacy Detection**:

For performance-critical environments, privacy detection can be disabled:

.. code-block:: ini

    [function-sort]
    enable-privacy-detection = no

This reduces the plugin to near-zero performance overhead while maintaining all sorting functionality.

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

See Also
--------

* :doc:`release` - Release management and changelog workflow for contributors
* :doc:`claude` - Specific guidelines for Claude Code AI assistant
* :doc:`testing` - Comprehensive testing guide
* :doc:`api` - Complete API reference
