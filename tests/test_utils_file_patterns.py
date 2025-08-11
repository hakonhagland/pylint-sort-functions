"""Tests for file pattern matching and test detection utilities."""

from pylint_sort_functions import utils


class TestUtilsFilePatterns:
    """Test cases for file pattern matching utility functions."""

    def test_is_unittest_file_with_privacy_config_exclude_dirs(self) -> None:
        """Test is_unittest_file with privacy config exclude directories."""
        # Test basic functionality without config
        assert utils.is_unittest_file("package.tests.test_utils") is True
        assert utils.is_unittest_file("package.lib.utils") is False

        # Test with custom exclude directories
        privacy_config = {"exclude_dirs": ["specs", "qa"], "exclude_patterns": []}

        # Custom directories should be detected as test files
        assert (
            utils.is_unittest_file("package.specs.test_utils", privacy_config) is True
        )
        assert utils.is_unittest_file("package.qa.validation", privacy_config) is True

        # Non-excluded directories should fall back to built-in detection
        assert (
            utils.is_unittest_file("package.tests.test_utils", privacy_config) is True
        )
        assert utils.is_unittest_file("package.lib.utils", privacy_config) is False

    def test_is_unittest_file_with_privacy_config_exclude_patterns(self) -> None:
        """Test is_unittest_file with privacy config exclude patterns."""
        privacy_config = {
            "exclude_dirs": [],
            "exclude_patterns": ["*_spec.py", "integration_*.py", "*_check.py"],
        }

        # Patterns should be detected as test files
        assert utils.is_unittest_file("package.lib.utils_spec", privacy_config) is True
        assert (
            utils.is_unittest_file("package.qa.integration_auth", privacy_config)
            is True
        )
        assert (
            utils.is_unittest_file("package.validation.health_check", privacy_config)
            is True
        )

        # Non-matching patterns should fall back to built-in detection
        assert (
            utils.is_unittest_file("package.tests.test_utils", privacy_config) is True
        )
        assert utils.is_unittest_file("package.lib.utils", privacy_config) is False

    def test_is_unittest_file_with_additional_test_patterns(self) -> None:
        """Test is_unittest_file with additional test patterns."""
        privacy_config = {
            "exclude_dirs": [],
            "exclude_patterns": [],
            "additional_test_patterns": ["scenario_*.py", "*_spec.py", "demo_*.py"],
        }

        # Additional patterns should be detected as test files
        assert (
            utils.is_unittest_file("package.lib.scenario_auth", privacy_config) is True
        )
        assert utils.is_unittest_file("package.qa.user_spec", privacy_config) is True
        assert (
            utils.is_unittest_file("package.examples.demo_basic", privacy_config)
            is True
        )

        # Built-in patterns should still work
        assert (
            utils.is_unittest_file("package.tests.test_utils", privacy_config) is True
        )
        assert utils.is_unittest_file("package.lib.utils", privacy_config) is False

    def test_is_unittest_file_with_override_test_detection(self) -> None:
        """Test is_unittest_file with override test detection enabled."""
        privacy_config = {
            "exclude_dirs": ["qa"],
            "exclude_patterns": ["*_spec.py"],
            "additional_test_patterns": ["scenario_*.py"],
            "override_test_detection": True,
        }

        # Only configured patterns should work
        assert utils.is_unittest_file("package.qa.validation", privacy_config) is True
        assert utils.is_unittest_file("package.lib.user_spec", privacy_config) is True
        assert (
            utils.is_unittest_file("package.examples.scenario_auth", privacy_config)
            is True
        )

        # Built-in patterns should be ignored when override is True
        assert (
            utils.is_unittest_file("package.tests.test_utils", privacy_config) is False
        )
        assert (
            utils.is_unittest_file("package.lib.test_something", privacy_config)
            is False
        )
        assert utils.is_unittest_file("package.conftest", privacy_config) is False

    def test_matches_file_pattern_glob_patterns(self) -> None:
        """Test _matches_file_pattern with various glob patterns."""
        # Test exact matches
        assert utils._matches_file_pattern("test_utils", "test_*.py") is True
        assert utils._matches_file_pattern("utils_test", "*_test.py") is True
        assert utils._matches_file_pattern("conftest", "conftest.py") is True

        # Test non-matches
        assert utils._matches_file_pattern("utils", "test_*.py") is False
        assert utils._matches_file_pattern("test_something", "*_test.py") is False

        # Test complex patterns
        assert (
            utils._matches_file_pattern("integration_auth", "integration_*.py") is True
        )
        assert (
            utils._matches_file_pattern(
                "package.tests.integration_auth", "integration_*.py"
            )
            is True
        )
        assert (
            utils._matches_file_pattern("auth_integration", "integration_*.py") is False
        )

        # Test directory-like patterns
        assert utils._matches_file_pattern("package.qa.validation", "*/qa/*.py") is True
        assert utils._matches_file_pattern("package.lib.utils", "*/qa/*.py") is False

    def test_matches_file_pattern_empty_module_name(self) -> None:
        """Test _matches_file_pattern with empty module name (edge case)."""
        # Edge case: empty string should still work
        assert utils._matches_file_pattern("", "*.py") is True
        assert utils._matches_file_pattern("", "test_*.py") is False

    def test_matches_file_pattern_edge_cases(self) -> None:
        """Test _matches_file_pattern with edge cases."""
        # Test empty module name (should hit fallback at line 818)
        assert utils._matches_file_pattern("", "*.py") is True
        assert utils._matches_file_pattern("", "test_*.py") is False
