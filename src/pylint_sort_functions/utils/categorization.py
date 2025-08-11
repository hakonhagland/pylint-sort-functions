"""Method categorization system for flexible sorting organization.

This module provides the categorization framework that allows methods to be
organized into multiple categories (properties, test methods, etc.) instead
of just the binary public/private distinction.
"""

import fnmatch
from dataclasses import dataclass, field

from astroid import nodes  # type: ignore[import-untyped]

from .ast_analysis import is_private_function
from .decorators import decorator_matches_pattern, get_decorator_strings


@dataclass
class MethodCategory:
    """Configuration for a method category in the sorting system.

    Defines how methods are categorized based on patterns, decorators, and other
    criteria. Categories determine the sorting order and section organization.

    :param name: Unique identifier for this category (e.g., 'properties')
    :type name: str
    :param patterns: List of glob patterns to match names (e.g., ['test_*'])
    :type patterns: list[str]
    :param decorators: List of decorator patterns (e.g., ['@property'])
    :type decorators: list[str]
    :param priority: Priority for conflict resolution, higher values win
    :type priority: int
    :param section_header: Comment header text for this category
    :type section_header: str
    """

    name: str
    patterns: list[str] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    priority: int = 0
    section_header: str = ""


@dataclass
class CategoryConfig:
    """Configuration for the method categorization system.

    Defines the complete categorization scheme including all categories,
    default behavior, and compatibility settings.

    :param categories: List of method categories in sorting order
    :type categories: list[MethodCategory]
    :param default_category: Category name for methods that do not match patterns
    :type default_category: str
    :param enable_categories: Enable multi-category system (false = backward
        compatibility)
    :type enable_categories: bool
    :param category_sorting: How to sort within categories ('alphabetical' or
        'declaration')
    :type category_sorting: str
    """

    categories: list[MethodCategory] = field(default_factory=list)
    default_category: str = "public_methods"
    enable_categories: bool = False  # Backward compatibility - disabled by default
    category_sorting: str = "alphabetical"  # or "declaration" to preserve order

    def __post_init__(self) -> None:
        """Initialize with default binary categories if none provided."""
        if not self.categories:
            self.categories = self._get_default_categories()

    def _get_default_categories(self) -> list[MethodCategory]:
        """Get default binary public/private categories for backward compatibility.

        :returns: List of default method categories (public, private)
        :rtype: list[MethodCategory]
        """
        return [
            MethodCategory(
                name="public_methods",
                patterns=["*"],  # Catch-all for non-private methods
                section_header="# Public methods",
            ),
            MethodCategory(
                name="private_methods",
                patterns=["_*"],  # Methods starting with underscore
                priority=1,  # Higher priority than public catch-all
                section_header="# Private methods",
            ),
        ]


def categorize_method(  # pylint: disable=function-should-be-private
    func: nodes.FunctionDef, config: CategoryConfig | None = None
) -> str:
    """Determine the category for a method based on configuration patterns.

    This replaces the binary is_private_function() with a flexible categorization
    system that supports multiple method types (properties, test methods, etc.).

    When enable_categories=False (default), provides backward compatible behavior
    by returning 'public_methods' or 'private_methods' based on naming convention.

    :param func: Function definition node to categorize
    :type func: nodes.FunctionDef
    :param config: Category configuration, uses default if None
    :type config: CategoryConfig | None
    :returns: Category name for the method (e.g., 'properties', 'test_methods')
    :rtype: str
    """
    if config is None:
        config = CategoryConfig()

    # For backward compatibility, when categories disabled, use original logic
    if not config.enable_categories:
        return "private_methods" if is_private_function(func) else "public_methods"

    # Find matching categories, prioritizing higher priority values
    matching_categories: list[tuple[MethodCategory, int]] = []

    for category in config.categories:
        match_priority = _get_category_match_priority(func, category)
        if match_priority > 0:
            matching_categories.append((category, match_priority))

    if not matching_categories:
        # No matches found, use default category
        return config.default_category

    # Sort by priority (higher first), then by category priority field
    matching_categories.sort(key=lambda x: (x[1], x[0].priority), reverse=True)

    return matching_categories[0][0].name


def find_method_section_boundaries(  # pylint: disable=function-should-be-private
    lines: list[str], config: CategoryConfig
) -> dict[int, str]:
    """Map line numbers to their section categories based on headers.

    Creates a mapping from line numbers to category names, where each line
    between section headers belongs to the category of the preceding header.

    :param lines: Source code lines to analyze
    :type lines: list[str]
    :param config: Category configuration with section headers
    :type config: CategoryConfig
    :returns: Dict mapping line numbers to category names
    :rtype: dict[int, str]
    """
    boundaries = {}
    current_section = None

    # Parse all section headers first
    headers = parse_section_headers(lines, config)
    header_lines = {line_num: category for category, (line_num, _) in headers.items()}

    # Map each line to its section
    for line_num in range(len(lines)):
        # Check if this line is a section header
        if line_num in header_lines:
            current_section = header_lines[line_num]

        # Assign current section to this line
        if current_section:
            boundaries[line_num] = current_section

    return boundaries


