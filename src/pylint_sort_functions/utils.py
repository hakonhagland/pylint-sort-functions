"""Utility functions for AST analysis and sorting logic.

This module provides the core analysis functions for the pylint-sort-functions plugin.

NOTE: Module size (1114 lines) exceeds 1000-line guideline.
Refactoring tracked in GitHub issue #37:
https://github.com/hakonhagland/pylint-sort-functions/issues/37
It includes functions for:

1. Function/method sorting validation
2. Public/private function separation validation
3. Function privacy detection (identifying functions that should be private)
4. Framework-aware sorting with decorator exclusions

For detailed information about the sorting algorithm and rules, see the documentation
at docs/sorting.rst which explains the complete sorting methodology, special method
handling, privacy detection, and configuration options.

Function Privacy Detection:
The plugin uses import analysis to identify functions that should be private by
scanning actual usage patterns across the project:
- Analyzes cross-module imports and function calls in all Python files
- Identifies functions that are only used within their own module
- Skips common public API patterns (main, run, setup, etc.)
- Provides accurate detection based on real usage patterns
"""

# pylint: disable=too-many-lines

import ast
import fnmatch
import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

from astroid import nodes  # type: ignore[import-untyped]


@dataclass
class MethodCategory:
    """Configuration for a method category in the sorting system.

    Defines how methods are categorized based on patterns, decorators, and other
    criteria. Categories determine the sorting order and section organization.

    :param name: Unique identifier for this category (e.g., 'properties')
    :type name: str
    :param patterns: List of glob patterns to match names (e.g., ['test_*'])
    :type patterns: list[str]
    :param decorators: List of decorator patterns (e.g., ['@property'])
    :type decorators: list[str]
    :param priority: Priority for conflict resolution, higher values win
    :type priority: int
    :param section_header: Comment header text for this category
    :type section_header: str
    """

    name: str
    patterns: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    priority: int = 0
    section_header: str = ""


@dataclass
class CategoryConfig:
    """Configuration for the method categorization system.

    Defines the complete categorization scheme including all categories,
    default behavior, and compatibility settings.

    :param categories: List of method categories in sorting order
    :type categories: list[MethodCategory]
    :param default_category: Category name for methods that do not match patterns
    :type default_category: str
    :param enable_categories: Enable multi-category system (false = backward
        compatibility)
    :type enable_categories: bool
    :param category_sorting: How to sort within categories ('alphabetical' or
        'declaration')
    :type category_sorting: str
    """

    categories: list[MethodCategory] = field(default_factory=list)
    default_category: str = "public_methods"
    enable_categories: bool = False  # Backward compatibility - disabled by default
    category_sorting: str = "alphabetical"  # or "declaration" to preserve order

    def __post_init__(self) -> None:
        """Initialize with default binary categories if none provided."""
        if not self.categories:
            self.categories = self._get_default_categories()

    def _get_default_categories(self) -> list[MethodCategory]:
        """Get default binary public/private categories for backward compatibility.

        :returns: List of default method categories (public, private)
        :rtype: list[MethodCategory]
        """
        return [
            MethodCategory(
                name="public_methods",
                patterns=["*"],  # Catch-all for non-private methods
                section_header="# Public methods",
            ),
            MethodCategory(
                name="private_methods",
                patterns=["_*"],  # Methods starting with underscore
                priority=1,  # Higher priority than public catch-all
                section_header="# Private methods",
            ),
        ]


# Public functions


