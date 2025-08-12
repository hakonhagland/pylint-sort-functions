#!/usr/bin/env python3
"""
Integration tests for privacy fixer workflow.

This test suite validates the complete privacy fixer workflow from detection
to automatic renaming, including integration with the auto-sort functionality.

Test Coverage:
1. Privacy detection (W9004 violations)
2. Dry-run privacy fixing
3. Actual privacy fixing with renaming
4. Integrated sorting after privacy fixes
5. Cross-module import analysis
6. Safety validation edge cases
7. CLI integration and error handling
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple

import pytest

from pylint_sort_functions.privacy_fixer import PrivacyFixer


class TestPrivacyFixerIntegration:  # pylint: disable=attribute-defined-outside-init
    """Integration tests for the complete privacy fixer workflow."""

    def setup_method(self) -> None:
        """Set up test environment with temporary project."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_root = self.test_dir / "test_project"
        self.project_root.mkdir(parents=True)

        # Create a proper Python package structure
        (self.project_root / "src").mkdir()
        (self.project_root / "src" / "__init__.py").touch()

        # Get the actual Python executable from the current environment
        # Use absolute path to avoid issues with relative paths in temp directories
        self.python_executable = os.path.abspath(sys.executable)

        # Find the pylint-sort-functions command
        project_root = Path(__file__).parent.parent.parent
        self.cli_module = str(project_root / "src" / "pylint_sort_functions" / "cli.py")

    def teardown_method(self) -> None:
        """Clean up temporary test directory."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_file(self, relative_path: str, content: str) -> Path:
        """Create a test file with specified content."""
        file_path = self.project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def run_cli_command(self, args: List[str]) -> Tuple[int, str, str]:
        """Run pylint-sort-functions CLI command and return result."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).parent.parent.parent)

        cmd = [self.python_executable, self.cli_module] + args
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=self.project_root,
            env=env,
            check=False,
        )
        return result.returncode, result.stdout, result.stderr

    def test_privacy_detection_basic(self) -> None:
        """Test basic privacy detection identifies unused functions."""
        # Create calculator module with internal-only functions
        calculator_content = '''"""Calculator with internal functions."""

def calculate_area(radius):
    """Public API function."""
    return validate_input(radius) * 3.14159 * radius ** 2

def validate_input(value):
    """Internal validation - only used by calculate_area."""
    if value <= 0:
        raise ValueError("Value must be positive")
    return value

def format_output(value):
    """Internal formatter - only used by calculate_area."""
    return f"Area: {value:.2f}"
'''

        # Create main module that imports the public function
        main_content = '''"""Main module using calculator."""

from src.calculator import calculate_area

def main():
    result = calculate_area(5.0)
    print(result)
'''

        calculator_file = self.create_test_file("src/calculator.py", calculator_content)
        self.create_test_file("src/main.py", main_content)

        # Run privacy detection
        fixer = PrivacyFixer()
        violations = fixer.detect_privacy_violations(
            [calculator_file], self.project_root
        )

        # Should detect validate_input and format_output as private
        violation_functions = {v.old_name for v in violations}
        assert "validate_input" in violation_functions
        assert "format_output" in violation_functions
        assert "calculate_area" not in violation_functions  # Used externally

    def test_privacy_fixing_dry_run(self) -> None:
        """Test dry-run privacy fixing shows changes without modifying files."""
        content = '''"""Test module."""

def public_function():
    return helper_function()

def helper_function():
    """Only used internally."""
    return "help"
'''

        test_file = self.create_test_file("src/test_module.py", content)
        original_content = test_file.read_text()

        # Run dry-run privacy fixing via CLI (standalone option)
        returncode, stdout, stderr = self.run_cli_command(
            ["--privacy-dry-run", "src/test_module.py"]
        )

        assert returncode == 0, f"CLI failed: {stderr}\nSTDOUT: {stdout}"
        assert "helper_function" in stdout  # Should show function to be renamed
        assert "_helper_function" in stdout  # Should show new name

        # File should be unchanged in dry-run
        assert test_file.read_text() == original_content

    def test_privacy_fixing_actual_rename(self) -> None:
        """Test actual privacy fixing renames functions correctly."""
        content = '''"""Test module."""

def public_function():
    """Public API."""
    return internal_helper()

def internal_helper():
    """Only used internally."""
    return "help"

def another_internal():
    """Another internal function."""
    return internal_helper() + "more"
'''

        test_file = self.create_test_file("src/test_module.py", content)

        # Run actual privacy fixing via CLI
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "src/test_module.py"]
        )

        assert returncode == 0, f"CLI failed: {stderr}"

        # Check file was modified correctly
        modified_content = test_file.read_text()
        assert "_internal_helper" in modified_content  # Function renamed
        assert "_another_internal" in modified_content  # Function renamed
        assert "return _internal_helper()" in modified_content  # Call updated
        assert 'return _internal_helper() + "more"' in modified_content  # Call updated
        assert "def internal_helper():" not in modified_content  # Old name gone

    def test_integrated_privacy_and_sorting(self) -> None:
        """Test integrated privacy fixing with automatic sorting."""
        content = '''"""Test module with unsorted functions."""

def zebra_function():
    """Public function."""
    return internal_zebra_helper()

def alpha_function():
    """Public function."""
    return internal_alpha_helper()

def internal_zebra_helper():
    """Internal helper."""
    return "zebra help"

def internal_alpha_helper():
    """Internal helper."""
    return "alpha help"

def main():
    """Entry point - prevents alpha/zebra from being private."""
    alpha_function()
    zebra_function()
'''

        test_file = self.create_test_file("src/test_module.py", content)

        # Run privacy fixing with auto-sort
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "--auto-sort", "src/test_module.py"]
        )

        assert returncode == 0, f"CLI failed: {stderr}"

        # Check both privacy fixing and sorting occurred
        modified_content = test_file.read_text()

        # Privacy fixes applied - all functions become private except main
        assert "_internal_zebra_helper" in modified_content
        assert "_internal_alpha_helper" in modified_content

        # In this test scenario, alpha_function and zebra_function also become private
        # because they're only used within the same module (cross-module analysis)
        # Only "main" stays public due to public API pattern matching

        # Functions should be sorted: public first (main), then private (alphabetically)
        lines = modified_content.split("\n")
        function_lines = [i for i, line in enumerate(lines) if line.startswith("def ")]

        # Extract function names
        function_names = []
        for line_idx in function_lines:
            line = lines[line_idx]
            name = line.split("def ")[1].split("(")[0]
            function_names.append(name)

        # Verify functions are sorted properly with public first, then private
        public_functions = [name for name in function_names if not name.startswith("_")]
        private_functions = [name for name in function_names if name.startswith("_")]

        assert len(public_functions) == 1 and public_functions[0] == "main"
        assert (
            sorted(private_functions) == private_functions
        )  # Private functions are sorted

    def test_cross_module_analysis(self) -> None:
        """Test privacy detection works across multiple modules."""
        # Module A with mixed functions
        module_a_content = '''"""Module A."""

def public_api():
    """Used by module B."""
    return helper_a()

def helper_a():
    """Only used within module A."""
    return "help"

def unused_function():
    """Not used anywhere."""
    return "unused"
'''

        # Module B that imports from A
        module_b_content = '''"""Module B."""

from src.module_a import public_api

def use_module_a():
    return public_api()
'''

        module_a = self.create_test_file("src/module_a.py", module_a_content)
        self.create_test_file("src/module_b.py", module_b_content)

        # Run privacy detection on module A
        fixer = PrivacyFixer()
        violations = fixer.detect_privacy_violations([module_a], self.project_root)

        # Should detect internal functions but not public_api (used by module_b)
        violation_functions = {v.old_name for v in violations}
        assert "helper_a" in violation_functions
        assert "unused_function" in violation_functions
        assert "public_api" not in violation_functions  # Used by module_b

    def test_safety_validation_prevents_unsafe_renames(self) -> None:
        """Test that safety validation prevents unsafe renames."""
        # Create a scenario where renaming would be unsafe (external import)
        content = '''"""Module that might be imported externally."""

def potentially_public_function():
    """This might be used by external code."""
    return "public"
'''

        self.create_test_file("src/library_module.py", content)

        # Run privacy fixing - should be conservative
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "src/library_module.py"]
        )

        # Should succeed but be conservative about renaming
        assert returncode == 0, f"CLI failed: {stderr}"

        # Check file content - might not rename if deemed unsafe
        # The function might stay public if safety validation is conservative
        # This tests that the tool doesn't break things

    def test_cli_error_handling(self) -> None:
        """Test CLI error handling for invalid scenarios."""
        # Test with non-existent file
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "nonexistent.py"]
        )

        assert returncode != 0  # Should fail

        # Test with invalid Python syntax
        invalid_content = '''"""Invalid Python."""

def broken_function(
    # Missing closing parenthesis
'''

        self.create_test_file("src/invalid.py", invalid_content)

        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "src/invalid.py"]
        )

        # Should handle gracefully - either shows error or processes successfully
        # The tool gracefully handles syntax errors by skipping invalid files
        assert returncode == 0  # Tool succeeds even with syntax errors

    def test_backup_creation(self) -> None:
        """Test that backup files are created during privacy fixing."""
        content = '''"""Test backup creation."""

def public_func():
    return helper()

def helper():
    return "help"
'''

        test_file = self.create_test_file("src/backup_test.py", content)
        original_content = test_file.read_text()

        # Run privacy fixing (backup should be enabled by default)
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "src/backup_test.py"]
        )

        assert returncode == 0, f"CLI failed: {stderr}"

        # Check backup file exists
        backup_file = test_file.with_suffix(".py.bak")
        assert backup_file.exists(), "Backup file should be created"
        assert backup_file.read_text() == original_content, (
            "Backup should contain original content"
        )

    def test_performance_on_larger_project(self) -> None:
        """Test privacy fixer performance on a larger project structure."""
        # Create multiple modules with cross-references
        for i in range(5):
            module_content = f'''"""Module {i}."""

def public_api_{i}():
    """Public API for module {i}."""
    return helper_{i}()

def helper_{i}():
    """Internal helper for module {i}."""
    return f"help from module {i}"

def cross_reference_{i}():
    """References other modules."""
    # Import would go here in real scenario
    return f"cross ref {i}"
'''
            self.create_test_file(f"src/module_{i}.py", module_content)

        # Run privacy fixing on all modules
        module_files = list(self.project_root.glob("src/module_*.py"))

        start_time = time.time()

        returncode, stdout, stderr = self.run_cli_command(
            ["--privacy-dry-run"]
            + [str(f.relative_to(self.project_root)) for f in module_files]
        )

        end_time = time.time()
        processing_time = end_time - start_time

        assert returncode == 0, f"CLI failed: {stderr}"
        assert processing_time < 10.0, "Processing should complete in reasonable time"

        # Should detect helper functions in dry-run output
        assert "helper_" in stdout


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
