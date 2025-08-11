"""Tests for the FunctionSortChecker internal methods."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import astroid  # type: ignore[import-untyped]
from astroid import nodes
from pylint.testutils import CheckerTestCase

from pylint_sort_functions.checker import FunctionSortChecker


class TestFunctionSortCheckerInternals(CheckerTestCase):
    """Test cases for FunctionSortChecker internal methods."""

    CHECKER_CLASS = FunctionSortChecker

    def test_visit_classdef_calls_utils(self) -> None:
        """Test that visit_classdef calls utility functions and adds messages."""
        mock_node = Mock(spec=nodes.ClassDef)
        mock_node.name = "TestClass"

        with (
            patch(
                "pylint_sort_functions.utils.get_methods_from_class"
            ) as mock_get_methods,
            patch(
                "pylint_sort_functions.utils.are_methods_sorted_with_exclusions"
            ) as mock_are_sorted,
            patch(
                "pylint_sort_functions.utils.are_functions_properly_separated"
            ) as mock_are_separated,
        ):
            mock_get_methods.return_value = []
            mock_are_sorted.return_value = False
            mock_are_separated.return_value = False

            # Mock the add_message method and linter config
            self.checker.add_message = Mock()
            self.checker.linter = Mock()
            self.checker.linter.config.ignore_decorators = []

            self.checker.visit_classdef(mock_node)

            # Verify utility functions were called
            mock_get_methods.assert_called_once_with(mock_node)
            # Note: CategoryConfig parameter is now passed to the sorting function
            assert mock_are_sorted.call_count == 1
            mock_are_separated.assert_called_once_with([])

            # Verify both messages were added
            expected_calls = [
                (("unsorted-methods",), {"node": mock_node, "args": ("TestClass",)}),
                (
                    ("mixed-function-visibility",),
                    {"node": mock_node, "args": ("class TestClass",)},
                ),
            ]
            assert self.checker.add_message.call_count == 2
            for expected_call in expected_calls:
                assert expected_call in [
                    (call.args, call.kwargs)
                    for call in self.checker.add_message.call_args_list
                ]

    def test_visit_classdef_no_messages_when_sorted(self) -> None:
        """Test that visit_classdef doesn't add messages when methods are sorted."""
        mock_node = Mock(spec=nodes.ClassDef)
        mock_node.name = "TestClass"

        with (
            patch(
                "pylint_sort_functions.utils.get_methods_from_class"
            ) as mock_get_methods,
            patch("pylint_sort_functions.utils._are_methods_sorted") as mock_are_sorted,
            patch(
                "pylint_sort_functions.utils.are_functions_properly_separated"
            ) as mock_are_separated,
        ):
            mock_get_methods.return_value = []
            mock_are_sorted.return_value = True
            mock_are_separated.return_value = True

            # Mock the add_message method
            self.checker.add_message = Mock()

            self.checker.visit_classdef(mock_node)

            # Verify no messages were added
            self.checker.add_message.assert_not_called()

    def test_visit_module_calls_utils(self) -> None:
        """Test that visit_module calls utility functions and adds messages."""
        mock_node = Mock(spec=nodes.Module)

        with (
            patch(
                "pylint_sort_functions.utils.get_functions_from_node"
            ) as mock_get_functions,
            patch(
                "pylint_sort_functions.utils.are_functions_sorted_with_exclusions"
            ) as mock_are_sorted,
        ):
            mock_get_functions.return_value = []
            mock_are_sorted.return_value = False

            # Mock the add_message method
            self.checker.add_message = Mock()

            self.checker.visit_module(mock_node)

            # Verify utility functions were called
            mock_get_functions.assert_called_once_with(mock_node)
            # Note: CategoryConfig parameter is now passed to the sorting function
            assert mock_are_sorted.call_count == 1

            # Verify message was added
            self.checker.add_message.assert_called_once_with(
                "unsorted-functions", node=mock_node, args=("module",)
            )

    def test_visit_module_no_message_when_sorted(self) -> None:
        """Test that visit_module doesn't add message when functions are sorted."""
        mock_node = Mock(spec=nodes.Module)

        with (
            patch(
                "pylint_sort_functions.utils.get_functions_from_node"
            ) as mock_get_functions,
            patch(
                "pylint_sort_functions.utils.are_functions_sorted_with_exclusions"
            ) as mock_are_sorted,
        ):
            mock_get_functions.return_value = []
            mock_are_sorted.return_value = True

            # Mock the add_message method
            self.checker.add_message = Mock()

            self.checker.visit_module(mock_node)

            # Verify no message was added
            self.checker.add_message.assert_not_called()

    def test_visit_module_no_path_info(self) -> None:
        """Test visit_module when linter has no current_file attribute."""
        content = '''
def example_function():
    """A simple function."""
    return "example"
'''

        module = astroid.parse(content)

        # Mock linter without current_file attribute
        from unittest.mock import Mock

        mock_linter = Mock()
        del mock_linter.current_file  # Remove the attribute entirely

        with (
            patch.object(self.checker, "linter", mock_linter),
            # Should not crash and not add messages for simple function
            self.assertNoMessages(),
        ):
            self.checker.visit_module(module)

    def test_get_module_path_with_current_file(self) -> None:
        """Test _get_module_path when linter has current_file."""
        # Set up the linter with a current_file
        test_path = "/path/to/test.py"
        self.checker.linter.current_file = test_path

        result = self.checker._get_module_path()

        assert result is not None
        assert result == Path(test_path).resolve()

    def test_get_module_path_without_current_file(self) -> None:
        """Test _get_module_path when linter has no current_file."""
        # Remove current_file attribute if it exists
        if hasattr(self.checker.linter, "current_file"):
            delattr(self.checker.linter, "current_file")

        result = self.checker._get_module_path()

        assert result is None

    def test_get_project_root_with_markers(self) -> None:
        """Test _get_project_root finding project markers."""
        # Use a temporary directory for testing

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create project structure
            project_dir = Path(temp_dir) / "project"
            src_dir = project_dir / "src"
            src_dir.mkdir(parents=True)

            # Create a project marker
            (project_dir / "pyproject.toml").touch()

            # Test file path
            test_file = src_dir / "module.py"

            result = self.checker._get_project_root(test_file)

            # Should find project_dir as the root
            assert result == project_dir

    def test_get_project_root_fallback(self) -> None:
        """Test _get_project_root fallback when no markers found."""
        # Use a path without project markers
        test_file = Path("/tmp/isolated/module.py")

        result = self.checker._get_project_root(test_file)

        # Should fallback to parent directory
        assert result == test_file.parent

    def test_check_function_privacy_heuristic(self) -> None:
        """Test _check_function_privacy_heuristic does nothing (fallback mode)."""
        # Create a mock function and module
        mock_func = Mock(spec=nodes.FunctionDef)
        mock_func.name = "test_function"
        mock_module = Mock(spec=nodes.Module)

        functions = [mock_func]

        # Mock add_message
        self.checker.add_message = Mock()

        # Call the method
        self.checker._check_function_privacy_heuristic(functions, mock_module)

        # Verify add_message was NOT called (heuristic mode does nothing)
        self.checker.add_message.assert_not_called()

    def test_check_function_privacy_no_project_root(self) -> None:
        """Test _check_function_privacy when project root cannot be determined."""
        # Create a mock function and module
        mock_func = Mock(spec=nodes.FunctionDef)
        mock_func.name = "test_function"
        mock_module = Mock(spec=nodes.Module)

        functions = [mock_func]

        # Mock _get_module_path to return a path
        with patch.object(self.checker, "_get_module_path") as mock_get_path:
            mock_get_path.return_value = Path("/some/path/module.py")

            # Mock _get_project_root to return None (project root not found)
            with patch.object(self.checker, "_get_project_root") as mock_get_root:
                mock_get_root.return_value = None

                # Mock _check_function_privacy_heuristic
                with patch.object(
                    self.checker, "_check_function_privacy_heuristic"
                ) as mock_heuristic:
                    # Call the method
                    self.checker._check_function_privacy(functions, mock_module)

                    # Verify the heuristic method was called as fallback
                    mock_heuristic.assert_called_once_with(functions, mock_module)
