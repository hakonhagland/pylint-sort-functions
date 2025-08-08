"""Tests for auto-fix functionality."""  # pylint: disable=too-many-lines

import os
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

from pylint_sort_functions.auto_fix import (
    AutoFixConfig,
    FunctionSorter,
    sort_python_file,
)


class TestAutoFix:
    """Test auto-fix functionality."""

    def test_basic_function_sorting(self) -> None:
        """Test basic function sorting works."""
        unsorted_code = '''"""Test module with unsorted functions."""


def zebra():
    """Last function alphabetically."""
    return "zebra"


def apple():
    """First function alphabetically."""
    return "apple"


def banana():
    """Middle function alphabetically."""
    return "banana"
'''

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(unsorted_code)
            temp_file = Path(f.name)

        try:
            # Test auto-fix
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True  # File was modified

            # Check the result
            sorted_content = temp_file.read_text()

            # Verify functions are now sorted
            lines = sorted_content.splitlines()
            function_lines = [
                i for i, line in enumerate(lines) if line.startswith("def ")
            ]

            assert len(function_lines) == 3
            # Should be apple, banana, zebra
            assert "def apple():" in lines[function_lines[0]]
            assert "def banana():" in lines[function_lines[1]]
            assert "def zebra():" in lines[function_lines[2]]

        finally:
            # Clean up
            temp_file.unlink()

    def test_private_function_sorting(self) -> None:
        """Test private function sorting."""
        unsorted_code = '''"""Test module with unsorted private functions."""


def zebra_public():
    """Public function."""
    return "zebra"


def apple_public():
    """Public function."""
    return "apple"


def _zebra_private():
    """Private function."""
    return "_zebra"


def _apple_private():
    """Private function."""
    return "_apple"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(unsorted_code)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True

            sorted_content = temp_file.read_text()
            lines = sorted_content.splitlines()
            function_lines = [
                i for i, line in enumerate(lines) if line.startswith("def ")
            ]

            # Should be: apple_public, zebra_public, _apple_private, _zebra_private
            assert "def apple_public():" in lines[function_lines[0]]
            assert "def zebra_public():" in lines[function_lines[1]]
            assert "def _apple_private():" in lines[function_lines[2]]
            assert "def _zebra_private():" in lines[function_lines[3]]

        finally:
            temp_file.unlink()

    def test_no_change_when_already_sorted(self) -> None:
        """Test that no change is made when functions are already sorted."""
        sorted_code = '''"""Test module with sorted functions."""


def apple():
    """First function."""
    return "apple"


def banana():
    """Second function."""
    return "banana"


def zebra():
    """Third function."""
    return "zebra"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sorted_code)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is False  # No modification needed

            # Content should be unchanged
            final_content = temp_file.read_text()
            assert final_content == sorted_code

        finally:
            temp_file.unlink()

    def test_dry_run_mode(self) -> None:
        """Test dry-run mode doesn't modify files."""
        unsorted_code = '''"""Test module."""


def zebra():
    return "zebra"


def apple():
    return "apple"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(unsorted_code)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=True, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True  # Would modify

            # Content should be unchanged in dry-run
            final_content = temp_file.read_text()
            assert final_content == unsorted_code

        finally:
            temp_file.unlink()

    def test_decorator_exclusions(self) -> None:
        """Test that functions with excluded decorators are not sorted."""
        code_with_decorators = '''"""Test module with decorators."""

import click


def zebra_helper():
    """Helper function that should be sorted."""
    return "zebra"


@click.command()
def create():
    """Click command that should be excluded."""
    return "create"


def apple_helper():
    """Helper function that should be sorted."""
    return "apple"


@click.command()
def delete():
    """Click command that should be excluded."""
    return "delete"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_decorators)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(
                dry_run=False, backup=False, ignore_decorators=["@click.command"]
            )
            result = sort_python_file(temp_file, config)

            assert result is True

            sorted_content = temp_file.read_text()
            lines = sorted_content.splitlines()

            # Helper functions should be sorted: apple_helper, zebra_helper
            # Decorated functions should remain in original positions
            apple_line = next(
                i for i, line in enumerate(lines) if "def apple_helper():" in line
            )
            zebra_line = next(
                i for i, line in enumerate(lines) if "def zebra_helper():" in line
            )

            # apple_helper should come before zebra_helper
            assert apple_line < zebra_line

            # Decorated functions should still exist
            assert any("@click.command()" in line for line in lines)
            assert any("def create():" in line for line in lines)
            assert any("def delete():" in line for line in lines)

        finally:
            temp_file.unlink()

    def test_backup_functionality(self) -> None:
        """Test backup file creation."""
        unsorted_code = '''"""Test module."""

def zebra():
    return "zebra"

def apple():
    return "apple"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(unsorted_code)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=True)
            result = sort_python_file(temp_file, config)

            assert result is True

            # Check that backup file was created
            backup_path = temp_file.with_suffix(f"{temp_file.suffix}.bak")
            assert backup_path.exists()

            # Backup should contain original unsorted content
            backup_content = backup_path.read_text()
            assert backup_content == unsorted_code

            # Clean up backup
            backup_path.unlink()

        finally:
            temp_file.unlink()

    def test_error_handling_invalid_syntax(self) -> None:
        """Test error handling with invalid Python syntax."""
        invalid_code = '''"""Test module with invalid syntax."""

