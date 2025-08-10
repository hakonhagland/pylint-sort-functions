#!/usr/bin/env python3
"""Test cases for Phase 2 functionality: Test file updates for privacy fixer."""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

from pylint_sort_functions.privacy_fixer import FunctionTestReference, PrivacyFixer


class TestPhase2TestFileUpdates:
    """Test Phase 2 test file update functionality."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.fixer = PrivacyFixer()  # pylint: disable=attribute-defined-outside-init

    def test_update_import_statements_basic(self) -> None:
        """Test basic import statement updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_module.py"
            test_file.write_text(
                "from src.module import helper_function, other_func\n"
                "\n"
                "def test_something():\n"
                "    result = helper_function()\n"
                "    assert result\n"
            )

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="from src.module import helper_function",
                ),
            ]

            result = self.fixer._update_import_statements(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result is True
            updated_content = test_file.read_text()
            assert (
                "from src.module import _helper_function, other_func" in updated_content
            )

    def test_update_import_statements_multiple_formats(self) -> None:
        """Test import statement updates with different formats."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_complex.py"
            test_file.write_text(
                "from src.module import (\n"
                "    helper_function,\n"
                "    other_func,\n"
                "    third_func\n"
                ")\n"
                "from utils import helper_function as helper\n"
            )

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=2,  # Line with helper_function
                    col=0,
                    context="import",
                    reference_text="helper_function",
                ),
            ]

            result = self.fixer._update_import_statements(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result is True
            updated_content = test_file.read_text()
            assert "_helper_function," in updated_content
            # Should not affect the aliased import
            assert "from utils import helper_function as helper" in updated_content

    def test_update_mock_patterns_patch_decorator(self) -> None:
        """Test updating mock patch decorators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_mocks.py"
            test_file.write_text(
                "from unittest.mock import patch\n"
                "\n"
                "@patch('src.module.helper_function')\n"
                "def test_with_patch(mock_helper):\n"
                "    result = helper_function()\n"
                "    assert result\n"
            )

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=3,
                    col=0,
                    context="mock_patch",
                    reference_text="src.module.helper_function",
                ),
            ]

            result = self.fixer._update_mock_patterns(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result is True
            updated_content = test_file.read_text()
            assert "@patch('src.module._helper_function')" in updated_content

    def test_update_mock_patterns_mocker_calls(self) -> None:
        """Test updating mocker.patch() calls."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_mocker.py"
            test_file.write_text(
                "def test_with_mocker(mocker):\n"
                '    mocker.patch("src.module.helper_function", '
                'return_value="mocked")\n'
                "    result = helper_function()\n"
                "    assert result == 'mocked'\n"
            )

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=2,
                    col=0,
                    context="mock_patch",
                    reference_text="src.module.helper_function",
                ),
            ]

            result = self.fixer._update_mock_patterns(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result is True
            updated_content = test_file.read_text()
            assert 'mocker.patch("src.module._helper_function"' in updated_content

    def test_update_test_file_comprehensive(self) -> None:
        """Test comprehensive test file update with both imports and mocks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_comprehensive.py"
            original_content = (
                "from unittest.mock import patch\n"
                "from src.module import helper_function, other_func\n"
                "\n"
                "@patch('src.module.helper_function')\n"
                "def test_with_patch(mock_helper):\n"
                "    result = helper_function()\n"
                "    assert result\n"
                "\n"
                "def test_with_mocker(mocker):\n"
                '    mocker.patch("src.module.helper_function")\n'
                "    result = helper_function()\n"
            )
            test_file.write_text(original_content)

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=2,
                    col=0,
                    context="import",
                    reference_text="from src.module import helper_function",
                ),
                FunctionTestReference(
                    file_path=test_file,
                    line=4,
                    col=0,
                    context="mock_patch",
                    reference_text="src.module.helper_function",
                ),
                FunctionTestReference(
                    file_path=test_file,
                    line=10,
                    col=0,
                    context="mock_patch",
                    reference_text="src.module.helper_function",
                ),
            ]

            result = self.fixer.update_test_file(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result["success"] is True
            assert result["import_changes"] is True
            assert result["mock_changes"] is True
            assert result["total_references"] == 3

            updated_content = test_file.read_text()
            assert (
                "from src.module import _helper_function, other_func" in updated_content
            )
            assert "@patch('src.module._helper_function')" in updated_content
            assert 'mocker.patch("src.module._helper_function")' in updated_content

    def test_update_test_file_with_backup(self) -> None:
        """Test test file update creates backup files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_backup.py"
            original_content = "from src.module import helper_function\n"
            test_file.write_text(original_content)

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="from src.module import helper_function",
                ),
            ]

            # Create fixer with backup enabled
            fixer = PrivacyFixer(backup=True)
            result = fixer.update_test_file(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result["success"] is True
            assert result["backup"] is not None

            backup_file = Path(result["backup"])
            assert backup_file.exists()
            assert backup_file.read_text() == original_content

    def test_update_test_file_syntax_error_rollback(self) -> None:
        """Test rollback when syntax validation fails."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_syntax.py"
            # Create valid content that will have invalid syntax after update
            original_content = "from src.module import helper_function\n"
            test_file.write_text(original_content)

            # Create a mock that will make the update create invalid syntax
            original_update_import = self.fixer.test_updater._update_import_statements

            def mock_update_import_statements(  # pylint: disable=unused-argument
                test_file: Path,
                old_name: str,
                new_name: str,
                test_references: list[FunctionTestReference],
            ) -> bool:
                # This will create invalid syntax by writing malformed content
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(
                        "from src.module import _helper_function(\n"
                    )  # Invalid syntax
                return True

            # Using setattr to avoid MyPy method assignment error
            setattr(
                self.fixer.test_updater,
                "_update_import_statements",
                mock_update_import_statements,
            )

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="from src.module import helper_function",
                ),
            ]

            try:
                result = self.fixer.update_test_file(
                    test_file, "helper_function", "_helper_function", test_references
                )

                # Should fail due to syntax error and rollback
                assert result["success"] is False
                assert "Syntax validation failed" in result["error"]

                # File should be restored to original content
                current_content = test_file.read_text()
                assert current_content == original_content

            finally:
                # Restore the original method
                setattr(self.fixer, "_update_import_statements", original_update_import)

    def test_update_test_file_no_changes_needed(self) -> None:
        """Test update when no references match the context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_no_changes.py"
            original_content = "from src.module import other_function\n"
            test_file.write_text(original_content)

            # Empty test references - no changes needed
            test_references: list[FunctionTestReference] = []

            result = self.fixer.update_test_file(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result["success"] is True
            assert result["import_changes"] is False
            assert result["mock_changes"] is False
            assert result["total_references"] == 0

            # Content should remain unchanged
            assert test_file.read_text() == original_content

    def test_update_test_file_exception_handling(self) -> None:
        """Test exception handling during test file updates."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "nonexistent.py"
            # Don't create the file - this will cause an exception

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="helper_function",
                ),
            ]

            result = self.fixer.update_test_file(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result["success"] is False
            assert "Update failed:" in result["error"]

    def test_update_import_statements_no_matching_references(self) -> None:
        """Test import updater when no references match."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_no_match.py"
            original_content = "from src.module import other_function\n"
            test_file.write_text(original_content)

            # References that don't match any import context
            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="mock_patch",  # Wrong context
                    reference_text="helper_function",
                ),
            ]

            result = self.fixer._update_import_statements(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result is False  # No changes made
            assert test_file.read_text() == original_content

    def test_update_mock_patterns_no_matching_references(self) -> None:
        """Test mock updater when no references match."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_no_mock.py"
            original_content = "def test_function():\n    pass\n"
            test_file.write_text(original_content)

            # References that don't match any mock context
            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",  # Wrong context
                    reference_text="helper_function",
                ),
            ]

            result = self.fixer._update_mock_patterns(
                test_file, "helper_function", "_helper_function", test_references
            )

            assert result is False  # No changes made
            assert test_file.read_text() == original_content

    def test_update_methods_exception_handling(self) -> None:
        """Test exception handling in update methods."""
        # Test with invalid file path
        invalid_file = Path("/nonexistent/path/file.py")

        test_references = [
            FunctionTestReference(
                file_path=invalid_file,
                line=1,
                col=0,
                context="import",
                reference_text="helper_function",
            ),
        ]

        # Should handle exceptions gracefully
        result = self.fixer._update_import_statements(
            invalid_file, "helper_function", "_helper_function", test_references
        )
        assert result is False

        result = self.fixer._update_mock_patterns(
            invalid_file, "helper_function", "_helper_function", test_references
        )
        assert result is False


