"""Tests for the plugin registration function."""

from unittest.mock import Mock

from pylint_sort_functions import register
from pylint_sort_functions.checker import FunctionSortChecker


def test_register_creates_checker() -> None:
    """Test that register function creates and registers checker."""
    mock_linter = Mock()

    register(mock_linter)

    # Verify the checker was registered
    mock_linter.register_checker.assert_called_once()

    # Verify the registered checker is correct type
    registered_checker = mock_linter.register_checker.call_args[0][0]
    assert isinstance(registered_checker, FunctionSortChecker)
