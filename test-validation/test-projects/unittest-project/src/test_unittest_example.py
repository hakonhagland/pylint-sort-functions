"""Unittest test class demonstrating framework preset method organization."""

import unittest


class TestUserService(unittest.TestCase):
    """Example unittest test class with conventional method organization."""
    
    # Test fixtures (should come first)
    def setUp(self):
        """Setup test fixtures."""
        self.user_service = "test_service"
        self.test_data = {"id": 1, "name": "Test User"}
    
    def tearDown(self):
        """Cleanup after tests."""
        self.user_service = None
        self.test_data = None
    
    @classmethod
    def setUpClass(cls):
        """Class-level setup."""
        cls.shared_data = "shared"
    
    @classmethod
    def tearDownClass(cls):
        """Class-level cleanup."""
        cls.shared_data = None
    
    # Test methods (should come second)
    def test_user_creation(self):
        """Test user creation functionality."""
        self.assertIsNotNone(self.user_service)
        self.assertEqual(self.test_data["name"], "Test User")
    
    def test_user_validation(self):
        """Test user validation."""
        self.assertTrue(self.test_data["id"] > 0)
    
    # Public helper methods (should come third)
    def create_test_user(self):
        """Create a test user for testing."""
        return {"id": 2, "name": "Another User"}
    
    def validate_user_data(self, data):
        """Validate user data structure."""
        return "id" in data and "name" in data
    
    # Private helper methods (should come last)
    def _cleanup_resources(self):
        """Private cleanup helper."""
        pass
    
    def _setup_mock_data(self):
        """Private setup helper."""
        return {"mock": True}


# Test that regular functions still trigger violations when out of order
def zebra_function():
    """Function that should come after alpha_function."""
    return "zebra"


def alpha_function():
    """Should come before zebra_function."""
    return "alpha"