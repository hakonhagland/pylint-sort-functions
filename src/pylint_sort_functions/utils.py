"""Utility functions for AST analysis and sorting logic."""

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
