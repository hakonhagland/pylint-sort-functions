"""Math utilities module - imports from calculator."""

from src.calculator import format_result


def display_calculation_result(value):
    """Display a formatted calculation result."""
    formatted = format_result(value, precision=3)
    print(f"Result: {formatted}")


def unused_helper_function():
    """This function is only used within this module."""
    return "This should be made private"
