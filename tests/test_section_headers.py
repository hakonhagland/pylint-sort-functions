"""Comprehensive tests for Phase 2 section header functionality.

This module tests all the new section header functionality including:
- Header detection and parsing
- Section boundary mapping
- Method validation against sections
- Integration with checker functionality
"""

import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import Mock

from astroid import extract_node  # type: ignore[import-untyped]

from pylint_sort_functions.checker import FunctionSortChecker
from pylint_sort_functions.utils import (
    CategoryConfig,
    MethodCategory,
    are_methods_in_correct_sections,
    find_empty_section_headers,
    find_method_section_boundaries,
    find_missing_section_headers,
    get_expected_section_for_method,
    get_section_violations,
    is_method_in_correct_section,
    parse_section_headers,
)


class TestSectionHeaderParsing(unittest.TestCase):
    """Test section header parsing functionality."""

    def test_parse_section_headers_basic(self) -> None:
        """Test basic section header parsing."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", section_header="# Test methods"),
                MethodCategory(
                    name="public_methods", section_header="# Public methods"
                ),
            ],
        )

        lines = [
            "# Test methods",
            "def test_something():",
            "    pass",
            "",
            "# Public methods",
            "def public_method():",
            "    pass",
        ]

        headers = parse_section_headers(lines, config)
        self.assertEqual(len(headers), 2)
        self.assertIn("test_methods", headers)
        self.assertIn("public_methods", headers)
        self.assertEqual(headers["test_methods"], (0, "# Test methods"))
        self.assertEqual(headers["public_methods"], (4, "# Public methods"))

    def test_parse_section_headers_no_headers(self) -> None:
        """Test parsing when no section headers are present."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", section_header="# Test methods"),
            ],
        )

        lines = ["def test_something():", "    pass"]

        headers = parse_section_headers(lines, config)
        self.assertEqual(len(headers), 0)

    def test_parse_section_headers_empty_header_text(self) -> None:
        """Test parsing with categories that have empty section headers."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", section_header=""),  # Empty header
                MethodCategory(
                    name="public_methods", section_header="# Public methods"
                ),
            ],
        )

        lines = ["# Public methods", "def public_method():", "    pass"]

        headers = parse_section_headers(lines, config)
        self.assertEqual(len(headers), 1)
        self.assertIn("public_methods", headers)

    def test_parse_section_headers_non_comment_lines(self) -> None:
        """Test that non-comment lines are properly skipped."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="public_methods", section_header="# Public methods"
                ),
            ],
        )

        lines = [
            "def some_function():",
            "    pass",
            "# Public methods",
            "def public_method():",
            "    pass",
        ]

        headers = parse_section_headers(lines, config)
        self.assertEqual(len(headers), 1)
        self.assertEqual(headers["public_methods"], (2, "# Public methods"))


class TestSectionBoundaries(unittest.TestCase):
    """Test section boundary mapping functionality."""

    def test_find_method_section_boundaries_basic(self) -> None:
        """Test basic section boundary mapping."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", section_header="# Test methods"),
                MethodCategory(
                    name="public_methods", section_header="# Public methods"
                ),
            ],
        )

        lines = [
            "# Test methods",  # Line 0
            "def test_something():",  # Line 1
            "    pass",  # Line 2
            "",  # Line 3
            "# Public methods",  # Line 4
            "def public_method():",  # Line 5
            "    pass",  # Line 6
        ]

        boundaries = find_method_section_boundaries(lines, config)

        # Lines 0-3 should be in test_methods section
        self.assertEqual(boundaries[0], "test_methods")
        self.assertEqual(boundaries[1], "test_methods")
        self.assertEqual(boundaries[2], "test_methods")
        self.assertEqual(boundaries[3], "test_methods")

        # Lines 4-6 should be in public_methods section
        self.assertEqual(boundaries[4], "public_methods")
        self.assertEqual(boundaries[5], "public_methods")
        self.assertEqual(boundaries[6], "public_methods")

    def test_find_method_section_boundaries_no_headers(self) -> None:
        """Test boundary mapping when no headers are found."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", section_header="# Test methods"),
            ],
        )

        lines = ["def some_function():", "    pass"]

        boundaries = find_method_section_boundaries(lines, config)
        self.assertEqual(len(boundaries), 0)


