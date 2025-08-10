Privacy Fixer System
====================

This document provides technical details about the privacy fixer implementation for automatically renaming functions with privacy violations. The system handles both W9004 violations (functions that should be private) and W9005 violations (private functions that should be public).

Overview
--------

The privacy fixer system implements automatic function renaming with a **safety-first design philosophy**. It identifies privacy violations through bidirectional analysis:

- **W9004 Detection**: Public functions that should be private (add underscore prefix)
- **W9005 Detection**: Private functions that should be public (remove underscore prefix)

The system can automatically apply these renames, but only when it can guarantee the safety of the operation.

**Core Principle**: Better to skip a function than to rename it incorrectly.

The system operates in four phases:

1. **Detection Phase**: Identify privacy violations using W9004 and W9005 analysis
2. **Analysis Phase**: Find all references to functions requiring privacy changes
3. **Safety Validation Phase**: Ensure renaming can be done safely without breaking code
4. **Renaming Phase**: Apply the actual renames and update all references
5. **Optional Sorting Phase**: Automatically resort functions after privacy fixes with ``--auto-sort``

Design Philosophy
-----------------

Safety-First Architecture
~~~~~~~~~~~~~~~~~~~~~~~~~

The implementation prioritizes safety over completeness:

- **Conservative Approach**: Only rename functions where ALL references can be found and validated
- **Comprehensive Analysis**: Analyze all possible reference types (calls, assignments, decorators, etc.)
- **Validation Guards**: Multiple safety checks prevent unsafe operations
- **Dry-Run Support**: Preview changes before applying them
- **Backup Creation**: Automatic backup files for safety

**Trade-off**: Some valid renamings may be skipped to ensure zero false positives.

User Control and Transparency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Explicit Opt-in**: Users must explicitly request privacy fixes (``--fix-privacy`` flag)
- **Clear Reporting**: Detailed reports explain what can/cannot be renamed and why
- **Incremental Processing**: Users can apply fixes file-by-file for better control
- **Rollback Support**: Backup files allow easy rollback of changes

Architecture Overview
---------------------

Core Components
~~~~~~~~~~~~~~~

The privacy fixer consists of three main classes:

.. code-block:: text

    ┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │ FunctionReference │    │  RenameCandidate │    │   PrivacyFixer   │
    │                 │    │                  │    │                  │
    │ - AST node      │    │ - Function node  │    │ - Analysis logic │
    │ - Location info │    │ - Old/new names  │    │ - Safety checks  │
    │ - Context type  │    │ - References     │    │ - Apply renames  │
    │                 │    │ - Safety status  │    │ - Generate report│
    └─────────────────┘    └──────────────────┘    └──────────────────┘

**Data Flow**:

.. code-block:: text

    Module AST -> Find References -> Safety Validation -> Rename Application
                       |                       |                      |
                       v                       v                      v
              FunctionReference    RenameCandidate      Updated Source

Integration Points
~~~~~~~~~~~~~~~~~~

The privacy fixer integrates with existing system components:

- **W9004 Detection**: Uses existing ``should_function_be_private()`` logic from ``utils.py``
- **AST Analysis**: Leverages same ``astroid`` infrastructure as the PyLint plugin
- **CLI Integration**: Extends existing CLI with ``--fix-privacy`` argument
- **Configuration**: Respects existing ``public-api-patterns`` configuration

Implementation Details
----------------------

1. FunctionReference Class
~~~~~~~~~~~~~~~~~~~~~~~~~~

Represents a single reference to a function within a module.

.. code-block:: python

    class FunctionReference(NamedTuple):
        """Represents a reference to a function within a module."""

        node: nodes.NodeNG      # AST node containing the reference
        line: int               # Line number of the reference
        col: int                # Column offset of the reference
        context: str            # Type of reference

**Reference Context Types**:

- ``"call"``: Function call (``function_name()``)
- ``"assignment"``: Variable assignment (``var = function_name``)
- ``"decorator"``: Decorator usage (``@function_name``)
- ``"reference"``: Generic name reference

**Usage Example**:

.. code-block:: python

    # For code: result = helper_function()
    ref = FunctionReference(
        node=call_node,
        line=42,
        col=12,
        context="call"
    )

2. RenameCandidate Class
~~~~~~~~~~~~~~~~~~~~~~~~

Represents a function that potentially can be renamed to private.

