#!/usr/bin/env python3
"""
Test suite for decorator exclusion functionality.

This module tests the new framework-aware sorting that excludes functions
with specific decorators from sorting requirements.
"""

import astroid
import pytest
from astroid import nodes

from pylint_sort_functions.utils import (
    are_functions_sorted_with_exclusions,
    are_methods_sorted_with_exclusions,
    decorator_matches_pattern,
    function_has_excluded_decorator,
    get_decorator_strings,
)


def parse_function_from_code(code: str) -> nodes.FunctionDef:
    """Helper to parse a function from Python code string."""
    module = astroid.parse(code)
    # Find the first function definition
    for node in module.body:
        if isinstance(node, nodes.FunctionDef):
            return node
    raise ValueError("No function found in code")


def parse_functions_from_code(code: str) -> list[nodes.FunctionDef]:
    """Helper to parse all functions from Python code string."""
    module = astroid.parse(code)
    functions = []
    for node in module.body:
        if isinstance(node, nodes.FunctionDef):
            functions.append(node)
    return functions


def test_parse_function_error():
    """Test that parse_function_from_code raises ValueError when no function found."""
    code = """
# This is just a comment, no functions
x = 42
"""
    with pytest.raises(ValueError, match="No function found in code"):
        parse_function_from_code(code)


class TestDecoratorMatching:
    """Test decorator pattern matching functionality."""

    def test_exact_match(self):
        """Test exact decorator pattern matching."""
        assert decorator_matches_pattern("@main.command", "@main.command")
        assert decorator_matches_pattern("@main.command()", "@main.command")
        assert decorator_matches_pattern("@main.command", "@main.command()")
        assert not decorator_matches_pattern("@main.other", "@main.command")

    def test_wildcard_matching(self):
        """Test wildcard pattern matching."""
        assert decorator_matches_pattern("@main.command", "@*.command")
        assert decorator_matches_pattern("@app.command", "@*.command")
        assert decorator_matches_pattern("@cli.command", "@*.command")
        assert not decorator_matches_pattern("@main.other", "@*.command")

    def test_pattern_normalization(self):
        """Test that patterns are normalized correctly."""
        # Patterns should work with or without @ prefix
        assert decorator_matches_pattern("@main.command", "main.command")
        assert decorator_matches_pattern("@main.command", "@main.command")

    def test_complex_patterns(self):
        """Test complex decorator patterns."""
        assert decorator_matches_pattern("@app.route", "@app.*")
        assert decorator_matches_pattern("@app.get", "@app.*")
        assert decorator_matches_pattern("@app.post", "@app.*")
        assert not decorator_matches_pattern("@other.route", "@app.*")


class TestDecoratorExtraction:
    """Test decorator string extraction from AST nodes."""

    def test_simple_decorator(self):
        """Test extraction of simple decorators."""
        code = """
@property
def test_func():
    pass
"""
        func = parse_function_from_code(code)
        decorators = get_decorator_strings(func)
        assert decorators == ["@property"]

    def test_attribute_decorator(self):
        """Test extraction of attribute decorators."""
        code = """
@main.command
def test_func():
    pass
"""
        func = parse_function_from_code(code)
        decorators = get_decorator_strings(func)
        assert decorators == ["@main.command"]

    def test_call_decorator(self):
        """Test extraction of call decorators."""
        code = """
@main.command()
def test_func():
    pass
"""
        func = parse_function_from_code(code)
        decorators = get_decorator_strings(func)
        assert decorators == ["@main.command()"]

    def test_multiple_decorators(self):
        """Test extraction of multiple decorators."""
        code = """
@property
@main.command()
def test_func():
    pass
"""
        func = parse_function_from_code(code)
        decorators = get_decorator_strings(func)
        assert "@property" in decorators
        assert "@main.command()" in decorators

    def test_no_decorators(self):
        """Test function with no decorators."""
        code = """
def test_func():
    pass
"""
        func = parse_function_from_code(code)
        decorators = get_decorator_strings(func)
        assert decorators == []

    def test_nested_attribute_decorator(self):
        """Test extraction of nested attribute decorators."""
        # This tests the more complex nested attribute case
        # We'll create a mock decorator node structure for this
        code = """
@deeply.nested.attribute
def test_func():
    pass
"""
        func = parse_function_from_code(code)
        decorators = get_decorator_strings(func)
        assert "@deeply.nested.attribute" in decorators

    def test_complex_decorator_fallback(self):
        """Test fallback handling for complex decorators."""
        # Create a complex decorator that should trigger the fallback
        from pylint_sort_functions.utils import _decorator_node_to_string

        # Create a mock complex decorator node that doesn't match our patterns
        class MockComplexDecorator:  # pylint: disable=too-few-public-methods
            """Mock decorator for testing fallback behavior."""

        mock_decorator = MockComplexDecorator()
        result = _decorator_node_to_string(mock_decorator)
        assert result == ""  # Should return empty string for unknown types


