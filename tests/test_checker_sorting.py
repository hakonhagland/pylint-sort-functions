"""Tests for the FunctionSortChecker sorting functionality."""

from pathlib import Path

import astroid  # type: ignore[import-untyped]
from astroid import nodes
from pylint.testutils import CheckerTestCase, MessageTest

from pylint_sort_functions.checker import FunctionSortChecker

# Path to test files directory
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestFunctionSortCheckerSorting(CheckerTestCase):
    """Test cases for FunctionSortChecker sorting functionality."""

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

    def test_visit_module_mixed_function_visibility(self) -> None:
        """Test that visit_module detects mixed function visibility."""
        # Code with mixed visibility: public -> private -> public
        content = '''
def public_function_1():
    """First public function."""
    pass

def _private_function():
    """A private function."""
    pass

def public_function_2():
    """Second public function - should come before private."""
    pass
'''

        module = astroid.parse(content)

        with self.assertAddsMessages(
            MessageTest(
                msg_id="mixed-function-visibility",
                line=0,  # Module-level message appears on line 0
                node=module,
                args=("module",),
                col_offset=0,
            )
        ):
            self.checker.visit_module(module)
