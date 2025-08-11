"""File pattern matching utilities for Python project analysis.

This module provides utilities for finding Python files, detecting test files,
and matching file patterns using glob patterns.
"""

import fnmatch
from pathlib import Path
from typing import Any


def find_python_files(root_path: Path) -> list[Path]:  # pylint: disable=function-should-be-private
    """Find all Python files in a project directory.

    Recursively searches for files with .py extension while skipping common
    directories that should not be analyzed (build artifacts, virtual environments,
    caches, etc.).

    TODO: Make skip_dirs list configurable for project-specific needs.

    :param root_path: Root directory to search for Python files
    :type root_path: Path
    :returns: List of paths to Python files
    :rtype: list[Path]
    """
    python_files = []

    # Directories to skip
    skip_dirs = {
        "__pycache__",
        ".git",
        ".tox",
        ".pytest_cache",
        ".mypy_cache",
        "venv",
        ".venv",
        "env",
        ".env",
        "build",
        "dist",
        "*.egg-info",
        "node_modules",
    }

    for item in root_path.rglob("*.py"):
        # Skip if any parent directory should be skipped
        if any(skip_dir in item.parts for skip_dir in skip_dirs):
            continue

        python_files.append(item)

    return python_files


def is_unittest_file(  # pylint: disable=function-should-be-private,too-many-return-statements,too-many-branches
    module_name: str, privacy_config: dict[str, Any] | None = None
) -> bool:
    """Check if a module name indicates a unit test file.

    Detects test files based on configurable patterns and built-in heuristics.
    Can be configured to override built-in detection or add additional patterns.

    Built-in detection patterns:
    - Files in 'tests' or 'test' directories
    - Files starting with 'test_'
    - Files ending with '_test'
    - conftest.py files (pytest configuration)
    - Files containing 'test' in their path components

    :param module_name: The module name to check (e.g., 'package.tests.test_utils')
    :type module_name: str
    :param privacy_config: Privacy configuration with exclusion patterns
    :type privacy_config: dict[str, Any] | None
    :returns: True if module appears to be a test file
    :rtype: bool
    """
    if privacy_config is None:
        privacy_config = {}

    # Get configuration options
    exclude_dirs = privacy_config.get("exclude_dirs", [])
    exclude_patterns = privacy_config.get("exclude_patterns", [])
    additional_test_patterns = privacy_config.get("additional_test_patterns", [])
    override_test_detection = privacy_config.get("override_test_detection", False)

    # Check directory exclusions first
    lower_name = module_name.lower()
    parts = lower_name.split(".")

    # Check if file is in an excluded directory
    for exclude_dir in exclude_dirs:
        if exclude_dir.lower() in parts:
            return True

    # Check file pattern exclusions
    for pattern in exclude_patterns:
        if _matches_file_pattern(module_name, pattern):
            return True

    # Check additional test patterns
    for pattern in additional_test_patterns:
        if _matches_file_pattern(module_name, pattern):
            return True

    # If override is enabled, only use configured patterns
    if override_test_detection:
        return False

    # Built-in test detection (original logic)
    # Check if any directory in the path is a test directory
    if "tests" in parts or "test" in parts:
        return True

    # Get the file name (last component)
    if parts:
        filename = parts[-1]

        # Check for common test file patterns
        if filename.startswith("test_"):
            return True
        if filename.endswith("_test"):
            return True
        if filename == "conftest":  # pytest configuration file
            return True

    # Fallback: check if 'test' appears anywhere (catches edge cases)
    # This is more permissive but ensures we do not miss test files
    return "test" in lower_name


def _matches_file_pattern(module_name: str, pattern: str) -> bool:
    """Check if a module name matches a file pattern.

    Supports glob patterns for matching file names and paths.

    :param module_name: Module name to check (e.g., 'package.tests.test_utils')
    :type module_name: str
    :param pattern: Glob pattern to match against (e.g., 'test_*.py', '*_test.py')
    :type pattern: str
    :returns: True if module name matches pattern
    :rtype: bool
    """
    # Convert module name to filename-like format for pattern matching
    # e.g., "package.tests.test_utils" -> "package/tests/test_utils.py"
    file_path = module_name.replace(".", "/") + ".py"

    # Also check just the module name for direct matching
    parts = module_name.split(".")
    if parts:
        filename = parts[-1] + ".py"  # Add .py for pattern matching

        # Check both full path and just filename
        return fnmatch.fnmatch(file_path, pattern) or fnmatch.fnmatch(filename, pattern)

    return fnmatch.fnmatch(file_path, pattern)  # pragma: no cover