def apple():
    return "apple"

def invalid_function(
    # Missing closing parenthesis and colon
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(invalid_code)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            # Should return False due to syntax error
            assert result is False

        finally:
            temp_file.unlink()

    def test_class_methods_detection(self) -> None:
        """Test that class methods are detected for sorting needs."""
        code_with_class = '''"""Test module with class methods."""

class MyClass:
    def zebra_method(self):
        return "zebra"

    def apple_method(self):
        return "apple"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_class)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)

            # Should detect that class methods need sorting
            from pylint_sort_functions.auto_fix import FunctionSorter

            function_sorter = FunctionSorter(config)
            needs_sorting = function_sorter._file_needs_sorting(code_with_class)

            # Class methods need sorting, but implementation is not complete yet
            # The detection should work even if sorting is not implemented
            assert needs_sorting is True

        finally:
            temp_file.unlink()

    def test_file_does_not_need_sorting(self) -> None:
        """Test file that doesn't need sorting returns False."""
        sorted_code = '''"""Already sorted module."""

def apple():
    return "apple"

def banana():
    return "banana"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sorted_code)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            # Should return False because no sorting needed
            assert result is False

        finally:
            temp_file.unlink()

    def test_sort_python_files_function(self) -> None:
        """Test the sort_python_files utility function."""
        from pylint_sort_functions.auto_fix import sort_python_files

        # Create two test files
        unsorted_code1 = """def zebra(): return "zebra"
def apple(): return "apple"
"""

        already_sorted_code = """def apple(): return "apple"
def zebra(): return "zebra"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f1:
            f1.write(unsorted_code1)
            temp_file1 = Path(f1.name)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f2:
            f2.write(already_sorted_code)
            temp_file2 = Path(f2.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            files_processed, files_modified = sort_python_files(
                [temp_file1, temp_file2], config
            )

            # Should process 2 files, modify 1
            assert files_processed == 2
            assert files_modified == 1

        finally:
            temp_file1.unlink()
            temp_file2.unlink()

    def test_function_span_includes_comments_above_function(self) -> None:
        """Test that FunctionSpan includes comments above the function."""
        content = '''"""Test module with comments above functions."""

# This is an important comment about zebra_function
# It explains the complex logic
def zebra_function():
    """Zebra function docstring."""
    return "zebra"

def alpha_function():
    """Alpha function docstring."""
    return "alpha"

# Beta function handles special cases
# It should be used carefully
def beta_function():
    """Beta function docstring."""
    return "beta"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            f.flush()

            config = AutoFixConfig(dry_run=False, backup=False)
            sorter = FunctionSorter(config)

            result = sorter.sort_file(Path(f.name))

            assert result is True  # File was modified

            # Verify comments moved with their respective functions
            sorted_content = Path(f.name).read_text()

            # Check functions and comments are preserved
            assert "def alpha_function():" in sorted_content
            assert "def beta_function():" in sorted_content
            assert "def zebra_function():" in sorted_content
            assert (
                "# This is an important comment about zebra_function" in sorted_content
            )
            assert "# Beta function handles special cases" in sorted_content

            # Verify functions are sorted alphabetically
            func_positions = {
                "alpha": sorted_content.find("def alpha_function():"),
                "beta": sorted_content.find("def beta_function():"),
                "zebra": sorted_content.find("def zebra_function():"),
            }
            assert (
                func_positions["alpha"]
                < func_positions["beta"]
                < func_positions["zebra"]
            )

            # Verify comments appear before their functions
            zebra_comment = "# This is an important comment about zebra_function"
            beta_comment = "# Beta function handles special cases"
            zebra_comment_pos = sorted_content.find(zebra_comment)
            beta_comment_pos = sorted_content.find(beta_comment)
            assert zebra_comment_pos < func_positions["zebra"]
            assert beta_comment_pos < func_positions["beta"]

            os.unlink(f.name)

    def test_empty_file_handling(self) -> None:
        """Test handling of empty files."""
        empty_code = ""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(empty_code)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            # Should return False because no functions to sort
            assert result is False

        finally:
            temp_file.unlink()

    def test_class_method_sorting_basic(self) -> None:
        """Test basic class method sorting functionality."""
        code_with_unsorted_methods = '''"""Test module with unsorted class methods."""

class Calculator:
    """Calculator with unsorted methods."""

    def __init__(self, precision: int = 2) -> None:
        """Initialize calculator."""
        self.precision = precision

    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        return round(a - b, self.precision)

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return round(a + b, self.precision)

    def _validate_input(self, value: float) -> bool:
        """Validate numeric input."""
        return isinstance(value, (int, float))

    def _format_result(self, value: float) -> str:
        """Format calculation result."""
        return f"{value:.{self.precision}f}"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_unsorted_methods)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True

            # Check the sorted content
            sorted_content = temp_file.read_text()
            lines = sorted_content.strip().split("\n")

            # Find method definitions
            method_lines = [
                line.strip() for line in lines if line.strip().startswith("def ")
            ]

            # Should be: __init__, add, subtract, _format_result, _validate_input
            expected_methods = [
                "def __init__(self, precision: int = 2) -> None:",
                "def add(self, a: float, b: float) -> float:",
                "def subtract(self, a: float, b: float) -> float:",
                "def _format_result(self, value: float) -> str:",
                "def _validate_input(self, value: float) -> bool:",
            ]

            assert method_lines == expected_methods

        finally:
            temp_file.unlink()

    def test_class_method_sorting_multiple_classes(self) -> None:
        """Test sorting methods in multiple classes."""
        code_with_multiple_classes = '''"""Test module with multiple classes."""

class SortedClass:
    """Already sorted class."""

    def __init__(self) -> None:
        pass

    def method_a(self) -> str:
        return "a"

    def method_b(self) -> str:
        return "b"

class UnsortedClass:
    """Class with unsorted methods."""

    def __init__(self) -> None:
        pass

    def method_z(self) -> str:
        return "z"

    def method_a(self) -> str:
        return "a"

    def _private_z(self) -> str:
        return "_z"

    def _private_a(self) -> str:
        return "_a"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_multiple_classes)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True

            sorted_content = temp_file.read_text()

            # UnsortedClass should be sorted, SortedClass unchanged
            assert "def method_a(self) -> str:" in sorted_content
            assert "def method_z(self) -> str:" in sorted_content

            # Check that method_a comes before method_z in UnsortedClass
            # Find the UnsortedClass section first
            unsorted_class_start = sorted_content.find("class UnsortedClass:")

            # Find method_a and method_z within UnsortedClass (after its start)
            method_a_pos = sorted_content.find(
                "def method_a(self) -> str:", unsorted_class_start
            )
            method_z_pos = sorted_content.find(
                "def method_z(self) -> str:", unsorted_class_start
            )

            # method_a should come before method_z in UnsortedClass
            assert unsorted_class_start < method_a_pos < method_z_pos

        finally:
            temp_file.unlink()

    def test_class_method_sorting_with_decorators(self) -> None:
        """Test class method sorting with decorated methods."""
        code_with_decorated_methods = '''"""Test module with decorated class methods."""

class APIClass:
    """Class with decorated methods."""

    def __init__(self) -> None:
        pass

    @property
    def zebra_property(self) -> str:
        return "zebra"

    @property
    def apple_property(self) -> str:
        return "apple"

    def zebra_method(self) -> str:
        return "zebra"

    def apple_method(self) -> str:
        return "apple"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_decorated_methods)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True

            sorted_content = temp_file.read_text()

            # Check that methods are sorted alphabetically, including decorated ones
            # Expected: __init__, apple_method, apple_property, zebra_method,
            # zebra_property
            lines = [
                line.strip()
                for line in sorted_content.split("\n")
                if "def " in line and "class" not in line
            ]

            # Extract just the method names for easier assertion
            method_names = []
            for line in lines:
                if "def " in line:
                    method_name = line.split("def ")[1].split("(")[0]
                    method_names.append(method_name)

            expected_order = [
                "__init__",
                "apple_method",
                "apple_property",
                "zebra_method",
                "zebra_property",
            ]
            assert method_names == expected_order

        finally:
            temp_file.unlink()

    def test_class_method_sorting_no_change_when_sorted(self) -> None:
        """Test that already sorted class methods are not modified."""
        # Use the already sorted test file
        sorted_content = Path("tests/files/classes/sorted_methods.py").read_text()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(sorted_content)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            # Should return False because methods are already sorted
            assert result is False

            # Content should remain unchanged
            final_content = temp_file.read_text()
            assert final_content == sorted_content

        finally:
            temp_file.unlink()

    def test_class_method_sorting_with_content_after_methods(self) -> None:
        """Test class method sorting when there's content after the last method."""
        code_with_content_after = '''"""Test module with content after class methods."""

class TestClass:
    """Class with content after methods."""

    def zebra_method(self) -> str:
        """Last method alphabetically."""
        return "zebra"

    def apple_method(self) -> str:
        """First method alphabetically."""
        return "apple"

    # Class constant after methods (non-method content)
    CLASS_CONSTANT = "test"

# Module-level code after class
MODULE_CONSTANT = "module level"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_content_after)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True

            sorted_content = temp_file.read_text()

            # Verify methods are sorted but content after methods is preserved
            assert "def apple_method(self) -> str:" in sorted_content
            assert "def zebra_method(self) -> str:" in sorted_content
            assert 'CLASS_CONSTANT = "test"' in sorted_content
            assert 'MODULE_CONSTANT = "module level"' in sorted_content

            # Check that apple_method comes before zebra_method
            apple_pos = sorted_content.find("def apple_method(self) -> str:")
            zebra_pos = sorted_content.find("def zebra_method(self) -> str:")
            assert apple_pos < zebra_pos

        finally:
            temp_file.unlink()

    def test_section_header_displacement_bug(self) -> None:
        """Test that section header comments stay positioned correctly during sorting.

        This reproduces the bug described in GitHub issue #10 where section headers
        like '# Public functions' get displaced during function reordering.
        """
        code_with_section_headers = """from pathlib import Path

# Public functions

# Bad: Functions out of order
def zebra_function():
    pass

def alpha_function():  # Should come before zebra_function
    pass
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_section_headers)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True  # File should be modified

            sorted_content = temp_file.read_text()

            # Check that section header appears before both functions
            public_header_pos = sorted_content.find("# Public functions")
            alpha_pos = sorted_content.find("def alpha_function():")
            zebra_pos = sorted_content.find("def zebra_function():")

            # Section header should come before both functions
            assert public_header_pos < alpha_pos, (
                f"Section header at {public_header_pos} should come before "
                f"alpha function at {alpha_pos}"
            )
            assert public_header_pos < zebra_pos, (
                f"Section header at {public_header_pos} should come before "
                f"zebra function at {zebra_pos}"
            )

            # Functions should be in alphabetical order
            assert alpha_pos < zebra_pos, (
                f"Alpha function at {alpha_pos} should come before "
                f"zebra function at {zebra_pos}"
            )

        finally:
            temp_file.unlink()

    def test_multiple_section_headers(self) -> None:
        """Test section headers stay positioned and don't move with functions."""
        code_with_multiple_sections = '''"""Module with multiple sections."""

