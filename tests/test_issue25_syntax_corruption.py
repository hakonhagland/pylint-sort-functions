"""Test case for GitHub issue #25: Auto-sort creates syntax errors on complex classes.

This test demonstrates the critical bug where auto-sort corrupts complex Python files
with multiple class definitions, causing syntax errors and making files unexecutable.

The test focuses on the specific corruption patterns reported in the issue:
1. Lost class definitions (methods orphaned from their classes)
2. Orphaned closing syntax (parentheses, brackets without opening context)
3. Duplicate method definitions across different classes

GitHub Issue: https://github.com/hakonhagland/pylint-sort-functions/issues/25
"""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from pylint_sort_functions.auto_fix import AutoFixConfig, FunctionSorter


class TestIssue25SyntaxCorruption:
    """Test cases for issue #25 - auto-sort syntax corruption on complex classes."""

    # Public methods

    def test_class_with_complex_multiline_methods_preserves_syntax(self) -> None:
        """Test that complex multi-line methods are handled correctly by auto-sort.

        This test validates that the fix properly handles complex multi-line method
        signatures without creating syntax errors.
        """
        original_content = self._create_multiline_method_content()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(original_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=True)
            sorter = FunctionSorter(config)
            was_modified = sorter.sort_file(temp_path)

            result_content = temp_path.read_text()

            # CRITICAL: Validate syntax is preserved
            try:
                compile(result_content, str(temp_path), "exec")
            except SyntaxError as e:
                pytest.fail(
                    f"Auto-sort created syntax error: {e}\nResult:\n{result_content}"
                )

            # Validate method sorting and structure
            self._validate_simple_method_sorting(result_content, was_modified)

            # Ensure class structure is preserved
            assert "class TestClass:" in result_content
            assert "def another_method(self):" in result_content
            assert "def method_with_complex_args(" in result_content

        finally:
            temp_path.unlink()
            backup_path = temp_path.with_suffix(f"{temp_path.suffix}.bak")
            if backup_path.exists():
                backup_path.unlink()

    def test_complex_class_auto_sort_preserves_syntax(self) -> None:
        """Test that auto-sort preserves syntax on complex class hierarchies.

        This is the main reproduction case from issue #25. The test creates a
        Python file with multiple dialog classes (similar to PyQt applications)
        that have:
        - Complex inheritance (QDialog, QWidget)
        - super() calls that require proper class context
        - Methods with identical names across different classes
        - Mixed public/private method visibility

        Expected: Methods sorted within each class, classes preserved
        Actual (bug): Class definitions lost, methods orphaned, syntax errors
        """
        # Create test file content that triggers the corruption
        original_content = self._create_complex_test_content()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(original_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            # Create auto-fix configuration
            config = AutoFixConfig(
                dry_run=False,
                backup=True,
            )

            # Apply auto-sort
            sorter = FunctionSorter(config)
            was_modified = sorter.sort_file(temp_path)

            # Read the result
            result_content = temp_path.read_text()

            # Critical validation: The file must compile without syntax errors
            try:
                compile(result_content, str(temp_path), "exec")
            except SyntaxError as e:
                pytest.fail(
                    f"Auto-sort created syntax error: {e}\n"
                    f"Line {e.lineno}: {e.text}\n"
                    f"Result content:\n{result_content}"
                )

            # Validate that class structure is preserved
            self._validate_class_structure_preservation(result_content)

            # Validate method sorting within classes
            self._validate_method_sorting_within_classes(result_content, was_modified)

        finally:
            # Cleanup
            temp_path.unlink()
            backup_path = temp_path.with_suffix(f"{temp_path.suffix}.bak")
            if backup_path.exists():
                backup_path.unlink()

    def test_dry_run_with_validation_coverage(self) -> None:
        """Test coverage for dry-run mode after validation.

        This test ensures we cover the case where validation passes but
        we're in dry-run mode.
        """
        original_content = dedent("""
            class TestClass:
                def method_b(self):
                    pass

                def method_a(self):
                    pass
            """).strip()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(original_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            # Test dry-run mode
            config = AutoFixConfig(dry_run=True, backup=True)
            sorter = FunctionSorter(config)

            # This should return True for would-modify but not actually modify
            was_modified = sorter.sort_file(temp_path)

            # Should return True because it would modify in non-dry-run
            assert was_modified

            # File should be unchanged (dry run)
            result_content = temp_path.read_text()
            assert result_content == original_content

        finally:
            temp_path.unlink()
            backup_path = temp_path.with_suffix(f"{temp_path.suffix}.bak")
            if backup_path.exists():
                backup_path.unlink()

    def test_preserves_complex_inheritance_with_super_calls(self) -> None:
        """Test that super() calls remain properly associated with their classes.

        This test specifically validates the corruption where super() calls become
        orphaned from their class context, causing NameError at runtime.
        """
        original_content = dedent("""
            class BaseDialog:
                def __init__(self, title="Dialog"):
                    self.title = title

                def show(self):
                    print(f"Showing {self.title}")


            class CustomDialog(BaseDialog):
                def __init__(self, title="Custom"):
                    super().__init__(title)  # CRITICAL: Must stay in class context
                    self.custom_data = None

                def setup_data(self):
                    '''Setup custom data.'''
                    self.custom_data = "initialized"

                def accept(self):
                    '''Accept the dialog.'''
                    super().show()  # CRITICAL: Must stay in class context

                def _validate_data(self):
                    '''Private validation.'''
                    return self.custom_data is not None
            """).strip()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(original_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            config = AutoFixConfig(dry_run=False, backup=True)
            sorter = FunctionSorter(config)
            sorter.sort_file(temp_path)

            result_content = temp_path.read_text()

            # Critical validation: File must compile
            try:
                compile(result_content, str(temp_path), "exec")
            except SyntaxError as e:
                pytest.fail(
                    f"Auto-sort created syntax error: {e}\nResult:\n{result_content}"
                )

            # Additional validation: super() calls must have valid class context
            # This is more complex to test statically, but we can check basic structure
            lines = result_content.splitlines()

            # Find all super() calls and verify they're properly indented
            # (in class methods)
            super_calls = [
                (i, line) for i, line in enumerate(lines) if "super()" in line
            ]

            for line_num, line_content in super_calls:
                # super() calls should be indented (inside methods, which are
                # inside classes)
                assert line_content.startswith("        "), (
                    f"super() call at line {line_num + 1} is not properly "
                    f"indented: {line_content}\n"
                    f"This suggests it's orphaned from its class/method context."
                )

                # Look backwards to ensure there's a method definition above
                found_method = False
                for i in range(line_num - 1, -1, -1):
                    if lines[i].strip().startswith("def ") and lines[i].startswith(
                        "    "
                    ):
                        found_method = True
                        break
                    if lines[i].strip().startswith("class ") or (
                        lines[i].strip().startswith("def ")
                        and not lines[i].startswith("    ")
                    ):
                        break

                assert found_method, (
                    f"super() call at line {line_num + 1} has no method "
                    f"context: {line_content.strip()}"
                )

        finally:
            temp_path.unlink()
            backup_path = temp_path.with_suffix(f"{temp_path.suffix}.bak")
            if backup_path.exists():
                backup_path.unlink()

    def test_syntax_validation_prevents_corruption(self) -> None:
        """Test that the fix includes proper syntax validation to prevent corruption.

        This test validates that the suggested fix from issue #25 is implemented:
        adding syntax validation after transformation with rollback capability.
        """
        # This is a placeholder for the eventual fix validation
        # When the bug is fixed, this test should pass

        # Create content that would trigger the original bug
        problematic_content = dedent("""
            class DialogA:
                def z_method(self):
                    super().__init__()
                    pass

                def a_method(self):
                    pass

            class DialogB:
                def z_method(self):  # Same name as DialogA
                    pass

                def a_method(self):  # Same name as DialogA
                    pass
            """).strip()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(problematic_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            # Store original content for comparison
            original_content = temp_path.read_text()

            config = AutoFixConfig(dry_run=False, backup=True)
            sorter = FunctionSorter(config)

            # Apply auto-sort
            was_modified = sorter.sort_file(temp_path)

            # Read result
            result_content = temp_path.read_text()

            # CRITICAL: Result must have valid syntax
            try:
                compile(result_content, str(temp_path), "exec")
            except SyntaxError as e:
                # This is the bug we're testing for
                pytest.fail(
                    f"ISSUE #25 REPRODUCED: Auto-sort created syntax error!\n"
                    f"Error: {e}\n"
                    f"Line {e.lineno}: {e.text}\n"
                    f"Original content:\n{original_content}\n"
                    f"Corrupted result:\n{result_content}\n"
                    f"\nThis confirms the critical bug reported in issue #25."
                )

            # If we reach here, the auto-sort preserved syntax (bug is fixed)
            if was_modified:
                # Additional validation that the transformation was meaningful
                assert "class DialogA:" in result_content
                assert "class DialogB:" in result_content
                assert result_content != original_content  # Should be sorted

        finally:
            temp_path.unlink()
            backup_path = temp_path.with_suffix(f"{temp_path.suffix}.bak")
            if backup_path.exists():
                backup_path.unlink()

    def test_syntax_validation_rollback_coverage(self) -> None:
        """Test coverage for syntax validation rollback scenario.

        This test specifically creates a scenario where the transformation
        would create invalid syntax to ensure our rollback logic is properly
        tested for coverage.
        """
        # Create a file that will pass initial validation but would fail
        # if we artificially corrupt it during transformation
        original_content = dedent("""
            class TestClass:
                def method_b(self):
                    pass

                def method_a(self):
                    pass
            """).strip()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write(original_content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            # Create a custom sorter that will intentionally create bad syntax
            # to test our validation logic
            from unittest.mock import patch

            config = AutoFixConfig(dry_run=False, backup=True)
            sorter = FunctionSorter(config)

            # Mock the _sort_functions_in_content method to return invalid syntax
            with patch.object(sorter, "_sort_functions_in_content") as mock_sort:
                mock_sort.return_value = "invalid python syntax {{{ "

                # This should trigger rollback due to syntax validation
                was_modified = sorter.sort_file(temp_path)

                # Should return False because validation rolled back
                assert not was_modified

                # File should be unchanged (rolled back to original)
                result_content = temp_path.read_text()
                assert result_content == original_content

            # NOTE: Line 919 in auto_fix.py (SyntaxError with lineno but no text) is
            # extremely rare in practice - Python's compile() almost always provides
            # error text. The test above covers the main syntax validation path.

        finally:
            temp_path.unlink()
            backup_path = temp_path.with_suffix(f"{temp_path.suffix}.bak")
            if backup_path.exists():
                backup_path.unlink()

    # Private methods

    def _create_complex_test_content(self) -> str:
        """Create test file content that triggers the corruption.

        Returns complex multi-class content similar to PyQt applications.
        """
        return dedent("""
            '''Complex file with multiple dialog classes that triggers corruption.'''

            from typing import Optional


            class SimpleClass:
                '''Simple class that should work fine.'''

                def method_b(self):
                    '''Second method.'''
                    pass

                def method_a(self):
                    '''First method.'''
                    pass


            class LicenseSelectionDialog:
                '''Dialog class with complex inheritance pattern.'''

                def __init__(self, task, parent: Optional = None):
                    '''Initialize dialog.'''
                    super().__init__(parent)  # This line breaks when class is lost
                    self.task = task
                    self.result_value = None

                def setup_ui(self):
                    '''Setup the user interface.'''
                    pass

                def accept(self):
                    '''Accept dialog.'''
                    self.result_value = "accepted"

                def get_result(self) -> Optional[str]:
                    '''Get the dialog result.'''
                    return self.result_value

                def _validate_input(self):
                    '''Private validation method.'''
                    return True


            class AnotherDialog:
                '''Another dialog class with same method names.'''

                def __init__(self, parent=None):
                    '''Initialize dialog.'''
                    super().__init__(parent)  # This also breaks
                    self.result_value = None

                def get_result(self) -> Optional[str]:
                    '''Get result - same name as above class method.'''
                    return self.result_value

                def setup_ui(self):
                    '''Setup UI - same name as above class method.'''
                    pass

                def _helper_method(self):
                    '''Private helper method.'''
                    pass
            """).strip()

    def _validate_class_structure_preservation(self, result_content: str) -> None:
        """Validate that class structure is preserved after auto-sort.

        Checks that all class definitions exist and methods are properly indented.
        """
        lines = result_content.splitlines()

        # Ensure all class definitions are preserved
        class_definitions = [
            line for line in lines if line.strip().startswith("class ")
        ]
        assert len(class_definitions) == 3, (
            f"Expected 3 class definitions, found {len(class_definitions)}. "
            f"Classes found: {class_definitions}"
        )

        # Ensure no orphaned super() calls (they must be inside a class context)
        super_calls = [line for line in lines if "super()" in line]
        for line_content in super_calls:
            # Find the line number
            line_index = lines.index(line_content)

            # Look backwards to find the class definition this belongs to
            found_class = False
            for i in range(line_index - 1, -1, -1):
                if lines[i].strip().startswith("class "):
                    found_class = True
                    break
                if lines[i].strip().startswith("def ") and not lines[i].startswith(
                    "    "
                ):
                    # Found a module-level function before a class
                    # super() is orphaned
                    break

            assert found_class, (
                f"Found orphaned super() call at line {line_index + 1}: "
                f"{line_content.strip()}\n"
                f"This indicates class definition was lost during auto-sort."
            )

        # Ensure methods are properly indented (inside classes)
        method_definitions = [line for line in lines if line.strip().startswith("def ")]
        for method_line in method_definitions:
            assert method_line.startswith("    "), (
                f"Found method definition not properly indented: "
                f"{method_line.strip()}\n"
                f"This indicates method was orphaned from its class."
            )

    def _validate_method_sorting_within_classes(
        self, result_content: str, was_modified: bool
    ) -> None:
        """Validate that methods are properly sorted within each class.

        Only validates sorting if the file was actually modified.
        """
        if not was_modified:
            return

        lines = result_content.splitlines()

        # Check for duplicate method definitions that shouldn't exist
        # Count occurrences of each method name
        method_names = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def "):
                # Extract method name
                method_name = stripped.split("(")[0].replace("def ", "").strip()
                method_names.append(method_name)

        # Methods like get_result appear in multiple classes - this is expected
        # and OK
        # But duplicate definitions in the same context would be a corruption

        # The key validation: if sorting was applied, methods within each
        # class should be sorted
        # Find each class and check if its methods are sorted
        current_class_methods: list[str] = []
        current_class = None

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class "):
                # Process previous class if any
                if current_class and current_class_methods:
                    # Check if methods are sorted (public first, then
                    # private, each alphabetically)
                    public_methods = [
                        m for m in current_class_methods if not m.startswith("_")
                    ]
                    private_methods = [
                        m for m in current_class_methods if m.startswith("_")
                    ]

                    # Public methods should be alphabetically sorted
                    assert public_methods == sorted(public_methods), (
                        f"Public methods in class {current_class} are not "
                        f"sorted: {public_methods}"
                    )

                    # Private methods should be alphabetically sorted
                    assert private_methods == sorted(private_methods), (
                        f"Private methods in class {current_class} are not "
                        f"sorted: {private_methods}"
                    )

                # Start new class
                current_class = stripped
                current_class_methods = []

            elif stripped.startswith("def ") and current_class:
                # Extract method name
                method_name = stripped.split("(")[0].replace("def ", "").strip()
                current_class_methods.append(method_name)

        # Process the last class
        if current_class and current_class_methods:
            public_methods = [m for m in current_class_methods if not m.startswith("_")]
            private_methods = [m for m in current_class_methods if m.startswith("_")]

            assert public_methods == sorted(public_methods), (
                f"Public methods in class {current_class} are not "
                f"sorted: {public_methods}"
            )
            assert private_methods == sorted(private_methods), (
                f"Private methods in class {current_class} are not "
                f"sorted: {private_methods}"
            )

    def _create_multiline_method_content(self) -> str:
        """Create test content with complex multi-line method signatures."""
        return dedent("""
            class TestClass:
                def method_with_complex_args(
                    self,
                    arg1: str,
                    arg2: int = 10,
                    arg3: Optional[dict] = None
                ):
                    '''Method with complex argument structure.'''
                    result = some_function(
                        arg1,
                        arg2
                    )
                    return result

                def another_method(self):
                    '''Simple method.'''
                    pass
            """).strip()

    def _validate_simple_method_sorting(
        self, result_content: str, was_modified: bool
    ) -> None:
        """Validate method sorting for simple test case."""
        if not was_modified:
            return

        lines = result_content.splitlines()

        # Find method definitions and ensure they're properly within the class
        method_lines = []
        in_class = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("class "):
                in_class = True
            elif stripped.startswith("def ") and in_class:
                # Method should be indented (inside class)
                assert line.startswith("    "), f"Method not properly indented: {line}"
                method_name = stripped.split("(")[0].replace("def ", "")
                method_lines.append(method_name)

        # Methods should be sorted: another_method before
        # method_with_complex_args
        expected_order = ["another_method", "method_with_complex_args"]
        assert method_lines == expected_order, (
            f"Methods not properly sorted. Expected {expected_order}, "
            f"got {method_lines}"
        )
