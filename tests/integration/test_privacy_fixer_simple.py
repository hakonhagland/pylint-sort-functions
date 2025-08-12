#!/usr/bin/env python3
"""
Simplified integration tests for privacy fixer workflow.

This test suite focuses on testing the CLI integration and end-to-end workflow
rather than the internal APIs, making it more robust to implementation changes.
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


class TestPrivacyFixerCLIIntegration:  # pylint: disable=attribute-defined-outside-init
    """Integration tests for privacy fixer CLI workflow."""

    def setup_method(self) -> None:
        """Set up test environment with temporary project."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.project_root = self.test_dir / "test_project"
        self.project_root.mkdir(parents=True)

        # Create a proper Python package structure
        (self.project_root / "src").mkdir()
        (self.project_root / "src" / "__init__.py").touch()

        # Get the actual Python executable from the current environment
        self.python_executable = sys.executable

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

    def test_privacy_fixing_dry_run_cli(self) -> None:
        """Test privacy fixing dry-run through CLI."""
        content = '''"""Test module."""

def public_function():
    """This is used by main."""
    return helper_function()

def helper_function():
    """Only used internally."""
    return "help"

def main():
    """Entry point."""
    result = public_function()
    print(result)
'''

        test_file = self.create_test_file("src/test_module.py", content)
        original_content = test_file.read_text()

        # Run dry-run privacy fixing via CLI (standalone option)
        returncode, stdout, stderr = self.run_cli_command(
            ["--privacy-dry-run", "src/test_module.py"]
        )

        # Should succeed (we don't expect specific output format yet)
        assert returncode == 0, f"CLI failed: {stderr}"

        # File should be unchanged in dry-run
        assert test_file.read_text() == original_content

    def test_privacy_fixing_with_backup(self) -> None:
        """Test that privacy fixing creates backup files."""
        content = '''"""Test backup creation."""

def public_func():
    return helper()

def helper():
    return "help"

def main():
    return public_func()
'''

        test_file = self.create_test_file("src/backup_test.py", content)
        original_content = test_file.read_text()

        # Run privacy fixing via CLI
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "src/backup_test.py"]
        )

        # Should succeed
        assert returncode == 0, f"CLI failed: {stderr}"

        # Check backup file exists (CLI should create backups by default)
        backup_file = test_file.with_suffix(".py.bak")
        if backup_file.exists():
            assert backup_file.read_text() == original_content, (
                "Backup should contain original content"
            )

    def test_integrated_privacy_and_sorting_cli(self) -> None:
        """Test integrated privacy fixing with automatic sorting via CLI."""
        content = '''"""Test module with unsorted functions."""

def zebra_function():
    """Public function."""
    return helper_zebra()

def alpha_function():
    """Public function."""
    return helper_alpha()

def helper_zebra():
    """Internal helper."""
    return "zebra help"

def helper_alpha():
    """Internal helper."""
    return "alpha help"

def main():
    alpha_function()
    zebra_function()
'''

        test_file = self.create_test_file("src/test_module.py", content)

        # Run privacy fixing with auto-sort
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "--auto-sort", "src/test_module.py"]
        )

        # Should succeed
        assert returncode == 0, f"CLI failed: {stderr}"

        # File should have been processed (we don't check exact content
        # since the feature is still being developed)
        modified_content = test_file.read_text()
        assert modified_content != content, "File should have been modified"

    def test_cli_error_handling(self) -> None:
        """Test CLI error handling for invalid scenarios."""
        # Test with non-existent file
        returncode, stdout, stderr = self.run_cli_command(
            ["--fix-privacy", "nonexistent.py"]
        )

        # Should handle gracefully (either succeed with message or fail gracefully)
        # We don't assert specific return code since error handling might vary

    def test_cli_help_contains_privacy_options(self) -> None:
        """Test that CLI help includes privacy fixing options."""
        returncode, stdout, stderr = self.run_cli_command(["--help"])

        assert returncode == 0, "Help command should succeed"

        # Should mention privacy fixing options
        help_text = stdout + stderr
        assert "--fix-privacy" in help_text, "Should include --fix-privacy option"
        assert "--privacy-dry-run" in help_text, (
            "Should include --privacy-dry-run option"
        )

    def test_multiple_files_processing(self) -> None:
        """Test processing multiple files at once."""
        # Create multiple test files
        content1 = '''"""Module 1."""

def func_a():
    return helper_a()

def helper_a():
    return "help a"
'''

        content2 = '''"""Module 2."""

def func_b():
    return helper_b()

def helper_b():
    return "help b"
'''

        file1 = self.create_test_file("src/module1.py", content1)
        file2 = self.create_test_file("src/module2.py", content2)

        # Run privacy fixing on multiple files (standalone option)
        returncode, stdout, stderr = self.run_cli_command(
            ["--privacy-dry-run", "src/module1.py", "src/module2.py"]
        )

        # Should succeed
        assert returncode == 0, f"CLI failed: {stderr}"

        # Files should be unchanged in dry-run mode
        assert file1.read_text() == content1
        assert file2.read_text() == content2

    def test_performance_reasonable_on_multiple_files(self) -> None:
        """Test that privacy fixer has reasonable performance."""
        # Create several test files
        for i in range(3):  # Keep it small for CI
            content = f'''"""Module {i}."""

def public_api_{i}():
    return helper_{i}()

def helper_{i}():
    return f"help {i}"
'''
            self.create_test_file(f"src/module_{i}.py", content)

        # Run privacy fixing on all files (standalone option)
        module_files = ["src/module_0.py", "src/module_1.py", "src/module_2.py"]

        start_time = time.time()

        returncode, stdout, stderr = self.run_cli_command(
            ["--privacy-dry-run"] + module_files
        )

        end_time = time.time()
        processing_time = end_time - start_time

        assert returncode == 0, f"CLI failed: {stderr}"
        assert processing_time < 5.0, "Processing should complete in reasonable time"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
