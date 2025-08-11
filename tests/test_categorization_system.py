"""Tests for the method categorization system.

This module tests the new flexible method categorization system including:
- CategoryConfig and MethodCategory data structures
- categorize_method() function
- Pattern matching (name patterns and decorators)
- Priority resolution and conflict handling
- Framework presets
- Configuration loading and validation
"""

import json
import unittest
from unittest.mock import Mock

from astroid import extract_node  # type: ignore[import-untyped]

from pylint_sort_functions.checker import FunctionSortChecker
from pylint_sort_functions.utils import (
    CategoryConfig,
    MethodCategory,
    _are_categories_properly_ordered,
    _get_category_match_priority,
    _get_function_categories,
    _method_name_matches_pattern,
    are_functions_sorted_with_exclusions,
    categorize_method,
)


class TestMethodCategory(unittest.TestCase):
    """Test MethodCategory data structure."""

    def test_method_category_creation(self) -> None:
        """Test creating a MethodCategory with all parameters."""
        category = MethodCategory(
            name="test_methods",
            patterns=["test_*"],
            decorators=["@pytest.fixture"],
            priority=10,
            section_header="# Test Methods",
        )

        self.assertEqual(category.name, "test_methods")
        self.assertEqual(category.patterns, ["test_*"])
        self.assertEqual(category.decorators, ["@pytest.fixture"])
        self.assertEqual(category.priority, 10)
        self.assertEqual(category.section_header, "# Test Methods")

    def test_method_category_defaults(self) -> None:
        """Test MethodCategory with default values."""
        category = MethodCategory(name="simple")

        self.assertEqual(category.name, "simple")
        self.assertEqual(category.patterns, [])
        self.assertEqual(category.decorators, [])
        self.assertEqual(category.priority, 0)
        self.assertEqual(category.section_header, "")


class TestCategoryConfig(unittest.TestCase):
    """Test CategoryConfig data structure."""

    def test_category_config_defaults(self) -> None:
        """Test CategoryConfig with default values."""
        config = CategoryConfig()

        self.assertEqual(config.default_category, "public_methods")
        self.assertFalse(config.enable_categories)
        self.assertEqual(config.category_sorting, "alphabetical")

        # Should have default categories
        self.assertEqual(len(config.categories), 2)
        category_names = [cat.name for cat in config.categories]
        self.assertIn("public_methods", category_names)
        self.assertIn("private_methods", category_names)

    def test_category_config_custom(self) -> None:
        """Test CategoryConfig with custom values."""
        custom_categories = [
            MethodCategory(name="properties", decorators=["@property"]),
            MethodCategory(name="methods", patterns=["*"]),
        ]

        config = CategoryConfig(
            categories=custom_categories,
            default_category="methods",
            enable_categories=True,
            category_sorting="declaration",
        )

        self.assertEqual(config.categories, custom_categories)
        self.assertEqual(config.default_category, "methods")
        self.assertTrue(config.enable_categories)
        self.assertEqual(config.category_sorting, "declaration")

    def test_get_default_categories(self) -> None:
        """Test the default category generation."""
        config = CategoryConfig()
        categories = config._get_default_categories()

        self.assertEqual(len(categories), 2)

        # Check public methods category
        public_cat = next(cat for cat in categories if cat.name == "public_methods")
        self.assertEqual(public_cat.patterns, ["*"])
        self.assertEqual(public_cat.priority, 0)

        # Check private methods category
        private_cat = next(cat for cat in categories if cat.name == "private_methods")
        self.assertEqual(private_cat.patterns, ["_*"])
        self.assertEqual(private_cat.priority, 1)