.. code-block:: python

    class RenameCandidate(NamedTuple):
        """Represents a function that can be safely renamed."""

        function_node: nodes.FunctionDef    # Original function AST node
        old_name: str                       # Current function name
        new_name: str                       # Proposed private name
        references: List[FunctionReference] # All found references
        is_safe: bool                      # Safety validation result
        safety_issues: List[str]           # Reasons if unsafe

**Lifecycle**:

1. **Creation**: Built from W9004 detection results
2. **Reference Analysis**: Populated with all found references
3. **Safety Validation**: ``is_safe`` and ``safety_issues`` determined
4. **Processing**: Either applied (if safe) or skipped (if unsafe)

**Status Examples**:

.. code-block:: python

    # Safe to rename
    safe_candidate = RenameCandidate(
        function_node=func_ast,
        old_name="helper_function",
        new_name="_helper_function",
        references=[ref1, ref2],
        is_safe=True,
        safety_issues=[]
    )

    # Unsafe to rename
    unsafe_candidate = RenameCandidate(
        function_node=func_ast,
        old_name="complex_function",
        new_name="_complex_function",
        references=[ref1],
        is_safe=False,
        safety_issues=["Function name found in string literals"]
    )

3. PrivacyFixer Class
~~~~~~~~~~~~~~~~~~~~~

Main orchestration class that coordinates the privacy fixing process.

.. code-block:: python

    class PrivacyFixer:
        """Handles automatic renaming of functions that should be private."""

        def __init__(self, dry_run: bool = False, backup: bool = True):
            self.dry_run = dry_run      # Preview mode
            self.backup = backup        # Create .bak files

**Key Methods**:

**analyze_module()** - *✅ IMPLEMENTED*
    Entry point for analyzing a module and identifying rename candidates using W9004/W9005 detection.

**find_function_references()** - *✅ IMPLEMENTED*
    Core reference detection using AST traversal with comprehensive pattern matching.

**is_safe_to_rename()** - *✅ IMPLEMENTED*
    Safety validation system with multiple conservative checks for name conflicts and dynamic references.

**apply_renames()** - *✅ IMPLEMENTED*
    Apply validated renames to source code with atomic operations and backup creation.

**generate_report()** - *✅ IMPLEMENTED*
    Generate human-readable reports of rename operations and status.

Reference Detection Algorithm
-----------------------------

The reference detection system uses recursive AST traversal to find all possible references to a target function.

AST Traversal Strategy
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def find_function_references(self, function_name: str, module_ast: nodes.Module):
        """Find all references using recursive AST traversal."""

        references = []
        decorator_nodes = set()  # Prevent double-counting

        def _check_node(node):
            # 1. Check for function calls
            # 2. Check for decorator usage
            # 3. Check for name references
            # 4. Recursively process children
            pass

        _check_node(module_ast)
        return references

**Reference Type Detection**:

1. **Function Calls**:

   .. code-block:: python

       # Detects: function_name()
       if isinstance(node, nodes.Call):
           if isinstance(node.func, nodes.Name) and node.func.name == function_name:
               # Found function call
               pass

2. **Decorator References**:

   .. code-block:: python

       # Detects: @function_name
       if hasattr(node, 'decorators') and node.decorators:
           for decorator in node.decorators.nodes:
               if isinstance(decorator, nodes.Name) and decorator.name == function_name:
                   # Found decorator usage
                   pass

3. **Assignment References**:

   .. code-block:: python

       # Detects: var = function_name
       if isinstance(node, nodes.Name) and node.name == function_name:
           if isinstance(node.parent, nodes.Assign):
               # Found assignment reference
               pass

**Duplicate Prevention**:

The algorithm prevents double-counting of decorator nodes that appear both as decorators and as name references during AST traversal:

.. code-block:: python

    decorator_nodes = set()

    # Mark decorator nodes to prevent double-counting
    decorator_nodes.add(id(decorator))

    # Skip if already processed as decorator
    if id(node) in decorator_nodes:
        pass

**Edge Cases Handled**:

- **Function Definitions**: Skips the function definition itself
- **Call Node Functions**: Avoids double-counting ``func`` in ``func()``
- **Complex Decorators**: Handles ``@module.decorator`` patterns
- **Nested References**: Recursively finds references in nested scopes

Safety Validation System
-------------------------

The safety validation system implements multiple conservative checks to ensure renaming operations won't break code.

