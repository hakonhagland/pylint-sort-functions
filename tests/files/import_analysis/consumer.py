"""Consumer module that imports from library."""

from library import get_config, public_api_function  # type: ignore[import-not-found]


def use_library() -> None:
    """Function that uses the library functions."""
    config = get_config()  # This import makes get_config() public
    result = public_api_function()  # This import makes public_api_function() public
    print(f"Config: {config}, Result: {result}")


def another_consumer() -> None:
    """Another function using library."""
    data = public_api_function()
    print(f"Data: {data}")