class TestPatternMatching(unittest.TestCase):
    """Test pattern matching functionality."""

    def test_method_name_matches_pattern(self) -> None:
        """Test name pattern matching with glob patterns."""
        # Test exact match
        self.assertTrue(_method_name_matches_pattern("test_example", "test_example"))

        # Test wildcard patterns
        self.assertTrue(_method_name_matches_pattern("test_example", "test_*"))
        self.assertTrue(_method_name_matches_pattern("setUp", "*Up"))
        self.assertTrue(_method_name_matches_pattern("mousePressEvent", "*Event"))

        # Test non-matches
        self.assertFalse(_method_name_matches_pattern("example_test", "test_*"))
        self.assertFalse(_method_name_matches_pattern("public_method", "_*"))

        # Test catch-all pattern
        self.assertTrue(_method_name_matches_pattern("anything", "*"))

    def test_get_category_match_priority(self) -> None:
        """Test priority calculation for pattern matching."""
        func = extract_node("def test_example(): pass")

        # Test decorator pattern (highest priority)
        decorator_category = MethodCategory(name="properties", decorators=["@property"])
        # No decorators on func, so no match
        self.assertEqual(_get_category_match_priority(func, decorator_category), 0)

        # Test specific name pattern (medium priority)
        name_category = MethodCategory(name="test_methods", patterns=["test_*"])
        self.assertEqual(_get_category_match_priority(func, name_category), 50)

        # Test catch-all pattern (low priority)
        catchall_category = MethodCategory(name="public_methods", patterns=["*"])
        self.assertEqual(_get_category_match_priority(func, catchall_category), 1)

        # Test no match
        no_match_category = MethodCategory(name="private_methods", patterns=["_*"])
        self.assertEqual(_get_category_match_priority(func, no_match_category), 0)


class TestCategorizeMethod(unittest.TestCase):
    """Test the categorize_method function."""

    def test_categorize_method_backward_compatibility(self) -> None:
        """Test categorize_method with categories disabled (backward compatibility)."""
        config = CategoryConfig(enable_categories=False)

        # Test public function
        public_func = extract_node("def public_method(): pass")
        result = categorize_method(public_func, config)
        self.assertEqual(result, "public_methods")

        # Test private function
        private_func = extract_node("def _private_method(): pass")
        result = categorize_method(private_func, config)
        self.assertEqual(result, "private_methods")

    def test_categorize_method_with_categories(self) -> None:
        """Test categorize_method with custom categories enabled."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"], priority=10),
                MethodCategory(name="public_methods", patterns=["*"], priority=1),
                MethodCategory(name="private_methods", patterns=["_*"], priority=2),
            ],
        )

        # Test method matching test pattern
        test_func = extract_node("def test_something(): pass")
        result = categorize_method(test_func, config)
        self.assertEqual(result, "test_methods")

        # Test private method
        private_func = extract_node("def _helper(): pass")
        result = categorize_method(private_func, config)
        self.assertEqual(result, "private_methods")

        # Test public method (fallback to catch-all)
        public_func = extract_node("def regular_method(): pass")
        result = categorize_method(public_func, config)
        self.assertEqual(result, "public_methods")

    def test_categorize_method_priority_resolution(self) -> None:
        """Test that higher priority categories win conflicts."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="low_priority", patterns=["test_*"], priority=1),
                MethodCategory(name="high_priority", patterns=["test_*"], priority=10),
            ],
        )

        test_func = extract_node("def test_conflict(): pass")
        result = categorize_method(test_func, config)
        self.assertEqual(result, "high_priority")

    def test_categorize_method_default_category(self) -> None:
        """Test fallback to default category when no patterns match."""
        config = CategoryConfig(
            enable_categories=True,
            default_category="fallback",
            categories=[MethodCategory(name="specific", patterns=["special_*"])],
        )

        normal_func = extract_node("def normal_method(): pass")
        result = categorize_method(normal_func, config)
        self.assertEqual(result, "fallback")

    def test_categorize_method_no_config(self) -> None:
        """Test categorize_method with no config provided."""
        func = extract_node("def public_method(): pass")
        result = categorize_method(func, None)
        self.assertEqual(result, "public_methods")


