"""Utility functions for AST analysis and sorting logic.

This module provides the core analysis functions for the pylint-sort-functions plugin.
It includes functions for:

1. Function/method sorting validation
2. Public/private function separation validation
3. Function privacy detection (identifying functions that should be private)

Function Privacy Detection Approach:
The plugin uses a heuristic-based approach to identify functions that should be private:
- Analyzes function naming patterns (helper/utility prefixes and keywords)
- Checks internal usage within the same module
- Applies conservative logic to minimize false positives
- Cannot detect cross-module imports (this is actually beneficial for reducing
  false positives on legitimate public API functions)

The approach prioritizes precision over recall - it's better to miss some candidates
than to incorrectly flag public API functions as needing to be private.
"""

import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

from astroid import nodes  # type: ignore[import-untyped]


def are_functions_properly_separated(functions: list[nodes.FunctionDef]) -> bool:
    """Check if public and private functions are properly separated.

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :returns: True if public functions come before private functions
    :rtype: bool
    """
    if len(functions) <= 1:
        return True

    # Track if we've seen any private functions
    seen_private = False

    for func in functions:
        if is_private_function(func):
            seen_private = True
        elif seen_private:
            # Found a public function after a private function
            return False

    return True


def are_functions_sorted(functions: list[nodes.FunctionDef]) -> bool:
    """Check if functions are sorted alphabetically within their visibility scope.

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :returns: True if functions are properly sorted
    :rtype: bool
    """
    if len(functions) <= 1:
        return True

    public_functions, private_functions = get_function_groups(functions)

    # Check if public functions are sorted
    public_names = [f.name for f in public_functions]
    if public_names != sorted(public_names):
        return False

    # Check if private functions are sorted
    private_names = [f.name for f in private_functions]
    if private_names != sorted(private_names):
        return False

    return True


def are_methods_sorted(methods: list[nodes.FunctionDef]) -> bool:
    """Check if methods are sorted alphabetically within their visibility scope.

    :param methods: List of method definition nodes
    :type methods: list[nodes.FunctionDef]
    :returns: True if methods are properly sorted
    :rtype: bool
    """
    # Methods follow the same sorting rules as functions
    return are_functions_sorted(methods)


def get_function_groups(
    functions: list[nodes.FunctionDef],
) -> tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]:
    """Split functions into public and private groups.

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :returns: Tuple of (public_functions, private_functions)
    :rtype: tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]
    """
    public_functions = [f for f in functions if not is_private_function(f)]
    private_functions = [f for f in functions if is_private_function(f)]
    return public_functions, private_functions


def get_functions_from_node(node: nodes.Module) -> list[nodes.FunctionDef]:
    """Extract function definitions from a module node.

    :param node: The module AST node to analyze
    :type node: nodes.Module
    :returns: List of function definition nodes
    :rtype: list[nodes.FunctionDef]
    """
    functions = []
    for child in node.body:
        if isinstance(child, nodes.FunctionDef):
            functions.append(child)
    return functions


def get_functions_used_in_module(module: nodes.Module) -> Set[str]:
    """Extract all function names that are called within a module.

    :param module: The module AST node to analyze
    :type module: nodes.Module
    :returns: Set of function names called within the module
    :rtype: Set[str]
    """
    used_functions: Set[str] = set()

    def visit_call(node: nodes.Call) -> None:
        """Visit Call nodes to find function calls."""
        if isinstance(node.func, nodes.Name):
            used_functions.add(node.func.name)

    def visit_node(node: nodes.NodeNG) -> None:
        """Recursively visit all nodes in the AST."""
        if isinstance(node, nodes.Call):
            visit_call(node)

        # Recursively visit all child nodes
        for child in node.get_children():
            visit_node(child)

    visit_node(module)
    return used_functions


def get_methods_from_class(node: nodes.ClassDef) -> list[nodes.FunctionDef]:
    """Extract method definitions from a class node.

    :param node: The class definition AST node to analyze
    :type node: nodes.ClassDef
    :returns: List of method definition nodes
    :rtype: list[nodes.FunctionDef]
    """
    methods = []
    for child in node.body:
        if isinstance(child, nodes.FunctionDef):
            methods.append(child)
    return methods


def is_private_function(func: nodes.FunctionDef) -> bool:
    """Check if a function is private (starts with underscore).

    :param func: Function definition node
    :type func: nodes.FunctionDef
    :returns: True if function name starts with underscore
    :rtype: bool
    """
    return bool(func.name.startswith("_"))


