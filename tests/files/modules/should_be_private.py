"""Module with functions that should be private - for testing W9004."""


def calculate_sum(a: int, b: int) -> int:
    """Calculate function used internally."""
    return validate_numbers(a, b)


def get_data() -> str:
    """This get_ function is only used internally."""
    return process_data("raw data")


def helper_function() -> str:
    """This function is only used internally and should be private."""
    return "helper result"


def main() -> None:
    """Entry point function - should stay public."""
    result = public_api_function()
    print(result)


def process_data(data: str) -> str:
    """This process_ function is only used internally."""
    return f"processed: {data}"


def public_api_function() -> str:
    """This is clearly a public API function."""
    return helper_function()


def validate_numbers(a: int, b: int) -> int:
    """Validation function used internally."""
    if isinstance(a, int) and isinstance(b, int):
        return a + b
    raise ValueError("Invalid numbers")