# Public functions

def zebra_public():
    """Public zebra function."""
    return "zebra"

def alpha_public():
    """Public alpha function."""
    return "alpha"

# Private functions

def _zebra_private():
    """Private zebra function."""
    return "_zebra"

def _alpha_private():
    """Private alpha function."""
    return "_alpha"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_multiple_sections)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True  # File should be modified

            sorted_content = temp_file.read_text()

            # Check section headers are preserved and don't get displaced
            public_header_pos = sorted_content.find("# Public functions")
            private_header_pos = sorted_content.find("# Private functions")

            # Both headers should exist
            assert public_header_pos >= 0, "Public functions header should be preserved"
            assert private_header_pos >= 0, (
                "Private functions header should be preserved"
            )

            # Headers should maintain their relative order
            assert public_header_pos < private_header_pos, (
                "Section headers should maintain relative order"
            )

            # Functions should be sorted (public first, then private, both alphabetical)
            alpha_public_pos = sorted_content.find("def alpha_public():")
            zebra_public_pos = sorted_content.find("def zebra_public():")
            alpha_private_pos = sorted_content.find("def _alpha_private():")
            zebra_private_pos = sorted_content.find("def _zebra_private():")

            # All functions should be found
            assert alpha_public_pos >= 0
            assert zebra_public_pos >= 0
            assert alpha_private_pos >= 0
            assert zebra_private_pos >= 0

            # Functions should be in sorted order: public alphabetical, then private
            assert alpha_public_pos < zebra_public_pos, (
                "Public functions should be sorted alphabetically"
            )
            assert alpha_private_pos < zebra_private_pos, (
                "Private functions should be sorted alphabetically"
            )
            assert zebra_public_pos < alpha_private_pos, (
                "All public functions should come before private functions"
            )

        finally:
            temp_file.unlink()

    def test_various_section_header_formats(self) -> None:
        """Test different section header formats are recognized and preserved."""
        code_with_various_headers = '''"""Module with various header formats."""

# Utility functions

def zebra_util():
    return "zebra"

## Helper functions

def alpha_helper():
    return "alpha_help"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_various_headers)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True

            sorted_content = temp_file.read_text()

            # Key test: section headers should not be displaced from original positions
            # Our fix prevents section headers from moving with individual functions
            util_header_pos = sorted_content.find("# Utility functions")
            helper_header_pos = sorted_content.find("## Helper functions")

            # Both headers should still exist in the file
            assert util_header_pos >= 0, "Utility functions header should be preserved"
            assert helper_header_pos >= 0, "Helper functions header should be preserved"

            # The section headers should appear in their original order
            # (this tests that they don't get mixed up during sorting)
            assert util_header_pos < helper_header_pos, (
                "Section headers should maintain relative order"
            )

        finally:
            temp_file.unlink()

    def test_function_comments_vs_section_headers(self) -> None:
        """Test function-specific comments move with functions, headers don't."""
        code_with_mixed_comments = '''"""Module with mixed comment types."""