def should_function_be_private(func: nodes.FunctionDef, module: nodes.Module) -> bool:
    """Check if a public function should be private based on usage patterns.

    This function uses heuristics to identify functions that are likely internal
    implementation details and should be marked as private (prefixed with underscore).

    Detection Criteria (ALL must be true):
    1. Function is currently public (doesn't start with underscore)
    2. Function name matches helper/utility patterns (see helper_patterns below)
    3. Function is called within the same module (indicates internal usage)
    4. Function is not a special method (__init__, __str__, etc.)
    5. Function is not a common public API pattern (main, run, setup, etc.)

    Helper Patterns Detected:
    - Prefixes: get_, set_, check_, validate_, parse_, format_, calculate_,
      process_, handle_, find_, extract_, convert_, transform_, build_,
      create_, make_
    - Contains: helper, util, internal, support
    - Predicates: is_, has_, can_, should_, will_, does_

    Cross-Module Usage Limitations:
    - CANNOT detect functions imported/used by other modules
    - Only analyzes calls within the same module
    - This is actually beneficial: functions used externally won't be flagged
    - Conservative approach reduces false positives

    Examples:
        # Will be flagged (helper pattern + internal usage):
        def get_data():
            return process_internal_data()

        def process_internal_data():  # Called by get_data() above
            return "data"

        # Will NOT be flagged (helper pattern but no internal usage):
        def parse_config():  # Likely used by other modules
            return {"setting": "value"}

        # Will NOT be flagged (no helper pattern):
        def save():  # Public API function
            return store_data()

    :param func: Function definition node to analyze
    :type func: nodes.FunctionDef
    :param module: The module containing the function
    :type module: nodes.Module
    :returns: True if the function should be marked as private
    :rtype: bool
    """
    # Skip if already private
    if is_private_function(func):
        return False

    # Skip special methods (dunder methods)
    if func.name.startswith("__") and func.name.endswith("__"):
        return False

    # Skip common public API patterns
    public_patterns = {
        "main",  # Common entry point
        "run",  # Common entry point
        "setup",  # Setup functions
        "teardown",  # Teardown functions
    }
    if func.name in public_patterns:
        return False

    # Get all function names used in this module
    used_functions = get_functions_used_in_module(module)

    # If the function is called within the module but not by functions
    # outside this module, it should probably be private
    # For now, we use a simple heuristic: if it's only used internally
    # and follows certain naming patterns, suggest making it private

    # Check if function name suggests it's a helper/utility function
    # These patterns are based on common Python naming conventions for internal
    # implementation details vs. public API functions
    helper_patterns = {
        "get_",
        "set_",
        "check_",
        "validate_",
        "parse_",
        "format_",
        "calculate_",
        "process_",
        "handle_",
        "find_",
        "extract_",
        "convert_",
        "transform_",
        "build_",
        "create_",
        "make_",
        "helper",
        "util",
        "internal",
        "support",
    }

    # Check if function name contains helper patterns (not just starts with)
    contains_helper_pattern = any(
        pattern in func.name.lower() for pattern in helper_patterns
    )

    is_used_internally = func.name in used_functions

    # Additional heuristic: check if function is only called by other functions
    # in the same module and not used at module level (suggesting internal use)
    if is_used_internally and contains_helper_pattern:
        return True

    # Enhanced heuristic: function that is used internally but has generic names
    # that suggest utility/helper nature
    internal_indicators = {
        "is_",
        "has_",
        "can_",
        "should_",
        "will_",
        "does_",  # Predicate functions
    }

    starts_with_predicate = any(
        func.name.startswith(pattern) for pattern in internal_indicators
    )

    # If it's a predicate function used internally, likely should be private
    return starts_with_predicate and is_used_internally


# Import Analysis Functions


def find_python_files(root_path: Path) -> List[Path]:
    """Find all Python files in a project directory.
    
    :param root_path: Root directory to search for Python files
    :type root_path: Path
    :returns: List of Python file paths
    :rtype: List[Path]
    """
    python_files = []
    
    for root, dirs, files in os.walk(root_path):
        # Skip common non-source directories
        dirs[:] = [d for d in dirs if d not in {
            '__pycache__', '.git', '.tox', '.pytest_cache', 
            'node_modules', '.venv', 'venv', 'dist', 'build'
        }]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(Path(root) / file)
    
    return python_files