def are_functions_properly_separated(functions: list[nodes.FunctionDef]) -> bool:
    """Check if public and private functions are properly separated.

    This function only verifies the ordering constraint: public functions must
    appear before private functions. It does not check for section comment headers
    like "# Public functions" or "# Private functions" - that would be a separate
    validation if implemented.

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


def are_functions_sorted_with_exclusions(
    functions: list[nodes.FunctionDef],
    ignore_decorators: list[str] | None = None,
    config: CategoryConfig | None = None,
) -> bool:
    """Check if functions are sorted alphabetically, excluding decorator-dependent ones.

    This is the enhanced version of _are_functions_sorted that supports framework-aware
    sorting by excluding functions with specific decorators that create dependencies.

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :param ignore_decorators: List of decorator patterns to ignore
    :type ignore_decorators: list[str] | None
    :param config: Category configuration, uses default if None
    :type config: CategoryConfig | None
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
    return _are_functions_sorted(sortable_functions, config)


def are_methods_sorted_with_exclusions(
    methods: list[nodes.FunctionDef],
    ignore_decorators: list[str] | None = None,
    config: CategoryConfig | None = None,
) -> bool:
    """Check if methods are sorted alphabetically, excluding decorator-dependent ones.

    :param methods: List of method definition nodes
    :type methods: list[nodes.FunctionDef]
    :param ignore_decorators: List of decorator patterns to ignore
    :type ignore_decorators: list[str] | None
    :param config: Category configuration, uses default if None
    :type config: CategoryConfig | None
    :returns: True if methods are properly sorted (excluding ignored ones)
    :rtype: bool
    """
    # Methods follow the same sorting rules as functions
    return are_functions_sorted_with_exclusions(methods, ignore_decorators, config)


def categorize_method(  # pylint: disable=function-should-be-private
    func: nodes.FunctionDef, config: CategoryConfig | None = None
) -> str:
    """Determine the category for a method based on configuration patterns.

    This replaces the binary is_private_function() with a flexible categorization
    system that supports multiple method types (properties, test methods, etc.).

    When enable_categories=False (default), provides backward compatible behavior
    by returning 'public_methods' or 'private_methods' based on naming convention.

    :param func: Function definition node to categorize
    :type func: nodes.FunctionDef
    :param config: Category configuration, uses default if None
    :type config: CategoryConfig | None
    :returns: Category name for the method (e.g., 'properties', 'test_methods')
    :rtype: str
    """
    if config is None:
        config = CategoryConfig()

    # For backward compatibility, when categories disabled, use original logic
    if not config.enable_categories:
        return "private_methods" if is_private_function(func) else "public_methods"

    # Find matching categories, prioritizing higher priority values
    matching_categories: list[tuple[MethodCategory, int]] = []

    for category in config.categories:
        match_priority = _get_category_match_priority(func, category)
        if match_priority > 0:
            matching_categories.append((category, match_priority))

    if not matching_categories:
        # No matches found, use default category
        return config.default_category

    # Sort by priority (higher first), then by category priority field
    matching_categories.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

    return matching_categories[0][0].name


def find_python_files(root_path: Path) -> list[Path]:  # pylint: disable=function-should-be-private
    """Find all Python files in a project directory.

    Recursively searches for files with .py extension while skipping common
    directories that should not be analyzed (build artifacts, virtual environments,
    caches, etc.).

    TODO: Make skip_dirs list configurable for project-specific needs.

    :param root_path: Root directory to search for Python files
    :type root_path: Path
    :returns: List of paths to Python files
    :rtype: list[Path]
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
    func: nodes.FunctionDef, ignore_decorators: list[str] | None
) -> bool:
    """Check if a function should be excluded from sorting due to its decorators.

    Some decorators create dependencies that make alphabetical sorting inappropriate.
    For example, Click commands or Flask routes may need specific ordering for proper
    framework behavior.

    :param func: Function definition node to check
    :type func: nodes.FunctionDef
    :param ignore_decorators: List of decorator patterns to match against
    :type ignore_decorators: list[str] | None
    :returns: True if function should be excluded from sorting requirements
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


