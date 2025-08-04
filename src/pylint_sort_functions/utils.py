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

import ast
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple

from astroid import nodes  # type: ignore[import-untyped]

# Public functions


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
        if _is_private_function(func):
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

    public_functions, private_functions = _get_function_groups(functions)

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


def get_functions_from_node(node: nodes.Module) -> list[nodes.FunctionDef]:
    """Extract all function definitions from a module.

    :param node: Module AST node
    :type node: nodes.Module
    :returns: List of function definition nodes
    :rtype: list[nodes.FunctionDef]
    """
    functions = []
    for child in node.body:
        if isinstance(child, nodes.FunctionDef):
            functions.append(child)
    return functions


def get_methods_from_class(node: nodes.ClassDef) -> list[nodes.FunctionDef]:
    """Extract all method definitions from a class.

    :param node: Class definition node
    :type node: nodes.ClassDef
    :returns: List of method definition nodes
    :rtype: list[nodes.FunctionDef]
    """
    methods = []
    for child in node.body:
        if isinstance(child, nodes.FunctionDef):
            methods.append(child)
    return methods


def should_function_be_private(func: nodes.FunctionDef, module: nodes.Module) -> bool:  # pylint: disable=too-many-return-statements,too-many-branches
    """Determine if a function should be marked as private using heuristics.

    This is the original heuristic-based approach that analyzes:
    1. Function naming patterns (helper/utility prefixes and keywords)
    2. Internal usage within the same module

    Limitations:
    - Cannot detect cross-module imports (by design, to reduce false positives)
    - May miss some functions that should be private
    - Conservative approach prioritizes precision over recall

    :param func: Function definition node to analyze
    :type func: nodes.FunctionDef
    :param module: The module containing the function
    :type module: nodes.Module
    :returns: True if the function should be marked as private
    :rtype: bool
    """
    # Skip if already private
    if _is_private_function(func):
        return False

    # Skip special methods (dunder methods)
    if func.name.startswith("__") and func.name.endswith("__"):
        return False

    # Skip common public API patterns
    public_patterns = {
        "main",
        "run",
        "execute",
        "start",
        "stop",
        "setup",
        "teardown",
        "init",
        "create",
        "build",
        "register",
        "configure",
        "connect",
        "disconnect",
        "open",
        "close",
        "load",
        "save",
        "export",
        "import",
    }

    # Extract base name without get/set/validate prefixes
    base_name = func.name
    for prefix in ["get_", "set_", "is_", "has_", "validate_", "check_"]:
        if func.name.startswith(prefix):
            base_name = func.name[len(prefix) :]
            break

    # If the base name matches a public pattern, keep it public
    if base_name in public_patterns:
        return False

    # Check for common helper/utility patterns that suggest private usage
    helper_patterns = [
        "helper",
        "util",
        "internal",
        "impl",
        "private",
        "process",
        "parse",
        "format",
        "convert",
        "transform",
        "extract",
        "build",
        "create",
        "make",
        "compute",
        "calculate",
        "determine",
        "resolve",
        "handle",
        "dispatch",
    ]

    # Check if function has helper/utility naming patterns
    has_helper_pattern = False
    lower_name = func.name.lower()
    for pattern in helper_patterns:
        if pattern in lower_name:
            has_helper_pattern = True
            break

    # Common prefixes that suggest helper functions
    helper_prefixes = [
        "_",  # Already handled above, but kept for completeness
        "do_",
        "get_",
        "set_",
        "is_",
        "has_",
        "check_",
        "validate_",
        "parse_",
        "format_",
        "convert_",
        "transform_",
        "process_",
        "handle_",
        "extract_",
        "build_",
        "create_",
        "make_",
        "find_",
        "search_",
        "filter_",
        "sort_",
        "merge_",
        "split_",
        "join_",
        "encode_",
        "decode_",
        "serialize_",
        "deserialize_",
        "read_",
        "write_",
        "load_",
        "save_",
        "fetch_",
        "store_",
        "update_",
        "delete_",
        "remove_",
        "clean_",
        "prepare_",
        "initialize_",
        "finalize_",
        "wrap_",
        "unwrap_",
    ]

    for prefix in helper_prefixes:
        if func.name.startswith(prefix) and len(func.name) > len(prefix):
            has_helper_pattern = True
            break

    # If it doesn't have helper patterns, don't flag it
    if not has_helper_pattern:
        return False

    # Additional check: Skip if it's clearly a public API method
    # (e.g., getter/setter for a public attribute)
    if func.name.startswith(("get_", "set_")) and len(func.name) > 4:
        # If it looks like a property accessor for a public attribute, keep it public
        attribute_name = func.name[4:]
        if not attribute_name.startswith("_"):
            return False

    # If the function matches common public API patterns, keep it public
    # NOTE: This line is unreachable due to the logic at line 183 which already
    # checks if base_name is in public_patterns. Since base_name is derived from
    # func.name by removing prefixes, any func.name in public_patterns would have
    # its base_name also in public_patterns, causing an early return at line 183.
    # This is defensive code kept for logical completeness.
    if func.name in public_patterns:  # pragma: no cover
        return False

    # Get all function names used in this module
    used_functions = _get_functions_used_in_module(module)

    # If the function is called within the module but not by functions
    # outside this module, it should probably be private
    # For now, we use a simple heuristic: if it's only used internally
    # (called within the same module) and has helper patterns, suggest making it private
    if func.name in used_functions and has_helper_pattern:
        return True

    # Don't flag functions that aren't used at all (they might be public API)
    return False


