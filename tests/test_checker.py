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

    def test_function_should_be_private_no_path_info(self) -> None:
        """Test that no privacy warnings are generated without path information."""
        # Without path info, the checker falls back to heuristic approach
        # Since heuristics have been disabled, no functions should be flagged
        test_file = TEST_FILES_DIR / "modules" / "should_be_private.py"

        # Read and parse the test file
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        # Parse file into AST without path context
        module = astroid.parse(content, module_name="should_be_private")

        # With heuristics disabled, no messages should be generated
        with self.assertAddsMessages():
            # Run our checker on the parsed module
            self.checker.visit_module(module)

    def test_function_should_be_private_with_import_analysis(self) -> None:
        """Test import analysis correctly identifies should-be-private functions."""
        # Mock the linter to provide path information so import analysis runs
        test_file = TEST_FILES_DIR / "modules" / "should_be_private.py"

        # Read and parse the test file
        with open(test_file, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content, module_name="should_be_private")

        # Mock linter with current_file to enable import analysis
        self.checker.linter.current_file = str(test_file)

        # Import analysis should identify functions that should be private
        # All functions except 'main' should be flagged (main is in public_patterns)
        with self.assertAddsMessages(
            MessageTest(
                msg_id="function-should-be-private",
                line=4,  # calculate_sum
                node=module.body[0],
                args=("calculate_sum",),
                col_offset=0,
                end_line=4,
                end_col_offset=17,
            ),
            MessageTest(
                msg_id="function-should-be-private",
                line=9,  # get_data
                node=module.body[1],
                args=("get_data",),
                col_offset=0,
                end_line=9,
                end_col_offset=12,
            ),
            MessageTest(
                msg_id="function-should-be-private",
                line=14,  # helper_function
                node=module.body[2],
                args=("helper_function",),
                col_offset=0,
                end_line=14,
                end_col_offset=19,
            ),
            MessageTest(
                msg_id="function-should-be-private",
                line=25,  # process_data
                node=module.body[4],
                args=("process_data",),
                col_offset=0,
                end_line=25,
                end_col_offset=16,
            ),
            MessageTest(
                msg_id="function-should-be-private",
                line=30,  # public_api_function
                node=module.body[5],
                args=("public_api_function",),
                col_offset=0,
                end_line=30,
                end_col_offset=23,
            ),
            MessageTest(
                msg_id="function-should-be-private",
                line=35,  # validate_numbers
                node=module.body[6],
                args=("validate_numbers",),
                col_offset=0,
                end_line=35,
                end_col_offset=20,
            ),
        ):
            # Run our checker on the parsed module
            self.checker.visit_module(module)

        # Clean up mock
        self.checker.linter.current_file = None

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
        import tempfile

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

    def test_configuration_options(self) -> None:
        """Test that configuration options are properly defined."""
        # Verify options are defined
        assert hasattr(self.checker, "options")
        assert isinstance(self.checker.options, tuple)
        assert len(self.checker.options) == 2

        # Test public-api-patterns option
        public_api_option = self.checker.options[0]
        assert public_api_option[0] == "public-api-patterns"
        assert public_api_option[1]["type"] == "csv"
        assert "main" in public_api_option[1]["default"]

        # Test enable-privacy-detection option
        privacy_option = self.checker.options[1]
        assert privacy_option[0] == "enable-privacy-detection"
        assert privacy_option[1]["type"] == "yn"
        assert privacy_option[1]["default"] is True

    def test_privacy_detection_disabled(self) -> None:
        """Test that privacy detection can be disabled via configuration."""
        from unittest.mock import Mock

        content = """
def unused_function():
    pass
"""
        module = astroid.parse(content)

        # Mock linter with privacy detection disabled
        mock_linter = Mock()
        mock_linter.config.enable_privacy_detection = False

        with patch.object(self.checker, "linter", mock_linter):
            with self.assertNoMessages():
                self.checker.visit_module(module)

    def test_custom_public_api_patterns(self) -> None:
        """Test that custom public API patterns are used in privacy detection."""
        from pathlib import Path
        from unittest.mock import Mock, patch

        content = """
def handler():
    pass

def processor():
    pass
"""
        module = astroid.parse(content)

        # Mock linter with custom public API patterns
        mock_linter = Mock()
        mock_linter.config.enable_privacy_detection = True
        mock_linter.config.public_api_patterns = ["handler", "processor"]
        mock_linter.current_file = "/test/module.py"

        with patch.object(self.checker, "linter", mock_linter):
            with patch.object(self.checker, "_get_project_root") as mock_project_root:
                mock_project_root.return_value = Path("/test")

                with patch(
                    "pylint_sort_functions.utils.should_function_be_private"
                ) as mock_should_private:
                    mock_should_private.return_value = False

                    with self.assertNoMessages():
                        self.checker.visit_module(module)

                    # Verify should_function_be_private was called with custom patterns
                    assert mock_should_private.call_count == 2
                    call_args = mock_should_private.call_args_list[0]
                    # Check the fourth argument (public_patterns)
                    assert call_args[0][3] == {"handler", "processor"}