class TestFunctionExclusion:
    """Test function exclusion based on decorators."""

    def test_exclude_click_command(self):
        """Test exclusion of Click command functions."""
        code = """
@main.command()
def create():
    pass
"""
        func = parse_function_from_code(code)
        ignore_patterns = ["@main.command"]

        assert function_has_excluded_decorator(func, ignore_patterns)

    def test_exclude_flask_route(self):
        """Test exclusion of Flask route functions."""
        code = """
@app.route('/')
def index():
    return 'Hello'
"""
        func = parse_function_from_code(code)
        ignore_patterns = ["@app.route"]

        assert function_has_excluded_decorator(func, ignore_patterns)

    def test_exclude_with_wildcard(self):
        """Test exclusion using wildcard patterns."""
        code = """
@main.command()
def create():
    pass
"""
        func = parse_function_from_code(code)
        ignore_patterns = ["@*.command"]

        assert function_has_excluded_decorator(func, ignore_patterns)

    def test_no_exclusion(self):
        """Test function that should not be excluded."""
        code = """
@property
def some_property():
    pass
"""
        func = parse_function_from_code(code)
        ignore_patterns = ["@main.command"]

        assert not function_has_excluded_decorator(func, ignore_patterns)

    def test_empty_ignore_list(self):
        """Test with empty ignore list."""
        code = """
@main.command()
def create():
    pass
"""
        func = parse_function_from_code(code)
        ignore_patterns = []

        assert not function_has_excluded_decorator(func, ignore_patterns)


