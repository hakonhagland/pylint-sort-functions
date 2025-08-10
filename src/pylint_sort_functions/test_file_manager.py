"""Test file discovery and reference detection for privacy fixing.

This module provides functionality to find test files and analyze them for
function references that need to be updated when functions are privatized.
It handles both AST-based and string-based analysis of test files.

Part of the refactoring described in GitHub Issue #32.
"""

import re
from pathlib import Path
from typing import List

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import utils

# Import types that will be referenced
from pylint_sort_functions.privacy_types import FunctionTestReference


class TestFileManager:
    """Test file discovery and reference detection.

    Handles finding test files and analyzing them for function references
    that need to be updated when functions are privatized.
    """

    # Public methods

    def find_test_files(self, project_root: Path) -> List[Path]:
        """Find all test files in the project.

        Uses the existing test detection logic to identify files that should
        be updated when functions are privatized.

        :param project_root: Root directory of the project
        :returns: List of paths to test files
        """
        # Get all Python files in the project
        all_python_files = utils.find_python_files(project_root)
        test_files = []

        for file_path in all_python_files:
            try:
                # Convert to module name for test detection
                relative_path = file_path.relative_to(project_root)
                module_name = str(relative_path.with_suffix("")).replace("/", ".")

                if utils.is_unittest_file(module_name):
                    test_files.append(file_path)
            except ValueError:
                # Skip files that can't be made relative to project root
                continue

        return test_files

    def find_test_references(
        self, function_name: str, test_files: List[Path]
    ) -> List[FunctionTestReference]:
        """Find all references to a function in test files.

        Scans test files for various types of function references:
        - Import statements: from module import func
        - Mock patches: @patch('module.func'), mocker.patch('module.func')
        - Direct calls: module.func(), func()

        :param function_name: Name of the function to find references for
        :param test_files: List of test files to scan
        :returns: List of test file references
        """
        test_references = []

        for test_file in test_files:
            try:
                with open(test_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Try to parse as AST for import detection
                try:
                    module = astroid.parse(content, module_name=str(test_file))
                    file_refs = self._find_references_in_test_file(
                        function_name, test_file, module, content
                    )
                    test_references.extend(file_refs)
                except Exception:  # pylint: disable=broad-exception-caught
                    # If AST parsing fails, try string-based detection
                    file_refs = self._find_string_references_in_test_file(
                        function_name, test_file, content
                    )
                    test_references.extend(file_refs)

            except Exception:  # pylint: disable=broad-exception-caught
                # Skip files that can't be read
                continue

        return test_references

    # Private methods

    def _find_references_in_test_file(
        self,
        function_name: str,
        test_file: Path,
        module: nodes.Module,
        content: str,
    ) -> List[FunctionTestReference]:
        """Find function references in a test file using AST analysis.

        :param function_name: Name of the function to find
        :param test_file: Path to the test file being analyzed
        :param module: Parsed AST module
        :param content: File content for line-based analysis
        :returns: List of test references found
        """
        references = []

        # Find import statements
        for node in module.nodes_of_class((nodes.ImportFrom, nodes.Import)):
            if isinstance(node, nodes.ImportFrom):
                # Handle: from module import func1, func2
                if node.names:
                    for name, alias in node.names:
                        if name == function_name:
                            # Use alias if present, otherwise use original name
                            import_name = alias if alias else name
                            references.append(
                                FunctionTestReference(
                                    file_path=test_file,
                                    line=node.lineno,
                                    col=node.col_offset,
                                    context="import",
                                    reference_text=(
                                        f"from {node.module} import {name}"
                                        f"{' as ' + import_name if alias else ''}"
                                    ),
                                )
                            )

        # Find string-based mock patches in the content
        string_refs = self._find_string_references_in_test_file(
            function_name, test_file, content
        )
        references.extend(string_refs)

        return references

    def _find_string_references_in_test_file(
        self, function_name: str, test_file: Path, content: str
    ) -> List[FunctionTestReference]:
        """Find function references in test file using string-based analysis.

        This handles cases where AST parsing fails or for string literals
        like mock patches that contain function names.

        :param function_name: Name of the function to find
        :param test_file: Path to the test file being analyzed
        :param content: File content to search
        :returns: List of test references found
        """
        references = []
        lines = content.split("\n")

        # Pattern for mock patches: @patch('module.function_name')
        patch_pattern = rf"@patch\(['\"]([^'\"]*\.{re.escape(function_name)})['\"]"

        # Pattern for mocker.patch calls: mocker.patch('module.function_name')
        mocker_pattern = rf"\.patch\(['\"]([^'\"]*\.{re.escape(function_name)})['\"]"

        for line_num, line in enumerate(lines, 1):
            # Check for patch decorators
            match = re.search(patch_pattern, line)
            if match:
                references.append(
                    FunctionTestReference(
                        file_path=test_file,
                        line=line_num,
                        col=match.start(),
                        context="mock_patch",
                        reference_text=match.group(1),
                    )
                )

            # Check for mocker.patch calls
            match = re.search(mocker_pattern, line)
            if match:
                references.append(
                    FunctionTestReference(
                        file_path=test_file,
                        line=line_num,
                        col=match.start(),
                        context="mock_patch",
                        reference_text=match.group(1),
                    )
                )

        return references