def should_function_be_private_with_import_analysis(
    func: nodes.FunctionDef, module_path: Path, project_root: Path
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

    Technical Approach:
    - Scans entire project directory for Python files
    - Parses import statements from all files
    - May be slower on large projects (caching could help)

    :param func: Function definition node to analyze
    :type func: nodes.FunctionDef
    :param module_path: Path to the module file
    :type module_path: Path
    :param project_root: Root directory of the project
    :type project_root: Path
    :returns: True if the function should be marked as private
    :rtype: bool
    """
    # Skip if already private
    if _is_private_function(func):
        return False

    # Skip special methods (dunder methods)
    if func.name.startswith("__") and func.name.endswith("__"):
        return False

    # Skip common public API patterns (same as heuristic approach)
    public_patterns = {"main", "run", "execute", "start", "stop", "setup", "teardown"}
    if func.name in public_patterns:
        return False

    # Key improvement: Check if function is actually used by other modules
    is_used_externally = _is_function_used_externally(
        func.name, module_path, project_root
    )

    # If not used externally, it should probably be private
    return not is_used_externally


# Private functions


def _build_cross_module_usage_graph(project_root: Path) -> Dict[str, Set[str]]:
    """Build a graph of which functions are used by which modules.

    This creates a mapping from function names to the set of modules that import them.

    :param project_root: Root directory of the project
    :type project_root: Path
    :returns: Dictionary mapping function names to set of importing modules
    :rtype: Dict[str, Set[str]]
    """
    usage_graph: Dict[str, Set[str]] = {}
    python_files = _find_python_files(project_root)

    for file_path in python_files:
        # Get relative module name (e.g., "src/package/module.py" -> "package.module")
        try:
            relative_path = file_path.relative_to(project_root)
            module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")

            # Skip __init__ and test files for cleaner analysis
            if module_name.endswith("__init__") or "test" in module_name.lower():
                continue

            _, function_imports, attribute_accesses = _extract_imports_from_file(
                file_path
            )

            # Record direct function imports (from module import function)
            for _, function_name in function_imports:
                if function_name not in usage_graph:
                    usage_graph[function_name] = set()
                usage_graph[function_name].add(module_name)

            # Record attribute accesses (module.function calls)
            for _, function_name in attribute_accesses:
                if function_name not in usage_graph:
                    usage_graph[function_name] = set()
                usage_graph[function_name].add(module_name)

        except (ValueError, OSError):
            # Skip files that can't be processed
            continue

    return usage_graph


def _extract_imports_from_file(
    file_path: Path,
) -> Tuple[Set[str], Set[Tuple[str, str]], Set[Tuple[str, str]]]:
    """Extract import information from a Python file.

    :param file_path: Path to the Python file to analyze
    :type file_path: Path
    :returns: Tuple of:
            module_imports: Set of module names from direct imports
            function_imports: Set of (module, function) tuples from direct imports
            attribute_accesses: Set of (module, attribute) tuples from dot notation
    :rtype: Tuple[Set[str], Set[Tuple[str, str]], Set[Tuple[str, str]]]
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        module_imports: Set[str] = set()
        function_imports: Set[Tuple[str, str]] = set()
        attribute_accesses: Set[Tuple[str, str]] = set()

        # Track module aliases for attribute access detection
        imported_modules: Dict[str, str] = {}

        # First pass: extract direct imports
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
                    module_imports.add(node.module)  # Add the module itself
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


def _find_python_files(root_path: Path) -> List[Path]:
    """Find all Python files in a project directory.

    :param root_path: Root directory to search for Python files
    :type root_path: Path
    :returns: List of paths to Python files
    :rtype: List[Path]
    """
    python_files = []

    # Directories to skip
    skip_dirs = {
        "__pycache__",
        ".git",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        "*.egg-info",
        "node_modules",
    }

    for item in root_path.rglob("*.py"):
        # Skip if any parent directory should be skipped
        if any(skip_dir in item.parts for skip_dir in skip_dirs):
            continue

        python_files.append(item)

    return python_files


def _get_function_groups(
    functions: list[nodes.FunctionDef],
) -> tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]:
    """Split functions into public and private groups.

    :param functions: List of function definitions
    :type functions: list[nodes.FunctionDef]
    :returns: Tuple of (public_functions, private_functions)
    :rtype: tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]
    """
    public_functions = [f for f in functions if not _is_private_function(f)]
    private_functions = [f for f in functions if _is_private_function(f)]
    return public_functions, private_functions