def is_private_function(func: nodes.FunctionDef) -> bool:
    """Check if a function is private (starts with underscore).

    DEPRECATED: This function is maintained for backward compatibility.
    New code should use categorize_method() with appropriate configuration.

    Functions starting with a single underscore are considered private by convention.
    Dunder methods (double underscore) like __init__ are not considered private
    as they are special methods with specific meanings in Python.

    :param func: Function definition node
    :type func: nodes.FunctionDef
    :returns: True if function name starts with underscore but not double underscore
    :rtype: bool
    """
    return func.name.startswith("_") and not _is_dunder_method(func)


def is_unittest_file(  # pylint: disable=function-should-be-private,too-many-return-statements,too-many-branches
    module_name: str, privacy_config: dict[str, Any] | None = None
) -> bool:
    """Check if a module name indicates a unit test file.

    Detects test files based on configurable patterns and built-in heuristics.
    Can be configured to override built-in detection or add additional patterns.

    Built-in detection patterns:
    - Files in 'tests' or 'test' directories
    - Files starting with 'test_'
    - Files ending with '_test'
    - conftest.py files (pytest configuration)
    - Files containing 'test' in their path components

    :param module_name: The module name to check (e.g., 'package.tests.test_utils')
    :type module_name: str
    :param privacy_config: Privacy configuration with exclusion patterns
    :type privacy_config: dict[str, Any] | None
    :returns: True if module appears to be a test file
    :rtype: bool
    """
    if privacy_config is None:
        privacy_config = {}

    # Get configuration options
    exclude_dirs = privacy_config.get("exclude_dirs", [])
    exclude_patterns = privacy_config.get("exclude_patterns", [])
    additional_test_patterns = privacy_config.get("additional_test_patterns", [])
    override_test_detection = privacy_config.get("override_test_detection", False)

    # Check directory exclusions first
    lower_name = module_name.lower()
    parts = lower_name.split(".")

    # Check if file is in an excluded directory
    for exclude_dir in exclude_dirs:
        if exclude_dir.lower() in parts:
            return True

    # Check file pattern exclusions
    for pattern in exclude_patterns:
        if _matches_file_pattern(module_name, pattern):
            return True

    # Check additional test patterns
    for pattern in additional_test_patterns:
        if _matches_file_pattern(module_name, pattern):
            return True

    # If override is enabled, only use configured patterns
    if override_test_detection:
        return False

    # Built-in test detection (original logic)
    # Check if any directory in the path is a test directory
    if "tests" in parts or "test" in parts:
        return True

    # Get the file name (last component)
    if parts:
        filename = parts[-1]

        # Check for common test file patterns
        if filename.startswith("test_"):
            return True
        if filename.endswith("_test"):
            return True
        if filename == "conftest":  # pytest configuration file
            return True

    # Fallback: check if 'test' appears anywhere (catches edge cases)
    # This is more permissive but ensures we do not miss test files
    return "test" in lower_name


def should_function_be_private(
    func: nodes.FunctionDef,
    module_path: Path,
    project_root: Path,
    public_patterns: set[str] | None = None,
    privacy_config: dict[str, Any] | None = None,
) -> bool:
    """Detect if a function should be private based on import analysis.

    Analyzes actual usage patterns across the project to determine if a function
    is only used within its own module and should therefore be made private.

    Detection Logic:
    1. Skip if already private (starts with underscore)
    2. Skip special methods (__init__, __str__, etc.)
    3. Skip configurable public API patterns (main, run, setup, etc.)
    4. Check if function is imported/used by other modules
    5. If not used externally, suggest making it private

    :param func: Function definition node to analyze
    :type func: nodes.FunctionDef
    :param module_path: Path to the module file
    :type module_path: Path
    :param project_root: Root directory of the project
    :type project_root: Path
    :param public_patterns: Set of function names to always treat as public.
                           If None, uses default patterns (main, run, execute, etc.)
    :type public_patterns: set[str] | None
    :returns: True if the function should be marked as private
    :rtype: bool
    """
    # Skip if already private
    if is_private_function(func):
        return False

    # Skip special methods (dunder methods)
    if _is_dunder_method(func):
        return False

    # Skip common public API patterns that are called by external systems
    # These are entry points, framework callbacks, or conventional APIs that
    # will not show up in import analysis (e.g., main() called by Python runtime,
    # setup/teardown called by test frameworks)
    if public_patterns is None:
        public_patterns = {
            "main",
            "run",
            "execute",
            "start",
            "stop",
            "setup",
            "teardown",
        }
    if func.name in public_patterns:
        return False

    # Check if function is actually used by other modules
    is_used_externally = _is_function_used_externally(
        func.name, module_path, project_root, privacy_config
    )

    # If not used externally, it should probably be private
    return not is_used_externally


