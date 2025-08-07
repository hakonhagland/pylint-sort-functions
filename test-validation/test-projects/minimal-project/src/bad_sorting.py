"""Test module with intentional sorting violations."""


def zebra_function():
    """Public function out of order."""
    pass


def alpha_function():
    """Should come before zebra."""
    pass


def _private_helper():
    """Private function in wrong position."""
    pass


def public_after_private():
    """Public function after private."""
    pass


class BadClass:
    """Class with method sorting issues."""

    def zebra_method(self):
        """Method out of order."""
        pass

    def alpha_method(self):
        """Should come before zebra."""
        pass
