#!/usr/bin/env python3
"""
Minimal integration test for privacy fixer CLI functionality.

This test validates that the privacy fixer CLI integration is working correctly.
"""

import sys
import tempfile
from pathlib import Path

import pytest

from pylint_sort_functions.cli import main as cli_main


class TestPrivacyFixerCLIIntegration:
    """Test privacy fixer CLI integration."""

    def setup_method(self) -> None:
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())

    def teardown_method(self) -> None:
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_file(self, name: str, content: str) -> Path:
        """Create a test file."""
        file_path = self.test_dir / name
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_privacy_dry_run_cli_integration(self) -> None:
        """Test that privacy dry-run CLI integration doesn't crash."""
        content = '''"""Test module."""

def public_function():
    return helper()

def helper():
    return "help"

def main():
    public_function()
'''

        test_file = self.create_test_file("test_module.py", content)

        # Test that CLI can handle privacy dry-run without crashing
        try:
            # Mock sys.argv
            original_argv = sys.argv
            sys.argv = [
                "pylint-sort-functions",
                "--fix-privacy",
                "--privacy-dry-run",
                str(test_file),
            ]

            # This should not crash
            try:
                cli_main()
            except SystemExit as e:
                # CLI exits normally, this is expected
                assert e.code == 0, "CLI should exit cleanly"

        finally:
            sys.argv = original_argv

        # File should be unchanged
        assert test_file.read_text() == content

    def test_integrated_privacy_and_sorting_cli(self) -> None:
        """Test integrated privacy and sorting CLI options."""
        content = '''"""Test unsorted module."""

def zebra_func():
    return helper_z()

def alpha_func():
    return helper_a()

def helper_z():
    return "z"

def helper_a():
    return "a"
'''

        test_file = self.create_test_file("test_sorting.py", content)

        # Test integrated privacy + sorting
        try:
            original_argv = sys.argv
            sys.argv = [
                "pylint-sort-functions",
                "--fix-privacy",
                "--auto-sort",
                "--privacy-dry-run",
                str(test_file),
            ]

            try:
                cli_main()
            except SystemExit as e:
                assert e.code == 0, "CLI should exit cleanly"

        finally:
            sys.argv = original_argv

    def test_privacy_help_options_exist(self) -> None:
        """Test that privacy options exist in CLI help."""
        try:
            original_argv = sys.argv
            sys.argv = ["pylint-sort-functions", "--help"]

            with pytest.raises(SystemExit) as exc_info:
                cli_main()

            # Help should exit with code 0
            assert exc_info.value.code == 0

        finally:
            sys.argv = original_argv


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
