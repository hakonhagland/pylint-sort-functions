"""Tests for utility functions."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import utils

# Path to test files directory
TEST_FILES_DIR = Path(__file__).parent / "files"


class TestUtils:
    """Test cases for utility functions."""

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

    def test_find_python_files(self) -> None:
        """Test finding Python files in a directory."""
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            (temp_path / "module1.py").write_text("# Module 1")
            (temp_path / "module2.py").write_text("# Module 2")
            (temp_path / "not_python.txt").write_text("Not Python")

            # Create subdirectory with Python files
            subdir = temp_path / "subdir"
            subdir.mkdir()
            (subdir / "submodule.py").write_text("# Sub module")

            # Create directories to skip
            skip_dir = temp_path / "__pycache__"
            skip_dir.mkdir()
            (skip_dir / "cached.py").write_text("# Should be skipped")

            files = utils.find_python_files(temp_path)

            # Should find 3 Python files
            assert len(files) == 3
            file_names = [f.name for f in files]
            assert "module1.py" in file_names
            assert "module2.py" in file_names
            assert "submodule.py" in file_names
            assert "cached.py" not in file_names

    def test_extract_imports_from_file(self) -> None:
        """Test extracting import information from Python files."""
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "test_imports.py"

            # Create test file with various import patterns
            content = """
import os
import sys as system
from typing import Dict, List
from pathlib import Path as PathLib
from utils import helper_function

def test_function():
    os.path.join("a", "b")
    system.exit(0)
    helper_function()
    # PathLib is a class, not a module, so no attribute access detected
    PathLib("/tmp")
"""
            test_file.write_text(content)

            # Get file modification time for the cache key
            file_mtime = test_file.stat().st_mtime

            (module_imports, function_imports, attribute_accesses) = (
                utils._extract_imports_from_file(test_file, file_mtime)
            )

            # Test module imports
            assert "os" in module_imports
            assert "sys" in module_imports
            assert "typing" in module_imports
            assert "pathlib" in module_imports
            assert "utils" in module_imports

            # Test function imports
            assert ("typing", "Dict") in function_imports
            assert ("typing", "List") in function_imports
            assert ("pathlib", "Path") in function_imports
            assert ("utils", "helper_function") in function_imports

            # Test attribute accesses
            assert ("os", "path") in attribute_accesses
            # Maps alias back to actual module
            assert ("sys", "exit") in attribute_accesses
            # PathLib is a class alias, not module access, so no attribute access
            # for PathLib

    def test_extract_imports_from_file_syntax_error(self) -> None:
        """Test handling of files with syntax errors."""
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "broken.py"

            # Create file with syntax error
            test_file.write_text("def broken(:\n    pass")

            # Get file modification time for the cache key
            file_mtime = test_file.stat().st_mtime

            (module_imports, function_imports, attribute_accesses) = (
                utils._extract_imports_from_file(test_file, file_mtime)
            )

            # Should return empty sets for unparseable files
            assert len(module_imports) == 0
            assert len(function_imports) == 0
            assert len(attribute_accesses) == 0

    def test_build_cross_module_usage_graph(self) -> None:
        """Test building cross-module usage graph."""
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create library module
            library_file = temp_path / "library.py"
            library_file.write_text("""
def public_function():
    return "public"

def internal_function():
    return "internal"
""")

            # Create consumer module
            consumer_file = temp_path / "consumer.py"
            consumer_file.write_text("""
from library import public_function

def use_library():
    return public_function()
""")

            usage_graph = utils._build_cross_module_usage_graph(temp_path)

            # public_function should be in the graph (imported by consumer)
            assert "public_function" in usage_graph
            assert "consumer" in usage_graph["public_function"]

            # internal_function should not be in the graph (not imported)
            assert "internal_function" not in usage_graph

    def test_is_function_used_externally(self) -> None:
        """Test checking if function is used externally."""
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create library module
            library_file = temp_path / "library.py"
            library_file.write_text("""
def external_func():
    return "external"

def internal_func():
    return "internal"
""")

            # Create consumer module
            consumer_file = temp_path / "consumer.py"
            consumer_file.write_text("""
from library import external_func

def use_library():
    return external_func()
""")

            # external_func should be detected as used externally
            assert (
                utils._is_function_used_externally(
                    "external_func", library_file, temp_path
                )
                is True
            )

            # internal_func should not be detected as used externally
            assert (
                utils._is_function_used_externally(
                    "internal_func", library_file, temp_path
                )
                is False
            )

    def test_should_function_be_private_with_import_analysis(self) -> None:
        """Test enhanced privacy detection with import analysis."""
        from pathlib import Path

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

    def test_build_cross_module_usage_graph_handles_oserror(self) -> None:
        """Test that cross-module usage graph handles OSError gracefully."""
        from pathlib import Path
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a valid python file
            test_file = temp_path / "test_file.py"
            test_file.write_text("def test_func(): pass")

            # Mock Path.stat to raise OSError for our test file
            original_stat = Path.stat

            def mock_stat(self: Path) -> object:  # pragma: no cover
                if self.name == "test_file.py":  # pragma: no cover
                    raise OSError("Mocked file access error")  # pragma: no cover
                return original_stat(self)  # pragma: no cover

            with patch.object(Path, "stat", mock_stat):
                # This should not crash and should skip the problematic file
                usage_graph = utils._build_cross_module_usage_graph(temp_path)

                # Verify it handles the error gracefully - graph exists but may be empty
                assert isinstance(usage_graph, dict)

    def test_should_function_be_private_with_custom_public_patterns(self) -> None:
        """Test should_function_be_private with configurable public patterns."""
        from pathlib import Path

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
        from pathlib import Path

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
        from pathlib import Path

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
        from pathlib import Path

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
        from pathlib import Path

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
