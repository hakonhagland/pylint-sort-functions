"""Module with sorted public functions but unsorted private functions."""


def calculate_area(width: float, height: float) -> float:
    """Calculate area of rectangle."""
    return width * height


def process_data(data: list[str]) -> list[str]:
    """Process input data."""
    return [item.strip().lower() for item in data]


def validate_input(value: str) -> bool:
    """Validate user input."""
    return value.strip() != ""


def _validate_internal(data: dict[str, str]) -> bool:
    """Internal validation function."""
    return len(data) > 0


def _helper_function(value: int) -> int:
    """Helper function for internal use."""
    return value * 2


def _format_output(data: list[str]) -> str:
    """Format data for output."""
    return ", ".join(data)