# Public functions

# This is a specific comment about zebra_function
# It should move with the function
def zebra_function():
    return "zebra"

# This is a specific comment about alpha_function
def alpha_function():
    return "alpha"
'''

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code_with_mixed_comments)
            temp_file = Path(f.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=False)
            result = sort_python_file(temp_file, config)

            assert result is True

            sorted_content = temp_file.read_text()

            # Section header should stay at the top
            public_header_pos = sorted_content.find("# Public functions")
            alpha_pos = sorted_content.find("def alpha_function():")
            zebra_pos = sorted_content.find("def zebra_function():")

            assert public_header_pos < alpha_pos
            assert public_header_pos < zebra_pos
            assert alpha_pos < zebra_pos

            # Function-specific comments should move with their functions
            zebra_comment_pos = sorted_content.find(
                "# This is a specific comment about zebra_function"
            )
            alpha_comment_pos = sorted_content.find(
                "# This is a specific comment about alpha_function"
            )

            # Comments should appear right before their respective functions
            assert zebra_comment_pos < zebra_pos
            assert alpha_comment_pos < alpha_pos

            # Alpha function and its comment should come first
            assert alpha_comment_pos < zebra_comment_pos

        finally:
            temp_file.unlink()

    def test_section_header_detection_patterns(self) -> None:
        """Test various section header patterns are correctly detected."""
        from pylint_sort_functions.auto_fix import AutoFixConfig, FunctionSorter

        config = AutoFixConfig()
        sorter = FunctionSorter(config)

        # Test organizational patterns (covers the missing line in coverage)
        assert sorter._is_section_header_comment("## functions")
        assert sorter._is_section_header_comment("=== methods ===")
        assert sorter._is_section_header_comment("--- helper functions ---")

        # Test keyword patterns
        assert sorter._is_section_header_comment("# Public functions")
        assert sorter._is_section_header_comment("# private methods")
        assert sorter._is_section_header_comment("API functions")

        # Test non-header comments
        assert not sorter._is_section_header_comment(
            "# This is a specific function comment"
        )
        assert not sorter._is_section_header_comment("# TODO: implement this")
        assert not sorter._is_section_header_comment("# Bug fix for issue #123")

    def test_automatic_section_header_insertion_basic(self) -> None:
        """Test automatic section header insertion with mixed visibility functions."""
        content = '''"""Test module with unsorted mixed functions."""

