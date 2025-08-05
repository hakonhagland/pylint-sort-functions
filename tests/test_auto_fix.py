"""Tests for auto-fix functionality."""

import os
import tempfile
from pathlib import Path

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
