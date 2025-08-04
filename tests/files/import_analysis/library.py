"""Library module with mixed public/private functions."""


def public_api_function() -> str:
    """This is clearly a public API function - used by other modules."""
    return format_data("raw data")


def format_data(data: str) -> str:
    """This looks public but is only used internally - should be private."""
    return f"formatted: {data}"


def get_config() -> dict[str, str]:
    """This looks like helper but is used by other modules - should stay public."""
    return {"setting": "value"}


def internal_helper() -> str:
    """This is only used internally - should be private."""
    return "helper result"


def validate_input(value: str) -> bool:
    """This looks like helper and is only used internally - should be private."""
    result = internal_helper()
    return len(value) > 0 and result == "helper result"


def main() -> None:
    """Entry point - should stay public."""
    print(public_api_function())