class TestMethodValidation(unittest.TestCase):
    """Test method validation against sections."""

    def test_is_method_in_correct_section_correct(self) -> None:
        """Test method validation when methods are in correct sections."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    section_header="# Public methods",
                ),
            ],
        )

        lines = [
            "# Test methods",
            "def test_something():",
            "    pass",
            "# Public methods",
            "def public_method():",
            "    pass",
        ]

        # Test method in test section (correct)
        test_method = extract_node("def test_something(): pass")
        self.assertTrue(is_method_in_correct_section(test_method, 1, lines, config))

        # Public method in public section (correct)
        public_method = extract_node("def public_method(): pass")
        self.assertTrue(is_method_in_correct_section(public_method, 4, lines, config))

    def test_is_method_in_correct_section_incorrect(self) -> None:
        """Test method validation when methods are in wrong sections."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    section_header="# Public methods",
                ),
            ],
        )

        lines = [
            "# Test methods",
            "def public_method():",  # Wrong! Public method in test section
            "    pass",
            "# Public methods",
            "def test_something():",  # Wrong! Test method in public section
            "    pass",
        ]

        # Public method in test section (incorrect)
        public_method = extract_node("def public_method(): pass")
        self.assertFalse(is_method_in_correct_section(public_method, 1, lines, config))

        # Test method in public section (incorrect)
        test_method = extract_node("def test_something(): pass")
        self.assertFalse(is_method_in_correct_section(test_method, 4, lines, config))

    def test_get_expected_section_for_method(self) -> None:
        """Test getting expected section for methods."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        # Test method should go in test_methods section
        test_method = extract_node("def test_something(): pass")
        expected = get_expected_section_for_method(test_method, config)
        self.assertEqual(expected, "test_methods")

        # Public method should go in public_methods section
        public_method = extract_node("def public_method(): pass")
        expected = get_expected_section_for_method(public_method, config)
        self.assertEqual(expected, "public_methods")


class TestSectionViolations(unittest.TestCase):
    """Test section violation detection."""

    def test_get_section_violations(self) -> None:
        """Test detection of section violations."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    section_header="# Public methods",
                ),
            ],
        )

        lines = [
            "# Test methods",
            "def public_method():",  # Violation: public method in test section
            "    pass",
            "# Public methods",
            "def test_something():",  # Violation: test method in public section
            "    pass",
        ]

        methods = [
            extract_node("def public_method(): pass"),
            extract_node("def test_something(): pass"),
        ]
        methods[0].lineno = 2  # public_method at line 2 (in test section)
        methods[1].lineno = 5  # test_something at line 5 (in public section)

        violations = get_section_violations(methods, lines, config)
        self.assertEqual(len(violations), 2)

        # Check first violation
        method1, expected1, actual1 = violations[0]
        self.assertEqual(method1.name, "public_method")
        self.assertEqual(expected1, "public_methods")
        self.assertEqual(actual1, "test_methods")

        # Check second violation
        method2, expected2, actual2 = violations[1]
        self.assertEqual(method2.name, "test_something")
        self.assertEqual(expected2, "test_methods")
        self.assertEqual(actual2, "public_methods")

    def test_get_section_violations_no_violations(self) -> None:
        """Test when there are no section violations."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    section_header="# Public methods",
                ),
            ],
        )

        lines = [
            "# Test methods",
            "def test_something():",
            "    pass",
            "# Public methods",
            "def public_method():",
            "    pass",
        ]

        methods = [
            extract_node("def test_something(): pass"),
            extract_node("def public_method(): pass"),
        ]
        methods[0].lineno = 2  # test_something at line 2 (correct section)
        methods[1].lineno = 5  # public_method at line 5 (correct section)

        violations = get_section_violations(methods, lines, config)
        self.assertEqual(len(violations), 0)

    def test_are_methods_in_correct_sections(self) -> None:
        """Test bulk validation of method sections."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    section_header="# Public methods",
                ),
            ],
        )

        # Test with correct sections
        correct_lines = [
            "# Test methods",
            "def test_something():",
            "    pass",
            "# Public methods",
            "def public_method():",
            "    pass",
        ]

        methods = [
            extract_node("def test_something(): pass"),
            extract_node("def public_method(): pass"),
        ]
        methods[0].lineno = 2
        methods[1].lineno = 5

        self.assertTrue(are_methods_in_correct_sections(methods, correct_lines, config))

        # Test with incorrect sections
        incorrect_lines = [
            "# Test methods",
            "def public_method():",  # Wrong section
            "    pass",
            "# Public methods",
            "def test_something():",  # Wrong section
            "    pass",
        ]

        # Update line numbers for incorrect case
        methods[0].lineno = 5  # test_something at line 5 (in public section - wrong)
        methods[1].lineno = 2  # public_method at line 2 (in test section - wrong)

        self.assertFalse(
            are_methods_in_correct_sections(methods, incorrect_lines, config)
        )