Validation Categories
~~~~~~~~~~~~~~~~~~~~~

1. **Name Conflict Detection**
   *Status: ✅ Fully implemented with module AST scanning*

   Checks if the proposed private name already exists:

   .. code-block:: python

       def _has_name_conflict(self, candidate: RenameCandidate) -> bool:
           # Check module AST for existing function with new_name
           # Conservative approach: assumes conflict if check fails
           return False  # or True on exception

2. **Dynamic Reference Detection**
   *Status: ✅ Framework implemented with conservative detection*

   Identifies dynamic references that can't be safely renamed:

   .. code-block:: python

       # These patterns make renaming unsafe:
       getattr(obj, "function_name")         # Dynamic attribute access
       hasattr(obj, "function_name")         # Dynamic attribute check
       setattr(obj, "function_name", value)  # Dynamic attribute setting
       eval("function_name()")               # Code evaluation
       exec("result = function_name()")      # Code execution

3. **String Literal Detection**
   *Status: ✅ Framework implemented with conservative validation*

   Finds function names embedded in string literals:

   .. code-block:: python

       # These make renaming potentially unsafe:
       sql_query = "SELECT * FROM helper_function_results"
       log_message = f"Calling helper_function with args {args}"
       documentation = """The helper_function does..."""

4. **Reference Context Validation**
   *Status: ✅ Implemented*

   Ensures all references are in contexts we can handle:

   .. code-block:: python

       def validate_contexts(candidate):
           safe_contexts = {"call", "assignment", "decorator", "reference"}
           issues = []

           # Any reference in an unknown context is considered unsafe
           for ref in candidate.references:
               if ref.context not in safe_contexts:
                   issues.append(f"Unsafe context: {ref.context}")

           return len(issues) == 0

Conservative Safety Design
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Default to Unsafe**: When validation cannot be completed, the system assumes unsafe conditions.

.. code-block:: python

    def _has_name_conflict(self, candidate: RenameCandidate) -> bool:
        try:
            # Attempt to check for conflicts
            return self._check_module_for_conflicts(candidate)
        except Exception:
            return True  # Conservative: assume conflict exists

**Multiple Validation Layers**: All checks must pass for a rename to be considered safe:

.. code-block:: python

    def is_safe_to_rename(self, candidate: RenameCandidate) -> Tuple[bool, List[str]]:
        issues = []

        if self._has_name_conflict(candidate):
            issues.append("Name conflict detected")

        if self._has_dynamic_references(candidate):
            issues.append("Dynamic references found")

        if self._has_string_references(candidate):
            issues.append("String references found")

        # All checks must pass
        return len(issues) == 0, issues

Integration with Privacy Detection System
------------------------------------------

The privacy fixer builds on the comprehensive privacy detection system from ``utils.py`` which includes both W9004 and W9005 detection.

Detection Integration
~~~~~~~~~~~~~~~~~~~~~

**Bidirectional Detection Logic** (in ``utils.py``):

.. code-block:: python

    def should_function_be_private(
        func: nodes.FunctionDef,
        module_path: Path,
        project_root: Path,
        public_patterns: Optional[Set[str]] = None,
    ) -> bool:
        """Detect if a public function should be private based on import analysis."""

    def should_function_be_public(
        func: nodes.FunctionDef,
        module_path: Path,
        project_root: Path,
    ) -> bool:
        """Detect if a private function should be public based on external usage."""

**Privacy Fixer Integration**:

.. code-block:: python

    def analyze_module(self, module_path: Path, project_root: Path,
                      public_patterns: Optional[Set[str]] = None) -> List[RenameCandidate]:
        """Identify privacy violations using W9004/W9005 detection."""
        # Implementation:
        # 1. Parse module AST
        # 2. Extract all functions
        # 3. Use should_function_be_private() for W9004 candidates
        # 4. Use should_function_be_public() for W9005 candidates
        # 5. Build RenameCandidate objects
        # 6. Run reference detection and safety validation

**Configuration Consistency**:

Both systems respect the same configuration options:

- ``public-api-patterns``: Functions to treat as public API
- ``enable-privacy-detection``: Whether to perform privacy analysis
- ``privacy-exclude-dirs``: Directories to exclude from privacy analysis
- ``privacy-exclude-patterns``: File patterns to exclude from privacy analysis
- ``privacy-additional-test-patterns``: Additional test file patterns
- ``privacy-update-tests``: Enable automatic test file updates
- ``privacy-override-test-detection``: Override built-in test detection

