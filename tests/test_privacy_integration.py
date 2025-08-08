"""Integration tests for privacy fixer workflow."""

import tempfile
from pathlib import Path

import pytest

from pylint_sort_functions.cli import main as cli_main


class TestPrivacyFixerIntegration:
    """Integration tests for privacy fixer CLI functionality."""

    def test_privacy_dry_run_integration(self) -> None:
        """Test privacy dry-run integration works end-to-end."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = Path(tmp_dir)
            test_file = test_dir / "test_module.py"

            content = '''"""Test module."""

def public_function():
    return helper()

def helper():
    return "help"

def main():
    public_function()
'''
            test_file.write_text(content, encoding="utf-8")
            original_content = test_file.read_text()

            # Test CLI integration with privacy dry-run
            import sys

            original_argv = sys.argv
            try:
                sys.argv = [
                    "pylint-sort-functions",
                    "--fix-privacy",
                    "--privacy-dry-run",
                    str(test_file),
                ]

                try:
                    cli_main()
                except SystemExit as e:  # pragma: no cover
                    assert e.code == 0, "CLI should exit cleanly"  # pragma: no cover

            finally:
                sys.argv = original_argv

            # File should be unchanged in dry-run
            assert test_file.read_text() == original_content

    def test_integrated_privacy_and_sorting(self) -> None:
        """Test integrated privacy fixing with sorting."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = Path(tmp_dir)
            test_file = test_dir / "test_sorting.py"

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
            test_file.write_text(content, encoding="utf-8")

            # Test integrated CLI options
            import sys

            original_argv = sys.argv
            try:
                sys.argv = [
                    "pylint-sort-functions",
                    "--fix-privacy",
                    "--auto-sort",
                    "--privacy-dry-run",
                    str(test_file),
                ]

                try:
                    cli_main()
                except SystemExit as e:  # pragma: no cover
                    assert e.code == 0, "CLI should exit cleanly"  # pragma: no cover

            finally:
                sys.argv = original_argv

    @pytest.mark.integration
    def test_privacy_fixer_with_real_project_structure(self) -> None:
        """Test privacy fixer with realistic project structure."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            project_root = Path(tmp_dir)
            src_dir = project_root / "src"
            src_dir.mkdir()

            # Create main module
            main_content = '''"""Main module."""

from src.utils import format_result

def main():
    result = format_result(42)
    print(result)
'''
            (project_root / "main.py").write_text(main_content, encoding="utf-8")

            # Create utils module with mixed public/private functions
            utils_content = '''"""Utilities module."""

def format_result(value):
    """Public API - used by main.py."""
    return validate_and_format(value)

def validate_and_format(value):
    """Internal helper - should potentially be private."""
    if not isinstance(value, (int, float)):
        raise ValueError("Value must be numeric")
    return f"Result: {value}"

def unused_helper():
    """Completely unused - should definitely be private."""
    return "unused"
'''
            (src_dir / "utils.py").write_text(utils_content, encoding="utf-8")
            (src_dir / "__init__.py").touch()

            # Run privacy analysis in dry-run mode
            import sys

            original_argv = sys.argv
            try:
                sys.argv = [
                    "pylint-sort-functions",
                    "--fix-privacy",
                    "--privacy-dry-run",
                    str(src_dir / "utils.py"),
                ]

                try:
                    cli_main()
                except SystemExit as e:  # pragma: no cover
                    assert e.code == 0, (
                        "CLI should handle real project structure"
                    )  # pragma: no cover

            finally:
                sys.argv = original_argv