class TestCategoryOrdering(unittest.TestCase):
    """Test category ordering validation."""

    def test_are_categories_properly_ordered_correct(self) -> None:
        """Test with correctly ordered functions."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
                MethodCategory(name="private_methods", patterns=["_*"]),
            ],
        )

        functions = [
            extract_node("def test_something(): pass"),  # test_methods
            extract_node("def public_method(): pass"),  # public_methods
            extract_node("def _private_method(): pass"),  # private_methods
        ]

        result = _are_categories_properly_ordered(functions, config)
        self.assertTrue(result)

    def test_are_categories_properly_ordered_incorrect(self) -> None:
        """Test with incorrectly ordered functions."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
                MethodCategory(name="private_methods", patterns=["_*"]),
            ],
        )

        functions = [
            extract_node("def public_method(): pass"),  # public_methods
            extract_node(
                "def test_something(): pass"
            ),  # test_methods (should come first)
            extract_node("def _private_method(): pass"),  # private_methods
        ]

        result = _are_categories_properly_ordered(functions, config)
        self.assertFalse(result)

    def test_are_categories_properly_ordered_empty(self) -> None:
        """Test with empty function list."""
        config = CategoryConfig()
        result = _are_categories_properly_ordered([], config)
        self.assertTrue(result)


class TestFunctionCategories(unittest.TestCase):
    """Test function categorization grouping."""

    def test_get_function_categories(self) -> None:
        """Test grouping functions by categories."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
                MethodCategory(name="private_methods", patterns=["_*"]),
            ],
        )

        functions = [
            extract_node("def test_one(): pass"),
            extract_node("def test_two(): pass"),
            extract_node("def public_method(): pass"),
            extract_node("def _private_method(): pass"),
        ]

        categories = _get_function_categories(functions, config)

        self.assertEqual(len(categories["test_methods"]), 2)
        self.assertEqual(len(categories["public_methods"]), 1)
        self.assertEqual(len(categories["private_methods"]), 1)

        # Verify function names
        test_names = [f.name for f in categories["test_methods"]]
        self.assertIn("test_one", test_names)
        self.assertIn("test_two", test_names)


class TestSortingIntegration(unittest.TestCase):
    """Test integration with existing sorting functions."""

    def test_are_functions_sorted_with_exclusions_with_config(self) -> None:
        """Test sorting validation with CategoryConfig."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
                MethodCategory(name="private_methods", patterns=["_*"]),
            ],
        )

        # Correctly sorted functions
        correct_functions = [
            extract_node("def test_a(): pass"),
            extract_node("def test_b(): pass"),
            extract_node("def public_a(): pass"),
            extract_node("def public_b(): pass"),
            extract_node("def _private_a(): pass"),
            extract_node("def _private_b(): pass"),
        ]

        result = are_functions_sorted_with_exclusions(correct_functions, [], config)
        self.assertTrue(result)

        # Incorrectly sorted functions (wrong category order)
        incorrect_functions = [
            extract_node("def public_a(): pass"),  # public before test
            extract_node("def test_a(): pass"),
            extract_node("def _private_a(): pass"),
        ]

        result = are_functions_sorted_with_exclusions(incorrect_functions, [], config)
        self.assertFalse(result)

    def test_are_functions_sorted_backward_compatibility(self) -> None:
        """Test that sorting works with categories disabled."""
        config = CategoryConfig(enable_categories=False)

        # Correctly sorted functions (public then private)
        correct_functions = [
            extract_node("def public_b(): pass"),
            extract_node("def public_a(): pass"),  # Should be alphabetical
            extract_node("def _private_b(): pass"),
            extract_node("def _private_a(): pass"),  # Should be alphabetical
        ]

        # This should fail because within each group, they're not alphabetical
        result = are_functions_sorted_with_exclusions(correct_functions, [], config)
        self.assertFalse(result)

        # Now with proper alphabetical order
        proper_functions = [
            extract_node("def public_a(): pass"),
            extract_node("def public_b(): pass"),
            extract_node("def _private_a(): pass"),
            extract_node("def _private_b(): pass"),
        ]

        result = are_functions_sorted_with_exclusions(proper_functions, [], config)
        self.assertTrue(result)


