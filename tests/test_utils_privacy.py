"""Tests for privacy detection and analysis utilities."""

import tempfile
from pathlib import Path

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import utils

# Path to test files directory
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestUtilsPrivacy:
    """Test cases for privacy detection utility functions."""

    def test_should_function_be_private_dunder_methods(self) -> None:
        """Test that dunder methods are not flagged as should be private."""
        file_path = TEST_FILES_DIR / "modules" / "dunder_methods.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)

        # Test __get_something__ method (first function)
        dunder_func = module.body[0]
        assert isinstance(dunder_func, nodes.FunctionDef)
        assert dunder_func.name == "__get_something__"

        # Using dummy paths for testing
        module_path = Path("dummy_module.py")
        project_root = Path(".")
        result = utils.should_function_be_private(
            dunder_func, module_path, project_root
        )

        # Dunder methods should never be flagged as should be private
        assert result is False

        # Test get_helper function (second function)
        helper_func = module.body[1]
        assert isinstance(helper_func, nodes.FunctionDef)
        assert helper_func.name == "get_helper"

        result = utils.should_function_be_private(
            helper_func, module_path, project_root
        )

        # get_helper is not imported or used by any other module in the test setup
        # With import analysis, it should be flagged as a candidate for being private
        assert result is True

    def test_should_function_be_private_with_import_analysis(self) -> None:
        """Test enhanced privacy detection with import analysis."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create library module
            library_file = temp_path / "library.py"
            library_content = """
def public_api():
    return "public"

def internal_helper():
    return "internal"

def main():
    return "entry point"

def __special__():
    return "special"
"""
            library_file.write_text(library_content)

            # Create consumer module
            consumer_file = temp_path / "consumer.py"
            consumer_file.write_text("""
from library import public_api

def use_library():
    return public_api()
""")

            # Parse the library module
            module = astroid.parse(library_content)
            functions = utils.get_functions_from_node(module)

            # Test each function
            public_api_func = functions[0]
            internal_helper_func = functions[1]
            main_func = functions[2]
            special_func = functions[3]

            # public_api should not be flagged (used externally)
            result = utils.should_function_be_private(
                public_api_func, library_file, temp_path
            )
            assert result is False

            # internal_helper should be flagged (not used externally)
            result = utils.should_function_be_private(
                internal_helper_func, library_file, temp_path
            )
            assert result is True

            # main should not be flagged (public pattern)
            result = utils.should_function_be_private(
                main_func, library_file, temp_path
            )
            assert result is False

            # __special__ should not be flagged (dunder method)
            result = utils.should_function_be_private(
                special_func, library_file, temp_path
            )
            assert result is False

    def test_should_function_be_private_with_custom_public_patterns(self) -> None:
        """Test should_function_be_private with configurable public patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create library module with custom public API patterns
            library_file = temp_path / "library.py"
            library_content = """
def handler():
    return "handles requests"

def processor():
    return "processes data"

def internal_utility():
    return "utility"

def main():
    return "default pattern"
"""
            library_file.write_text(library_content)

            # Parse the library module
            module = astroid.parse(library_content)
            functions = utils.get_functions_from_node(module)

            handler_func = functions[0]
            processor_func = functions[1]
            internal_func = functions[2]
            main_func = functions[3]

            # Test with default patterns - only main should be excluded
            assert (
                utils.should_function_be_private(handler_func, library_file, temp_path)
                is True
            )
            assert (
                utils.should_function_be_private(
                    processor_func, library_file, temp_path
                )
                is True
            )
            assert (
                utils.should_function_be_private(internal_func, library_file, temp_path)
                is True
            )
            assert (
                utils.should_function_be_private(main_func, library_file, temp_path)
                is False
            )  # main is default pattern

            # Test with custom patterns - handler and processor should now be excluded
            custom_patterns = {"handler", "processor", "main"}
            assert (
                utils.should_function_be_private(
                    handler_func, library_file, temp_path, custom_patterns
                )
                is False
            )
            assert (
                utils.should_function_be_private(
                    processor_func, library_file, temp_path, custom_patterns
                )
                is False
            )
            assert (
                utils.should_function_be_private(
                    internal_func, library_file, temp_path, custom_patterns
                )
                is True
            )
            assert (
                utils.should_function_be_private(
                    main_func, library_file, temp_path, custom_patterns
                )
                is False
            )

            # Test with empty patterns set - all functions should be private candidates
            empty_patterns: set[str] = set()
            assert (
                utils.should_function_be_private(
                    handler_func, library_file, temp_path, empty_patterns
                )
                is True
            )
            assert (
                utils.should_function_be_private(
                    processor_func, library_file, temp_path, empty_patterns
                )
                is True
            )
            assert (
                utils.should_function_be_private(
                    internal_func, library_file, temp_path, empty_patterns
                )
                is True
            )
            assert (
                utils.should_function_be_private(
                    main_func, library_file, temp_path, empty_patterns
                )
                is True
            )

    def test_should_function_be_public_basic(self) -> None:
        """Test should_function_be_public basic functionality."""
        # Create test functions
        public_func = astroid.extract_node("def public_function(): pass  #@")
        dunder_func = astroid.extract_node("def __init__(self): pass  #@")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test_module.py"
            test_file.write_text("# Test module")

            # Public function should return False (already public)
            assert (
                utils.should_function_be_public(public_func, test_file, temp_path)
                is False
            )

            # Dunder method should return False (not considered private)
            assert (
                utils.should_function_be_public(dunder_func, test_file, temp_path)
                is False
            )

    def test_should_function_be_public_with_external_usage(self) -> None:
        """Test should_function_be_public detects external usage correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create main module that imports a private function
            main_file = temp_path / "main.py"
            main_file.write_text("""
