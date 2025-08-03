"""Main checker class for enforcing function and method sorting.

The FunctionSortChecker is used by PyLint itself, not by end users directly.
PyLint discovers this checker via the plugin entry point and manages its lifecycle.

How it works:
    1. PyLint loads the plugin and calls register() function
    2. register() creates a FunctionSortChecker instance and gives it to PyLint
    3. PyLint walks the AST (Abstract Syntax Tree) of user code
    4. For each AST node, PyLint calls corresponding visit_* methods on this checker
    5. The checker analyzes nodes and calls self.add_message() when issues are found

User Experience:
    $ pylint --load-plugins=pylint_sort_functions mycode.py
    # PyLint automatically uses this checker and reports any sorting violations

The visitor pattern: PyLint calls visit_module() for modules and visit_classdef()
for class definitions. Each method analyzes the code structure and reports issues.
"""

from typing import TYPE_CHECKING, Any

from astroid import nodes  # type: ignore[import-untyped]
from pylint.checkers import BaseChecker

from pylint_sort_functions import messages, utils

if TYPE_CHECKING:
    pass


class FunctionSortChecker(BaseChecker):
    """Checker to enforce alphabetical sorting of functions and methods."""

    name = "function-sort"
    msgs: dict[str, Any] = messages.MESSAGES

    def visit_module(self, node: nodes.Module) -> None:
        """Visit a module node to check function sorting.

        :param node: The module AST node to analyze
        :type node: nodes.Module
        """
        functions = utils.get_functions_from_node(node)
        if not utils.are_functions_sorted(functions):
            self.add_message("unsorted-functions", node=node, args=("module",))

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Visit a class definition to check method sorting.

        :param node: The class definition AST node to analyze
        :type node: nodes.ClassDef
        """
        methods = utils.get_methods_from_class(node)
        if not utils.are_methods_sorted(methods):
            self.add_message("unsorted-methods", node=node, args=(node.name,))

        if not utils.are_functions_properly_separated(methods):
            self.add_message(
                "mixed-function-visibility",
                node=node,
                args=(f"class {node.name}",),
            )