def extract_imports_from_file(file_path: Path) -> Tuple[Set[str], Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """Extract import information from a Python file.
    
    :param file_path: Path to Python file to analyze
    :type file_path: Path
    :returns: Tuple of (module_imports, function_imports, attribute_accesses)
             module_imports: Set of module names imported
             function_imports: Set of (module, function) tuples from direct imports
             attribute_accesses: Set of (module, attribute) tuples from dot notation
    :rtype: Tuple[Set[str], Set[Tuple[str, str]], Set[Tuple[str, str]]]
    """
    try:
        import ast
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        tree = ast.parse(content)
        
        module_imports: Set[str] = set()
        function_imports: Set[Tuple[str, str]] = set()
        attribute_accesses: Set[Tuple[str, str]] = set()
        
        # First pass: collect imports
        imported_modules: Dict[str, str] = {}  # alias -> module_name
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                # Handle: import module [as alias]
                for alias in node.names:
                    module_name = alias.name
                    alias_name = alias.asname if alias.asname else alias.name
                    module_imports.add(module_name)
                    imported_modules[alias_name] = module_name
                    
            elif isinstance(node, ast.ImportFrom):
                # Handle: from module import function [as alias]
                if node.module:
                    for alias in node.names:
                        function_name = alias.name
                        alias_name = alias.asname if alias.asname else alias.name
                        function_imports.add((node.module, function_name))
                        # Also track the alias for attribute access detection
                        imported_modules[alias_name] = node.module
        
        # Second pass: find attribute accesses (module.function calls)
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # Handle: module.function_name or alias.function_name
                if isinstance(node.value, ast.Name):
                    module_alias = node.value.id
                    if module_alias in imported_modules:
                        actual_module = imported_modules[module_alias]
                        attribute_accesses.add((actual_module, node.attr))
                        
        return module_imports, function_imports, attribute_accesses
        
    except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
        # If file can't be parsed, return empty sets
        return set(), set(), set()


def build_cross_module_usage_graph(project_root: Path) -> Dict[str, Set[str]]:
    """Build a graph of which functions are used by which modules.
    
    This creates a mapping from function names to the set of modules that import them.
    
    :param project_root: Root directory of the project to analyze
    :type project_root: Path
    :returns: Dictionary mapping function names to set of importing modules
    :rtype: Dict[str, Set[str]]
    """
    usage_graph: Dict[str, Set[str]] = {}
    python_files = find_python_files(project_root)
    
    for file_path in python_files:
        # Get relative module name (e.g., "src/package/module.py" -> "package.module")
        try:
            relative_path = file_path.relative_to(project_root)
            module_name = str(relative_path.with_suffix('')).replace(os.sep, '.')
            
            # Skip __init__ and test files for cleaner analysis
            if module_name.endswith('__init__') or 'test' in module_name.lower():
                continue
                
            module_imports, function_imports, attribute_accesses = extract_imports_from_file(file_path)
            
            # Record direct function imports (from module import function)
            for imported_module, function_name in function_imports:
                if function_name not in usage_graph:
                    usage_graph[function_name] = set()
                usage_graph[function_name].add(module_name)
                
            # Record attribute accesses (module.function calls)
            for imported_module, function_name in attribute_accesses:
                if function_name not in usage_graph:
                    usage_graph[function_name] = set()
                usage_graph[function_name].add(module_name)
                
        except ValueError:
            # Skip files outside project root
            continue
            
    return usage_graph


def is_function_used_externally(
    func_name: str, 
    module_path: Path, 
    project_root: Path
) -> bool:
    """Check if a function is imported/used by other modules.
    
    :param func_name: Name of the function to check
    :type func_name: str
    :param module_path: Path to the module containing the function
    :type module_path: Path
    :param project_root: Root directory of the project
    :type project_root: Path
    :returns: True if function is used by other modules
    :rtype: bool
    """
    usage_graph = build_cross_module_usage_graph(project_root)
    
    if func_name not in usage_graph:
        return False
        
    # Get the current module name
    try:
        relative_path = module_path.relative_to(project_root)
        current_module = str(relative_path.with_suffix('')).replace(os.sep, '.')
        
        # Remove current module from usage set to see if used externally
        external_users = usage_graph[func_name] - {current_module}
        
        return len(external_users) > 0
        
    except ValueError:
        # If we can't determine the module name, assume it's used externally
        return True


def should_function_be_private_with_import_analysis(
    func: nodes.FunctionDef, 
    module: nodes.Module,
    module_path: Path,
    project_root: Path
) -> bool:
    """Enhanced version using import analysis to detect cross-module usage.
    
    This version provides more accurate detection by analyzing actual import
    patterns across the entire project, rather than just heuristics.
    
    Detection Logic:
    1. Skip if already private (starts with underscore)
    2. Skip special methods (__init__, __str__, etc.)
    3. Skip common public API patterns (main, run, setup, etc.)
    4. Check if function is imported/used by other modules
    5. If not used externally, suggest making it private
    
    Advantages over heuristic approach:
    - More accurate: doesn't rely on naming patterns alone
    - Detects actual usage: only flags truly unused external functions
    - Comprehensive: analyzes entire project for imports
    
    Performance considerations:
    - Scans entire project directory for Python files
    - Parses import statements from all files
    - May be slower on large projects (caching could help)
    
    :param func: Function definition node to analyze
    :type func: nodes.FunctionDef
    :param module: The module containing the function
    :type module: nodes.Module
    :param module_path: Path to the module file
    :type module_path: Path
    :param project_root: Root directory of the project
    :type project_root: Path
    :returns: True if the function should be marked as private
    :rtype: bool
    """
    # Skip if already private
    if is_private_function(func):
        return False
    
    # Skip special methods (dunder methods)
    if func.name.startswith("__") and func.name.endswith("__"):
        return False
    
    # Skip common public API patterns
    public_patterns = {
        "main",  # Common entry point
        "run",   # Common entry point
        "setup", # Setup functions
        "teardown", # Teardown functions
        "register",  # Registration functions (like our pylint plugin)
    }
    if func.name in public_patterns:
        return False
    
    # Key improvement: Check if function is actually used by other modules
    is_used_externally = is_function_used_externally(
        func.name, module_path, project_root
    )
    
    # If not used externally, it should probably be private
    # No need for naming pattern heuristics - actual usage is definitive
    return not is_used_externally
