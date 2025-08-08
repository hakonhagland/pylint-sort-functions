"""Main checker class for enforcing function and method sorting.

The FunctionSortChecker is used by PyLint itself, not by end users directly.
PyLint discovers this checker via the plugin entry point and manages its lifecycle.

For detailed information about the sorting rules and algorithm, see docs/sorting.rst.

How it works:
    1. PyLint loads the plugin and calls register() function (the plugin entry point
       defined in __init__.py and configured in pyproject.toml)
    2. register() creates a FunctionSortChecker instance and gives it to PyLint
    3. PyLint walks the AST (Abstract Syntax Tree) of user code
    4. For each AST node, PyLint calls corresponding visit_* methods on this checker
       (we only implement visit_module and visit_classdef from the many available)
    5. The checker analyzes nodes and calls self.add_message() when issues are found

User Experience:
    $ pylint --load-plugins=pylint_sort_functions mycode.py
    # PyLint automatically uses this checker and reports any sorting violations

The visitor pattern: PyLint calls visit_module() for modules and visit_classdef()
for class definitions. Each method analyzes the code structure and reports issues.
"""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from astroid import nodes  # type: ignore[import-untyped]
from pylint.checkers import BaseChecker

from pylint_sort_functions import messages, utils

if TYPE_CHECKING:
    pass


class FunctionSortChecker(BaseChecker):
    """Checker to enforce alphabetical sorting of functions and methods.

    Inherits from PyLint's BaseChecker which provides the visitor pattern
    infrastructure. PyLint will automatically call our visit_* methods as it
    traverses the AST.
    """

    name = "function-sort"  # Identifier used by PyLint for this checker
    msgs: dict[str, Any] = messages.MESSAGES  # Message definitions from messages.py
    options = (
        (
            "public-api-patterns",
            {
                "default": [
                    "main",
                    "run",
                    "execute",
                    "start",
                    "stop",
                    "setup",
                    "teardown",
                ],
                "type": "csv",
                "metavar": "<pattern1,pattern2,...>",
                "help": (
                    "List of function names to always treat as public API. "
                    "These functions will not be flagged for privacy even if only used "
                    "internally. Useful for entry points and framework callbacks."
                ),
            },
        ),
        (
            "enable-privacy-detection",
            {
                "default": True,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Enable detection of functions that should be made private "
                    "based on usage analysis."
                ),
            },
        ),
        (
            "ignore-decorators",
            {
                "default": [],
                "type": "csv",
                "metavar": "<pattern1,pattern2,...>",
                "help": (
                    "Decorator patterns to exclude from sorting requirements. "
                    "Supports exact matches and wildcards (e.g., @app.route)."
                ),
            },
        ),
    )

    # Public methods

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Visit a class definition to check method sorting.

        Called by PyLint for each class definition in the code.

        :param node: The class definition AST node to analyze
        :type node: nodes.ClassDef
        """
        methods = utils.get_methods_from_class(node)

        # Get configured decorator exclusions
        ignore_decorators = self.linter.config.ignore_decorators or []

        if not utils.are_methods_sorted_with_exclusions(methods, ignore_decorators):
            # Report unsorted methods - see docs/usage.rst for message details
            self.add_message("unsorted-methods", node=node, args=(node.name,))

        if not utils.are_functions_properly_separated(methods):
            # Report mixed visibility - see docs/usage.rst for suppression options
            self.add_message(
                "mixed-function-visibility",
                node=node,
                args=(f"class {node.name}",),
            )

    def visit_module(self, node: nodes.Module) -> None:
        """Visit a module node to check function sorting and privacy.

        Called by PyLint once for each Python module (file) being analyzed.

        :param node: The module AST node to analyze
        :type node: nodes.Module
        """
        functions = utils.get_functions_from_node(node)

        # Get configured decorator exclusions
        ignore_decorators = self.linter.config.ignore_decorators or []

        if not utils.are_functions_sorted_with_exclusions(functions, ignore_decorators):
            # Report unsorted functions - see docs/usage.rst for configuration
            self.add_message("unsorted-functions", node=node, args=("module",))

        if not utils.are_functions_properly_separated(functions):
            # Report mixed visibility - see docs/usage.rst for severity levels
            self.add_message("mixed-function-visibility", node=node, args=("module",))

        # Check if any public functions should be private
        self._check_function_privacy(functions, node)

    # Private methods

    def _check_function_privacy(
        self, functions: list[nodes.FunctionDef], node: nodes.Module
    ) -> None:
        """Check if any public functions should be private using import analysis.

        :param functions: List of functions to check
        :type functions: list[nodes.FunctionDef]
        :param node: The module node
        :type node: nodes.Module
        """
        # Check if privacy detection is enabled
        if not self.linter.config.enable_privacy_detection:
            return

        module_path = self._get_module_path()
        if not module_path:
            # Fallback to heuristic approach when path info unavailable
            self._check_function_privacy_heuristic(functions, node)
            return

        project_root = self._get_project_root(module_path)
        if not project_root:
            # Fallback to heuristic approach when project root can't be determined
            self._check_function_privacy_heuristic(functions, node)
            return

        # Get configured public API patterns
        public_patterns = set(self.linter.config.public_api_patterns)

        # Use import analysis for more accurate detection
        for func in functions:
            if utils.should_function_be_private(
                func, module_path, project_root, public_patterns
            ):
                # Report function that should be private
                # See docs/usage.rst for privacy detection feature
                self.add_message(
                    "function-should-be-private", node=func, args=(func.name,)
                )
            elif utils.should_function_be_public(func, module_path, project_root):
                # Report private function that should be public
                # See docs/usage.rst for privacy detection feature
                self.add_message(
                    "function-should-be-public", node=func, args=(func.name,)
                )

    def _check_function_privacy_heuristic(
        self,
        functions: list[nodes.FunctionDef],
        node: nodes.Module,  # pylint: disable=unused-argument
    ) -> None:
        """Check function privacy using heuristic approach (fallback).

        Used when import analysis is not available due to missing path information.

        :param functions: List of functions to check
        :type functions: list[nodes.FunctionDef]
        :param node: The module node
        :type node: nodes.Module
        """
        # Skip privacy check in heuristic mode - we can't determine without paths
        # This fallback mode is rarely used (only when linter has no file info)
        pass  # pragma: no cover

    def _get_module_path(self) -> Path | None:
        """Get the current module's file path from the linter.

        :returns: Path to the module file, or None if not available
        :rtype: Path | None
        """
        # Defensive check: ensure linter has current_file attribute
        # (version compatibility)
        if hasattr(self.linter, "current_file") and self.linter.current_file:
            return Path(self.linter.current_file).resolve()
        return None

    def _get_project_root(self, module_path: Path) -> Path | None:
        """Find the project root directory by looking for common project markers.

        :param module_path: Path to the current module
        :type module_path: Path
        :returns: Project root path, or module's parent directory as fallback
        :rtype: Path | None
        """
        # Common project markers that indicate a project root
        project_markers = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            ".git",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
        ]

        current = module_path.parent
        while current != current.parent:
            # Check if any project marker exists in current directory
            if any((current / marker).exists() for marker in project_markers):
                return current
            current = current.parent

        # Fallback: use the module's parent directory
        # This handles cases where we're testing in isolated directories
        return module_path.parent
