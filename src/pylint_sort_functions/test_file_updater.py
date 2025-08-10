"""Safe test file modification and update operations for privacy fixing.

This module provides functionality to safely update test files when functions
are privatized. It handles backing up files, making changes, validating syntax,
and rolling back if needed.

Part of the refactoring described in GitHub Issue #32.
"""

import ast
import shutil
from pathlib import Path
from typing import Any, Dict, List

# Import types that will be referenced
from pylint_sort_functions.privacy_types import FunctionTestReference


class TestFileUpdater:  # pylint: disable=too-few-public-methods
    """Safe test file modification and update operations.

    Handles updating test files with new function names while providing
    backup and rollback capabilities for safety.
    """

    def __init__(self, backup: bool = True):
        """Initialize the test file updater.

        :param backup: If True, create .bak files before modifying originals
        """
        self.backup = backup

    # Public methods

    def update_test_file(
        self,
        test_file: Path,
        old_name: str,
        new_name: str,
        test_references: List[FunctionTestReference],
    ) -> Dict[str, Any]:
        """Update a test file to use the new function name with backup and rollback.

        This is the main entry point for safely updating test files. It creates
        a backup, applies updates, validates the result, and rolls back if needed.

        :param test_file: Path to the test file to update
        :param old_name: Original function name
        :param new_name: New private function name (with underscore)
        :param test_references: List of test references to update
        :returns: Report of the update operation
        """
        backup_file = None

        try:
            # Create backup if backup is enabled
            if self.backup:
                backup_file = Path(f"{test_file}.bak")
                shutil.copy2(test_file, backup_file)

            # Track changes made
            import_changes = False
            mock_changes = False

            # Apply import statement updates
            if any(ref.context == "import" for ref in test_references):
                import_changes = self._update_import_statements(
                    test_file, old_name, new_name, test_references
                )

            # Apply mock pattern updates
            if any(ref.context == "mock_patch" for ref in test_references):
                mock_changes = self._update_mock_patterns(
                    test_file, old_name, new_name, test_references
                )

            # Validate the updated file syntax
            if import_changes or mock_changes:
                try:
                    with open(test_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    ast.parse(content)  # This will raise SyntaxError if invalid

                    return {
                        "success": True,
                        "file": str(test_file),
                        "backup": str(backup_file) if backup_file else None,
                        "import_changes": import_changes,
                        "mock_changes": mock_changes,
                        "total_references": len(test_references),
                    }

                except SyntaxError:
                    # Syntax validation failed - rollback
                    if backup_file and backup_file.exists():
                        shutil.copy2(backup_file, test_file)
                        backup_file.unlink()  # Remove the backup since we used it

                    return {
                        "success": False,
                        "error": "Syntax validation failed - changes rolled back",
                        "file": str(test_file),
                    }
            else:
                # No changes needed
                if backup_file and backup_file.exists():
                    backup_file.unlink()  # Remove unnecessary backup

                return {
                    "success": True,
                    "file": str(test_file),
                    "import_changes": False,
                    "mock_changes": False,
                    "total_references": len(test_references),
                }

        except Exception as e:  # pylint: disable=broad-exception-caught
            # General error - rollback if possible
            if backup_file and backup_file.exists():
                try:
                    shutil.copy2(backup_file, test_file)
                    backup_file.unlink()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass  # Best effort rollback

            return {
                "success": False,
                "error": f"Update failed: {str(e)}",
                "file": str(test_file),
            }

    # Private methods

    def _update_import_statements(  # pylint: disable=too-many-nested-blocks
        self,
        test_file: Path,
        old_name: str,
        new_name: str,
        test_references: List[FunctionTestReference],
    ) -> bool:
        """Update import statements in a test file to use the new function name.

        This method handles AST-based modifications of import statements to replace
        old function names with new private function names.

        :param test_file: Path to the test file to update
        :param old_name: Original function name
        :param new_name: New private function name (with underscore)
        :param test_references: List of test references to update
        :returns: True if file was successfully updated
        """
        try:
            # Read the current file content
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Track if any changes were made
            changes_made = False
            lines = content.split("\n")

            # Process each import-related test reference
            for ref in test_references:
                if ref.context == "import":
                    # For multi-line imports, the reference line might not be the
                    # ImportFrom node line. So we need to check if the specific
                    # line contains the function name
                    line_idx = ref.line - 1  # Convert to 0-based index
                    if line_idx < len(lines):
                        old_line = lines[line_idx]
                        # Check if this line contains the function name to replace
                        if old_name in old_line:
                            # Replace the function name in various patterns
                            new_line = (
                                old_line.replace(f" {old_name}", f" {new_name}")
                                .replace(f" {old_name},", f" {new_name},")
                                .replace(f"({old_name}", f"({new_name}")
                                .replace(f"({old_name},", f"({new_name},")
                                .replace(f"    {old_name},", f"    {new_name},")
                                .replace(f"    {old_name}", f"    {new_name}")
                            )

                            if new_line != old_line:
                                lines[line_idx] = new_line
                                changes_made = True

            # Write the updated content back to the file if changes were made
            if changes_made:
                updated_content = "\n".join(lines)
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(updated_content)

            return changes_made

        except Exception:  # pylint: disable=broad-exception-caught
            # If file operations fail, return False
            return False

    def _update_mock_patterns(
        self,
        test_file: Path,
        old_name: str,
        new_name: str,
        test_references: List[FunctionTestReference],
    ) -> bool:
        """Update mock patch patterns in a test file to use the new function name.

        This method handles string-based modifications of mock patches to replace
        old function names with new private function names.

        :param test_file: Path to the test file to update
        :param old_name: Original function name
        :param new_name: New private function name (with underscore)
        :param test_references: List of test references to update
        :returns: True if file was successfully updated
        """
        try:
            # Read the current file content
            with open(test_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Track if any changes were made
            changes_made = False
            lines = content.split("\n")

            # Process each mock-related test reference
            for ref in test_references:
                if ref.context == "mock_patch":
                    # Update the specific line containing the mock patch
                    line_idx = ref.line - 1  # Convert to 0-based index
                    if line_idx < len(lines):
                        old_line = lines[line_idx]
                        # Replace the function name in the mock patch string
                        # Handle both single and double quotes
                        new_line = old_line.replace(
                            f".{old_name}'", f".{new_name}'"
                        ).replace(f'.{old_name}"', f'.{new_name}"')

                        if new_line != old_line:
                            lines[line_idx] = new_line
                            changes_made = True

            # Write the updated content back to the file if changes were made
            if changes_made:
                updated_content = "\n".join(lines)
                with open(test_file, "w", encoding="utf-8") as f:
                    f.write(updated_content)

            return changes_made

        except Exception:  # pylint: disable=broad-exception-caught
            # If file operations fail, return False
            return False
