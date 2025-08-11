"""AST analysis utilities for function and method extraction.

This module provides core AST analysis functions for extracting and analyzing
function and method definitions from Python code.
"""

from astroid import nodes  # type: ignore[import-untyped]


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


def is_dunder_method(func: nodes.FunctionDef) -> bool:
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
    return func.name.startswith("_") and not is_dunder_method(func)
