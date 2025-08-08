Privacy Fixer System
====================

This document provides technical details about the privacy fixer implementation for automatically renaming functions that should be private (identified by W9004 violations).

Overview
--------

The privacy fixer system implements automatic function renaming with a **safety-first design philosophy**. It identifies functions that should be private (detected by W9004 warnings) and can automatically rename them by adding underscore prefixes, but only when it can guarantee the safety of the operation.

**Core Principle**: Better to skip a function than to rename it incorrectly.

The system operates in three phases:

1. **Analysis Phase**: Identify functions that should be private and find all their references
2. **Safety Validation Phase**: Ensure renaming can be done safely without breaking code
3. **Renaming Phase**: Apply the actual renames and update all references

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

**analyze_module()** - *🚧 TODO: Implementation pending*
    Entry point for analyzing a module and identifying rename candidates.

**find_function_references()** - *✅ IMPLEMENTED*
    Core reference detection using AST traversal with comprehensive pattern matching.

**is_safe_to_rename()** - *✅ IMPLEMENTED (basic validation)*
    Safety validation system with multiple conservative checks.

**apply_renames()** - *🚧 TODO: Implementation pending*
    Apply validated renames to source code with atomic operations.

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
   *Status: 🚧 Basic framework implemented, full implementation pending*

   Checks if the proposed private name already exists:

   .. code-block:: python

       def _has_name_conflict(self, candidate: RenameCandidate) -> bool:
           # TODO: Check module AST for existing function with new_name
           # For now, conservatively assumes no conflicts
           return False

2. **Dynamic Reference Detection**
   *Status: 🚧 Framework implemented, detection logic pending*

   Identifies dynamic references that can't be safely renamed:

   .. code-block:: python

       # These patterns make renaming unsafe:
       getattr(obj, "function_name")         # Dynamic attribute access
       hasattr(obj, "function_name")         # Dynamic attribute check
       setattr(obj, "function_name", value)  # Dynamic attribute setting
       eval("function_name()")               # Code evaluation
       exec("result = function_name()")      # Code execution

3. **String Literal Detection**
   *Status: 🚧 Framework implemented, scanning pending*

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

Integration with Existing W9004 Detection
------------------------------------------

The privacy fixer builds on the existing W9004 (function-should-be-private) detection system from ``utils.py``.

Detection Integration
~~~~~~~~~~~~~~~~~~~~~

**Existing Detection Logic** (in ``utils.py``):

.. code-block:: python

    def should_function_be_private(
        func: nodes.FunctionDef,
        module_path: Path,
        project_root: Path,
        public_patterns: Optional[Set[str]] = None,
    ) -> bool:
        """Detect if a function should be private based on import analysis."""

**Privacy Fixer Integration**:

.. code-block:: python

    def analyze_module(self, module_path: Path, project_root: Path,
                      public_patterns: Optional[Set[str]] = None) -> List[RenameCandidate]:
        """Build on existing W9004 detection for candidate identification."""
        # TODO: Implementation will:
        # 1. Parse module AST
        # 2. Extract all functions
        # 3. Use should_function_be_private() to identify candidates
        # 4. Build RenameCandidate objects
        # 5. Run reference detection and safety validation

**Configuration Consistency**:

Both systems respect the same configuration options:
- ``public-api-patterns``: Functions to treat as public API
- ``enable-privacy-detection``: Whether to perform privacy analysis

CLI Integration (Planned)
--------------------------

The privacy fixer will integrate with the existing CLI system through new arguments.

New CLI Arguments
~~~~~~~~~~~~~~~~~

**--fix-privacy**
    *Status: 🚧 Planned*

    Enable automatic privacy fixing mode:

    .. code-block:: bash

        pylint-sort-functions --fix-privacy src/

    **Behavior**:
    - Identifies W9004 violations (functions that should be private)
    - Performs safety analysis
    - Applies safe renames automatically
    - Reports unsafe cases for manual review

**--privacy-dry-run**
    *Status: 🚧 Planned*

    Preview privacy fixes without applying them:

    .. code-block:: bash

        pylint-sort-functions --fix-privacy --privacy-dry-run src/

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

- **Core Architecture**: All three main classes designed and implemented
- **Reference Detection**: Complete AST traversal with comprehensive pattern matching
- **Safety Validation Framework**: Basic validation structure with extensible design
- **Report Generation**: Human-readable status reports with detailed explanations
- **Test Coverage**: Comprehensive test suite with 12 test cases covering all implemented functionality

**🚧 In Progress**:

- **Safety Validation Logic**: Framework exists, implementing comprehensive validation rules
- **Technical Documentation**: This document provides complete architectural overview

**📋 Planned Implementation**:

1. **Complete Safety Validation** (next priority)

   - Name conflict detection with module AST scanning
   - Dynamic reference detection (getattr, eval, exec patterns)
   - String literal scanning for function name references
   - Enhanced context validation

2. **Rename Application System**

   - Atomic file operations with rollback support
   - Source code modification with reference updates
   - Backup file creation and management
   - Error recovery and partial operation handling

3. **CLI Integration**

   - ``--fix-privacy`` argument implementation
   - ``--privacy-dry-run`` mode support
   - Integration with existing CLI argument parsing
   - Progress reporting and verbose output modes

4. **Module Analysis Implementation**

   - Integration with existing W9004 detection logic
   - Project-wide analysis coordination
   - Configuration option support
   - Performance optimization for large projects

Development Phases
~~~~~~~~~~~~~~~~~~

**Phase 1: Core Safety System** *(In Progress)*
    Complete the safety validation system with comprehensive checks for all identified risk categories.

**Phase 2: Rename Implementation** *(Next)*
    Implement the actual source code modification system with atomic operations and error recovery.

**Phase 3: CLI Integration** *(Following)*
    Add command-line interface integration with the existing CLI system and user experience polish.

**Phase 4: Testing and Optimization** *(Final)*
    Comprehensive integration testing, performance optimization, and documentation completion.

Usage Examples (When Complete)
-------------------------------

*Note: These examples show the planned usage patterns when implementation is complete.*

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

Integration with Function Sorting
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Fix both sorting and privacy in one operation
    pylint-sort-functions --fix --fix-privacy src/

    # Configuration respects existing patterns
    pylint-sort-functions --fix-privacy --public-patterns "main,setup" src/

**Combined Operation**:

1. Fix function sorting violations (existing functionality)
2. Identify functions that should be private (W9004 detection)
3. Apply safe privacy renames
4. Re-sort functions with updated names
5. Generate comprehensive report

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

**Current Test Suite** (12 tests, all passing):

.. code-block:: bash

    tests/test_privacy_fixer.py::TestPrivacyFixer::test_initialization
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_find_function_references_simple_call
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_find_function_references_assignment
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_find_function_references_decorator
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_find_function_references_multiple
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_find_function_references_ignores_definition
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_safety_validation_safe_case
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_generate_report_empty
    tests/test_privacy_fixer.py::TestPrivacyFixer::test_generate_report_with_candidates
    tests/test_privacy_fixer.py::TestFunctionReference::test_function_reference_creation
    tests/test_privacy_fixer.py::TestRenameCandidate::test_rename_candidate_creation
    tests/test_privacy_fixer.py::TestPrivacyFixerIntegration::test_full_workflow_dry_run

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