def get_expected_section_for_method(  # pylint: disable=function-should-be-private
    method: nodes.FunctionDef, config: CategoryConfig
) -> str:
    """Get expected section name for a method based on categorization.

    Uses the categorization system to determine which section header a method
    should appear under according to the configuration.

    :param method: Method node to analyze
    :type method: nodes.FunctionDef
    :param config: Category configuration
    :type config: CategoryConfig
    :returns: Expected category/section name for this method
    :rtype: str
    """
    return categorize_method(method, config)


def is_method_in_correct_section(  # pylint: disable=function-should-be-private
    method: nodes.FunctionDef,
    method_line: int,
    lines: list[str],
    config: CategoryConfig,
) -> bool:
    """Check if a method is positioned in its correct section.

    Validates that a method appears under the appropriate section header
    according to its categorization.

    :param method: Method node to validate
    :type method: nodes.FunctionDef
    :param method_line: Line number where method is defined (0-based)
    :type method_line: int
    :param lines: Source code lines
    :type lines: list[str]
    :param config: Category configuration
    :type config: CategoryConfig
    :returns: True if method is in correct section, False otherwise
    :rtype: bool
    """
    # Get expected section for this method
    expected_section = get_expected_section_for_method(method, config)

    # Get section boundaries mapping
    boundaries = find_method_section_boundaries(lines, config)

    # Check if method line has correct section assignment
    actual_section = boundaries.get(method_line)

    return actual_section == expected_section


def parse_section_headers(  # pylint: disable=function-should-be-private
    lines: list[str], config: CategoryConfig
) -> dict[str, tuple[int, str]]:
    """Parse existing section headers and map them to categories.

    Scans source code lines to find comment lines that match section header
    patterns for any of the configured categories. Returns a mapping from
    category names to their header line numbers and text.

    :param lines: Source code lines to scan for headers
    :type lines: list[str]
    :param config: Category configuration with header patterns
    :type config: CategoryConfig
    :returns: Dict mapping category names to (line_number, header_text) tuples
    :rtype: dict[str, tuple[int, str]]
    """
    headers = {}

    for line_num, line in enumerate(lines):
        stripped_line = line.strip()

        # Skip non-comment lines
        if not stripped_line.startswith("#"):
            continue

        # Check if this line matches any category's section header
        for category in config.categories:
            if category.section_header and _is_header_match(
                stripped_line, category.section_header, config
            ):
                headers[category.name] = (line_num, stripped_line)
                break  # Each line can only match one category

    return headers


def _get_category_match_priority(
    func: nodes.FunctionDef, category: MethodCategory
) -> int:
    """Calculate match priority for a function against a category.

    Returns 0 if no match, positive integer if match (higher = better match).
    Priority calculation:
    - Decorator match: 100 (highest priority - most specific)
    - Name pattern match: 50 (medium priority)
    - Catch-all pattern (*): 1 (lowest priority - fallback)

    :param func: Function definition node to check
    :type func: nodes.FunctionDef
    :param category: Category to test against
    :type category: MethodCategory
    :returns: Match priority (0 = no match, >0 = match strength)
    :rtype: int
    """
    priority = 0

    # Check decorator patterns (highest priority)
    if category.decorators:
        function_decorators = get_decorator_strings(func)
        for decorator_pattern in category.decorators:
            for func_decorator in function_decorators:
                if decorator_matches_pattern(func_decorator, decorator_pattern):
                    priority = max(priority, 100)
                    break

    # Check name patterns (medium priority)
    if category.patterns:
        for pattern in category.patterns:
            if _method_name_matches_pattern(func.name, pattern):
                if pattern == "*":
                    # Catch-all pattern gets lowest priority
                    priority = max(priority, 1)
                else:
                    # Specific patterns get medium priority
                    priority = max(priority, 50)
                break

    return priority


def _is_header_match(
    comment_line: str,
    header_pattern: str,
    config: CategoryConfig,  # pylint: disable=unused-argument
) -> bool:
    """Check if a comment line matches a section header pattern.

    Supports flexible matching including case-insensitive comparison and
    substring matching for section headers.

    :param comment_line: Comment line to check (already stripped)
    :type comment_line: str
    :param header_pattern: Expected header text pattern
    :type header_pattern: str
    :param config: Category configuration (for future case sensitivity options)
    :type config: CategoryConfig
    :returns: True if comment matches header pattern
    :rtype: bool
    """
    # For now, use case-insensitive exact match
    # Future enhancement: Add case sensitivity options to CategoryConfig
    return comment_line.lower() == header_pattern.lower()


def _method_name_matches_pattern(method_name: str, pattern: str) -> bool:
    """Check if a method name matches a glob pattern.

    Supports standard glob patterns:
    - * matches any sequence of characters
    - ? matches any single character
    - [seq] matches any character in seq
    - [!seq] matches any character not in seq

    :param method_name: Method name to check
    :type method_name: str
    :param pattern: Glob pattern to match against
    :type pattern: str
    :returns: True if method name matches pattern
    :rtype: bool
    """
    return fnmatch.fnmatch(method_name, pattern)
