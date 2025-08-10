"""Safe file operations with backup and rollback capabilities for privacy fixing.

This module provides functionality for safe file operations including backup
creation, content modification, syntax validation, and rollback mechanisms.
Used by the privacy fixing system to ensure safe updates.

Part of the refactoring described in GitHub Issue #32.
"""

import ast
import re
from pathlib import Path
from typing import Any, Dict, List

# Import types that will be referenced
from pylint_sort_functions.privacy_types import RenameCandidate


class FileOperations:
    """Safe file operations with backup and rollback capabilities.

    Handles file backup, content modification, validation, and recovery
    operations for safe privacy fixing transformations.
    """

    def __init__(self, backup: bool = True):
        """Initialize the file operations handler.

        :param backup: If True, create .bak files before modifying originals
        """
        self.backup = backup

    # Public methods

    def apply_renames_to_file(
        self, file_path: Path, candidates: List[RenameCandidate], dry_run: bool = False
    ) -> Dict[str, Any]:
        """Apply renames to a specific file with backup and validation.

        :param file_path: Path to the file to modify
        :param candidates: List of rename candidates for this file
        :param dry_run: If True, only report what would be changed without applying
        :returns: Report of changes made to this file
        """
        if dry_run:
            # In dry-run mode, just report what would be changed
            return {
                "renamed": len([c for c in candidates if c.is_safe]),
                "skipped": len([c for c in candidates if not c.is_safe]),
                "errors": [],
                "dry_run": True,
            }

        try:
            # Read the original file content
            original_content = self.read_file(file_path)

            # Create backup if requested
            backup_path = None
            if self.backup:
                backup_path = self.create_backup(file_path)

            # Apply renames to the content
            modified_content = self._apply_renames_to_content(
                original_content, candidates
            )

            # Write the modified content back to the file
            if modified_content != original_content:
                self.write_file(file_path, modified_content)

            # Validate syntax after modification
            modified_syntax_valid = (
                modified_content == original_content or self.validate_syntax(file_path)
            )
            if not modified_syntax_valid:
                # Restore from backup if validation fails
                if backup_path:  # pragma: no cover
                    self.restore_from_backup(file_path, backup_path)  # pragma: no cover
                raise SyntaxError(  # pragma: no cover
                    "Modified file has invalid syntax"
                )

            return {
                "renamed": len([c for c in candidates if c.is_safe]),
                "skipped": len([c for c in candidates if not c.is_safe]),
                "errors": [],
                "backup": str(backup_path) if backup_path else None,
            }

        except Exception as e:  # pylint: disable=broad-exception-caught
            return {
                "renamed": 0,
                "skipped": len(candidates),
                "errors": [f"Failed to process {file_path}: {str(e)}"],
            }

    def cleanup_backup(self, backup_path: Path) -> None:
        """Remove a backup file if it exists.

        :param backup_path: Path to the backup file to remove
        """
        if backup_path.exists():
            backup_path.unlink()

    def create_backup(self, file_path: Path) -> Path:
        """Create a backup of a file before modification.

        :param file_path: Path to the file to back up
        :returns: Path to the backup file
        """
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        content = self.read_file(file_path)
        self.write_file(backup_path, content)
        return backup_path

    def read_file(self, file_path: Path) -> str:
        """Read content from a file with UTF-8 encoding.

        :param file_path: Path to the file to read
        :returns: File content as string
        """
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    def restore_from_backup(self, file_path: Path, backup_path: Path) -> None:
        """Restore a file from its backup.

        :param file_path: Path to the file to restore
        :param backup_path: Path to the backup file
        """
        if backup_path.exists():
            content = self.read_file(backup_path)
            self.write_file(file_path, content)

    def validate_syntax(self, file_path: Path) -> bool:
        """Validate that a Python file has correct syntax.

        :param file_path: Path to the file to validate
        :returns: True if syntax is valid, False otherwise
        """
        try:
            content = self.read_file(file_path)
            ast.parse(content)
            return True
        except (SyntaxError, UnicodeDecodeError):  # pragma: no cover
            return False  # pragma: no cover

    # Private methods

    def write_file(self, file_path: Path, content: str) -> None:
        """Write content to a file with UTF-8 encoding.

        :param file_path: Path to the file to write
        :param content: Content to write
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _apply_renames_to_content(
        self, content: str, candidates: List[RenameCandidate]
    ) -> str:
        """Apply function name renames to file content.

        This uses a conservative string replacement approach that:
        1. Only processes safe candidates
        2. Uses word boundaries to avoid partial matches
        3. Preserves original formatting and structure

        :param content: Original file content
        :param candidates: List of rename candidates
        :returns: Modified file content
        """
        modified_content = content

        # Only process safe candidates
        safe_candidates = [c for c in candidates if c.is_safe]

        for candidate in safe_candidates:
            old_name = candidate.old_name
            new_name = candidate.new_name

            # Use word boundaries to ensure we only match complete function names
            # This pattern matches:
            # - Function definitions: def old_name(
            # - Function calls: old_name(
            # - Assignments: var = old_name
            # - Decorators: @old_name
            pattern = rf"\b{re.escape(old_name)}\b"

            modified_content = re.sub(pattern, new_name, modified_content)

        return modified_content
