"""Module with unsorted functions - should trigger W9001."""


def validate_input(value: str) -> bool:
    """Validate user input."""
    return value.strip() != ""


def calculate_area(width: float, height: float) -> float:
    """Calculate area of rectangle."""
    return width * height


def process_data(data: list[str]) -> list[str]:
    """Process input data."""
    return [item.strip().lower() for item in data]


def _validate_internal(data: dict[str, str]) -> bool:
    """Internal validation function."""
    return len(data) > 0


def _format_output(data: list[str]) -> str:
    """Format data for output."""
    return ", ".join(data)


def _helper_function(value: int) -> int:
    """Helper function for internal use."""
    return value * 2
