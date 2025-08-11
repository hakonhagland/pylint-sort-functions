"""Tests for multi-category auto-fix functionality."""

import unittest

import astroid  # type: ignore[import-untyped]

from pylint_sort_functions.auto_fix import AutoFixConfig, FunctionSorter
from pylint_sort_functions.utils.categorization import CategoryConfig, MethodCategory


class TestAutoFixMultiCategory(unittest.TestCase):
    """Test multi-category auto-fix functionality."""

    def test_multi_category_section_headers_disabled(self) -> None:
        """Test multi-category headers when feature is disabled."""
        config = AutoFixConfig(
            enable_multi_category_headers=False,
            add_section_headers=True,
        )
        sorter = FunctionSorter(config)

        # Create test spans with mixed visibility to trigger headers
        from pylint_sort_functions.auto_fix import FunctionSpan

        # Create sample function nodes - public and private to trigger headers
        func1 = astroid.extract_node("def public_method(): pass")
        func2 = astroid.extract_node("def _private_method(): pass")

        spans = [
            FunctionSpan(func1, 1, 2, "def public_method(): pass\n", "public_method"),
            FunctionSpan(
                func2, 3, 4, "def _private_method(): pass\n", "_private_method"
            ),
        ]

        # Should fall back to original binary headers
        result = sorter._add_multi_category_section_headers_to_functions(
            spans, is_methods=True
        )

        # Should contain traditional section headers when mixed visibility
        result_text = "".join(result)
        self.assertIn("Public methods", result_text)
        self.assertIn("Private methods", result_text)

    def test_multi_category_section_headers_no_config(self) -> None:
        """Test multi-category headers when category_config is None."""
        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=None,  # No category config
            add_section_headers=True,
        )
        sorter = FunctionSorter(config)

        # Create test spans with mixed visibility to trigger headers
        from pylint_sort_functions.auto_fix import FunctionSpan

        # Create sample function nodes - public and private to trigger headers
        func1 = astroid.extract_node("def public_method(): pass")
        func2 = astroid.extract_node("def _private_method(): pass")

        spans = [
            FunctionSpan(func1, 1, 2, "def public_method(): pass\n", "public_method"),
            FunctionSpan(
                func2, 3, 4, "def _private_method(): pass\n", "_private_method"
            ),
        ]

        # Should fall back to original binary headers
        result = sorter._add_multi_category_section_headers_to_functions(
            spans, is_methods=True
        )

        # Should contain traditional section headers when mixed visibility
        result_text = "".join(result)
        self.assertIn("Public methods", result_text)
        self.assertIn("Private methods", result_text)

    def test_multi_category_section_headers_enabled(self) -> None:
        """Test multi-category headers when feature is enabled."""
        category_config = CategoryConfig(
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

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
            add_section_headers=True,
        )
        sorter = FunctionSorter(config)

        # Create test spans
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def test_method(): pass")
        func2 = astroid.extract_node("def public_method(): pass")

        spans = [
            FunctionSpan(func1, 1, 2, "def test_method(): pass\n", "test_method"),
            FunctionSpan(func2, 3, 4, "def public_method(): pass\n", "public_method"),
        ]

        result = sorter._add_multi_category_section_headers_to_functions(
            spans, is_methods=True
        )
        result_text = "".join(result)

        # Should contain category-specific headers
        self.assertIn("# Test methods", result_text)
        self.assertIn("# Public methods", result_text)

    def test_multi_category_section_headers_fallback_header(self) -> None:
        """Test multi-category headers with fallback header generation."""
        category_config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods", patterns=["test_*"], section_header=""
                ),  # Empty header
                MethodCategory(
                    name="special_category", patterns=["special_*"], section_header=""
                ),  # Empty header
            ],
        )

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
            add_section_headers=True,
        )
        sorter = FunctionSorter(config)

        # Create test spans
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def special_function(): pass")
        spans = [
            FunctionSpan(
                func1, 1, 2, "def special_function(): pass\n", "special_function"
            ),
        ]

        result = sorter._add_multi_category_section_headers_to_functions(
            spans, is_methods=True
        )
        result_text = "".join(result)

        # Should contain fallback header (category name converted to title case)
        self.assertIn("# Special Category", result_text)

    def test_multi_category_sorting_disabled(self) -> None:
        """Test multi-category sorting when feature is disabled."""
        config = AutoFixConfig(enable_multi_category_headers=False)
        sorter = FunctionSorter(config)

        # Create test spans
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def zebra_method(): pass")
        func2 = astroid.extract_node("def alpha_method(): pass")

        spans = [
            FunctionSpan(func1, 1, 2, "def zebra_method(): pass\n", "zebra_method"),
            FunctionSpan(func2, 3, 4, "def alpha_method(): pass\n", "alpha_method"),
        ]

        result = sorter._sort_function_spans(spans)

        # Should use binary sorting - alphabetical order
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "alpha_method")
        self.assertEqual(result[1].name, "zebra_method")

    def test_multi_category_sorting_no_config(self) -> None:
        """Test multi-category sorting when category_config is None."""
        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=None,
        )
        sorter = FunctionSorter(config)

        # Create test spans
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def test_method(): pass")
        spans = [FunctionSpan(func1, 1, 2, "def test_method(): pass\n", "test_method")]

        result = sorter._sort_function_spans_by_categories(spans)

        # Should return original spans when no config
        self.assertEqual(result, spans)

    def test_multi_category_sorting_with_categories(self) -> None:
        """Test multi-category sorting with categories defined."""
        category_config = CategoryConfig(
            enable_categories=True,
            category_sorting="alphabetical",
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"], priority=1),
                MethodCategory(name="public_methods", patterns=["*"], priority=0),
            ],
        )

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
        )
        sorter = FunctionSorter(config)

        # Create test spans - mixed order
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def zebra_method(): pass")  # public
        func2 = astroid.extract_node("def test_alpha(): pass")  # test
        func3 = astroid.extract_node("def alpha_method(): pass")  # public
        func4 = astroid.extract_node("def test_zebra(): pass")  # test

        spans = [
            FunctionSpan(func1, 1, 2, "def zebra_method(): pass\n", "zebra_method"),
            FunctionSpan(func2, 3, 4, "def test_alpha(): pass\n", "test_alpha"),
            FunctionSpan(func3, 5, 6, "def alpha_method(): pass\n", "alpha_method"),
            FunctionSpan(func4, 7, 8, "def test_zebra(): pass\n", "test_zebra"),
        ]

        result = sorter._sort_function_spans_by_categories(spans)

        # Should sort by category order, then alphabetically within each category
        # test_methods first (alphabetically: test_alpha, test_zebra)
        # public_methods second (alphabetically: alpha_method, zebra_method)
        self.assertEqual(len(result), 4)
        self.assertEqual(result[0].name, "test_alpha")
        self.assertEqual(result[1].name, "test_zebra")
        self.assertEqual(result[2].name, "alpha_method")
        self.assertEqual(result[3].name, "zebra_method")

    def test_multi_category_sorting_with_excluded_decorators(self) -> None:
        """Test multi-category sorting with excluded decorators."""
        category_config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
            ignore_decorators=["@pytest.fixture"],
        )
        sorter = FunctionSorter(config)

        # Create test spans with excluded decorator
        from pylint_sort_functions.auto_fix import FunctionSpan

        # Mock a function with excluded decorator
        func1_code = """
@pytest.fixture
def setup_data():
    pass
"""
        func1 = astroid.extract_node(func1_code.strip())
        func2 = astroid.extract_node("def alpha_method(): pass")

        spans = [
            FunctionSpan(func1, 1, 4, func1_code, "setup_data"),
            FunctionSpan(func2, 5, 6, "def alpha_method(): pass\n", "alpha_method"),
        ]

        result = sorter._sort_function_spans_by_categories(spans)

        # Excluded function should be at the end
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "alpha_method")  # Sortable first
        self.assertEqual(result[1].name, "setup_data")  # Excluded last

    def test_multi_category_sorting_declaration_order(self) -> None:
        """Test multi-category sorting with declaration order preserved."""
        category_config = CategoryConfig(
            enable_categories=True,
            category_sorting="declaration",  # Preserve declaration order
            categories=[
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
        )
        sorter = FunctionSorter(config)

        # Create test spans in specific order
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def zebra_method(): pass")
        func2 = astroid.extract_node("def alpha_method(): pass")

        spans = [
            FunctionSpan(func1, 1, 2, "def zebra_method(): pass\n", "zebra_method"),
            FunctionSpan(func2, 3, 4, "def alpha_method(): pass\n", "alpha_method"),
        ]

        result = sorter._sort_function_spans_by_categories(spans)

        # Should preserve declaration order (not sort alphabetically)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, "zebra_method")  # Original order preserved
        self.assertEqual(result[1].name, "alpha_method")

    def test_multi_category_headers_with_section_disabled(self) -> None:
        """Test multi-category with headers disabled but multi-category enabled."""
        category_config = CategoryConfig(
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

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
            add_section_headers=False,  # Headers disabled - triggers lines 200-207
        )
        sorter = FunctionSorter(config)

        # Create test spans
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def test_method(): pass")
        func2 = astroid.extract_node("def public_method(): pass")

        spans = [
            FunctionSpan(func1, 1, 2, "def test_method(): pass\n", "test_method"),
            FunctionSpan(func2, 3, 4, "def public_method(): pass\n", "public_method"),
        ]

        result = sorter._add_multi_category_section_headers_to_functions(
            spans, is_methods=True
        )
        result_text = "".join(result)

        # Should NOT contain headers since add_section_headers=False
        self.assertNotIn("# Test methods", result_text)
        self.assertNotIn("# Public methods", result_text)
        # Should contain the function texts
        self.assertIn("def test_method():", result_text)
        self.assertIn("def public_method():", result_text)

    def test_multi_category_headers_with_category_section_headers(self) -> None:
        """Test multi-category headers detection with category-specific headers."""
        category_config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="setup_methods",
                    patterns=["setup_*"],
                    section_header="# Setup methods",
                ),
            ],
        )

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
            add_section_headers=True,
        )
        sorter = FunctionSorter(config)

        # Test section header detection with category-specific headers (covers 696-698)
        # This should trigger the loop in _is_section_header_comment

        # Test standard headers first
        self.assertTrue(sorter._is_section_header_comment("# Public methods"))

        # Test category-specific headers - this should trigger lines 696-698
        self.assertTrue(sorter._is_section_header_comment("# Test methods"))
        self.assertTrue(sorter._is_section_header_comment("# Setup methods"))

        # Test case insensitive matching
        config_case_insensitive = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
            add_section_headers=True,
            section_header_case_sensitive=False,
        )
        sorter_case_insensitive = FunctionSorter(config_case_insensitive)

        # Should match different cases when case sensitivity is disabled
        self.assertTrue(
            sorter_case_insensitive._is_section_header_comment("# test methods")
        )
        self.assertTrue(
            sorter_case_insensitive._is_section_header_comment("# SETUP METHODS")
        )

    def test_multi_category_sort_function_spans_integration(self) -> None:
        """Test _sort_function_spans calls _sort_function_spans_by_categories."""
        category_config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"], priority=1),
                MethodCategory(name="public_methods", patterns=["*"], priority=0),
            ],
        )

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
        )
        sorter = FunctionSorter(config)

        # Create test spans
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def public_method(): pass")
        func2 = astroid.extract_node("def test_something(): pass")

        spans = [
            FunctionSpan(func1, 1, 2, "def public_method(): pass\n", "public_method"),
            FunctionSpan(func2, 3, 4, "def test_something(): pass\n", "test_something"),
        ]

        # This should trigger line 916: return self._sort_function_spans_by_categories
        result = sorter._sort_function_spans(spans)

        # Should be sorted by category priority (test_methods first, public second)
        self.assertEqual(len(result), 2)
        self.assertEqual(
            result[0].name, "test_something"
        )  # test_methods category first
        self.assertEqual(
            result[1].name, "public_method"
        )  # public_methods category second

    def test_multi_category_headers_disabled_newline_handling(self) -> None:
        """Test multi-category with headers disabled and spans without newlines."""
        category_config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"]),
                MethodCategory(name="public_methods", patterns=["*"]),
            ],
        )

        config = AutoFixConfig(
            enable_multi_category_headers=True,
            category_config=category_config,
            add_section_headers=False,  # Headers disabled - triggers lines 200-207
        )
        sorter = FunctionSorter(config)

        # Create test spans
        from pylint_sort_functions.auto_fix import FunctionSpan

        func1 = astroid.extract_node("def test_method(): pass")
        func2 = astroid.extract_node("def public_method(): pass")

        # Create spans without newlines - this should trigger line 205
        spans = [
            FunctionSpan(
                func1, 1, 2, "def test_method(): pass", "test_method"
            ),  # No newline
            FunctionSpan(
                func2, 3, 4, "def public_method(): pass", "public_method"
            ),  # No newline
        ]

        result = sorter._add_multi_category_section_headers_to_functions(
            spans, is_methods=True
        )
        result_text = "".join(result)

        # Should contain the function texts with proper newline spacing
        self.assertIn("def test_method():", result_text)
        self.assertIn("def public_method():", result_text)
        # Should have proper spacing between functions
        self.assertTrue("\n\n" in result_text or result_text.count("\n") >= 2)


if __name__ == "__main__":
    unittest.main()
