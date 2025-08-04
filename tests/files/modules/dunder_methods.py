"""Module with dunder methods - should not be flagged."""


def __get_something__() -> str:
    """Special dunder method with get pattern - should not be flagged."""
    return "test"


def get_helper() -> str:
    """Helper function used internally."""
    return __get_something__()  # Uses dunder method
