"""Tests for CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from pylint_sort_functions.cli import (
    _find_project_root,
    _find_python_files_from_paths,
    main,
)


class TestCLI:
    """Test CLI functionality."""

    def test_conflicting_privacy_options(self) -> None:
        """Test conflicting privacy options."""
        test_args = ["--fix-privacy", "--privacy-dry-run", "test.py"]

        with patch("sys.argv", ["pylint-sort-functions"] + test_args):
            result = main()
            assert result == 1

    def test_find_project_root(self) -> None:
        """Test project root finding logic."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create pyproject.toml to mark as project root
            (temp_path / "pyproject.toml").write_text("[tool.test]\\nkey = 'value'")

            # Create nested directory
            nested_dir = temp_path / "src" / "project"
            nested_dir.mkdir(parents=True)

            # Test finding root from nested directory
            result = _find_project_root(nested_dir)
            assert result.resolve() == temp_path.resolve()

    def test_find_project_root_fallback(self) -> None:
        """Test project root finding fallback behavior."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            nested_dir = temp_path / "no" / "markers"
            nested_dir.mkdir(parents=True)

            # No project markers, should fallback to parent
            result = _find_project_root(nested_dir)
            assert result.resolve() == nested_dir.resolve()

    def test_find_python_files_with_directory(self) -> None:
        """Test finding Python files in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Python files
            py_file1 = temp_path / "test1.py"
            py_file2 = temp_path / "test2.py"
            non_py_file = temp_path / "test.txt"

            py_file1.write_text("def test(): pass")
            py_file2.write_text("def test(): pass")
            non_py_file.write_text("not python")

            result = _find_python_files_from_paths([temp_path])

            # Should find both Python files
            assert len(result) == 2
            assert py_file1 in result
            assert py_file2 in result
            assert non_py_file not in result

    def test_find_python_files_with_file(self) -> None:
        """Test finding Python files when given a single file."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            temp_file = Path(f.name)

        try:
            result = _find_python_files_from_paths([temp_file])
            assert result == [temp_file]
        finally:
            temp_file.unlink()

    def test_fix_privacy_mode(self) -> None:
        """Test fix privacy mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""def helper(): return 'help'
def main(): return helper()""")
            temp_file = Path(f.name)

        try:
            test_args = ["--fix-privacy", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                result = main()
                assert result == 0
        finally:
            temp_file.unlink()

    def test_main_check_only_mode(self) -> None:
        """Test main function in check-only mode."""
        test_args = ["test.py"]

        with patch("sys.argv", ["pylint-sort-functions"] + test_args):
            result = main()
            # Check-only mode returns 0 regardless of file existence
            assert result == 0

    def test_main_general_exception(self) -> None:
        """Test main function handles general exceptions."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"def test(): pass")
            temp_file = Path(f.name)

        try:
            test_args = ["--fix", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                with patch(
                    "pylint_sort_functions.auto_fix.sort_python_files",
                    side_effect=RuntimeError("Test error"),
                ):
                    result = main()
                    assert result == 1
        finally:
            temp_file.unlink()

    def test_main_keyboard_interrupt(self) -> None:
        """Test main function handles KeyboardInterrupt."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"def test(): pass")
            temp_file = Path(f.name)

        try:
            test_args = ["--fix", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                with patch(
                    "pylint_sort_functions.auto_fix.sort_python_files",
                    side_effect=KeyboardInterrupt,
                ):
                    result = main()
                    assert result == 1
        finally:
            temp_file.unlink()

    def test_main_no_fix_no_dry_run(self) -> None:
        """Test main function with neither --fix nor --dry-run."""
        test_args = ["test.py"]

        with patch("sys.argv", ["pylint-sort-functions"] + test_args):
            result = main()
            # Should exit successfully in check-only mode
            assert result == 0

    def test_main_path_resolution_error(self) -> None:
        """Test main function handles path resolution errors."""
        test_args = ["--fix", "test.py"]

        with patch("sys.argv", ["pylint-sort-functions"] + test_args):
            with patch("pathlib.Path.resolve", side_effect=OSError("Path error")):
                result = main()
                assert result == 1

    def test_main_verbose_output(self) -> None:
        """Test main function with verbose output."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"def zebra(): pass\\ndef apple(): pass")
            temp_file = Path(f.name)

        try:
            test_args = ["--fix", "--verbose", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                result = main()
                assert result == 0
        finally:
            temp_file.unlink()

    def test_main_with_ignore_decorators(self) -> None:
        """Test main function with ignore decorators option."""
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"@app.route('/test')\\ndef test(): pass")
            temp_file = Path(f.name)

        try:
            test_args = ["--fix", "--ignore-decorators", "@app.route", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                result = main()
                assert result == 0
        finally:
            temp_file.unlink()

    def test_main_with_no_python_files(self) -> None:
        """Test main function when no Python files found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_args = ["--fix", temp_dir]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                result = main()
                assert result == 0  # No files to process

    def test_main_with_nonexistent_path(self) -> None:
        """Test main function with non-existent path."""
        test_args = ["--fix", "nonexistent.py"]

        with patch("sys.argv", ["pylint-sort-functions"] + test_args):
            with patch("pathlib.Path.exists", return_value=False):
                result = main()
                assert result == 1

    def test_privacy_dry_run_mode(self) -> None:
        """Test privacy dry-run mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""def helper(): return 'help'
def main(): return helper()""")
            temp_file = Path(f.name)

        try:
            test_args = ["--privacy-dry-run", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                result = main()
                assert result == 0
        finally:
            temp_file.unlink()

    def test_privacy_with_auto_sort_dry_run(self) -> None:
        """Test privacy fixing with auto-sort in dry-run mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""def zebra(): return helper()
def helper(): return 'help'
def main(): return zebra()""")
            temp_file = Path(f.name)

        try:
            test_args = ["--privacy-dry-run", "--auto-sort", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                result = main()
                assert result == 0
        finally:
            temp_file.unlink()

    def test_privacy_with_auto_sort_fix_mode(self) -> None:
        """Test privacy fixing with auto-sort in fix mode."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("""def zebra(): return helper()
def helper(): return 'help'
def main(): return zebra()""")
            temp_file = Path(f.name)

        try:
            test_args = ["--fix-privacy", "--auto-sort", "--no-backup", str(temp_file)]

            with patch("sys.argv", ["pylint-sort-functions"] + test_args):
                result = main()
                assert result == 0
        finally:
            temp_file.unlink()