def _get_functions_used_in_module(module: nodes.Module) -> Set[str]:
    """Extract all function names that are called within a module.

    :param module: The module AST node to analyze
    :type module: nodes.Module
    :returns: Set of function names that are called in the module
    :rtype: Set[str]
    """
    used_functions = set()

    # Walk through all nodes in the module
    for node in module.nodes_of_class(nodes.Call):
        # Direct function calls (e.g., my_function())
        if isinstance(node.func, nodes.Name):
            used_functions.add(node.func.name)
        # Method calls (e.g., obj.method())
        elif isinstance(node.func, nodes.Attribute):
            used_functions.add(node.func.attrname)

    return used_functions


def _is_function_used_externally(
    func_name: str, module_path: Path, project_root: Path
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
    usage_graph = _build_cross_module_usage_graph(project_root)

    if func_name not in usage_graph:
        return False

    # Get the module name of the function being checked
    try:
        relative_path = module_path.relative_to(project_root)
        current_module = str(relative_path.with_suffix("")).replace(os.sep, ".")
    except ValueError:
        # If we can't determine the module name, assume it's used externally
        return True

    # Check if function is used by any module other than its own
    using_modules = usage_graph[func_name]
    external_usage = [m for m in using_modules if m != current_module]

    return len(external_usage) > 0


def _is_private_function(func: nodes.FunctionDef) -> bool:
    """Check if a function is private (starts with underscore).

    :param func: Function definition node
    :type func: nodes.FunctionDef
    :returns: True if function name starts with underscore
    :rtype: bool
    """
    return func.name.startswith("_") and not func.name.startswith("__")