from utils import _helper_function

def main():
    return _helper_function()
""")

            # Create utils module with private function
            utils_file = temp_path / "utils.py"
            utils_file.write_text("""
def _helper_function():
    return "help"

def _internal_only():
    return "internal"
""")

            # Parse the functions
            with open(utils_file, encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name="utils")
            helper_func = module.body[0]  # _helper_function
            internal_func = module.body[1]  # _internal_only

            # _helper_function should be flagged (used externally)
            assert (
                utils.should_function_be_public(helper_func, utils_file, temp_path)
                is True
            )

            # _internal_only should not be flagged (not used externally)
            assert (
                utils.should_function_be_public(internal_func, utils_file, temp_path)
                is False
            )

    def test_should_function_be_public_no_external_usage(self) -> None:
        """Test should_function_be_public returns False for private functions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create standalone module with only private functions
            utils_file = temp_path / "standalone.py"
            utils_file.write_text("""
def _helper_one():
    return _helper_two()

def _helper_two():
    return "help"

def main():
    return _helper_one()
""")

            # Parse the functions
            with open(utils_file, encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name="standalone")
            helper_one = module.body[0]  # _helper_one
            helper_two = module.body[1]  # _helper_two

            # Both private functions should not be flagged (no external usage)
            assert (
                utils.should_function_be_public(helper_one, utils_file, temp_path)
                is False
            )
            assert (
                utils.should_function_be_public(helper_two, utils_file, temp_path)
                is False
            )

    def test_should_function_be_public_cross_module_import(self) -> None:
        """Test should_function_be_public detects cross-module imports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create package structure
            package_dir = temp_path / "mypackage"
            package_dir.mkdir()
            (package_dir / "__init__.py").touch()

            # Create module A that exports a private function
            module_a = package_dir / "module_a.py"
            module_a.write_text("""
def _shared_utility():
    return "shared"

def _truly_private():
    return "private"
""")

            # Create module B that imports from A
            module_b = package_dir / "module_b.py"
            module_b.write_text("""
from mypackage.module_a import _shared_utility

def use_shared():
    return _shared_utility()
""")

            # Parse module A functions
            with open(module_a, encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name="mypackage.module_a")
            shared_func = module.body[0]  # _shared_utility
            private_func = module.body[1]  # _truly_private

            # _shared_utility should be flagged (imported by module B)
            assert (
                utils.should_function_be_public(shared_func, module_a, temp_path)
                is True
            )

            # _truly_private should not be flagged (not used externally)
            assert (
                utils.should_function_be_public(private_func, module_a, temp_path)
                is False
            )

    def test_should_function_be_private_excludes_test_usage_issue_26(self) -> None:
        """Test that functions used only by test files should not be marked as private.

        This test demonstrates issue #26: Privacy detection should exclude test files
        from analysis to prevent breaking test imports.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a library module with functions
            library_file = temp_path / "library.py"
            library_file.write_text("""
def public_api():
    \"\"\"This is used by production code.\"\"\"
    return "public"

def helper_function():
    \"\"\"This is only used by tests - should remain public.\"\"\"
    return "helper"

def _already_private():
    \"\"\"Already private function.\"\"\"
    return "private"
""")

            # Create a production module that uses public_api
            app_file = temp_path / "app.py"
            app_file.write_text("""
from library import public_api

def main():
    return public_api()
""")

            # Create test files with different naming patterns
            self._create_test_files_for_issue_26(temp_path)

            # Parse the library module
            with open(library_file, encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name="library")

            public_api_func = module.body[0]  # public_api
            helper_func = module.body[1]  # helper_function
            private_func = module.body[2]  # _already_private

            # public_api is used by production code, should not be marked private
            assert (
                utils.should_function_be_private(
                    public_api_func, library_file, temp_path
                )
                is False
            )

            # helper_function is ONLY used by test files
            # With improved test detection (Approach 1):
            # - Test files are properly excluded from analysis
            # - helper_function has no external usage (tests don't count)
            # - Therefore it WILL be marked as should be private
            #
            # This is actually the CORRECT behavior for Approach 1, but highlights
            # why Approach 2 (updating test files) would be better
            should_be_private = utils.should_function_be_private(
                helper_func, library_file, temp_path
            )

            # With proper test file exclusion, functions used only by tests
            # will be marked as needing to be private (True)
            # This is the expected behavior for Approach 1
            assert should_be_private is True, (
                f"With proper test exclusion, helper_function should be "
                f"marked as private. Got should_be_private={should_be_private}. "
                f"This demonstrates that Approach 1 works but has limitations - "
                f"see issue #28 for Approach 2 which would update test files."
            )

            # _already_private should remain as-is (already private)
            assert (
                utils.should_function_be_private(private_func, library_file, temp_path)
                is False
            )  # Returns False because it's already private

    def test_helper_method(self) -> None:
        """Test helper method for test file creation."""
        # This is a simple test to ensure helper method works
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            self._create_test_files_for_issue_26(temp_path)

            # Verify test files were created
            assert (temp_path / "test_library.py").exists()
            assert (temp_path / "tests" / "test_integration.py").exists()
            assert (temp_path / "library_test.py").exists()
            assert (temp_path / "conftest.py").exists()

    def test_should_function_be_private_with_privacy_config(self) -> None:
        """Test should_function_be_private respects privacy configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create library with functions
            library_file = temp_path / "library.py"
            library_file.write_text("""
