"""Tests for the FunctionSortChecker."""

from pathlib import Path
from unittest.mock import Mock, patch

import astroid  # type: ignore[import-untyped]
from astroid import nodes
from pylint.testutils import CheckerTestCase, MessageTest

from pylint_sort_functions.checker import FunctionSortChecker

# Path to test files directory
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestFunctionSortChecker(CheckerTestCase):
    """Test cases for FunctionSortChecker."""

    CHECKER_CLASS = FunctionSortChecker

    def test_mixed_visibility_fail(self) -> None:
        """Test that mixed public/private functions trigger warnings."""
        # TODO: Implement test for mixed visibility functions
        pass

    def test_sorted_functions_pass(self) -> None:
        """Test that properly sorted functions don't trigger warnings."""
        # TODO: Implement test for correctly sorted functions
        pass

    def test_sorted_methods_pass(self) -> None:
        """Test that properly sorted methods don't trigger warnings."""
        # TODO: Implement test for correctly sorted methods
        pass

    def test_unsorted_functions_fail(self) -> None:
        """Test that unsorted functions trigger warnings."""
        # Integration test: Run pylint on real file with unsorted functions
        test_file = TEST_FILES_DIR / "modules" / "unsorted_functions.py"

        # Read and parse the test file
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        # Parse file into AST
        module = astroid.parse(content, module_name="unsorted_functions")

        # Use pylint testing framework to verify checker generates expected message
        with self.assertAddsMessages(
            MessageTest(
                msg_id="unsorted-functions",
                line=0,  # Module-level message appears on line 0 in pylint
                node=module,  # The actual AST node
                args=("module",),
                col_offset=0,  # Column offset for module-level messages
            )
        ):
            # Run our checker on the parsed module
            self.checker.visit_module(module)

    def test_unsorted_methods_fail(self) -> None:
        """Test that unsorted methods trigger warnings."""
        # TODO: Implement test for incorrectly sorted methods
        pass

    def test_visit_classdef_calls_utils(self) -> None:
        """Test that visit_classdef calls utility functions and adds messages."""
        mock_node = Mock(spec=nodes.ClassDef)
        mock_node.name = "TestClass"

        with (
            patch(
                "pylint_sort_functions.utils.get_methods_from_class"
            ) as mock_get_methods,
            patch("pylint_sort_functions.utils.are_methods_sorted") as mock_are_sorted,
            patch(
                "pylint_sort_functions.utils.are_functions_properly_separated"
            ) as mock_are_separated,
        ):
            mock_get_methods.return_value = []
            mock_are_sorted.return_value = False
            mock_are_separated.return_value = False

            # Mock the add_message method
            self.checker.add_message = Mock()

            self.checker.visit_classdef(mock_node)

            # Verify utility functions were called
            mock_get_methods.assert_called_once_with(mock_node)
            mock_are_sorted.assert_called_once_with([])
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
            patch("pylint_sort_functions.utils.are_methods_sorted") as mock_are_sorted,
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
                "pylint_sort_functions.utils.are_functions_sorted"
            ) as mock_are_sorted,
        ):
            mock_get_functions.return_value = []
            mock_are_sorted.return_value = False

            # Mock the add_message method
            self.checker.add_message = Mock()

            self.checker.visit_module(mock_node)

            # Verify utility functions were called
            mock_get_functions.assert_called_once_with(mock_node)
            mock_are_sorted.assert_called_once_with([])

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
                "pylint_sort_functions.utils.are_functions_sorted"
            ) as mock_are_sorted,
        ):
            mock_get_functions.return_value = []
            mock_are_sorted.return_value = True

            # Mock the add_message method
            self.checker.add_message = Mock()

            self.checker.visit_module(mock_node)

            # Verify no message was added
            self.checker.add_message.assert_not_called()