def zebra_function():
    """Public zebra function."""
    return "zebra"

def alpha_function():
    """Public alpha function."""
    return "alpha"

def _zebra_private():
    """Private zebra function."""
    return "_zebra"

def _alpha_private():
    """Private alpha function."""
    return "_alpha"
'''

        # Configure with section headers enabled
        config = AutoFixConfig(
            add_section_headers=True,
            public_header="# Public functions",
            private_header="# Private functions",
        )

        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        expected = '''"""Test module with unsorted mixed functions."""

# Public functions

def alpha_function():
    """Public alpha function."""
    return "alpha"

def zebra_function():
    """Public zebra function."""
    return "zebra"


# Private functions

def _alpha_private():
    """Private alpha function."""
    return "_alpha"
def _zebra_private():
    """Private zebra function."""
    return "_zebra"'''

        assert result.strip() == expected.strip()

    def test_automatic_section_header_insertion_only_public(self) -> None:
        """Test that headers are not added when only public functions exist."""
        content = '''"""Test module with only public functions."""

def zebra_function():
    return "zebra"

def alpha_function():
    return "alpha"
'''

        config = AutoFixConfig(add_section_headers=True)
        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        expected = '''"""Test module with only public functions."""

def alpha_function():
    return "alpha"

def zebra_function():
    return "zebra"