def should_function_be_public(
    func: nodes.FunctionDef,
    module_path: Path,
    project_root: Path,
    privacy_config: dict[str, Any] | None = None,
) -> bool:
    """Detect if a private function should be public based on external usage analysis.

    Analyzes actual usage patterns across the project to determine if a function
    that is currently marked as private is actually used by other modules and
    should therefore be made public.

    Detection Logic:
    1. Skip if already public (does not start with underscore)
    2. Skip special methods (dunder methods like __init__, __str__, etc.)
    3. Check if the private function is imported/used by other modules
    4. If used externally, suggest making it public

    :param func: Function definition node to analyze
    :type func: nodes.FunctionDef
    :param module_path: Path to the module file
    :type module_path: Path
    :param project_root: Root directory of the project
    :type project_root: Path
    :returns: True if the function should be made public
    :rtype: bool
    """
    # Skip if already public (does not start with underscore)
    if not is_private_function(func):
        return False

    # Skip special methods (dunder methods like __init__, __str__, etc.)
    # Note: This check is defensive - current logic means dunder methods
    # are never considered private by is_private_function above
    if _is_dunder_method(func):  # pragma: no cover
        return False  # pragma: no cover

    # Check if this private function is actually used by other modules
    is_used_externally = _is_function_used_externally(
        func.name, module_path, project_root, privacy_config
    )

    # If used externally, it should be public
    return is_used_externally


# Private functions


def _are_categories_properly_ordered(
    functions: list[nodes.FunctionDef], config: CategoryConfig
) -> bool:
    """Check if functions appear in the correct category order.

    Verifies that functions appear in the order defined by config.categories.
    For example, if categories are [properties, public_methods, private_methods],
    then all properties must appear before all public_methods, etc.

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :param config: Category configuration defining order
    :type config: CategoryConfig
    :returns: True if functions are in correct category order
    :rtype: bool
    """
    if not functions:
        return True

    category_order = {cat.name: i for i, cat in enumerate(config.categories)}
    seen_categories = set()
    last_category_index = -1

    for func in functions:
        category = categorize_method(func, config)
        category_index = category_order.get(category, len(config.categories))

        if category in seen_categories:
            # We've seen this category before - check if we're still in it or
            # moving backward
            if category_index < last_category_index:
                return False  # Categories are mixed/out of order
        else:
            # First time seeing this category
            if category_index < last_category_index:
                return False  # This category should have appeared earlier
            seen_categories.add(category)
            last_category_index = category_index

    return True


def _are_functions_sorted(
    functions: list[nodes.FunctionDef], config: CategoryConfig | None = None
) -> bool:  # pylint: disable=function-should-be-private
    """Check if functions are sorted alphabetically within their category scope.

    Functions are expected to be sorted with categories in the order defined by
    the configuration, and alphabetically within each category.

    For backward compatibility, when config.enable_categories=False:
    - Public functions (including dunder methods like __init__) sorted first
    - Private functions (single underscore prefix) sorted alphabetically second

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :param config: Category configuration, uses default if None
    :type config: CategoryConfig | None
    :returns: True if functions are properly sorted
    :rtype: bool
    """
    if len(functions) <= 1:
        return True

    if config is None:
        config = CategoryConfig()

    # For backward compatibility, use the original binary logic
    if not config.enable_categories:
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

    # New multi-category logic
    categorized_functions = _get_function_categories(functions, config)

    # Check sorting within each category
    for category_name in [cat.name for cat in config.categories]:
        if category_name in categorized_functions:
            category_functions = categorized_functions[category_name]
            if config.category_sorting == "alphabetical":
                names = [f.name for f in category_functions]
                if names != sorted(names):
                    return False
            # If category_sorting == "declaration", preserve order (always sorted)

    # Check that categories appear in the correct order
    return _are_categories_properly_ordered(functions, config)