def public_function():
    return "public"

def internal_function():
    return "internal"
""")

            # Create test file that uses internal_function
            test_file = temp_path / "test_library.py"
            test_file.write_text("""
from library import internal_function

def test_internal():
    assert internal_function() == "internal"
""")

            # Create custom test-like file that uses internal_function
            spec_file = temp_path / "library_spec.py"
            spec_file.write_text("""
from library import internal_function

def spec_internal():
    assert internal_function() == "internal"
""")

            # Parse functions
            with open(library_file, encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name="library")
            internal_func = module.body[1]

            # Without privacy config, internal_function should NOT be marked as private
            # because it's used by library_spec.py which is not detected as a test file
            assert (
                utils.should_function_be_private(internal_func, library_file, temp_path)
                is False
            )

            # With privacy config that includes spec files as tests
            privacy_config = {
                "exclude_dirs": [],
                "exclude_patterns": [],
                "additional_test_patterns": ["*_spec.py"],
            }

            # internal_function is still only used by test-like files, should be private
            assert (
                utils.should_function_be_private(
                    internal_func, library_file, temp_path, None, privacy_config
                )
                is True
            )

    def test_should_function_be_public_with_privacy_config(self) -> None:
        """Test should_function_be_public respects privacy configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create library with private function
            library_file = temp_path / "library.py"
            library_file.write_text("""
def _helper_function():
    return "helper"
""")

            # Create custom test-like file that imports the private function
            spec_file = temp_path / "library_spec.py"
            spec_file.write_text("""
from library import _helper_function

def spec_helper():
    assert _helper_function() == "helper"
""")

            # Parse function
            with open(library_file, encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name="library")
            helper_func = module.body[0]

            # Without additional patterns, _helper_function IS used externally
            # by library_spec.py
            assert (
                utils.should_function_be_public(helper_func, library_file, temp_path)
                is True
            )

            # With privacy config that excludes spec files from analysis
            privacy_config = {
                "exclude_dirs": [],
                "exclude_patterns": [],
                "additional_test_patterns": ["*_spec.py"],
            }

            # _helper_function is still not used by non-test code, should stay private
            assert (
                utils.should_function_be_public(
                    helper_func, library_file, temp_path, privacy_config
                )
                is False
            )

    def test_privacy_config_backward_compatibility(self) -> None:
        """Test privacy functions work without privacy config (backward compat)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create simple library
            library_file = temp_path / "library.py"
            library_file.write_text("""
def public_function():
    return "public"

def _private_function():
    return "private"
""")

            # Parse functions
            with open(library_file, encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name="library")
            public_func = module.body[0]
            private_func = module.body[1]

            # Test that functions work with None privacy_config
            assert (
                utils.should_function_be_private(
                    public_func, library_file, temp_path, None, None
                )
                is True
            )  # No external usage, should be private

            assert (
                utils.should_function_be_public(
                    private_func, library_file, temp_path, None
                )
                is False
            )  # No external usage, should stay private

    # Private methods

    def _create_test_files_for_issue_26(self, temp_path: Path) -> None:
        """Helper to create test files for issue #26 test case."""
        # Pattern 1: test_*.py in root
        test_file1 = temp_path / "test_library.py"
        test_file1.write_text("""
from library import helper_function
import mock

def test_helper():
    assert helper_function() == "helper"

@mock.patch('library.helper_function')
def test_with_mock(mock_helper):
    mock_helper.return_value = "mocked"
""")

        # Pattern 2: tests/ directory
        tests_dir = temp_path / "tests"
        tests_dir.mkdir()
        test_file2 = tests_dir / "test_integration.py"
        test_file2.write_text("""
from library import helper_function

def test_integration():
    result = helper_function()
    assert result == "helper"
""")

        # Pattern 3: *_test.py pattern
        test_file3 = temp_path / "library_test.py"
        test_file3.write_text("""
from library import helper_function

class TestLibrary:
    def test_helper_method(self):
        assert helper_function() == "helper"
""")

        # Pattern 4: conftest.py (pytest configuration)
        conftest_file = temp_path / "conftest.py"
        conftest_file.write_text("""
from library import helper_function

def pytest_configure(config):
    # Use helper_function in test configuration
    helper_function()
""")