'''

        assert result.strip() == expected.strip()

    def test_automatic_section_header_insertion_only_private(self) -> None:
        """Test that headers are not added when only private functions exist."""
        content = '''"""Test module with only private functions."""

def _zebra_private():
    return "_zebra"

def _alpha_private():
    return "_alpha"
'''

        config = AutoFixConfig(add_section_headers=True)
        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        expected = '''"""Test module with only private functions."""

def _alpha_private():
    return "_alpha"

def _zebra_private():
    return "_zebra"
'''

        assert result.strip() == expected.strip()

    def test_automatic_section_header_insertion_disabled(self) -> None:
        """Test that headers are not added when feature is disabled."""
        content = '''"""Test module with mixed functions."""

def zebra_function():
    return "zebra"

def _alpha_private():
    return "_alpha"
'''

        config = AutoFixConfig(add_section_headers=False)
        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        expected = '''"""Test module with mixed functions."""

def zebra_function():
    return "zebra"

def _alpha_private():
    return "_alpha"
'''

        assert result.strip() == expected.strip()

    def test_automatic_section_header_insertion_methods(self) -> None:
        """Test automatic section header insertion for class methods."""
        content = '''"""Test module with class methods."""

class TestClass:
    def zebra_method(self):
        return "zebra"

    def alpha_method(self):
        return "alpha"

    def _zebra_private(self):
        return "_zebra"

    def _alpha_private(self):
        return "_alpha"
'''

        config = AutoFixConfig(
            add_section_headers=True,
            public_method_header="# Public methods",
            private_method_header="# Private methods",
        )

        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        # Should contain both method headers
        assert "# Public methods" in result
        assert "# Private methods" in result
        # Methods should be sorted within their sections
        assert "def alpha_method(self)" in result
        assert "def zebra_method(self)" in result
        assert "def _alpha_private(self)" in result
        assert "def _zebra_private(self)" in result

    def test_automatic_section_header_custom_headers(self) -> None:
        """Test automatic section header insertion with custom header text."""
        content = '''"""Test module with custom headers."""

def zebra_function():
    return "zebra"

def _alpha_private():
    return "_alpha"
