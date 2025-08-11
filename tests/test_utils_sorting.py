"""Tests for sorting validation utilities."""

from pathlib import Path
from unittest.mock import Mock

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import utils

# Path to test files directory
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestUtilsSorting:
    """Test cases for sorting validation utility functions."""

    def test_are_functions_properly_separated_empty_list(self) -> None:
        """Test separation validation with empty list."""
        functions: list[nodes.FunctionDef] = []

        result = utils.are_functions_properly_separated(functions)
        assert result is True

    def test_are_functions_properly_separated_false(self) -> None:
        """Test function visibility separation with mixed visibility."""
        file_path = TEST_FILES_DIR / "modules" / "mixed_visibility.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils.are_functions_properly_separated(functions)
        assert result is False

    def test_are_functions_properly_separated_true(self) -> None:
        """Test function visibility separation with properly separated functions."""
        file_path = TEST_FILES_DIR / "modules" / "sorted_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils.are_functions_properly_separated(functions)
        assert result is True

    def test_are_functions_sorted_empty_list(self) -> None:
        """Test sorting validation with empty list."""
        functions: list[nodes.FunctionDef] = []

        result = utils._are_functions_sorted(functions)
        assert result is True

    def test_are_functions_sorted_false(self) -> None:
        """Test function sorting validation with unsorted functions."""
        file_path = TEST_FILES_DIR / "modules" / "unsorted_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils._are_functions_sorted(functions)
        assert result is False

    def test_are_functions_sorted_false_private_only(self) -> None:
        """Test function sorting validation with unsorted private functions."""
        file_path = TEST_FILES_DIR / "modules" / "unsorted_private_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils._are_functions_sorted(functions)
        assert result is False

    def test_are_functions_sorted_true(self) -> None:
        """Test function sorting validation with sorted functions."""
        file_path = TEST_FILES_DIR / "modules" / "sorted_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils._are_functions_sorted(functions)
        assert result is True

    def test_are_methods_sorted_false(self) -> None:
        """Test method sorting validation with unsorted methods."""
        file_path = TEST_FILES_DIR / "classes" / "unsorted_methods.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        class_node = module.body[0]
        assert isinstance(class_node, nodes.ClassDef)
        methods = utils.get_methods_from_class(class_node)

        result = utils._are_methods_sorted(methods)
        assert result is False

    def test_are_methods_sorted_true(self) -> None:
        """Test method sorting validation with sorted methods."""
        file_path = TEST_FILES_DIR / "classes" / "sorted_methods.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        class_node = module.body[0]
        assert isinstance(class_node, nodes.ClassDef)
        methods = utils.get_methods_from_class(class_node)

        result = utils._are_methods_sorted(methods)
        assert result is True

    def test_get_function_groups(self) -> None:
        """Test function grouping by visibility."""
        # Create mock functions
        public_func = Mock(spec=nodes.FunctionDef)
        public_func.name = "public_function"

        private_func = Mock(spec=nodes.FunctionDef)
        private_func.name = "_private_function"

        functions = [public_func, private_func]

        public_functions, private_functions = utils._get_function_groups(functions)

        assert len(public_functions) == 1
        assert len(private_functions) == 1
        assert public_functions[0] == public_func
        assert private_functions[0] == private_func

    def test_get_function_groups_empty_list(self) -> None:
        """Test function grouping with empty list."""
        functions: list[nodes.FunctionDef] = []

        public_functions, private_functions = utils._get_function_groups(functions)

        assert public_functions == []
        assert private_functions == []
