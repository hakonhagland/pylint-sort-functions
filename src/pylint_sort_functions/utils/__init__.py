"""Utility functions for AST analysis and sorting logic.

This module provides the core analysis functions for the pylint-sort-functions plugin.
Refactored from a single 1117-line file into focused modules for better maintainability.

For backward compatibility, all public functions are re-exported from their
specialized modules. All existing imports continue to work unchanged.

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

# Re-export all public functions for backward compatibility
# All existing imports continue to work:
# from pylint_sort_functions.utils import CategoryConfig  ✓
# from pylint_sort_functions import utils; utils.get_functions_from_node()  ✓

# AST Analysis functions
# AST Analysis functions
from .ast_analysis import (
    get_functions_from_node,
    get_methods_from_class,
    is_dunder_method,
    is_private_function,
)

# Categorization system
from .categorization import (
    CategoryConfig,
    MethodCategory,
    _get_category_match_priority,
    _method_name_matches_pattern,
    categorize_method,
    find_method_section_boundaries,
    get_expected_section_for_method,
    is_method_in_correct_section,
    parse_section_headers,
)

# Decorator analysis
from .decorators import (
    _decorator_node_to_string,
    decorator_matches_pattern,
    function_has_excluded_decorator,
    get_decorator_strings,
)

# File pattern utilities
from .file_patterns import (
    _matches_file_pattern,
    find_python_files,
    is_unittest_file,
)

# Privacy analysis
from .privacy import (
    _build_cross_module_usage_graph,
    _extract_attribute_accesses,
    _extract_imports_from_file,
    _is_function_used_externally,
    should_function_be_private,
    should_function_be_public,
)

# Sorting validation logic
from .sorting import (
    _are_categories_properly_ordered,
    _are_functions_sorted,
    _are_methods_sorted,
    _get_function_categories,
    _get_function_groups,
    are_functions_properly_separated,
    are_functions_sorted_with_exclusions,
    are_methods_in_correct_sections,
    are_methods_sorted_with_exclusions,
    find_empty_section_headers,
    find_missing_section_headers,
    get_section_violations,
)

__all__ = [
    # Public API - Core functionality
    "CategoryConfig",
    "MethodCategory",
    "are_functions_properly_separated",
    "are_functions_sorted_with_exclusions",
    "are_methods_in_correct_sections",
    "are_methods_sorted_with_exclusions",
    "categorize_method",
    "decorator_matches_pattern",
    "find_empty_section_headers",
    "find_method_section_boundaries",
    "find_missing_section_headers",
    "find_python_files",
    "function_has_excluded_decorator",
    "get_decorator_strings",
    "get_expected_section_for_method",
    "get_functions_from_node",
    "get_methods_from_class",
    "get_section_violations",
    "is_dunder_method",
    "is_method_in_correct_section",
    "is_private_function",
    "is_unittest_file",
    "parse_section_headers",
    "should_function_be_private",
    "should_function_be_public",
    # Private functions that tests depend on
    "_are_categories_properly_ordered",
    "_are_functions_sorted",
    "_are_methods_sorted",
    "_build_cross_module_usage_graph",
    "_decorator_node_to_string",
    "_extract_attribute_accesses",
    "_extract_imports_from_file",
    "_get_category_match_priority",
    "_get_function_categories",
    "_get_function_groups",
    "_is_function_used_externally",
    "_matches_file_pattern",
    "_method_name_matches_pattern",
]