'''

        config = AutoFixConfig(
            add_section_headers=True,
            public_header="## PUBLIC API ##",
            private_header="## INTERNAL HELPERS ##",
        )

        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        assert "## PUBLIC API ##" in result
        assert "## INTERNAL HELPERS ##" in result

    def test_mixed_visibility_functions_detection(self) -> None:
        """Test _has_mixed_visibility_functions helper method."""
        config = AutoFixConfig()
        sorter = FunctionSorter(config)

        # Create mock function spans
        public_span = MagicMock()
        public_span.node.name = "public_func"

        private_span = MagicMock()
        private_span.node.name = "_private_func"

        # Mock the is_private_function utility
        with patch(
            "pylint_sort_functions.utils.is_private_function"
        ) as mock_is_private:

            def side_effect(node: Any) -> bool:
                return node.name.startswith("_")  # type: ignore[no-any-return]

            mock_is_private.side_effect = side_effect

            # Test mixed visibility
            mixed_spans = [public_span, private_span]
            assert sorter._has_mixed_visibility_functions(mixed_spans)  # type: ignore[arg-type]

            # Test only public
            public_only = [public_span]
            assert not sorter._has_mixed_visibility_functions(public_only)  # type: ignore[arg-type]

            # Test only private
            private_only = [private_span]
            assert not sorter._has_mixed_visibility_functions(private_only)  # type: ignore[arg-type]  # pylint: disable=line-too-long

    def test_find_existing_section_headers(self) -> None:
        """Test _find_existing_section_headers helper method."""
        config = AutoFixConfig()
        sorter = FunctionSorter(config)

        lines = [
            "# Module docstring",
            "",
            "# Public functions",
            "def func1():",
            "    pass",
            "",
            "# Private functions",
            "def _func2():",
            "    pass",
        ]

        headers = sorter._find_existing_section_headers(lines)

        expected = {"public_functions": 2, "private_functions": 6}

        assert headers == expected

    def test_find_existing_section_headers_with_methods(self) -> None:
        """Test _find_existing_section_headers with method headers."""
        config = AutoFixConfig()
        sorter = FunctionSorter(config)

        lines = [
            "class TestClass:",
            "    # Public methods",
            "    def method1(self):",
            "        pass",
            "",
            "    # Private methods",
            "    def _method2(self):",
            "        pass",
        ]

        headers = sorter._find_existing_section_headers(lines)

        expected = {"public_methods": 1, "private_methods": 5}

        assert headers == expected

    def test_spacing_logic_for_functions_without_trailing_newlines(self) -> None:
        """Test that proper spacing is added for functions without trailing newlines."""
        config = AutoFixConfig(add_section_headers=False)
        sorter = FunctionSorter(config)

        # Create mock function spans - test both cases:
        # 1. Function with no newline at all
        # 2. Function with single newline (not double)
        span1 = MagicMock()
        span1.text = "def func1():\n    pass"  # No trailing newline at all
        span1.node.name = "func1"

        span2 = MagicMock()
        span2.text = "def func2():\n    pass\n"  # Only one trailing newline
        span2.node.name = "func2"

        span3 = MagicMock()
        span3.text = "def func3():\n    pass\n\n"  # Already has proper spacing
        span3.node.name = "func3"

        spans = [span1, span2, span3]

        # Mock is_private_function to return False for all (public functions only)
        with patch(
            "pylint_sort_functions.utils.is_private_function", return_value=False
        ):
            result = sorter._add_section_headers_to_functions(spans, is_methods=False)  # type: ignore[arg-type]  # pylint: disable=line-too-long

        # Should have proper spacing added:
        # - span1 needs both newline + extra newline (line 468 + 469)
        # - span2 needs only extra newline (line 469 only)
        # - span3 doesn't need anything (already has double newline)
        expected = [
            "def func1():\n    pass",  # span1.text
            "\n",  # Added by line 468 (no newline at end)
            "\n",  # Added by line 469 (spacing)
            "def func2():\n    pass\n",  # span2.text
            "\n",  # Added by line 469 (spacing)
            "def func3():\n    pass\n\n",  # span3.text (no additions needed)
        ]
        assert result == expected

    def test_file_needs_sorting_section_headers_only(self) -> None:
        """Test _file_needs_sorting detects when only section headers are needed."""
        # Test module functions that are sorted but need headers
        module_content = """def alpha_function():
    return "alpha"

def _zebra_private():
    return "_zebra"
"""
        config = AutoFixConfig(add_section_headers=True)
        sorter = FunctionSorter(config)

        # Functions are already sorted, but should need processing for headers
        assert sorter._file_needs_sorting(module_content)

        # Test class methods that are sorted but need headers
        class_content = """class TestClass:
    def __init__(self):
        pass

    def alpha_method(self):
        return "alpha"

    def _zebra_private(self):
        return "_zebra"
"""
        assert sorter._file_needs_sorting(class_content)

        # Test that without section headers, content doesn't need processing
        config_no_headers = AutoFixConfig(add_section_headers=False)
        sorter_no_headers = FunctionSorter(config_no_headers)
        assert not sorter_no_headers._file_needs_sorting(module_content)
        assert not sorter_no_headers._file_needs_sorting(class_content)

    def test_configurable_section_header_detection(self) -> None:
        """Test configurable section header detection patterns."""
        # Test custom header detection
        config = AutoFixConfig(
            public_header="=== PUBLIC API ===",
            private_header="=== INTERNAL ===",
            additional_section_patterns=["--- Custom Pattern ---", "## Special ##"],
        )
        sorter = FunctionSorter(config)

        # Should detect configured headers
        assert sorter._is_section_header_comment("=== PUBLIC API ===")
        assert sorter._is_section_header_comment("=== INTERNAL ===")

        # Should detect additional patterns
        assert sorter._is_section_header_comment("--- Custom Pattern ---")
        assert sorter._is_section_header_comment("## Special ##")

        # Should still detect default patterns for backward compatibility
        assert sorter._is_section_header_comment("# Public functions")
        assert sorter._is_section_header_comment("# Private methods")

        # Case insensitive by default
        assert sorter._is_section_header_comment("=== public api ===")
        assert sorter._is_section_header_comment("--- CUSTOM PATTERN ---")

    def test_case_sensitive_section_header_detection(self) -> None:
        """Test case-sensitive section header detection."""
        config = AutoFixConfig(
            public_header="Public API",
            section_header_case_sensitive=True,
            additional_section_patterns=["Custom Pattern"],
        )
        sorter = FunctionSorter(config)

        # Should detect exact case matches
        assert sorter._is_section_header_comment("Public API")
        assert sorter._is_section_header_comment("Custom Pattern")

        # Should NOT detect different case
        assert not sorter._is_section_header_comment("public api")
        assert not sorter._is_section_header_comment("CUSTOM PATTERN")

        # Default patterns should still work with exact case
        assert sorter._is_section_header_comment("public functions")
        assert not sorter._is_section_header_comment("PUBLIC FUNCTIONS")

    def test_custom_headers_prevent_duplication(self) -> None:
        """Test that custom headers are detected to prevent duplication."""
        content = """=== PUBLIC API ===

def alpha_function():
    return "alpha"

=== INTERNAL ===

def _zebra_private():
    return "_zebra"
"""

        config = AutoFixConfig(
            add_section_headers=True,
            public_header="=== PUBLIC API ===",
            private_header="=== INTERNAL ===",
        )
        sorter = FunctionSorter(config)

        # The file already has the custom headers, so it shouldn't need modification
        # for header insertion (though it might still need processing for other reasons)
        result = sorter._sort_functions_in_content(content)

        # Should not have duplicate headers
        assert result.count("=== PUBLIC API ===") == 1
        assert result.count("=== INTERNAL ===") == 1

    def test_preserve_main_block_at_end(self) -> None:
        """Test that if __name__ == __main__ blocks are preserved at the end."""
        content = '''"""Test module."""

