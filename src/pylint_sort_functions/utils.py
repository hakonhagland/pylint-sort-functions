"""Utility functions for AST analysis and sorting logic.

This module provides the core analysis functions for the pylint-sort-functions plugin.
It includes functions for:

1. Function/method sorting validation
2. Public/private function separation validation
3. Function privacy detection (identifying functions that should be private)
4. Framework-aware sorting with decorator exclusions

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
import re
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


def are_functions_sorted_with_exclusions(  # pylint: disable=function-should-be-private
    functions: list[nodes.FunctionDef], ignore_decorators: list[str] | None = None
) -> bool:
    """Check if functions are sorted alphabetically, excluding decorator-dependent ones.

    This is the enhanced version of are_functions_sorted that supports framework-aware
    sorting by excluding functions with specific decorators that create dependencies.

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :param ignore_decorators: List of decorator patterns to ignore
    :type ignore_decorators: list[str] | None
    :returns: True if functions are properly sorted (excluding ignored ones)
    :rtype: bool
    """
    if ignore_decorators is None:
        ignore_decorators = []

    # Filter out functions with excluded decorators
    sortable_functions = [
        func
        for func in functions
        if not function_has_excluded_decorator(func, ignore_decorators)
    ]

    # Use existing sorting logic on the filtered functions
    return are_functions_sorted(sortable_functions)


def are_methods_sorted(methods: list[nodes.FunctionDef]) -> bool:
    """Check if methods are sorted alphabetically within their visibility scope.

    :param methods: List of method definition nodes
    :type methods: list[nodes.FunctionDef]
    :returns: True if methods are properly sorted
    :rtype: bool
    """
    # Methods follow the same sorting rules as functions
    return are_functions_sorted(methods)


def are_methods_sorted_with_exclusions(  # pylint: disable=function-should-be-private
    methods: list[nodes.FunctionDef], ignore_decorators: list[str] | None = None
) -> bool:
    """Check if methods are sorted alphabetically, excluding decorator-dependent ones.

    :param methods: List of method definition nodes
    :type methods: list[nodes.FunctionDef]
    :param ignore_decorators: List of decorator patterns to ignore
    :type ignore_decorators: list[str] | None
    :returns: True if methods are properly sorted (excluding ignored ones)
    :rtype: bool
    """
    # Methods follow the same sorting rules as functions
    return are_functions_sorted_with_exclusions(methods, ignore_decorators)


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


def should_function_be_private(func: nodes.FunctionDef, module: nodes.Module) -> bool:  # pylint: disable=unused-argument
    """Legacy heuristic-based privacy detection (deprecated).

    This function is kept for backward compatibility but always returns False.
    The preferred approach is should_function_be_private_with_import_analysis()
    which provides more accurate detection based on actual usage patterns.

    :param func: Function definition node to analyze
    :type func: nodes.FunctionDef
    :param module: The module containing the function
    :type module: nodes.Module
    :returns: Always returns False (heuristics disabled)
    :rtype: bool
    """
    # Heuristic-based detection has been disabled in favor of import analysis
    # This fallback is only used when path information is unavailable
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
    if is_private_function(func):
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


def _decorator_matches_pattern(decorator_str: str, pattern: str) -> bool:
    """Check if a decorator string matches an ignore pattern.

    Supports exact matches and simple wildcard patterns.

    :param decorator_str: Decorator string to check (e.g., "@main.command()")
    :type decorator_str: str
    :param pattern: Pattern to match against (e.g., "@main.command", "@*.command")
    :type pattern: str
    :returns: True if decorator matches the pattern
    :rtype: bool
    """
    # Normalize patterns by ensuring they start with @
    if not pattern.startswith("@"):
        pattern = f"@{pattern}"

    # Exact match
    if decorator_str == pattern:
        return True

    # Remove parentheses for pattern matching (treat @main.command() as @main.command)
    decorator_base = decorator_str.rstrip("()")
    pattern_base = pattern.rstrip("()")

    if decorator_base == pattern_base:
        return True

    # Simple wildcard support: @*.command matches @main.command, @app.command, etc.
    if "*" in pattern_base:
        # Convert simple wildcard pattern to regex
        # First escape the pattern, then replace escaped wildcards with regex
        regex_pattern = re.escape(pattern_base)
        regex_pattern = regex_pattern.replace(r"\*", r"[^.]+")
        regex_pattern = f"^{regex_pattern}$"
        if re.match(regex_pattern, decorator_base):
            return True

    return False


def _decorator_node_to_string(decorator: nodes.NodeNG) -> str:
    """Convert a decorator AST node to its string representation.

    :param decorator: Decorator AST node
    :type decorator: nodes.NodeNG
    :returns: String representation of the decorator (without @ prefix)
    :rtype: str
    """
    if isinstance(decorator, nodes.Name):
        # Simple decorator: @decorator_name
        return str(decorator.name)

    if isinstance(decorator, nodes.Attribute):
        # Attribute decorator: @obj.method
        if isinstance(decorator.expr, nodes.Name):
            return f"{decorator.expr.name}.{decorator.attrname}"
        # Handle nested attributes: @obj.nested.method
        base = _decorator_node_to_string(decorator.expr)
        if base:
            return f"{base}.{decorator.attrname}"

    if isinstance(decorator, nodes.Call):
        # Function call decorator: @decorator() or @obj.method(args)
        func_str = _decorator_node_to_string(decorator.func)
        if func_str:
            return f"{func_str}()"

    # Fallback for complex decorators - return empty string to skip
    return ""


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


def function_has_excluded_decorator(
    func: nodes.FunctionDef, ignore_decorators: list[str]
) -> bool:
    """Check if a function has any decorators that should be excluded from sorting.

    :param func: Function definition node to check
    :type func: nodes.FunctionDef
    :param ignore_decorators: List of decorator patterns to match against
    :type ignore_decorators: list[str]
    :returns: True if function has any excluded decorators
    :rtype: bool
    """
    if not ignore_decorators or not func.decorators:
        return False

    # Get string representations of all decorators on this function
    function_decorators = _get_decorator_strings(func)

    # Check if any decorator matches any ignore pattern
    for decorator_str in function_decorators:
        for ignore_pattern in ignore_decorators:
            if _decorator_matches_pattern(decorator_str, ignore_pattern):
                return True

    return False


def _get_decorator_strings(func: nodes.FunctionDef) -> list[str]:
    """Extract string representations of all decorators on a function.

    :param func: Function definition node
    :type func: nodes.FunctionDef
    :returns: List of decorator strings (e.g., ["@main.command()", "@app.route()"])
    :rtype: list[str]
    """
    if not func.decorators:
        return []

    decorator_strings = []
    for decorator in func.decorators.nodes:
        decorator_str = _decorator_node_to_string(decorator)
        if decorator_str:
            decorator_strings.append(f"@{decorator_str}")

    return decorator_strings


def _get_function_groups(
    functions: list[nodes.FunctionDef],
) -> tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]:
    """Split functions into public and private groups.

    :param functions: List of function definitions
    :type functions: list[nodes.FunctionDef]
    :returns: Tuple of (public_functions, private_functions)
    :rtype: tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]
    """
    public_functions = [f for f in functions if not is_private_function(f)]
    private_functions = [f for f in functions if is_private_function(f)]
    return public_functions, private_functions


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


def is_private_function(func: nodes.FunctionDef) -> bool:
    """Check if a function is private (starts with underscore).

    :param func: Function definition node
    :type func: nodes.FunctionDef
    :returns: True if function name starts with underscore
    :rtype: bool
    """
    return func.name.startswith("_") and not func.name.startswith("__")
