"""Decorator analysis and exclusion logic for framework-aware sorting.

This module provides functionality to analyze function decorators and determine
whether functions should be excluded from sorting requirements based on their
decorators (e.g., framework-specific decorators that create ordering dependencies).
"""

import re

from astroid import nodes  # type: ignore[import-untyped]


def decorator_matches_pattern(decorator_str: str, pattern: str) -> bool:
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
    function_decorators = get_decorator_strings(func)

    # Check if any decorator matches any ignore pattern
    for decorator_str in function_decorators:
        for ignore_pattern in ignore_decorators:
            if decorator_matches_pattern(decorator_str, ignore_pattern):
                return True

    return False


def get_decorator_strings(func: nodes.FunctionDef) -> list[str]:
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