For detailed configuration examples and real-world use cases, see :doc:`usage`.

Test File Exclusion System
~~~~~~~~~~~~~~~~~~~~~~~~~~~

As of version 1.3.2, the privacy detection system includes enhanced test file exclusion to prevent functions used only by tests from being incorrectly marked as private.

**Technical Implementation**:

The ``_is_unittest_file()`` function in ``utils.py`` implements comprehensive test file detection:

.. code-block:: python

    def _is_unittest_file(module_name: str) -> bool:
        """Check if a module name indicates a unit test file."""
        # Split into path components for precise matching
        parts = module_name.lower().split('.')

        # Check for test directories
        if 'tests' in parts or 'test' in parts:
            return True

        # Check file name patterns
        if parts:
            filename = parts[-1]
            if filename.startswith('test_') or filename.endswith('_test'):
                return True
            if filename == 'conftest':  # pytest configuration
                return True

        return 'test' in module_name.lower()  # Fallback

**Integration with Cross-Module Analysis**:

Test file exclusion is applied during the import analysis phase in ``_build_cross_module_usage_graph()``:

.. code-block:: python

    for file_path in python_files:
        module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")

        # Skip test files from privacy analysis
        if module_name.endswith("__init__") or _is_unittest_file(module_name):
            continue  # Exclude from usage tracking

**Impact on Privacy Detection**:

- **W9004 (should be private)**: Functions used only by tests will be marked as candidates for privatization since test usage is excluded from external usage calculations
- **W9005 (should be public)**: Private functions used by tests won't be flagged as needing to be public, preventing false positives from test code
- **Safety**: Prevents breaking test imports while maintaining accurate privacy detection for production code relationships

**Detected Test Patterns**:

.. code-block:: text

    tests/test_module.py          ✓ Excluded (tests/ directory)
    src/tests/helpers.py          ✓ Excluded (tests/ in path)
    test_integration.py           ✓ Excluded (test_ prefix)
    utils_test.py                 ✓ Excluded (_test suffix)
    conftest.py                   ✓ Excluded (pytest config)
    my_test_file.py              ✓ Excluded (contains 'test')

This addresses `GitHub issue #26 <https://github.com/hakonhagland/pylint-sort-functions/issues/26>`_ which identified incomplete test file detection causing test imports to break when functions were incorrectly privatized.

