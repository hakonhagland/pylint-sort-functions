#!/usr/bin/env python3
"""Additional test cases to cover missing lines for Phase 2."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from pylint_sort_functions.privacy_fixer import FunctionTestReference, PrivacyFixer


class TestCoverageGapsPhase2:
    """Test cases to cover missing lines in Phase 2 implementation."""

    def test_cli_file_path_handling(self) -> None:
        """Test CLI handling when path is file (not directory) - covers line 460."""
        from pylint_sort_functions.cli import _handle_privacy_fixing

        # Mock args with file path instead of directory
        args = Mock()
        args.fix_privacy = True
        args.privacy_dry_run = False
        args.verbose = False
        args.auto_sort = False

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a file path, not directory path
            test_file = Path(temp_dir) / "test_module.py"
            test_file.write_text("def test_function(): pass")

            python_files = [test_file]
            paths = [test_file]  # File path, not directory

            # Mock the privacy_fixer to return no candidates to avoid full workflow
            with patch("pylint_sort_functions.cli.PrivacyFixer") as mock_privacy_fixer:
                mock_instance = Mock()
                mock_instance.find_function_references.return_value = []
                mock_instance.is_safe_to_rename.return_value = (True, [])
                report = "No functions found that need privacy fixes."
                mock_instance.generate_report.return_value = report
                mock_privacy_fixer.return_value = mock_instance

                with patch(
                    "pylint_sort_functions.cli.utils.get_functions_from_node",
                    return_value=[],
                ):
                    with patch("pylint_sort_functions.cli.astroid.parse"):
                        result = _handle_privacy_fixing(args, python_files, paths)

                        assert result == 0

    def test_cli_test_file_update_reporting(self) -> None:  # pylint: disable=too-many-locals
        """Test CLI test file update success reporting - covers lines 475, 477-479."""
        from pylint_sort_functions.cli import _handle_privacy_fixing

        args = Mock()
        args.fix_privacy = True
        args.privacy_dry_run = False
        args.verbose = False
        args.auto_sort = False

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_module.py"
            test_file.write_text("def test_function(): pass")

            python_files = [test_file]
            paths = [Path(temp_dir)]

            # Mock privacy fixer to return test file update results
            with patch("pylint_sort_functions.cli.PrivacyFixer") as mock_privacy_fixer:
                mock_instance = Mock()

                # Mock function references
                mock_func = Mock()
                mock_func.name = "test_function"
                mock_instance.find_function_references.return_value = []
                mock_instance.is_safe_to_rename.return_value = (True, [])
                mock_instance.generate_report.return_value = (
                    "Functions to rename found."
                )

                # Mock apply_renames to return test file update results
                mock_instance.apply_renames.return_value = {
                    "renamed": 1,
                    "skipped": 0,
                    "errors": [],
                    "test_files_updated": 2,  # This covers line 475
                    "test_file_errors": [  # This covers lines 477-479
                        "Error updating test_file1.py: syntax error",
                        "Error updating test_file2.py: permission denied",
                    ],
                }
                mock_privacy_fixer.return_value = mock_instance

                with patch(
                    "pylint_sort_functions.cli.utils.get_functions_from_node",
                    return_value=[mock_func],
                ):
                    with patch(
                        "pylint_sort_functions.cli.utils.should_function_be_private",
                        return_value=True,
                    ):
                        with patch("pylint_sort_functions.cli.astroid.parse"):
                            with patch("builtins.print") as mock_print:
                                result = _handle_privacy_fixing(
                                    args, python_files, paths
                                )

                                assert result == 0
                                # Verify the print calls for test file reporting
                                calls = mock_print.call_args_list
                                print_calls = [str(call) for call in calls]

                                # Check that test file updates were reported
                                test_files_reported = any(
                                    "Updated 2 test files" in call
                                    for call in print_calls
                                )
                                assert test_files_reported, (
                                    f"Test file updates not reported. "
                                    f"Calls: {print_calls}"
                                )

                                # Check that test file errors were reported
                                test_errors_reported = any(
                                    "Test file update errors" in call
                                    for call in print_calls
                                )
                                assert test_errors_reported, (
                                    f"Test file errors not reported. "
                                    f"Calls: {print_calls}"
                                )

    def test_privacy_fixer_backup_unlink_coverage(self) -> None:  # pylint: disable=too-many-locals
        """Test backup file unlink during rollback - covers line 1052."""
        import shutil
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_rollback.py"
            test_file.write_text("from src.module import helper_function\n")

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="helper_function",
                ),
            ]

            # Create fixer that will trigger the rollback exception path
            fixer = PrivacyFixer(backup=True)

            # Mock the update to fail, triggering rollback
            original_update_import = fixer.test_updater._update_import_statements

            def mock_update_import(*args: Any) -> bool:
                raise RuntimeError("Update failure to trigger rollback")

            setattr(fixer.test_updater, "_update_import_statements", mock_update_import)

            # Mock shutil operations to control the rollback flow
            original_copy2 = shutil.copy2
            original_unlink = Path.unlink

            # Track if unlink was called (this covers line 1052)
            unlink_called = []

            def mock_unlink(self: Path) -> None:
                unlink_called.append(True)
                return original_unlink(self)

            # Let copy2 work normally for backup creation, then fail for rollback
            copy2_calls = []

            def mock_copy2(*args: Any) -> Any:
                copy2_calls.append(args)
                # First call (backup creation) succeeds
                # Second call (rollback) succeeds too, so we can test unlink
                return original_copy2(*args)

            try:
                with patch("shutil.copy2", mock_copy2):
                    with patch.object(Path, "unlink", mock_unlink):
                        result = fixer.update_test_file(
                            test_file,
                            "helper_function",
                            "_helper_function",
                            test_references,
                        )

                        # Should handle the rollback and call unlink
                        assert result["success"] is False
                        assert "Update failed" in result["error"]
                        assert len(unlink_called) > 0, (
                            "backup_file.unlink() was not called"
                        )

            finally:
                # Restore original method
                setattr(fixer, "_update_import_statements", original_update_import)
