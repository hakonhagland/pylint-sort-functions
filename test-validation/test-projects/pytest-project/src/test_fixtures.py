"""Pytest test file with fixture decorator exclusion testing."""

import pytest


# These decorated fixtures/tests should be excluded from sorting
@pytest.fixture(scope="session")
def database_connection():
    """Database connection fixture."""
    return {"connected": True}


@pytest.fixture
def user_data():
    """User data fixture."""
    return {"name": "test", "id": 1}


@pytest.mark.slow
@pytest.mark.integration
def test_user_creation(user_data):
    """Test user creation."""
    assert user_data["name"] == "test"


@pytest.mark.unit
def test_basic_functionality():
    """Basic functionality test."""
    assert True


@pytest.fixture(autouse=True)
def setup_teardown():
    """Auto-use fixture."""
    yield
    # cleanup


@pytest.parametrize(
    "value,expected",
    [
        (1, 2),
        (2, 3),
    ],
)
def test_increment(value, expected):
    """Parametrized test."""
    assert value + 1 == expected


# These regular functions should trigger sorting violations
def zebra_test_helper():
    """Test helper function out of order."""
    return "zebra"


def alpha_test_helper():
    """Should come before zebra_test_helper."""
    return "alpha"


def _zebra_private_helper():
    """Private helper out of order."""
    return "private"


def _alpha_private_helper():
    """Should come before _zebra_private_helper."""
    return "private"


class TestSuite:
    """Test suite class with method sorting issues."""

    def test_zebra_method(self):
        """Test method out of order."""
        assert True

    def test_alpha_method(self):
        """Should come before test_zebra_method."""
        assert True