def _are_methods_sorted(
    methods: list[nodes.FunctionDef], config: CategoryConfig | None = None
) -> bool:  # pylint: disable=function-should-be-private
    """Check if methods are sorted alphabetically within their category scope.

    :param methods: List of method definition nodes
    :type methods: list[nodes.FunctionDef]
    :param config: Category configuration, uses default if None
    :type config: CategoryConfig | None
    :returns: True if methods are properly sorted
    :rtype: bool
    """
    # Methods follow the same sorting rules as functions
    return _are_functions_sorted(methods, config)


def _build_cross_module_usage_graph(
    project_root: Path, privacy_config: dict[str, Any] | None = None
) -> dict[str, set[str]]:
    """Build a graph of which functions are used by which modules.

    This creates a mapping from function names to the set of modules that import them.

    WARNING: This is an expensive operation that scans the entire project.
    Results are cached during the analysis run to avoid redundant scanning.

    :param project_root: Root directory of the project
    :type project_root: Path
    :returns: Dictionary mapping function names to set of importing modules
    :rtype: dict[str, set[str]]
    """
    usage_graph: dict[str, set[str]] = {}
    python_files = find_python_files(project_root)

    for file_path in python_files:
        # Get relative module name (e.g., "src/package/module.py" -> "package.module")
        try:
            relative_path = file_path.relative_to(project_root)
            module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")

            # Skip __init__ files (they re-export for API organization)
            # not actual usage)
            # and test files (tests access internals, do not indicate public API)
            if module_name.endswith("__init__") or is_unittest_file(
                module_name, privacy_config
            ):
                continue

            # Get file modification time for cache key
            try:
                file_mtime = file_path.stat().st_mtime
            except OSError:  # pragma: no cover
                # If we cannot get mtime, skip this file
                continue

            _, function_imports, attribute_accesses = _extract_imports_from_file(
                file_path, file_mtime
            )

            # Record direct function imports
            # Example: from utils import calculate_total, validate_input
            for _, function_name in function_imports:
                if function_name not in usage_graph:
                    usage_graph[function_name] = set()
                usage_graph[function_name].add(module_name)

            # Record attribute accesses (module.function calls)
            # Example: result = utils.calculate_total(items)
            for _, function_name in attribute_accesses:
                if function_name not in usage_graph:
                    usage_graph[function_name] = set()
                usage_graph[function_name].add(module_name)

        except (ValueError, OSError):
            # Skip files that cannot be processed
            continue

    return usage_graph


