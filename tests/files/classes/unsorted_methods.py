"""Class with unsorted methods - should trigger W9002."""


class Calculator:
    """Calculator class with unsorted methods."""

    def __init__(self, precision: int = 2) -> None:
        """Initialize calculator."""
        self.precision = precision

    def subtract(self, a: float, b: float) -> float:
        """Subtract two numbers."""
        return round(a - b, self.precision)

    def add(self, a: float, b: float) -> float:
        """Add two numbers."""
        return round(a + b, self.precision)

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers."""
        return round(a * b, self.precision)

    def divide(self, a: float, b: float) -> float:
        """Divide two numbers."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return round(a / b, self.precision)

    def _validate_input(self, value: float) -> bool:
        """Validate numeric input."""
        return isinstance(value, (int, float))

    def _format_result(self, value: float) -> str:
        """Format calculation result."""
        return f"{value:.{self.precision}f}"
