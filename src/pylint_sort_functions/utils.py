"""Utility functions for AST analysis and sorting logic."""

from astroid import nodes


def get_functions_from_node(node: nodes.Module) -> list[nodes.FunctionDef]:
    """Extract function definitions from a module node.
    
    :param node: The module AST node to analyze
    :type node: nodes.Module
    :returns: List of function definition nodes
    :rtype: list[nodes.FunctionDef]
    """
    # TODO: Implement function extraction logic
    return []


def get_methods_from_class(node: nodes.ClassDef) -> list[nodes.FunctionDef]:
    """Extract method definitions from a class node.
    
    :param node: The class definition AST node to analyze
    :type node: nodes.ClassDef  
    :returns: List of method definition nodes
    :rtype: list[nodes.FunctionDef]
    """
    # TODO: Implement method extraction logic
    return []


def are_functions_sorted(functions: list[nodes.FunctionDef]) -> bool:
    """Check if functions are sorted alphabetically within their visibility scope.
    
    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :returns: True if functions are properly sorted
    :rtype: bool
    """
    # TODO: Implement sorting validation logic
    return True


def are_methods_sorted(methods: list[nodes.FunctionDef]) -> bool:
    """Check if methods are sorted alphabetically within their visibility scope.
    
    :param methods: List of method definition nodes
    :type methods: list[nodes.FunctionDef]
    :returns: True if methods are properly sorted
    :rtype: bool
    """
    # TODO: Implement method sorting validation logic
    return True


def are_functions_properly_separated(functions: list[nodes.FunctionDef]) -> bool:
    """Check if public and private functions are properly separated.
    
    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :returns: True if public functions come before private functions
    :rtype: bool
    """
    # TODO: Implement visibility separation validation logic
    return True


def is_private_function(func: nodes.FunctionDef) -> bool:
    """Check if a function is private (starts with underscore).
    
    :param func: Function definition node
    :type func: nodes.FunctionDef
    :returns: True if function name starts with underscore
    :rtype: bool
    """
    return func.name.startswith("_")


def get_function_groups(functions: list[nodes.FunctionDef]) -> tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]:
    """Split functions into public and private groups.
    
    :param functions: List of function definition nodes
    :type functions: list[nodes.FunctionDef]
    :returns: Tuple of (public_functions, private_functions)
    :rtype: tuple[list[nodes.FunctionDef], list[nodes.FunctionDef]]
    """
    public_functions = [f for f in functions if not is_private_function(f)]
    private_functions = [f for f in functions if is_private_function(f)]
    return public_functions, private_functions