def _decorator_matches_pattern(decorator_str: str, pattern: str) -> bool:
    """Check if a decorator string matches an ignore pattern.

    Supports exact matches and simple wildcard patterns. This allows users to
    exclude functions with specific decorators from sorting requirements when
    the decorators create ordering dependencies.

    Examples:
    - "@app.route" matches both @app.route and @app.route("/path")
    - "@*.command" matches @main.command(), @cli.command(), etc.

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


def _extract_attribute_accesses(
    tree: ast.AST,
    imported_modules: dict[str, str],
    attribute_accesses: set[tuple[str, str]],
) -> None:
    """Extract attribute access patterns from AST for import analysis.

    Helper function for _extract_imports_from_file to reduce complexity.

    :param tree: Parsed AST tree
    :type tree: ast.AST
    :param imported_modules: Map of aliases to actual module names
    :type imported_modules: dict[str, str]
    :param attribute_accesses: Set to populate with (module, attribute) tuples
    :type attribute_accesses: set[tuple[str, str]]
    """
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            # Handle: module.function_name or alias.function_name
            if isinstance(node.value, ast.Name):
                module_alias = node.value.id
                if module_alias in imported_modules:
                    actual_module = imported_modules[module_alias]
                    attribute_accesses.add((actual_module, node.attr))


@lru_cache(maxsize=128)
def _extract_imports_from_file(
    file_path: Path,
    file_mtime: float,  # pylint: disable=unused-argument
) -> tuple[set[str], set[tuple[str, str]], set[tuple[str, str]]]:
    """Extract import information from a Python file.

    This function is now cached to prevent redundant parsing of the same files
    during a single analysis run. The file modification time is included in the
    cache key to ensure cache invalidation when files change.

    Performance impact: For projects with 100+ files, this caching can provide
    50%+ performance improvement by avoiding repeated AST parsing of the same files.

    :param file_path: Path to the Python file to analyze
    :type file_path: Path
    :param file_mtime: File modification time (used for cache invalidation)
    :type file_mtime: float
    :returns: Tuple of:
            module_imports: Set of module names from direct imports
            function_imports: Set of (module, function) tuples from direct imports
            attribute_accesses: Set of (module, attribute) tuples from dot notation
    :rtype: tuple[set[str], set[tuple[str, str]], set[tuple[str, str]]]
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content)

        module_imports: set[str] = set()
        function_imports: set[tuple[str, str]] = set()
        attribute_accesses: set[tuple[str, str]] = set()

        # Track module aliases for attribute access detection
        imported_modules: dict[str, str] = {}

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
        _extract_attribute_accesses(tree, imported_modules, attribute_accesses)

        return module_imports, function_imports, attribute_accesses

    except (SyntaxError, UnicodeDecodeError, FileNotFoundError):
        # If file cannot be parsed, return empty sets
        return set(), set(), set()


def _get_category_match_priority(
    func: nodes.FunctionDef, category: MethodCategory
) -> int:
    """Calculate match priority for a function against a category.

    Returns 0 if no match, positive integer if match (higher = better match).
    Priority calculation:
    - Decorator match: 100 (highest priority - most specific)
    - Name pattern match: 50 (medium priority)
    - Catch-all pattern (*): 1 (lowest priority - fallback)

    :param func: Function definition node to check
    :type func: nodes.FunctionDef
    :param category: Category to test against
    :type category: MethodCategory
    :returns: Match priority (0 = no match, >0 = match strength)
    :rtype: int
    """
    priority = 0

    # Check decorator patterns (highest priority)
    if category.decorators:
        function_decorators = _get_decorator_strings(func)
        for decorator_pattern in category.decorators:
            for func_decorator in function_decorators:
                if _decorator_matches_pattern(func_decorator, decorator_pattern):
                    priority = max(priority, 100)
                    break

    # Check name patterns (medium priority)
    if category.patterns:
        for pattern in category.patterns:
            if _method_name_matches_pattern(func.name, pattern):
                if pattern == "*":
                    # Catch-all pattern gets lowest priority
                    priority = max(priority, 1)
                else:
                    # Specific patterns get medium priority
                    priority = max(priority, 50)
                break

    return priority


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


def _get_function_categories(
    functions: list[nodes.FunctionDef], config: CategoryConfig
) -> dict[str, list[nodes.FunctionDef]]:
    """Group functions by their categories.

    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :param config: Category configuration
    :type config: CategoryConfig
    :returns: Dictionary mapping category names to function lists
    :rtype: dict[str, list[nodes.FunctionDef]]
    """
    categories: dict[str, list[nodes.FunctionDef]] = {}

    for func in functions:
        category = categorize_method(func, config)
        if category not in categories:
            categories[category] = []
        categories[category].append(func)

    return categories