def zebra_function():
    """Last function alphabetically."""
    return "zebra"

def alpha_function():
    """First function alphabetically."""
    return "alpha"

if __name__ == "__main__":
    print("This should stay at the end!")
    alpha_function()
    zebra_function()
'''

        config = AutoFixConfig(add_section_headers=False)
        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        # Verify functions are sorted but main block stays at end
        expected_lines = [
            '"""Test module."""',
            "",
            "def alpha_function():",
            '    """First function alphabetically."""',
            '    return "alpha"',
            "",
            "def zebra_function():",
            '    """Last function alphabetically."""',
            '    return "zebra"',
            "",
            'if __name__ == "__main__":',
            '    print("This should stay at the end!")',
            "    alpha_function()",
            "    zebra_function()",
        ]

        result_lines = result.strip().split("\n")
        for i, expected in enumerate(expected_lines):
            assert result_lines[i] == expected, (
                f"Line {i}: expected '{expected}', got '{result_lines[i]}'"
            )

    def test_ast_based_boundary_detection_various_patterns(self) -> None:
        """Test AST-based boundary detection handles various __name__ patterns."""
        content = '''"""Test module with various patterns."""

def zebra_function():
    return "zebra"

def alpha_function():
    return "alpha"

# Module constants
VERSION = "1.0"
DEBUG = True

# Single quotes pattern
if __name__ == '__main__':
    print(f"Version {VERSION}")
    if DEBUG:
        alpha_function()
'''

        config = AutoFixConfig(add_section_headers=False)
        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        # Verify the AST-based approach correctly handles:
        # 1. Functions sorted alphabetically
        # 2. Module constants preserved in their original positions
        # 3. Single-quote __name__ pattern detected without hardcoding
        # 4. Comments between functions are correctly associated
        expected_lines = [
            '"""Test module with various patterns."""',
            "",
            "def alpha_function():",
            '    return "alpha"',
            "",
            "# Module constants",
            "",
            "def zebra_function():",
            '    return "zebra"',
            "",
            'VERSION = "1.0"',
            "DEBUG = True",
            "",
            "# Single quotes pattern",
            "if __name__ == '__main__':",
            '    print(f"Version {VERSION}")',
            "    if DEBUG:",
            "        alpha_function()",
        ]

        result_lines = result.strip().split("\n")
        for i, expected in enumerate(expected_lines):
            assert result_lines[i] == expected, (
                f"Line {i}: expected '{expected}', got '{result_lines[i]}'"
            )

    def test_ast_boundary_detection_end_of_file(self) -> None:
        """Test AST boundary detection with functions at end of file."""
        content = '''"""Test end-of-file boundary detection."""

def zebra_function():
    return "zebra"

def alpha_function():
    return "alpha"

# Trailing comment
'''

        config = AutoFixConfig(add_section_headers=False)
        sorter = FunctionSorter(config)
        result = sorter._sort_functions_in_content(content)

        # Verify functions are sorted and trailing content is correctly associated
        # The comment after alpha_function moves with it during sorting
        expected_lines = [
            '"""Test end-of-file boundary detection."""',
            "",
            "def alpha_function():",
            '    return "alpha"',
            "",
            "# Trailing comment",
            "",
            "def zebra_function():",
            '    return "zebra"',
        ]

        result_lines = result.strip().split("\n")
        for i, expected in enumerate(expected_lines):
            assert result_lines[i] == expected, (
                f"Line {i}: expected '{expected}', got '{result_lines[i]}'"
            )
