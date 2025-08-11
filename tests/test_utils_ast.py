"""Tests for AST node extraction utilities."""

from pathlib import Path
from unittest.mock import Mock

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import utils

# Path to test files directory
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestUtilsAST:
    """Test cases for AST node extraction utility functions."""

    def test_get_functions_from_node_empty(self) -> None:
        """Test function extraction from empty module."""
        file_path = TEST_FILES_DIR / "modules" / "empty_module.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        result = utils.get_functions_from_node(module)

        assert not result

    def test_get_functions_from_node_sorted(self) -> None:
        """Test function extraction from sorted module."""
        file_path = TEST_FILES_DIR / "modules" / "sorted_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        result = utils.get_functions_from_node(module)

        assert len(result) == 6
        function_names = [f.name for f in result]
        expected_names = [
            "calculate_area",
            "process_data",
            "validate_input",
            "_format_output",
            "_helper_function",
            "_validate_internal",
        ]
        assert function_names == expected_names

    def test_get_methods_from_class_sorted(self) -> None:
        """Test method extraction from sorted class."""
        file_path = TEST_FILES_DIR / "classes" / "sorted_methods.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        class_node = module.body[0]  # First node should be the Calculator class
        assert isinstance(class_node, nodes.ClassDef)

        result = utils.get_methods_from_class(class_node)

        assert len(result) == 7  # __init__ + 4 public + 2 private methods
        method_names = [m.name for m in result]
        expected_names = [
            "__init__",
            "add",
            "divide",
            "multiply",
            "subtract",
            "_format_result",
            "_validate_input",
        ]
        assert method_names == expected_names

    def test_is_private_function_with_private_name(self) -> None:
        """Test private function detection with underscore prefix."""
        mock_func = Mock(spec=nodes.FunctionDef)
        mock_func.name = "_private_function"

        result = utils.is_private_function(mock_func)

        assert result is True

    def test_is_private_function_with_public_name(self) -> None:
        """Test private function detection with public name."""
        mock_func = Mock(spec=nodes.FunctionDef)
        mock_func.name = "public_function"

        result = utils.is_private_function(mock_func)

        assert result is False