class TestSortingWithExclusions:
    """Test sorting functions with decorator exclusions."""

    def test_click_example_sorting(self):
        """Test Click application with decorator exclusions."""
        code = """
def helper():
    pass

def main():
    pass

@main.command()
def create():
    pass

@main.command()
def delete():
    pass
"""
        functions = parse_functions_from_code(code)
        ignore_patterns = ["@main.command"]

        # Without exclusions, this would fail (not alphabetical)
        # With exclusions, only helper and main are checked (alphabetical order)
        assert are_functions_sorted_with_exclusions(functions, ignore_patterns)

    def test_mixed_decorators(self):
        """Test with mix of excluded and non-excluded functions."""
        code = """
def aaa_function():
    pass

@main.command()
def zzz_command():
    pass

def bbb_function():
    pass

@app.route('/')
def yyy_route():
    pass

def ccc_function():
    pass
"""
        functions = parse_functions_from_code(code)
        ignore_patterns = ["@main.command", "@app.route"]

        # Only aaa_function, bbb_function, ccc_function should be checked for sorting
        # They are in alphabetical order, so this should pass
        assert are_functions_sorted_with_exclusions(functions, ignore_patterns)

    def test_sorting_fails_without_exclusions(self):
        """Test that sorting fails without proper exclusions."""
        code = """
def main():
    pass

@main.command()
def create():
    pass

def helper():
    pass
"""
        functions = parse_functions_from_code(code)

        # Without exclusions, all functions are checked: main, create, helper
        # This is not alphabetical (create should come before helper and main)
        assert not are_functions_sorted_with_exclusions(functions, [])

    def test_all_functions_excluded(self):
        """Test when all functions are excluded."""
        code = """
@main.command()
def create():
    pass

@main.command()
def delete():
    pass
"""
        functions = parse_functions_from_code(code)
        ignore_patterns = ["@main.command"]

        # All functions excluded, so sorting should pass (empty list considered sorted)
        assert are_functions_sorted_with_exclusions(functions, ignore_patterns)

    def test_no_exclusions(self):
        """Test with no exclusions (should behave like original function)."""
        code = """
def aaa():
    pass

def bbb():
    pass

def ccc():
    pass
"""
        functions = parse_functions_from_code(code)

        # Should behave like original are_functions_sorted
        assert are_functions_sorted_with_exclusions(functions, [])
        assert are_functions_sorted_with_exclusions(functions, None)

    def test_methods_with_exclusions(self):
        """Test method sorting with exclusions."""
        code = """
class TestClass:
    def helper_method(self):
        pass

    def main_method(self):
        pass

    @main_method.decorator
    def decorated_method(self):
        pass
"""
        # Parse the class and extract methods
        module = astroid.parse(code)
        class_node = module.body[0]  # Get the class
        methods = [
            node for node in class_node.body if isinstance(node, nodes.FunctionDef)
        ]

        # Test method sorting with exclusions
        ignore_patterns = ["@main_method.decorator"]
        assert are_methods_sorted_with_exclusions(methods, ignore_patterns)


class TestFrameworkExamples:
    """Test real-world framework examples."""

    def test_click_application(self):
        """Test complete Click application example."""
        code = """
import click

@click.group()
def main():
    pass

@main.command()
def create():
    pass

@main.command()
def delete():
    pass

def utility_function():
    pass
"""
        functions = parse_functions_from_code(code)
        ignore_patterns = ["@click.group", "@main.command"]

        # Only utility_function needs correct position relative to others
        assert are_functions_sorted_with_exclusions(functions, ignore_patterns)

    def test_flask_application(self):
        """Test Flask application example."""
        code = """
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return 'Home'

@app.route('/users')
def users():
    return 'Users'

def helper():
    pass
"""
        functions = parse_functions_from_code(code)
        ignore_patterns = ["@app.route"]

        # Only helper function is checked for sorting
        assert are_functions_sorted_with_exclusions(functions, ignore_patterns)

    def test_fastapi_application(self):
        """Test FastAPI application example."""
        code = """
from fastapi import FastAPI
app = FastAPI()

@app.get('/')
def root():
    return {'message': 'Hello World'}

@app.post('/items')
def create_item():
    return {'status': 'created'}

def utility():
    pass
"""
        functions = parse_functions_from_code(code)
        ignore_patterns = ["@app.get", "@app.post", "@app.*"]

        # Only utility function is checked
        assert are_functions_sorted_with_exclusions(functions, ignore_patterns)


if __name__ == "__main__":  # pragma: no cover
    # Run a simple test to verify functionality
    print("Testing decorator exclusion functionality...")

    # Test basic pattern matching
    assert decorator_matches_pattern("@main.command", "@main.command")
    assert decorator_matches_pattern("@main.command", "@*.command")
    print("✓ Pattern matching works")

    # Test Click example
    CODE = """
def helper():
    pass

def main():
    pass

@main.command()
def create():
    pass
"""
    functions = parse_functions_from_code(CODE)
    RESULT = are_functions_sorted_with_exclusions(functions, ["@main.command"])
    assert RESULT
    print("✓ Click example works")

    print("All tests passed! Decorator exclusion functionality is working.")
