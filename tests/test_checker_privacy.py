"""Tests for the FunctionSortChecker privacy detection functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import astroid  # type: ignore[import-untyped]
import pytest
from pylint.testutils import CheckerTestCase, MessageTest

from pylint_sort_functions.checker import FunctionSortChecker

# Path to test files directory
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestFunctionSortCheckerPrivacy(CheckerTestCase):
    """Test cases for FunctionSortChecker privacy detection functionality."""

    CHECKER_CLASS = FunctionSortChecker

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

    @pytest.mark.slow
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

    def test_w9005_private_should_be_public(self) -> None:
        """Test W9005 detection for private functions that should be public."""
        # Test case: private function used by external module
        module_content = """
def _helper_function():
    return "help"

def _internal_function():
    return "internal"

def public_function():
    return "public"
"""
        module = astroid.parse(module_content, module_name="test_module")

        # Mock linter with privacy detection enabled
        self.checker.linter.config.enable_privacy_detection = True
        self.checker.linter.current_file = str(Path("/test/project/src/utils.py"))

        # Mock path methods and privacy functions
        with (
            patch.object(self.checker, "_get_project_root") as mock_project_root,
            patch(
                "pylint_sort_functions.utils.should_function_be_private"
            ) as mock_should_be_private,
            patch(
                "pylint_sort_functions.utils.should_function_be_public"
            ) as mock_should_be_public,
        ):
            # Set up path mocking
            mock_project_root.return_value = Path("/test/project")
            # should_function_be_private should return False to allow elif branch
            mock_should_be_private.return_value = False
            # Only _helper_function should be flagged as should be public
            mock_should_be_public.side_effect = lambda func, *args: (
                func.name == "_helper_function"
            )

            # Expect both mixed-function-visibility and W9005 messages
            with self.assertAddsMessages(
                MessageTest(
                    msg_id="mixed-function-visibility",
                    line=0,  # Module-level message
                    node=module,
                    args=("module",),
                    col_offset=0,
                ),
                MessageTest(
                    msg_id="function-should-be-public",
                    line=2,  # _helper_function
                    node=module.body[0],  # First function
                    args=("_helper_function",),
                    col_offset=0,
                    end_line=2,
                    end_col_offset=20,
                ),
            ):
                # Run our checker on the parsed module
                self.checker.visit_module(module)

    def test_w9005_no_false_positives(self) -> None:
        """Test that W9005 doesn't flag public/genuine private functions."""
        # Test case: mix of public and genuinely private functions
        module_content = """
def public_function():
    return "public"

def _genuinely_private():
    return "private"

def __dunder_method__(self):
    return "dunder"
"""
        module = astroid.parse(module_content, module_name="test_module")

        # Mock linter with privacy detection enabled
        mock_linter = Mock()
        mock_linter.config.public_api_patterns = {
            "main",
            "run",
            "execute",
            "start",
            "stop",
            "setup",
            "teardown",
        }
        mock_linter.config.enable_privacy_detection = True
        mock_linter.current_file = str(Path("/test/project/src/utils.py"))

        # Mock both privacy detection functions to return False
        with (
            patch.object(self.checker, "linter", mock_linter),
            patch(
                "pylint_sort_functions.utils.should_function_be_private"
            ) as mock_should_be_private,
            patch(
                "pylint_sort_functions.utils.should_function_be_public"
            ) as mock_should_be_public,
        ):
            mock_should_be_private.return_value = False
            mock_should_be_public.return_value = False

            # No privacy messages should be generated
            with self.assertNoMessages():
                self.checker.visit_module(module)

    def test_w9005_mutually_exclusive_with_w9004(self) -> None:
        """Test that W9005 and W9004 are mutually exclusive (elif logic)."""
        # Test case: function that could theoretically trigger both
        module_content = """
def ambiguous_function():
    return "ambiguous"
"""
        module = astroid.parse(module_content, module_name="test_module")

        # Mock linter with privacy detection enabled
        self.checker.linter.config.enable_privacy_detection = True
        self.checker.linter.current_file = str(Path("/test/project/src/utils.py"))

        # Mock should_function_be_private to return True (W9004)
        # should_function_be_public should not even be called due to elif
        with (
            patch.object(self.checker, "_get_project_root") as mock_project_root,
            patch(
                "pylint_sort_functions.utils.should_function_be_private"
            ) as mock_should_be_private,
            patch(
                "pylint_sort_functions.utils.should_function_be_public"
            ) as mock_should_be_public,
        ):
            # Set up path mocking
            mock_project_root.return_value = Path("/test/project")
            mock_should_be_private.return_value = True
            mock_should_be_public.return_value = True  # Should not be called

            # Should only get W9004, not W9005
            with self.assertAddsMessages(
                MessageTest(
                    msg_id="function-should-be-private",
                    line=2,  # ambiguous_function
                    node=module.body[0],
                    args=("ambiguous_function",),
                    col_offset=0,
                    end_line=2,
                    end_col_offset=22,
                ),
            ):
                self.checker.visit_module(module)

            # Verify should_function_be_public was not called due to elif
            mock_should_be_public.assert_not_called()

    def test_privacy_analysis_with_exclude_dirs(self) -> None:
        """Test privacy analysis with exclude_dirs configuration."""
        from unittest.mock import Mock

        content = """
def helper_function():
    return "helper"
"""
        # Module content for testing (unused variable is intentional for test setup)
        _ = astroid.parse(content, module_name="mymodule")

        # Mock linter config with excluded directories
        mock_linter = Mock()
        mock_linter.config.enable_privacy_detection = True
        mock_linter.config.public_api_patterns = []
        mock_linter.config.privacy_exclude_dirs = ["tests", "qa"]
        mock_linter.config.privacy_exclude_patterns = []
        mock_linter.config.privacy_additional_test_patterns = []
        mock_linter.config.privacy_update_tests = False
        mock_linter.config.privacy_override_test_detection = False

        with patch.object(self.checker, "linter", mock_linter):
            # Test that _get_privacy_config returns the correct configuration
            privacy_config = self.checker._get_privacy_config()
            assert privacy_config["exclude_dirs"] == ["tests", "qa"]
            assert privacy_config["exclude_patterns"] == []
            assert privacy_config["additional_test_patterns"] == []
            assert privacy_config["update_tests"] is False
            assert privacy_config["override_test_detection"] is False

    def test_privacy_analysis_with_exclude_patterns(self) -> None:
        """Test privacy analysis with exclude_patterns configuration."""
        from unittest.mock import Mock

        # Mock linter config with excluded patterns
        mock_linter = Mock()
        mock_linter.config.enable_privacy_detection = True
        mock_linter.config.public_api_patterns = []
        mock_linter.config.privacy_exclude_dirs = []
        mock_linter.config.privacy_exclude_patterns = ["*_spec.py", "test_*.py"]
        mock_linter.config.privacy_additional_test_patterns = []
        mock_linter.config.privacy_update_tests = False
        mock_linter.config.privacy_override_test_detection = False

        with patch.object(self.checker, "linter", mock_linter):
            # Test that _get_privacy_config returns the correct configuration
            privacy_config = self.checker._get_privacy_config()
            assert privacy_config["exclude_dirs"] == []
            assert privacy_config["exclude_patterns"] == ["*_spec.py", "test_*.py"]
            assert privacy_config["additional_test_patterns"] == []
            assert privacy_config["update_tests"] is False
            assert privacy_config["override_test_detection"] is False

    def test_privacy_analysis_with_additional_test_patterns(self) -> None:
        """Test privacy analysis with additional_test_patterns configuration."""
        from unittest.mock import Mock

        # Mock linter config with additional test patterns
        mock_linter = Mock()
        mock_linter.config.enable_privacy_detection = True
        mock_linter.config.public_api_patterns = []
        mock_linter.config.privacy_exclude_dirs = []
        mock_linter.config.privacy_exclude_patterns = []
        mock_linter.config.privacy_additional_test_patterns = [
            "scenario_*.py",
            "*_demo.py",
        ]
        mock_linter.config.privacy_update_tests = False
        mock_linter.config.privacy_override_test_detection = False

        with patch.object(self.checker, "linter", mock_linter):
            # Test that _get_privacy_config returns the correct configuration
            privacy_config = self.checker._get_privacy_config()
            assert privacy_config["exclude_dirs"] == []
            assert privacy_config["exclude_patterns"] == []
            assert privacy_config["additional_test_patterns"] == [
                "scenario_*.py",
                "*_demo.py",
            ]
            assert privacy_config["update_tests"] is False
            assert privacy_config["override_test_detection"] is False