class TestMissingAndEmptyHeaders(unittest.TestCase):
    """Test detection of missing and empty section headers."""

    def test_find_missing_section_headers(self) -> None:
        """Test detection of missing required section headers."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    section_header="# Public methods",
                ),
            ],
        )

        # Lines with only public header, missing test header
        lines = [
            "# Public methods",
            "def public_method():",
            "    pass",
            "def test_something():",  # Test method but no test header
            "    pass",
        ]

        methods = [
            extract_node("def public_method(): pass"),
            extract_node("def test_something(): pass"),
        ]

        missing = find_missing_section_headers(methods, lines, config)
        self.assertEqual(missing, ["test_methods"])

    def test_find_empty_section_headers(self) -> None:
        """Test detection of empty section headers."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    section_header="# Public methods",
                ),
            ],
        )

        # Lines with test header but no test methods
        lines = [
            "# Test methods",  # Empty section
            "# Public methods",
            "def public_method():",
            "    pass",
        ]

        methods = [
            extract_node("def public_method(): pass"),
        ]

        empty = find_empty_section_headers(methods, lines, config)
        self.assertEqual(empty, ["test_methods"])


class TestCheckerIntegration(unittest.TestCase):
    """Test integration with the PyLint checker."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.checker = FunctionSortChecker.__new__(FunctionSortChecker)
        # Don't call __init__ to avoid linter setup

    def test_validate_sections_with_mock_file(self) -> None:
        """Test section validation with a temporary file."""
        # Create a temporary file with section violations
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            content = '''"""Test module with section violations."""

# Test methods
def public_method():
    """This should be in public section."""
    pass

# Public methods
def test_something():
    """This should be in test section."""
    pass
'''
            temp_file.write(content)
            temp_file.flush()

            temp_path = Path(temp_file.name)

        try:
            # Parse the content
            import astroid

            module = astroid.parse(content)
            functions = [
                node for node in module.body if isinstance(node, astroid.FunctionDef)
            ]

            # Mock the linter
            mock_linter = Mock()
            mock_linter.current_file = str(temp_path)
            mock_linter.config.enforce_section_headers = True
            mock_linter.config.require_section_headers = False
            mock_linter.config.allow_empty_sections = True
            mock_linter.config.enable_method_categories = True
            mock_linter.config.framework_preset = None
            mock_linter.config.method_categories = None
            mock_linter.config.category_sorting = "alphabetical"

            self.checker.linter = mock_linter

            # Collect messages
            messages: list[Any] = []
            self.checker.add_message = (  # type: ignore[method-assign]
                lambda *args, **kwargs: messages.append((args, kwargs))
            )

            # Test the validation
            self.checker._validate_function_sections(functions, module)

            # Should detect violations
            self.assertGreater(len(messages), 0)
            # Should contain method-wrong-section messages
            violation_messages = [
                msg for msg in messages if msg[0][0] == "method-wrong-section"
            ]
            self.assertGreater(len(violation_messages), 0)

        finally:
            # Clean up
            temp_path.unlink()

    def test_validate_sections_no_file(self) -> None:
        """Test section validation when file doesn't exist."""
        import astroid

        module = astroid.parse("def test(): pass")
        functions = [
            node for node in module.body if isinstance(node, astroid.FunctionDef)
        ]

        # Mock linter with non-existent file
        mock_linter = Mock()
        mock_linter.current_file = "/non/existent/file.py"
        mock_linter.config.enforce_section_headers = True

        self.checker.linter = mock_linter

        # Should not crash and not generate messages
        messages: list[Any] = []
        self.checker.add_message = (  # type: ignore[method-assign]
            lambda *args, **kwargs: messages.append((args, kwargs))
        )

        self.checker._validate_function_sections(functions, module)
        self.assertEqual(len(messages), 0)

    def test_get_module_path_with_invalid_path(self) -> None:
        """Test _get_module_path with invalid path to trigger error handling."""
        # Test with object that can't be converted to Path
        mock_linter = Mock()
        mock_linter.current_file = 123  # Invalid type that will cause TypeError
        self.checker.linter = mock_linter

        result = self.checker._get_module_path()
        self.assertIsNone(result)

    def test_validate_sections_with_missing_config_attrs(self) -> None:
        """Test section validation with missing configuration attributes."""
        import astroid

        module = astroid.parse("def test(): pass")
        functions = [
            node for node in module.body if isinstance(node, astroid.FunctionDef)
        ]

        # Mock linter without certain config attributes
        mock_linter = Mock()
        mock_linter.current_file = None
        # Remove specific attributes to test getattr defaults
        if hasattr(mock_linter.config, "require_section_headers"):
            delattr(mock_linter.config, "require_section_headers")
        if hasattr(mock_linter.config, "allow_empty_sections"):
            delattr(mock_linter.config, "allow_empty_sections")

        self.checker.linter = mock_linter

        messages: list[Any] = []
        self.checker.add_message = (  # type: ignore[method-assign]
            lambda *args, **kwargs: messages.append((args, kwargs))
        )

        # Should handle missing attributes gracefully
        self.checker._validate_function_sections(functions, module)
        self.assertEqual(len(messages), 0)

    def test_validate_sections_with_require_headers_enabled(self) -> None:
        """Test section validation with require_section_headers enabled."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            content = '''"""Test module missing section headers."""

def test_something():
    """A test method with no header."""
    pass

def public_method():
    """A public method with no header."""
    pass
'''
            temp_file.write(content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            import astroid

            module = astroid.parse(content)
            functions = [
                node for node in module.body if isinstance(node, astroid.FunctionDef)
            ]

            # Mock linter with require_section_headers enabled
            mock_linter = Mock()
            mock_linter.current_file = str(temp_path)
            mock_linter.config.enforce_section_headers = True
            mock_linter.config.require_section_headers = True  # Enable required headers
            mock_linter.config.allow_empty_sections = True
            mock_linter.config.enable_method_categories = True
            mock_linter.config.framework_preset = None
            mock_linter.config.method_categories = None
            mock_linter.config.category_sorting = "alphabetical"

            self.checker.linter = mock_linter

            messages: list[Any] = []
            self.checker.add_message = (  # type: ignore[method-assign]
                lambda *args, **kwargs: messages.append((args, kwargs))
            )

            self.checker._validate_function_sections(functions, module)

            # Should detect missing section headers
            missing_header_messages = [
                msg for msg in messages if msg[0][0] == "missing-section-header"
            ]
            self.assertGreater(len(missing_header_messages), 0)

        finally:
            temp_path.unlink()

    def test_validate_sections_with_disallow_empty_sections(self) -> None:
        """Test section validation with allow_empty_sections disabled."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            content = '''"""Test module with empty sections."""

# Test methods
# Empty section - no test methods

# Public methods
def public_method():
    """A public method."""
    pass
'''
            temp_file.write(content)
            temp_file.flush()
            temp_path = Path(temp_file.name)

        try:
            import astroid

            module = astroid.parse(content)
            functions = [
                node for node in module.body if isinstance(node, astroid.FunctionDef)
            ]

            # Mock linter with allow_empty_sections disabled and proper category config
            mock_linter = Mock()
            mock_linter.current_file = str(temp_path)
            mock_linter.config.enforce_section_headers = True
            mock_linter.config.require_section_headers = False
            mock_linter.config.allow_empty_sections = False  # Disable empty sections
            mock_linter.config.enable_method_categories = True
            mock_linter.config.framework_preset = (
                "pytest"  # Use pytest preset to have test methods category
            )
            mock_linter.config.method_categories = None
            mock_linter.config.category_sorting = "alphabetical"

            self.checker.linter = mock_linter

            messages: list[Any] = []
            self.checker.add_message = (  # type: ignore[method-assign]
                lambda *args, **kwargs: messages.append((args, kwargs))
            )

            self.checker._validate_function_sections(functions, module)

            # Should detect empty section headers
            empty_header_messages = [
                msg for msg in messages if msg[0][0] == "empty-section-header"
            ]
            self.assertGreater(len(empty_header_messages), 0)

        finally:
            temp_path.unlink()


if __name__ == "__main__":
    unittest.main()