class TestCheckerIntegration(unittest.TestCase):
    """Test integration with FunctionSortChecker."""

    def test_get_category_config_basic(self) -> None:
        """Test basic category config creation from checker."""
        # Create mock linter config
        mock_config = Mock()
        mock_config.enable_method_categories = False
        mock_config.category_sorting = "alphabetical"
        mock_config.framework_preset = None
        mock_config.method_categories = None

        mock_linter = Mock()
        mock_linter.config = mock_config

        # Create checker instance (bypass __init__)
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        config = checker._get_category_config()

        self.assertFalse(config.enable_categories)
        self.assertEqual(config.category_sorting, "alphabetical")
        self.assertEqual(len(config.categories), 2)  # Default categories

    def test_get_framework_preset_categories_pytest(self) -> None:
        """Test pytest preset category loading."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        categories = checker._get_framework_preset_categories("pytest")

        category_names = [cat.name for cat in categories]
        self.assertIn("test_fixtures", category_names)
        self.assertIn("test_methods", category_names)
        self.assertIn("public_methods", category_names)
        self.assertIn("private_methods", category_names)

        # Test specific patterns
        test_fixtures = next(cat for cat in categories if cat.name == "test_fixtures")
        self.assertIn("setUp", test_fixtures.patterns)
        self.assertIn("tearDown", test_fixtures.patterns)

    def test_get_framework_preset_categories_pyqt(self) -> None:
        """Test PyQt preset category loading."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        categories = checker._get_framework_preset_categories("pyqt")

        category_names = [cat.name for cat in categories]
        self.assertIn("initialization", category_names)
        self.assertIn("properties", category_names)
        self.assertIn("event_handlers", category_names)

        # Test specific patterns and decorators
        props = next(cat for cat in categories if cat.name == "properties")
        self.assertIn("@property", props.decorators)

        events = next(cat for cat in categories if cat.name == "event_handlers")
        self.assertIn("*Event", events.patterns)

    def test_get_framework_preset_categories_invalid(self) -> None:
        """Test error handling for invalid preset names."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        with self.assertRaises(ValueError) as context:
            checker._get_framework_preset_categories("invalid_preset")

        self.assertIn("Unknown framework preset", str(context.exception))
        self.assertIn("pytest", str(context.exception))  # Should list available

    def test_parse_method_categories_json_valid(self) -> None:
        """Test valid JSON configuration parsing."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        json_config = """[
            {
                "name": "properties",
                "decorators": ["@property", "@*.setter"],
                "priority": 5,
                "section_header": "# Properties"
            },
            {
                "name": "public_methods",
                "patterns": ["*"],
                "priority": 1
            }
        ]"""

        categories = checker._parse_method_categories_json(json_config)

        self.assertEqual(len(categories), 2)

        props = next(cat for cat in categories if cat.name == "properties")
        self.assertEqual(props.decorators, ["@property", "@*.setter"])
        self.assertEqual(props.priority, 5)
        self.assertEqual(props.section_header, "# Properties")

        methods = next(cat for cat in categories if cat.name == "public_methods")
        self.assertEqual(methods.patterns, ["*"])
        self.assertEqual(methods.priority, 1)

    def test_parse_method_categories_json_invalid_syntax(self) -> None:
        """Test error handling for invalid JSON syntax."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        invalid_json = '{"invalid": json syntax}'

        with self.assertRaises(json.JSONDecodeError):
            checker._parse_method_categories_json(invalid_json)

    def test_parse_method_categories_json_invalid_structure(self) -> None:
        """Test error handling for invalid JSON structure."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        # Not an array
        invalid_structure = '{"categories": []}'

        with self.assertRaises(ValueError) as context:
            checker._parse_method_categories_json(invalid_structure)

        self.assertIn("must be a JSON array", str(context.exception))

    def test_parse_method_categories_json_missing_name(self) -> None:
        """Test error handling for categories missing required name field."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        missing_name = '[{"patterns": ["test_*"]}]'

        with self.assertRaises(ValueError) as context:
            checker._parse_method_categories_json(missing_name)

        self.assertIn("missing required 'name' field", str(context.exception))

    def test_parse_method_categories_json_invalid_dict(self) -> None:
        """Test error handling for non-dict categories."""
        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        invalid_dict = '[{"name": "valid"}, "not a dict"]'

        with self.assertRaises(ValueError) as context:
            checker._parse_method_categories_json(invalid_dict)

        self.assertIn("Category 1 must be a JSON object", str(context.exception))

    def test_parse_method_categories_json_category_creation_error(self) -> None:
        """Test error handling for MethodCategory creation errors."""
        from unittest.mock import patch

        mock_linter = Mock()
        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        # Mock MethodCategory constructor to raise an exception during creation
        with patch("pylint_sort_functions.checker.MethodCategory") as mock_category:
            mock_category.side_effect = TypeError(
                "Mock MethodCategory creation failure"
            )

            invalid_category = '[{"name": "test"}]'

            with self.assertRaises(ValueError) as context:
                checker._parse_method_categories_json(invalid_category)

            # Should cover checker.py:474-475
            self.assertIn("Invalid category 0 (test)", str(context.exception))
            self.assertIn(
                "Mock MethodCategory creation failure", str(context.exception)
            )

    def test_get_category_config_with_error_handling(self) -> None:
        """Test configuration loading with error handling."""
        # Create mock linter config with invalid JSON
        mock_config = Mock()
        mock_config.enable_method_categories = True
        mock_config.category_sorting = "alphabetical"
        mock_config.framework_preset = None
        mock_config.method_categories = '{"invalid": "json"}'  # Invalid JSON array

        mock_linter = Mock()
        mock_linter.config = mock_config

        checker = FunctionSortChecker.__new__(FunctionSortChecker)
        checker.linter = mock_linter

        # This should not raise an exception, but use defaults
        config = checker._get_category_config()

        # Should have default categories despite configuration error
        self.assertEqual(len(config.categories), 2)
        self.assertTrue(config.enable_categories)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases for categorization system."""

    def test_decorator_pattern_matching(self) -> None:
        """Test decorator pattern matching priority."""
        func = extract_node("""
        @property
        def some_property(self):  #@
            pass
        """)

        category = MethodCategory(
            name="properties", decorators=["@property"], priority=10
        )

        priority = _get_category_match_priority(func, category)
        self.assertEqual(priority, 100)  # 100 for decorator match

    def test_category_sorting_declaration_order(self) -> None:
        """Test category sorting with declaration order."""
        config = CategoryConfig(
            enable_categories=True,
            category_sorting="declaration",
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        # Any order should be considered sorted when using declaration order
        functions = [
            extract_node("def test_b(): pass"),
            extract_node("def test_a(): pass"),  # Not alphabetical but should be OK
            extract_node("def public_b(): pass"),
            extract_node("def public_a(): pass"),  # Not alphabetical but should be OK
        ]

        result = are_functions_sorted_with_exclusions(functions, [], config)
        self.assertTrue(result)

    def test_category_ordering_violations(self) -> None:
        """Test detection of category ordering violations."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        # Functions with categories mixed up
        functions = [
            extract_node("def public_method(): pass"),  # public first
            extract_node("def test_method(): pass"),  # test second (wrong order)
            extract_node("def public_method2(): pass"),  # public third (mixed)
        ]

        result = _are_categories_properly_ordered(functions, config)
        self.assertFalse(result)

    def test_category_ordering_mixed_categories(self) -> None:
        """Test category ordering with mixed categories that appear multiple times."""
        config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        # Functions where same categories appear out of order
        functions = [
            extract_node("def test_a(): pass"),  # test_methods (index 0)
            extract_node("def public_a(): pass"),  # public_methods (index 1)
            extract_node(
                "def test_b(): pass"
            ),  # test_methods back to index 0 (violation!)
        ]

        result = _are_categories_properly_ordered(functions, config)
        self.assertFalse(result)  # Should cover utils.py:972

    def test_category_sorting_alphabetical_violations(self) -> None:
        """Test detection of non-alphabetical sorting within categories."""
        config = CategoryConfig(
            enable_categories=True,
            category_sorting="alphabetical",
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        # Functions with incorrect alphabetical order within category
        functions = [
            extract_node(
                "def test_zebra(): pass"
            ),  # test methods - wrong alphabetical order
            extract_node("def test_alpha(): pass"),  # test methods - should come first
            extract_node(
                "def public_method(): pass"
            ),  # public methods - correctly ordered
        ]

        result = are_functions_sorted_with_exclusions(functions, [], config)
        self.assertFalse(result)  # Should cover utils.py:601


if __name__ == "__main__":
    unittest.main()