class TestPhase2Integration:
    """Test Phase 2 integration with existing workflow."""

    def test_apply_renames_with_test_files(self) -> None:
        """Test apply_renames integrates with test file updates."""
        from pylint_sort_functions.privacy_fixer import RenameCandidate

        fixer = PrivacyFixer()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create test file structure
            tests_dir = project_root / "tests"
            tests_dir.mkdir()

            test_file = tests_dir / "test_module.py"
            test_file.write_text(
                "from src.module import helper_function\n"
                "@patch('src.module.helper_function')\n"
                "def test_helper():\n"
                "    pass\n"
            )

            # Create mock function node
            mock_func_node = Mock()
            mock_func_node.name = "helper_function"

            # Create test references
            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="from src.module import helper_function",
                ),
                FunctionTestReference(
                    file_path=test_file,
                    line=2,
                    col=0,
                    context="mock_patch",
                    reference_text="src.module.helper_function",
                ),
            ]

            candidates = [
                RenameCandidate(
                    function_node=mock_func_node,
                    old_name="helper_function",
                    new_name="_helper_function",
                    references=[],
                    test_references=test_references,
                    is_safe=True,
                    safety_issues=[],
                )
            ]

            # Mock the file rename part since we're focusing on test file updates
            original_apply_renames_to_file = fixer._apply_renames_to_file

            def mock_apply_renames_to_file(  # pylint: disable=unused-argument
                file_path: Path, file_candidates: list[RenameCandidate]
            ) -> dict[str, Any]:
                return {"renamed": 1, "skipped": 0, "errors": []}

            # Using setattr to avoid MyPy method assignment error
            setattr(fixer, "_apply_renames_to_file", mock_apply_renames_to_file)

            try:
                result = fixer.apply_renames(candidates, project_root)

                # Should have updated test files
                assert result["renamed"] == 1
                assert result["test_files_updated"] == 1
                assert len(result["test_file_errors"]) == 0

                # Verify test file was actually updated
                updated_content = test_file.read_text()
                assert "from src.module import _helper_function" in updated_content
                assert "@patch('src.module._helper_function')" in updated_content

            finally:
                # Restore original method
                setattr(fixer, "_apply_renames_to_file", original_apply_renames_to_file)

    def test_apply_renames_without_project_root(self) -> None:
        """Test apply_renames without project_root doesn't attempt test updates."""
        from pylint_sort_functions.privacy_fixer import RenameCandidate

        fixer = PrivacyFixer()

        mock_func_node = Mock()
        mock_func_node.name = "helper_function"

        candidates = [
            RenameCandidate(
                function_node=mock_func_node,
                old_name="helper_function",
                new_name="_helper_function",
                references=[],
                test_references=[],  # Has test references but no project_root
                is_safe=True,
                safety_issues=[],
            )
        ]

        # Mock the file rename part
        original_apply_renames_to_file = fixer._apply_renames_to_file

        def mock_apply_renames_to_file(  # pylint: disable=unused-argument
            file_path: Path, file_candidates: list[RenameCandidate]
        ) -> dict[str, Any]:
            return {"renamed": 1, "skipped": 0, "errors": []}

        # Using setattr to avoid MyPy method assignment error
        setattr(fixer, "_apply_renames_to_file", mock_apply_renames_to_file)

        try:
            result = fixer.apply_renames(candidates, project_root=None)

            # Should not include test file information
            assert result["renamed"] == 1
            assert "test_files_updated" not in result
            assert "test_file_errors" not in result

        finally:
            # Restore original method
            setattr(fixer, "_apply_renames_to_file", original_apply_renames_to_file)

    def test_apply_renames_dry_run_mode(self) -> None:
        """Test apply_renames in dry-run mode doesn't update test files."""
        from pylint_sort_functions.privacy_fixer import RenameCandidate

        fixer = PrivacyFixer(dry_run=True)

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            mock_func_node = Mock()
            mock_func_node.name = "helper_function"

            candidates = [
                RenameCandidate(
                    function_node=mock_func_node,
                    old_name="helper_function",
                    new_name="_helper_function",
                    references=[],
                    test_references=[Mock()],  # Has test references
                    is_safe=True,
                    safety_issues=[],
                )
            ]

            result = fixer.apply_renames(candidates, project_root)

            # In dry-run mode, should not attempt test file updates
            assert (
                "test_files_updated" not in result or result["test_files_updated"] == 0
            )

    def test_cli_integration_file_project_root(self) -> None:
        """Test CLI integration when paths contain files (not directories)."""
        import sys
        import tempfile
        from pathlib import Path
        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            test_file = project_root / "test_module.py"
            test_file.write_text("def test(): pass")

            # Mock sys.argv to simulate CLI call with file path (not directory)
            test_args = [
                "pylint-sort-functions",
                "--fix-privacy",
                str(test_file),  # File path, not directory
            ]

            with patch.object(sys, "argv", test_args):
                with patch(
                    "pylint_sort_functions.cli._handle_privacy_fixing"
                ) as mock_handle:
                    # Configure the mock to return early
                    mock_handle.return_value = 0

                    # Import and call main to trigger the CLI path
                    from pylint_sort_functions.cli import main

                    main()

                    # Verify the handler was called with file path
                    assert mock_handle.called
                    # File path should be converted to directory path as project root

    def test_test_file_update_error_reporting(self) -> None:
        """Test error reporting for test file update failures."""
        from unittest.mock import Mock

        from pylint_sort_functions.privacy_fixer import RenameCandidate

        fixer = PrivacyFixer()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create test file
            test_file = project_root / "test_module.py"
            test_file.write_text("from src.module import helper_function\n")

            mock_func_node = Mock()
            mock_func_node.name = "helper_function"

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="helper_function",
                ),
            ]

            candidates = [
                RenameCandidate(
                    function_node=mock_func_node,
                    old_name="helper_function",
                    new_name="_helper_function",
                    references=[],
                    test_references=test_references,
                    is_safe=True,
                    safety_issues=[],
                )
            ]

            # Mock apply_renames_to_file to return success
            original_apply_renames_to_file = fixer._apply_renames_to_file
            # Using setattr to avoid MyPy method assignment error
            setattr(
                fixer,
                "_apply_renames_to_file",
                lambda file_path, file_candidates: {
                    "renamed": 1,
                    "skipped": 0,
                    "errors": [],
                },
            )

            # Mock update_test_file to return failure (on component method)
            original_update_test_file = fixer.test_updater.update_test_file

            def mock_update_test_file(*_args: Any) -> dict[str, Any]:
                return {"success": False, "error": "Test update failed"}

            # Using setattr to avoid MyPy method assignment error
            setattr(fixer.test_updater, "update_test_file", mock_update_test_file)

            try:
                result = fixer.apply_renames(candidates, project_root)

                # Should have error reporting for test file updates
                assert result["renamed"] == 1
                assert result["test_files_updated"] == 0
                assert len(result["test_file_errors"]) == 1
                assert "Test update failed" in result["test_file_errors"][0]

            finally:
                setattr(fixer, "_apply_renames_to_file", original_apply_renames_to_file)
                setattr(
                    fixer.test_updater, "update_test_file", original_update_test_file
                )

    def test_test_file_update_exception_reporting(self) -> None:
        """Test exception reporting for test file update failures."""
        from unittest.mock import Mock

        from pylint_sort_functions.privacy_fixer import RenameCandidate

        fixer = PrivacyFixer()

        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create test file
            test_file = project_root / "test_module.py"
            test_file.write_text("from src.module import helper_function\n")

            mock_func_node = Mock()
            mock_func_node.name = "helper_function"

            test_references = [
                FunctionTestReference(
                    file_path=test_file,
                    line=1,
                    col=0,
                    context="import",
                    reference_text="helper_function",
                ),
            ]

            candidates = [
                RenameCandidate(
                    function_node=mock_func_node,
                    old_name="helper_function",
                    new_name="_helper_function",
                    references=[],
                    test_references=test_references,
                    is_safe=True,
                    safety_issues=[],
                )
            ]

            # Mock apply_renames_to_file to return success
            original_apply_renames_to_file = fixer._apply_renames_to_file
            # Using setattr to avoid MyPy method assignment error
            setattr(
                fixer,
                "_apply_renames_to_file",
                lambda file_path, file_candidates: {
                    "renamed": 1,
                    "skipped": 0,
                    "errors": [],
                },
            )

            # Mock update_test_file to raise exception (on component method)
            original_update_test_file = fixer.test_updater.update_test_file

            def mock_update_test_file(*args: Any) -> dict[str, Any]:
                raise RuntimeError("Simulated exception")

            # Using setattr to avoid MyPy method assignment error
            setattr(fixer.test_updater, "update_test_file", mock_update_test_file)

            try:
                result = fixer.apply_renames(candidates, project_root)

                # Should have exception reporting for test file updates
                assert result["renamed"] == 1
                assert result["test_files_updated"] == 0
                assert len(result["test_file_errors"]) == 1
                assert "Simulated exception" in result["test_file_errors"][0]

            finally:
                setattr(fixer, "_apply_renames_to_file", original_apply_renames_to_file)
                setattr(
                    fixer.test_updater, "update_test_file", original_update_test_file
                )

    def test_update_test_file_rollback_exception_handling(self) -> None:
        """Test exception handling during rollback operations."""
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

            # Mock shutil.copy2 to raise exception during rollback
            import shutil

            original_copy2 = shutil.copy2

            call_count = [0]

            def mock_copy2(*args: Any) -> Any:
                call_count[0] += 1
                if call_count[0] == 1:
                    # First call (backup creation) succeeds
                    return original_copy2(*args)
                # Second call (rollback) fails
                raise PermissionError("Cannot access backup file")

            # Mock the general exception path by making an exception occur
            original_update_import = fixer.test_updater._update_import_statements

            def mock_update_import(*args: Any) -> bool:
                raise RuntimeError("General update failure")

            # Using setattr to avoid MyPy method assignment error
            setattr(fixer.test_updater, "_update_import_statements", mock_update_import)

            with patch("shutil.copy2", mock_copy2):
                result = fixer.update_test_file(
                    test_file, "helper_function", "_helper_function", test_references
                )

                # Should handle the rollback exception gracefully
                assert result["success"] is False
                assert "Update failed" in result["error"]

            # Restore original method
            setattr(fixer, "_update_import_statements", original_update_import)
