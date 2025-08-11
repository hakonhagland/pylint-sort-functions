"""Tests for import extraction and cross-module analysis utilities."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from pylint_sort_functions import utils


class TestUtilsImports:
    """Test cases for import and cross-module analysis utility functions."""

    def test_find_python_files(self) -> None:
        """Test finding Python files in a directory."""
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

    def test_build_cross_module_usage_graph_handles_oserror(self) -> None:
        """Test that cross-module usage graph handles OSError gracefully."""
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
