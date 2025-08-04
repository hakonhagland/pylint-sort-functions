"""Tests for utility functions."""

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

        result = utils.are_functions_sorted(functions)
        assert result is True

    def test_are_functions_sorted_false(self) -> None:
        """Test function sorting validation with unsorted functions."""
        file_path = TEST_FILES_DIR / "modules" / "unsorted_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils.are_functions_sorted(functions)
        assert result is False

    def test_are_functions_sorted_false_private_only(self) -> None:
        """Test function sorting validation with unsorted private functions."""
        file_path = TEST_FILES_DIR / "modules" / "unsorted_private_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils.are_functions_sorted(functions)
        assert result is False

    def test_are_functions_sorted_true(self) -> None:
        """Test function sorting validation with sorted functions."""
        file_path = TEST_FILES_DIR / "modules" / "sorted_functions.py"
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        module = astroid.parse(content)
        functions = utils.get_functions_from_node(module)

        result = utils.are_functions_sorted(functions)
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

        result = utils.are_methods_sorted(methods)
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

        result = utils.are_methods_sorted(methods)
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

        result = utils._is_private_function(mock_func)

        assert result is True

    def test_is_private_function_with_public_name(self) -> None:
        """Test private function detection with public name."""
        mock_func = Mock(spec=nodes.FunctionDef)
        mock_func.name = "public_function"

        result = utils._is_private_function(mock_func)

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

        result = utils.should_function_be_private(dunder_func, module)

        # Dunder methods should never be flagged as should be private
        assert result is False

        # Test get_helper function (second function)
        helper_func = module.body[1]
        assert isinstance(helper_func, nodes.FunctionDef)
        assert helper_func.name == "get_helper"

        result = utils.should_function_be_private(helper_func, module)

        # get_helper has "get_" prefix but isn't called by anything else in the module
        # The heuristic approach only flags functions that have helper patterns
        # AND are used internally
        # Since get_helper is not called by other functions, it shouldn't be flagged
        assert result is False

    def test_find_python_files(self) -> None:
        """Test finding Python files in a directory."""
        import tempfile
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

            files = utils._find_python_files(temp_path)

            # Should find 3 Python files
            assert len(files) == 3
            file_names = [f.name for f in files]
            assert "module1.py" in file_names
            assert "module2.py" in file_names
            assert "submodule.py" in file_names
            assert "cached.py" not in file_names

    def test_extract_imports_from_file(self) -> None:
        """Test extracting import information from Python files."""
        import tempfile
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

            (module_imports, function_imports, attribute_accesses) = (
                utils._extract_imports_from_file(test_file)
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
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            test_file = temp_path / "broken.py"

            # Create file with syntax error
            test_file.write_text("def broken(:\n    pass")

            (module_imports, function_imports, attribute_accesses) = (
                utils._extract_imports_from_file(test_file)
            )

            # Should return empty sets for unparseable files
            assert len(module_imports) == 0
            assert len(function_imports) == 0
            assert len(attribute_accesses) == 0

    def test_build_cross_module_usage_graph(self) -> None:
        """Test building cross-module usage graph."""
        import tempfile
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
        import tempfile
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
        import tempfile
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
            result = utils.should_function_be_private_with_import_analysis(
                public_api_func, library_file, temp_path
            )
            assert result is False

            # internal_helper should be flagged (not used externally)
            result = utils.should_function_be_private_with_import_analysis(
                internal_helper_func, library_file, temp_path
            )
            assert result is True

            # main should not be flagged (public pattern)
            result = utils.should_function_be_private_with_import_analysis(
                main_func, library_file, temp_path
            )
            assert result is False

            # __special__ should not be flagged (dunder method)
            result = utils.should_function_be_private_with_import_analysis(
                special_func, library_file, temp_path
            )
            assert result is False
