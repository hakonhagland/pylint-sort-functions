"""Multiple classes with different sorting states."""


class SortedClass:
    """Class with properly sorted methods."""

    def __init__(self) -> None:
        """Initialize."""
        pass

    def method_a(self) -> str:
        """Method A."""
        return "a"

    def method_b(self) -> str:
        """Method B."""
        return "b"

    def _private_a(self) -> str:
        """Private method A."""
        return "_a"

    def _private_b(self) -> str:
        """Private method B."""
        return "_b"


class UnsortedClass:
    """Class with unsorted methods - should trigger W9002."""

    def __init__(self) -> None:
        """Initialize."""
        pass

    def method_z(self) -> str:
        """Method Z."""
        return "z"

    def method_a(self) -> str:
        """Method A."""
        return "a"

    def _private_z(self) -> str:
        """Private method Z."""
        return "_z"

    def _private_a(self) -> str:
        """Private method A."""
        return "_a"
