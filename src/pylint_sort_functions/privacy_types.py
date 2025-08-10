"""Common types and data structures for privacy fixing functionality.

This module contains the shared types used across the privacy fixing system,
extracted to avoid circular imports between modules.

Part of the refactoring described in GitHub Issue #32.
"""

from pathlib import Path
from typing import List, NamedTuple

from astroid import nodes  # type: ignore[import-untyped]


class FunctionReference(NamedTuple):
    """Represents a reference to a function within a module."""

    node: nodes.NodeNG
    line: int
    col: int
    context: str  # "call", "decorator", "assignment", etc.


class FunctionTestReference(NamedTuple):
    """Represents a reference to a function within a test file."""

    file_path: Path
    line: int
    col: int
    context: str  # "import", "mock_patch", "call", etc.
    reference_text: str  # The actual text that needs to be replaced


class RenameCandidate(NamedTuple):
    """Represents a function that is a candidate for renaming to private."""

    function_node: nodes.FunctionDef
    old_name: str
    new_name: str
    references: List[FunctionReference]
    test_references: List[FunctionTestReference]
    is_safe: bool
    safety_issues: List[str]