Test File Update System (Phase 2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Implemented in Version 2.0+** - *Status: ✅ COMPLETED*

As of Phase 2 implementation (GitHub issue #28), the privacy fixer includes automatic test file update functionality that resolves the fundamental limitation where 100% test coverage prevented any functions from being privatized.

**Problem Solved**: Previously, functions used by tests could not be privatized because test usage was excluded from analysis. This created a limitation where well-tested codebases couldn't benefit from privacy detection.

**Solution**: The system now automatically updates test files when functions are privatized, enabling production code to drive API design while keeping all tests working.

**Core Components**:

.. code-block:: python

    class TestReference(NamedTuple):
        """Represents a reference to a function within a test file."""

        file_path: Path
        line: int
        col: int
        context: str              # "import", "mock_patch", "call", etc.
        reference_text: str       # The actual text that needs to be replaced

**Enhanced RenameCandidate**:

.. code-block:: python

    class RenameCandidate(NamedTuple):
        """Represents a function that can be safely renamed."""

        function_node: nodes.FunctionDef
        old_name: str
        new_name: str
        references: List[FunctionReference]
        test_references: List[TestReference]  # NEW: references from test files
        is_safe: bool
        safety_issues: List[str]

**Test File Update Process**:

1. **Test File Detection**: Uses existing test detection logic to find all test files
2. **Reference Scanning**: Finds function references in test files via dual approach:
   - **AST-based**: Import statements parsing with astroid
   - **String-based**: Mock patch patterns via regex
3. **Safe Updates**: Backup creation, atomic updates, syntax validation, rollback on failure

**Reference Types Handled**:

**Import Statements**:

.. code-block:: python

    # Before privatization:
    from src.module import helper_function, other_func

    # After automatic update:
    from src.module import _helper_function, other_func

**Mock Patch Decorators**:

.. code-block:: python

    # Before:
    @patch('src.module.helper_function')
    def test_with_mock(mock_helper):
        result = helper_function()

    # After automatic update:
    @patch('src.module._helper_function')
    def test_with_mock(mock_helper):
        result = _helper_function()  # Import statement also updated

**Mocker Patch Calls**:

.. code-block:: python

    # Before:
    def test_with_mocker(mocker):
        mocker.patch('src.module.helper_function', return_value='mocked')
        result = helper_function()

    # After automatic update:
    def test_with_mocker(mocker):
        mocker.patch('src.module._helper_function', return_value='mocked')
        result = _helper_function()

**Multi-line Import Support**:

.. code-block:: python

    # Before:
    from src.module import (
        helper_function,
        other_func,
        third_func
    )

    # After automatic update:
    from src.module import (
        _helper_function,
        other_func,
        third_func
    )

**Safety Mechanisms**:

1. **Backup Creation**: Automatic `.bak` files for all modified test files
2. **Syntax Validation**: AST parsing validation after updates
3. **Atomic Operations**: Either all updates succeed or all are rolled back
4. **Error Recovery**: Graceful handling of update failures with detailed reporting

**Implementation Details**:

**Test File Update Methods**:

.. code-block:: python

    class PrivacyFixer:
        def update_test_file(self, test_file: Path, old_name: str,
                           new_name: str, test_references: List[TestReference]) -> Dict[str, Any]:
            """Main entry point for safely updating test files."""

        def _update_import_statements(self, test_file: Path, old_name: str,
                                    new_name: str, test_references: List[TestReference]) -> bool:
            """Update import statements using AST-based modifications."""

        def _update_mock_patterns(self, test_file: Path, old_name: str,
                                new_name: str, test_references: List[TestReference]) -> bool:
            """Update mock patch patterns using string-based modifications."""

**Integration with apply_renames()**:

.. code-block:: python

    def apply_renames(self, candidates: List[RenameCandidate],
                     project_root: Optional[Path] = None) -> Dict[str, Any]:
        """Enhanced to include test file updates when project_root is provided."""

        # 1. Apply renames to production files
        # 2. If project_root provided and renames successful:
        #    - Find all test files in project
        #    - Update test files for each renamed function
        #    - Report test file update results

**CLI Integration**:

.. code-block:: bash

    # Automatic test file updates when project root is available
    pylint-sort-functions --fix-privacy src/

    # Output includes test file update reporting:
    # Renamed 3 functions.
    # Updated 5 test files.

**Benefits Achieved**:

1. **Production-Driven API Design**: Production code relationships determine privacy, not test usage
2. **100% Test Coverage Compatible**: Well-tested codebases can now use privacy detection effectively
3. **No Broken Tests**: All test imports and mocks automatically updated to use new private names
4. **Safe Operations**: Comprehensive backup and rollback mechanisms prevent test breakage
5. **Transparent Process**: Clear reporting of test file modifications

**Example Workflow**:

.. code-block:: python

    # Production file: src/utils.py
    def helper_function():  # Should be private (only used internally)
        return "help"

    def public_api():       # Correctly public (used by other modules)
        return helper_function()

.. code-block:: python

    # Test file: tests/test_utils.py
    from src.utils import helper_function, public_api

    @patch('src.utils.helper_function')
    def test_helper(mock_helper):
        result = helper_function()
        assert result

.. code-block:: bash

    # Privacy fixer detects helper_function should be private
    pylint-sort-functions --fix-privacy src/

**Results**:

.. code-block:: python

    # Production file: src/utils.py (updated)
    def _helper_function():  # Now correctly private
        return "help"

    def public_api():        # Calls updated to use private name
        return _helper_function()

.. code-block:: python

    # Test file: tests/test_utils.py (automatically updated)
    from src.utils import _helper_function, public_api

    @patch('src.utils._helper_function')
    def test_helper(mock_helper):
        result = _helper_function()
        assert result

**Error Handling**:

- **Syntax Errors**: Automatic rollback if test file updates create invalid syntax
- **File Access Issues**: Graceful handling of permission errors or locked files
- **Partial Failures**: Detailed reporting of which test files succeeded/failed
- **Best Effort Recovery**: Restore original content from backups when possible

This advancement represents a significant improvement in the privacy fixer's practical utility, making it effective for real-world codebases with comprehensive test coverage.

CLI Integration
---------------

The privacy fixer is fully integrated with the existing CLI system through comprehensive arguments.

Implemented CLI Arguments
~~~~~~~~~~~~~~~~~~~~~~~~~

**--fix-privacy**
    *Status: ✅ IMPLEMENTED*

    Enable automatic privacy fixing mode:

    .. code-block:: bash

        pylint-sort-functions --fix-privacy src/

    **Behavior**:
    - Identifies W9004 violations (functions that should be private)
    - Identifies W9005 violations (private functions that should be public)
    - Performs comprehensive safety analysis
    - Applies safe renames automatically
    - Reports unsafe cases for manual review
    - Creates backup files for safety

**--privacy-dry-run**
    *Status: ✅ IMPLEMENTED*

    Preview privacy fixes without applying them:

    .. code-block:: bash

        pylint-sort-functions --fix-privacy --privacy-dry-run src/

**--auto-sort**
    *Status: ✅ IMPLEMENTED*

    Automatically resort functions after privacy fixes:

    .. code-block:: bash

        pylint-sort-functions --fix-privacy --auto-sort src/

    **Output Example**:

    .. code-block:: text

        Privacy Fix Analysis:

        ✅ Can safely rename 2 functions:
          • helper_function → _helper_function (3 references)
          • utility_func → _utility_func (1 reference)

        ⚠️  Cannot safely rename 1 function:
          • complex_helper: Function name found in string literals

**Integration with Existing Options**:

The privacy fixer respects existing configuration:

.. code-block:: bash

    # Respect public API patterns
    pylint-sort-functions --fix-privacy --public-patterns "main,setup,run" src/

    # Create backups (default behavior)
    pylint-sort-functions --fix-privacy --backup src/

    # Disable backups
    pylint-sort-functions --fix-privacy --no-backup src/

Error Handling and Edge Cases
------------------------------

The system handles various error conditions gracefully.

File System Errors
~~~~~~~~~~~~~~~~~~~

- **Permission Errors**: Skip files that cannot be read/written
- **Missing Files**: Report clearly and continue with remaining files
- **Backup Failures**: Abort rename if backup cannot be created (when enabled)

AST Parsing Errors
~~~~~~~~~~~~~~~~~~

- **Syntax Errors**: Skip files with invalid Python syntax
- **Encoding Issues**: Handle files with non-UTF-8 encoding gracefully
- **Large Files**: Process files of any size without memory issues

Reference Detection Edge Cases
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Import Aliases**:

.. code-block:: python

    from utils import helper_function as helper
    result = helper()  # Should be detected and renamed

**Nested Scopes**:

.. code-block:: python

    def outer():
        def inner():
            helper_function()  # Must be found in nested scope
        return inner

**Dynamic Code Patterns**:

.. code-block:: python

    # These make the function unsafe to rename
    func_name = "helper_function"
    globals()[func_name]()

    # String formatting with function names
    query = f"CALL {helper_function.__name__}()"

Implementation Status and Roadmap
----------------------------------

Current Implementation Status
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**✅ Completed Components**:

- **Core Architecture**: All four main classes fully implemented with comprehensive functionality (Phase 1 + 2)
- **Core API Methods**: detect_privacy_violations() method implemented with AST analysis
- **AST Function Analysis**: Complete function extraction with cross-module import analysis
- **Cross-Module Analysis**: Full import graph traversal to detect external function usage
- **Bidirectional Privacy Detection**: Both W9004 (should be private) and W9005 (should be public) detection
- **Reference Detection**: Complete AST traversal with comprehensive pattern matching for production and test files
- **Safety Validation System**: Multi-layer validation with name conflict detection and dynamic reference analysis
- **Rename Application System**: Atomic file operations with backup creation and rollback support
- **Test File Update System**: Automatic update of test files when functions are privatized (Phase 2)
- **CLI Integration**: Complete implementation of ``--fix-privacy``, ``--privacy-dry-run``, and ``--auto-sort`` arguments
- **Module Analysis**: Full integration with existing W9004/W9005 detection logic and configuration systems
- **Report Generation**: Human-readable status reports with detailed explanations and safety issue descriptions
- **Test Coverage**: Comprehensive test suite with 100% source code coverage including integration tests and Phase 2 functionality
- **Auto-Sort Integration**: Seamless workflow combining privacy fixes with automatic function sorting

**✅ Advanced Features Implemented**:

1. **Enhanced Safety Validation**

   - Name conflict detection with complete module AST scanning
   - Dynamic reference detection (getattr, eval, exec patterns)
   - String literal scanning for function name references
   - Comprehensive context validation with multiple safety layers

2. **Production-Ready CLI System**

   - Full argument parsing with error handling
   - Progress reporting and verbose output modes
   - Configuration integration with existing PyLint options
   - Backup file management with rollback support

3. **Integrated Workflow Support**

   - Privacy fixing followed by automatic function sorting
   - Consistent configuration across all tools
   - Performance optimization for large projects
   - Comprehensive error recovery and reporting

Development Status
~~~~~~~~~~~~~~~~~~

**✅ All Phases Complete (Including Phase 2 Enhancement)**:

**Phase 1: Core Safety System** *(COMPLETED)*
    Comprehensive safety validation system with multi-layer checks for all risk categories including name conflicts, dynamic references, and string literal detection.

**Phase 2: Test File Update System** *(COMPLETED - Issue #28)*
    Automatic test file update functionality that updates imports and mock patches when functions are privatized, enabling production code to drive API design while maintaining test compatibility.

**Phase 3: Rename Implementation** *(COMPLETED)*
    Full source code modification system with atomic operations, error recovery, and backup management.

**Phase 4: CLI Integration** *(COMPLETED)*
    Complete command-line interface integration with argument parsing, progress reporting, and configuration management.

**Phase 5: Testing and Optimization** *(COMPLETED)*
    Comprehensive integration testing, performance optimization, and complete documentation.

**Phase 2 Enhancements Completed**:

- **Test File Update Engine**: Automatic modification of test imports and mock patches
- **Dual Detection Strategy**: AST-based import updates + string-based mock pattern updates
- **Safe File Modification**: Backup creation, syntax validation, automatic rollback on failure
- **Multi-line Import Support**: Handles complex import statement formats
- **Comprehensive Test Coverage**: 15+ additional test cases for Phase 2 functionality

**Additional Enhancements Completed**:

- **W9005 Bidirectional Detection**: Private functions that should be public
- **Auto-Sort Integration**: Seamless privacy fixing + function sorting workflow
- **Advanced AST Processing**: Boundary detection improvements for complex Python constructs
- **Integration Test Suite**: End-to-end validation of CLI workflows

Usage Examples
--------------

The privacy fixer system is fully implemented and ready for production use.

Basic Privacy Fixing
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Analyze and fix privacy issues automatically
    pylint-sort-functions --fix-privacy src/

    # Preview changes without applying them
    pylint-sort-functions --fix-privacy --privacy-dry-run src/

**Example Output**:

.. code-block:: text

    Processing src/utils.py...
    Privacy Fix Analysis:

    ✅ Can safely rename 3 functions:
      • format_output → _format_output (2 references)
      • validate_input → _validate_input (4 references)
      • calculate_hash → _calculate_hash (1 reference)

    Applied 3 renames to src/utils.py
    Backup created: src/utils.py.bak

Integrated Privacy and Sorting Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Fix privacy issues and automatically resort functions
    pylint-sort-functions --fix-privacy --auto-sort src/

    # Combined operation with existing sorting fixes
    pylint-sort-functions --fix --fix-privacy --auto-sort src/

    # Configuration respects existing patterns
    pylint-sort-functions --fix-privacy --public-patterns "main,setup,handler" src/

**Integrated Workflow**:

1. Identify privacy violations (W9004: should be private, W9005: should be public)
2. Perform comprehensive safety analysis
3. Apply safe privacy renames with backup creation
4. Automatically resort functions with updated names (``--auto-sort``)
5. Generate detailed reports with safety explanations
6. Handle function sorting violations if ``--fix`` is also specified

**W9005 Detection Example**:

.. code-block:: python

    # Before: Private function used externally
    # utils.py contains:
    def _helper_function():  # Used by other modules
        return "help"

    # main.py imports it:
    from utils import _helper_function  # External usage detected

.. code-block:: bash

    # Privacy fixer detects W9005 and suggests:
    pylint-sort-functions --fix-privacy --auto-sort utils.py

.. code-block:: python

    # Result: Function renamed to public
    def helper_function():  # Now correctly public
        return "help"

Complex Project Example
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Large project with custom configuration
    pylint-sort-functions --fix-privacy \
        --public-patterns "main,run,setup,teardown,app_factory" \
        --verbose \
        --backup \
        src/ tests/

**Advanced Safety Example**:

.. code-block:: python

    # Before: Unsafe to rename due to string references
    def helper_function():
        return "help"

    def main():
        # This string reference makes renaming unsafe
        sql = "SELECT * FROM helper_function_cache"
        result = helper_function()

**Privacy Fixer Output**:

.. code-block:: text

    ⚠️  Cannot safely rename 1 function:
      • helper_function: Function name found in string literals
        Line 6: sql = "SELECT * FROM helper_function_cache"

This conservative approach prevents breaking SQL queries, log messages, or other string-based references to function names.

Testing Strategy
----------------

The privacy fixer includes comprehensive testing to ensure reliability and safety.

Unit Testing
~~~~~~~~~~~~

**Test Coverage Areas**:

- **Reference Detection**: All reference types and edge cases
- **Safety Validation**: Each validation rule with positive and negative cases
- **Report Generation**: Output formatting and content accuracy
- **Error Handling**: Graceful handling of invalid input and edge conditions

**Comprehensive Test Suite** (22+ tests, all passing):

**Unit Tests - Core Components**:

.. code-block:: bash

    tests/test_privacy_fixer.py::TestPrivacyFixer::test_initialization
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_find_function_references_*  # 8 test cases
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_safety_validation_*       # 6 test cases
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_generate_report_*         # 3 test cases
    tests/test_privacy_fixer.py::TestFunctionReference::test_*                    # 2 test cases
    tests/test_privacy_fixer.py::TestRenameCandidate::test_*                      # 2 test cases

**Integration Tests - Full Workflow**:

.. code-block:: bash

    tests/test_privacy_integration.py::TestPrivacyIntegration::test_*             # 5 test cases
    tests/test_cli.py::TestCLI::test_privacy_*                                    # 4 test cases

**W9005 Tests - Bidirectional Detection**:

.. code-block:: bash

    tests/test_utils.py::TestUtils::test_should_function_be_public_*              # 4 test cases
    tests/test_checker.py::TestChecker::test_w9005_*                              # 3 test cases

**Integration Test Project**:

.. code-block:: bash

    test-validation/test_privacy_cli_integration.py  # End-to-end CLI validation

Integration Testing
~~~~~~~~~~~~~~~~~~~

**Planned Integration Tests**:

- **End-to-End Workflow**: Complete privacy fixing process on real code samples
- **CLI Integration**: Command-line interface with various argument combinations
- **Configuration Integration**: Interaction with existing PyLint configuration options
- **Performance Testing**: Large codebase processing with timing measurements

Safety Testing
~~~~~~~~~~~~~~~

**Critical Safety Scenarios**:

- **False Positive Prevention**: Ensure safe functions are never incorrectly renamed
- **Partial Failure Handling**: Verify system behavior when some renames fail
- **Backup Integrity**: Confirm backup files allow complete rollback
- **Concurrent Access**: Handle files being modified during processing

**Test Data Sets**:

- **Safe Rename Cases**: Functions with clear, simple references
- **Unsafe Rename Cases**: Functions with dynamic references, string literals, conflicts
- **Edge Cases**: Complex inheritance, decorators, nested scopes, import aliases
- **Real-World Code**: Actual project code with realistic complexity

Conclusion
----------

The privacy fixer system provides a robust, safety-first approach to automatically renaming functions that should be private. The conservative design prioritizes correctness over completeness, ensuring that users can trust the automated renames while providing clear feedback about cases that require manual review.

**Key Strengths**:

- **Safety-First Design**: Multiple validation layers prevent incorrect renames
- **Comprehensive Analysis**: Finds all reference types through AST traversal
- **Clear User Feedback**: Detailed reports explain decisions and limitations
- **Integration**: Builds on existing W9004 detection and configuration systems
- **Testability**: Designed with comprehensive testing in mind

**Future Enhancement Opportunities**:

- **Machine Learning**: Could potentially improve dynamic reference detection
- **Interactive Mode**: Allow users to review and approve individual renames
- **Batch Processing**: Optimize for processing multiple files simultaneously
- **IDE Integration**: Provide integration points for development environments

The system represents a significant step forward in automated code organization while maintaining the safety and reliability standards expected in professional development environments.

See Also
--------

* :doc:`developer` - Complete development guide and architecture overview
* :doc:`sorting` - Function sorting rules and algorithm details
* :doc:`testing` - Testing strategies and validation approaches
* :doc:`api` - API reference for privacy fixer classes and methods
