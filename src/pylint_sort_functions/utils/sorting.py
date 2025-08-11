"""Core sorting validation logic for functions and methods.

This module provides the main sorting validation functions that check whether
functions and methods are properly sorted according to the configured rules.
"""

from astroid import nodes  # type: ignore[import-untyped]

from .ast_analysis import is_private_function
from .categorization import CategoryConfig, categorize_method
from .decorators import function_has_excluded_decorator


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
