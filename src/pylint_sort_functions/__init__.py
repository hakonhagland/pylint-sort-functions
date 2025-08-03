"""PyLint plugin to enforce alphabetical sorting of functions and methods."""

from typing import TYPE_CHECKING

from pylint_sort_functions import checker

if TYPE_CHECKING:
    from pylint.lint import PyLinter


def register(linter: "PyLinter") -> None:
    """Register the plugin with PyLint.

    This function is called by PyLint when the plugin is loaded.
    It registers the FunctionSortChecker with the linter.

    :param linter: The PyLint linter instance
    :type linter: PyLinter
    """
    linter.register_checker(checker.FunctionSortChecker(linter))
