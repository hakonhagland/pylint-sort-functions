"""Calculator module with functions that should be private."""

import math


def calculate_circle_area(radius):
    """Calculate the area of a circle."""
    return validate_positive_number(radius) * math.pi * radius**2


def calculate_square_area(side_length):
    """Calculate the area of a square."""
    return validate_positive_number(side_length) ** 2


def format_result(value, precision=2):
    """Format a numeric result for display."""
    return f"{value:.{precision}f}"


def validate_positive_number(value):
    """Validate that a number is positive - only used internally."""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("Value must be a positive number")
    return value


def log_calculation(operation, inputs, result):
    """Log a calculation - only used internally."""
    print(f"Operation: {operation}, Inputs: {inputs}, Result: {result}")


def main():
    """Main function - should always stay public."""
    area = calculate_circle_area(5.0)
    formatted = format_result(area)
    print(f"Circle area: {formatted}")


if __name__ == "__main__":
    main()
