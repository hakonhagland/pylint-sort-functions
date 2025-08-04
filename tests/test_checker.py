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
        """Test that mixed public/private methods trigger warnings."""
        # Integration test: Run pylint on real file with mixed visibility methods
        test_file = TEST_FILES_DIR / "classes" / "mixed_method_visibility.py"

        # Read and parse the test file
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        # Parse file into AST
        module = astroid.parse(content, module_name="mixed_method_visibility")

        # Get the first class (Calculator) from the module
        class_node = module.body[0]
        assert isinstance(class_node, nodes.ClassDef)

        # Use pylint testing framework to verify expected messages are generated
        with self.assertAddsMessages(
            MessageTest(
                msg_id="mixed-function-visibility",
                line=4,  # Class definition starts on line 4
                node=class_node,  # The actual class AST node
                args=("class Calculator",),  # Class name in the message
                col_offset=0,  # Column offset for class-level messages
                end_line=4,  # End line matches the class definition
                end_col_offset=16,  # End column offset
            )
        ):
            # Run our checker on the parsed class
            self.checker.visit_classdef(class_node)

    def test_sorted_functions_pass(self) -> None:
        """Test that properly sorted functions don't trigger warnings."""
        # Integration test: Run pylint on real file with sorted functions
        test_file = TEST_FILES_DIR / "modules" / "sorted_functions.py"

        # Read and parse the test file
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        # Parse file into AST
        module = astroid.parse(content, module_name="sorted_functions")

        # Use pylint testing framework to verify no messages are generated
        with self.assertAddsMessages():
            # Run our checker on the parsed module
            self.checker.visit_module(module)

    def test_sorted_methods_pass(self) -> None:
        """Test that properly sorted methods don't trigger warnings."""
        # Integration test: Create a simple class with only public methods (no __init__)
        # to avoid mixed visibility issue caused by __init__ being considered private
        test_code = '''
class SimpleClass:
    """Simple class with only public methods."""

    def method_a(self) -> str:
        """Method A."""
        return "a"

    def method_b(self) -> str:
        """Method B."""
        return "b"
'''

        # Parse code into AST
        module = astroid.parse(test_code, module_name="simple_class")

        # Get the class from the module
        class_node = module.body[0]
        assert isinstance(class_node, nodes.ClassDef)

        # Use pylint testing framework to verify no messages are generated
        with self.assertAddsMessages():
            # Run our checker on the parsed class
            self.checker.visit_classdef(class_node)

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
        # Integration test: Run pylint on real file with unsorted methods
        test_file = TEST_FILES_DIR / "classes" / "unsorted_methods.py"

        # Read and parse the test file
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        # Parse file into AST
        module = astroid.parse(content, module_name="unsorted_methods")

        # Get the first class (Calculator) from the module
        class_node = module.body[0]
        assert isinstance(class_node, nodes.ClassDef)

        # Use pylint testing framework to verify expected messages are generated
        # This file has unsorted methods (but properly separated visibility)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="unsorted-methods",
                line=4,  # Class definition starts on line 4
                node=class_node,  # The actual class AST node
                args=("Calculator",),  # Class name in the message
                col_offset=0,  # Column offset for class-level messages
                end_line=4,  # End line matches the class definition
                end_col_offset=16,  # End column offset
            ),
        ):
            # Run our checker on the parsed class
            self.checker.visit_classdef(class_node)

    def test_function_should_be_private_fail(self) -> None:
        """Test that functions that should be private trigger warnings."""
        # Integration test: Run pylint on real file with functions that should be
        # private
        test_file = TEST_FILES_DIR / "modules" / "should_be_private.py"

        # Read and parse the test file
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        # Parse file into AST
        module = astroid.parse(content, module_name="should_be_private")

        # Use pylint testing framework to verify expected messages are generated
        # We expect multiple functions to be flagged as should be private
        with self.assertAddsMessages(
            MessageTest(
                msg_id="function-should-be-private",
                line=14,  # helper_function
                node=module.body[2],  # Third function definition
                args=("helper_function",),
                col_offset=0,
                end_line=14,
                end_col_offset=19,
            ),
            MessageTest(
                msg_id="function-should-be-private",
                line=25,  # process_data
                node=module.body[4],  # Fifth function definition
                args=("process_data",),
                col_offset=0,
                end_line=25,
                end_col_offset=16,
            ),
            MessageTest(
                msg_id="function-should-be-private",
                line=35,  # validate_numbers
                node=module.body[6],  # Seventh function definition
                args=("validate_numbers",),
                col_offset=0,
                end_line=35,
                end_col_offset=20,
            ),
        ):
            # Run our checker on the parsed module
            self.checker.visit_module(module)

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
