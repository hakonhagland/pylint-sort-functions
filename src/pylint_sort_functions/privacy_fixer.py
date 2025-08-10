"""Privacy fixer for automatic function renaming.

This module provides functionality to automatically rename functions that should
be private (detected by W9004) by adding underscore prefixes.

The implementation follows a conservative approach:
1. Only rename functions where we can find ALL references safely
2. Provide dry-run mode to preview changes
3. Create backups by default
4. Report all changes clearly

Safety-first design ensures user confidence in the automated renaming.

Refactored version using composition as described in GitHub Issue #32.
"""

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Import the new modular components
from pylint_sort_functions.file_operations import FileOperations
from pylint_sort_functions.privacy_analyzer import PrivacyAnalyzer
from pylint_sort_functions.privacy_types import (
    FunctionReference,
    FunctionTestReference,
    RenameCandidate,
)
from pylint_sort_functions.test_file_manager import TestFileManager
from pylint_sort_functions.test_file_updater import TestFileUpdater

# Re-export types for backward compatibility
__all__ = [
    "PrivacyFixer",
    "FunctionReference",
    "RenameCandidate",
    "FunctionTestReference",
]


class PrivacyFixer:
    """Handles automatic renaming of functions that should be private.

    Refactored to use composition with focused components for better
    maintainability and separation of concerns.
    """

    def __init__(self, dry_run: bool = False, backup: bool = True):
        """Initialize the privacy fixer.

        :param dry_run: If True, only analyze and report changes without applying them
        :param backup: If True, create .bak files before modifying originals
        """
        self.dry_run = dry_run
        self.backup = backup
        self.rename_candidates: List[RenameCandidate] = []

        # Initialize component classes with composition
        self.analyzer = PrivacyAnalyzer()
        self.test_manager = TestFileManager()
        self.test_updater = TestFileUpdater(backup=backup)
        self.file_ops = FileOperations(backup=backup)

    # Public methods

    def analyze_module(
        self,
        files_or_module_path: Union[List[Path], Path],  # For backward compatibility
        project_root: Path,
        public_patterns_or_include_test_analysis: Optional[
            Union[Set[str], bool]
        ] = None,
    ) -> List[RenameCandidate]:
        """Analyze a module for functions that can be automatically renamed to private.

        This method supports two signatures for backward compatibility:
        1. New: analyze_module(files, project_root, include_test_analysis=True)
        2. Old: analyze_module(module_path, project_root, public_patterns=None)

        :param files_or_module_path: List of files (new) or single module path (old)
        :param project_root: Root directory of the project
        :param public_patterns_or_include_test_analysis: Set of public patterns (old)
            or include_test_analysis flag (new)
        :returns: List of functions that can be safely renamed
        """
        # Handle backward compatibility with old signature
        if isinstance(files_or_module_path, Path):
            # Old signature: analyze_module(module_path, project_root, public_patterns)
            # Return empty list for backward compatibility (was TODO placeholder)
            return []

        # New signature: analyze_module(files, project_root, include_test_analysis)
        files = files_or_module_path
        include_test_analysis = public_patterns_or_include_test_analysis
        if include_test_analysis is None:
            include_test_analysis = True

        # Use analyzer to detect privacy violations
        violations = self.analyzer.analyze_module_privacy(files, project_root)

        # Find test references if requested
        if include_test_analysis:
            test_files = self.test_manager.find_test_files(project_root)

            for candidate in violations:
                # Find test references for this function
                test_references = self.test_manager.find_test_references(
                    candidate.old_name, test_files
                )

                # Update candidate with test references
                updated_candidate = candidate._replace(test_references=test_references)
                violations[violations.index(candidate)] = updated_candidate

        # Validate safety for each candidate
        validated_candidates = []
        for candidate in violations:
            is_safe, issues = self.is_safe_to_rename(
                candidate
            )  # Use our own method for inheritance
            validated_candidate = candidate._replace(
                is_safe=is_safe, safety_issues=issues
            )
            validated_candidates.append(validated_candidate)

        self.rename_candidates = validated_candidates
        return validated_candidates

    def apply_renames(  # pylint: disable=too-many-locals,too-many-branches
        self, candidates: List[RenameCandidate], project_root: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Apply the function renames to the module files and update test files.

        :param candidates: List of validated rename candidates
        :param project_root: Root directory for finding test files (optional)
        :returns: Report of changes made
        """
        if not candidates:
            return {"renamed": 0, "skipped": 0, "reason": "No candidates provided"}

        # Group candidates by file path
        candidates_by_file = self._group_candidates_by_file(candidates)

        renamed_count = 0
        skipped_count = 0
        errors = []
        test_files_updated = 0
        test_file_errors = []

        # First, apply renames to the production files
        for file_path, file_candidates in candidates_by_file.items():
            try:
                result = self._apply_renames_to_file(file_path, file_candidates)
                renamed_count += result["renamed"]
                skipped_count += result["skipped"]
                if result.get("errors"):
                    errors.extend(result["errors"])
            except Exception as e:  # pylint: disable=broad-exception-caught
                error_msg = f"Error processing {file_path}: {str(e)}"
                errors.append(error_msg)
                skipped_count += len(file_candidates)

        # Second, update test files if project_root is provided and we have
        # successful renames
        if (  # pylint: disable=too-many-nested-blocks
            project_root and renamed_count > 0 and not self.dry_run
        ):
            # Process each successfully renamed candidate
            for file_path, file_candidates in candidates_by_file.items():
                for candidate in file_candidates:
                    if candidate.is_safe and candidate.test_references:
                        # Group test references by file
                        test_refs_by_file: Dict[Path, List[FunctionTestReference]] = {}
                        for ref in candidate.test_references:
                            if ref.file_path not in test_refs_by_file:
                                test_refs_by_file[ref.file_path] = []
                            test_refs_by_file[ref.file_path].append(ref)

                        # Update each test file that references this function
                        for test_file_path, refs in test_refs_by_file.items():
                            try:
                                test_result = self.test_updater.update_test_file(
                                    test_file_path,
                                    candidate.old_name,
                                    candidate.new_name,
                                    refs,
                                )

                                if test_result["success"]:
                                    test_files_updated += 1
                                else:
                                    error_msg = (
                                        f"Test file {test_file_path}: "
                                        f"{test_result.get('error', 'Update failed')}"
                                    )
                                    test_file_errors.append(error_msg)
                            except Exception as e:  # pylint: disable=broad-exception-caught
                                error_msg = (
                                    f"Error updating test file {test_file_path}: "
                                    f"{str(e)}"
                                )
                                test_file_errors.append(error_msg)

        # Prepare comprehensive report
        report = {
            "renamed": renamed_count,
            "skipped": skipped_count,
            "errors": errors,
        }

        # Add test file information if we attempted test updates
        if project_root:
            report["test_files_updated"] = test_files_updated
            report["test_file_errors"] = test_file_errors

        return report

    def detect_privacy_violations(
        self,
        files: List[Path],
        project_root: Path,
    ) -> List[RenameCandidate]:
        """Detect functions that should be private across multiple files.

        Delegates to the privacy analyzer for the actual detection logic.

        :param files: List of Python files to analyze
        :param project_root: Root directory of the project for cross-module analysis
        :returns: List of functions that violate privacy guidelines
        """
        return self.analyzer.analyze_module_privacy(files, project_root)

    def find_function_references(
        self,
        function_name: str,
        module_ast: Any,  # astroid nodes.Module
    ) -> List[FunctionReference]:
        """Find all references to a function within a module.

        Delegates to the privacy analyzer for the actual reference finding logic.

        :param function_name: Name of the function to find references for
        :param module_ast: AST of the module to search in
        :returns: List of all references found
        """
        return self.analyzer.find_function_references(function_name, module_ast)

    def find_test_files(self, project_root: Path) -> List[Path]:
        """Find all test files in the project.

        Delegates to the test file manager for the actual file discovery logic.

        :param project_root: Root directory of the project
        :returns: List of paths to test files
        """
        return self.test_manager.find_test_files(project_root)

    def find_test_references(
        self, function_name: str, test_files: List[Path]
    ) -> List[FunctionTestReference]:
        """Find all references to a function in test files.

        Delegates to the test file manager for the actual reference finding logic.

        :param function_name: Name of the function to find references for
        :param test_files: List of test files to scan
        :returns: List of test file references
        """
        return self.test_manager.find_test_references(function_name, test_files)

    def generate_report(self, candidates: List[RenameCandidate]) -> str:
        """Generate a human-readable report of rename operations.

        :param candidates: List of rename candidates
        :returns: Formatted report string
        """
        if not candidates:
            return "No functions found that need privacy fixes."

        report_lines = ["Privacy Fix Analysis:", ""]

        safe_count = sum(1 for c in candidates if c.is_safe)
        unsafe_count = len(candidates) - safe_count

        if safe_count > 0:
            report_lines.append(f"✅ Can safely rename {safe_count} functions:")
            for candidate in candidates:
                if candidate.is_safe:
                    ref_count = len(candidate.references)
                    report_lines.append(
                        f"  • {candidate.old_name} → {candidate.new_name} "
                        f"({ref_count} references)"
                    )
            report_lines.append("")

        if unsafe_count > 0:
            report_lines.append(f"⚠️  Cannot safely rename {unsafe_count} functions:")
            for candidate in candidates:
                if not candidate.is_safe:
                    issues = ", ".join(candidate.safety_issues)
                    report_lines.append(f"  • {candidate.old_name}: {issues}")
            report_lines.append("")

        return "\n".join(report_lines)

    def is_safe_to_rename(self, candidate: RenameCandidate) -> Tuple[bool, List[str]]:
        """Check if a function can be safely renamed.

        Conservative safety checks:
        1. No dynamic references (getattr, hasattr with strings)
        2. No string literals containing the function name
        3. No name conflicts with existing private functions
        4. All references are in contexts we can handle

        :param candidate: The rename candidate to validate
        :returns: Tuple of (is_safe, list_of_issues)
        """
        issues = []

        # Check for name conflicts - call our own methods that can be overridden
        if self._has_name_conflict(candidate):
            issues.append(f"Private function '{candidate.new_name}' already exists")

        # Check for dynamic references in the module
        if self._has_dynamic_references(candidate):
            issues.append("Contains dynamic references (getattr, hasattr, etc.)")

        # Check for string literals containing the function name
        if self._has_string_references(candidate):
            issues.append("Function name found in string literals")

        # Check if all references are in safe contexts
        unsafe_contexts = self._check_reference_contexts(candidate)
        if unsafe_contexts:
            issues.append(f"Unsafe reference contexts: {', '.join(unsafe_contexts)}")

        return len(issues) == 0, issues

    def update_test_file(
        self,
        test_file: Path,
        old_name: str,
        new_name: str,
        test_references: List[FunctionTestReference],
    ) -> Dict[str, Any]:
        """Update a test file to use the new function name with backup and rollback.

        Delegates to the test file updater for the actual update logic.

        :param test_file: Path to the test file to update
        :param old_name: Original function name
        :param new_name: New private function name (with underscore)
        :param test_references: List of test references to update
        :returns: Report of the update operation
        """
        return self.test_updater.update_test_file(
            test_file, old_name, new_name, test_references
        )

    # Private methods

    # Additional delegation methods for backward compatibility with tests
    # pylint: disable=protected-access

    def _apply_renames_to_content(
        self, content: str, candidates: List[RenameCandidate]
    ) -> str:
        """Apply function name renames to file content (backward compatibility)."""
        return self.file_ops._apply_renames_to_content(content, candidates)

    def _apply_renames_to_file(
        self, file_path: Path, candidates: List[RenameCandidate]
    ) -> Dict[str, Any]:
        """Apply renames to a specific file (backward compatibility)."""
        return self.file_ops.apply_renames_to_file(file_path, candidates, self.dry_run)

    def _build_import_graph(self, project_root: Path) -> Dict[Path, Set[str]]:
        """Build a graph of imports across the project (backward compatibility)."""
        return self.analyzer._build_import_graph(project_root)

    def _check_reference_contexts(self, candidate: RenameCandidate) -> List[str]:
        """Check if all references are in contexts we can safely handle."""
        return self.analyzer._check_reference_contexts(candidate)

    def _extract_function_imports(self, module: Any) -> Set[str]:
        """Extract function names that are imported by a module."""
        return self.analyzer._extract_function_imports(module)

    def _fallback_privacy_heuristics(self, func: Any) -> bool:
        """Fallback heuristics when cross-module analysis isn't available."""
        return self.analyzer._fallback_privacy_heuristics(func)

    def _find_references_in_test_file(
        self, function_name: str, test_file: Path, module: Any, content: str
    ) -> List[FunctionTestReference]:
        """Find function references in a test file using AST analysis."""
        return self.test_manager._find_references_in_test_file(
            function_name, test_file, module, content
        )

    def _find_string_references_in_test_file(
        self, function_name: str, test_file: Path, content: str
    ) -> List[FunctionTestReference]:
        """Find function references in test file using string-based analysis."""
        return self.test_manager._find_string_references_in_test_file(
            function_name, test_file, content
        )

    def _get_functions_from_module(self, module: Any) -> List[Any]:
        """Extract all function definitions from a module (backward compatibility)."""
        return self.analyzer._get_functions_from_module(module)

    def _group_candidates_by_file(  # pylint: disable=too-many-nested-blocks
        self, candidates: List[RenameCandidate]
    ) -> Dict[Path, List[RenameCandidate]]:
        """Group rename candidates by the file they belong to.

        :param candidates: List of rename candidates
        :returns: Dictionary mapping file paths to candidate lists
        """
        # For MVP, we'll extract file path from function node
        # In a more complete implementation, we'd track file paths explicitly
        candidates_by_file: Dict[Path, List[RenameCandidate]] = defaultdict(list)

        for candidate in candidates:
            # Extract file path from the function node
            file_path = None

            # Try to get file path from the AST node
            try:
                if hasattr(candidate.function_node, "root"):
                    root = candidate.function_node.root()
                    if hasattr(root, "file") and root.file and root.file != "<?>":
                        file_path = Path(root.file)
                    elif hasattr(root, "name") and root.name and root.name != "<?>":
                        # For astroid modules parsed with explicit names
                        file_path = Path(root.name)
            except Exception:  # pylint: disable=broad-exception-caught
                # If we can't get file path from node, continue to fallback
                pass

            # Fallback: use a unique identifier based on the node
            if file_path is None:
                # For testing scenarios, create unique file names based on function name
                # This ensures different functions get grouped separately when needed
                try:
                    node_id = (
                        id(candidate.function_node.root())
                        if hasattr(candidate.function_node, "root")
                        else id(candidate.function_node)
                    )
                except Exception:  # pylint: disable=broad-exception-caught
                    # If even getting the root fails, use the function node itself
                    node_id = id(candidate.function_node)
                file_path = Path(f"file_{node_id}.py")

            candidates_by_file[file_path].append(candidate)

        return dict(candidates_by_file)

    def _has_dynamic_references(self, candidate: RenameCandidate) -> bool:
        """Check for dynamic references that we can't safely rename."""
        return self.analyzer._has_dynamic_references(candidate)

    def _has_name_conflict(self, candidate: RenameCandidate) -> bool:
        """Check if renaming would create a name conflict."""
        return self.analyzer._has_name_conflict(candidate)

    def _has_string_references(self, candidate: RenameCandidate) -> bool:
        """Check for string literals containing the function name."""
        return self.analyzer._has_string_references(candidate)

    def _is_function_used_externally(
        self, func_name: str, file_path: Path, import_graph: Dict[Path, Set[str]]
    ) -> bool:
        """Check if a function is imported by other modules (backward compatibility)."""
        return self.analyzer._is_function_used_externally(
            func_name, file_path, import_graph
        )

    def _should_function_be_private(
        self, func: Any, file_path: Path, project_root: Path
    ) -> bool:
        """Determine if a function should be private based on cross-module usage."""
        return self.analyzer.should_function_be_private(func, file_path, project_root)

    def _update_import_statements(
        self,
        test_file: Path,
        old_name: str,
        new_name: str,
        test_references: List[FunctionTestReference],
    ) -> bool:
        """Update import statements in a test file to use the new function name."""
        return self.test_updater._update_import_statements(
            test_file, old_name, new_name, test_references
        )

    def _update_mock_patterns(
        self,
        test_file: Path,
        old_name: str,
        new_name: str,
        test_references: List[FunctionTestReference],
    ) -> bool:
        """Update mock patch patterns in a test file to use the new function name."""
        return self.test_updater._update_mock_patterns(
            test_file, old_name, new_name, test_references
        )