def _get_function_groups(
    functions: list[nodes.FunctionDef],
) -> tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]:
    """Split functions into public and private groups.

    DEPRECATED: This function is maintained for backward compatibility.
    New code should use _get_function_categories() with CategoryConfig.

    :param functions: List of function definitions
    :type functions: list[nodes.FunctionDef]
    :returns: Tuple of (public_functions, private_functions)
    :rtype: tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]
    """
    public_functions = [f for f in functions if not is_private_function(f)]
    private_functions = [f for f in functions if is_private_function(f)]
    return public_functions, private_functions


def _is_dunder_method(func: nodes.FunctionDef) -> bool:
    """Check if a function is a dunder/magic method.

    Dunder methods are special methods that start and end with double underscores,
    like __init__, __str__, __call__, etc.

    :param func: Function definition node
    :type func: nodes.FunctionDef
    :returns: True if function is a dunder method
    :rtype: bool
    """
    name: str = func.name  # Explicitly typed to satisfy mypy
    return name.startswith("__") and name.endswith("__")


def _is_function_used_externally(
    func_name: str,
    module_path: Path,
    project_root: Path,
    privacy_config: dict[str, Any] | None = None,
) -> bool:
    """Check if a function is imported/used by other modules.

    This is the core logic for privacy detection. If a function is only used
    within its own module, it is a candidate for being marked as private.

    WARNING: This builds the entire cross-module usage graph which can be
    expensive for large projects. The graph is cached via @lru_cache to
    mitigate repeated scanning.

    :param func_name: Name of the function to check
    :type func_name: str
    :param module_path: Path to the module containing the function
    :type module_path: Path
    :param project_root: Root directory of the project
    :type project_root: Path
    :returns: True if function is used by other modules, False if only used internally
    :rtype: bool
    """
    usage_graph = _build_cross_module_usage_graph(project_root, privacy_config)

    if func_name not in usage_graph:
        return False

    # Get the module name of the function being checked
    try:
        relative_path = module_path.relative_to(project_root)
        current_module = str(relative_path.with_suffix("")).replace(os.sep, ".")
    except ValueError:
        # If we cannot determine the module name, assume it is used externally
        return True

    # Check if function is used by any module other than its own
    using_modules = usage_graph[func_name]
    external_usage = [m for m in using_modules if m != current_module]

    return len(external_usage) > 0


def _matches_file_pattern(module_name: str, pattern: str) -> bool:
    """Check if a module name matches a file pattern.

    Supports glob patterns for matching file names and paths.

    :param module_name: Module name to check (e.g., 'package.tests.test_utils')
    :type module_name: str
    :param pattern: Glob pattern to match against (e.g., 'test_*.py', '*_test.py')
    :type pattern: str
    :returns: True if module name matches pattern
    :rtype: bool
    """
    # Convert module name to filename-like format for pattern matching
    # e.g., "package.tests.test_utils" -> "package/tests/test_utils.py"
    file_path = module_name.replace(".", "/") + ".py"

    # Also check just the module name for direct matching
    parts = module_name.split(".")
    if parts:
        filename = parts[-1] + ".py"  # Add .py for pattern matching

        # Check both full path and just filename
        return fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(filename, pattern)

    return fnmatch.fnmatch(file_path, pattern)  # pragma: no cover


def _method_name_matches_pattern(method_name: str, pattern: str) -> bool:
    """Check if a method name matches a glob pattern.

    Supports standard glob patterns:
    - * matches any sequence of characters
    - ? matches any single character
    - [seq] matches any character in seq
    - [!seq] matches any character not in seq

    :param method_name: Method name to check
    :type method_name: str
    :param pattern: Glob pattern to match against
    :type pattern: str
    :returns: True if method name matches pattern
    :rtype: bool
    """
    return fnmatch.fnmatch(method_name, pattern)
