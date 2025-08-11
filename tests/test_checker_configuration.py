"""Tests for the FunctionSortChecker configuration functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import astroid  # type: ignore[import-untyped]
from astroid import nodes
from pylint.testutils import CheckerTestCase

from pylint_sort_functions.checker import FunctionSortChecker


class TestFunctionSortCheckerConfiguration(CheckerTestCase):
    """Test cases for FunctionSortChecker configuration functionality."""

    CHECKER_CLASS = FunctionSortChecker

    def test_configuration_options(self) -> None:
        """Test that configuration options are properly defined."""
        # Verify options are defined
        assert hasattr(self.checker, "options")
        assert isinstance(self.checker.options, tuple)
        assert len(self.checker.options) == 15

        # Test public-api-patterns option
        public_api_option = self.checker.options[0]
        assert public_api_option[0] == "public-api-patterns"
        assert public_api_option[1]["type"] == "csv"
        assert "main" in public_api_option[1]["default"]

        # Test enable-privacy-detection option
        privacy_option = self.checker.options[1]
        assert privacy_option[0] == "enable-privacy-detection"
        assert privacy_option[1]["type"] == "yn"
        assert privacy_option[1]["default"] is True

    def test_privacy_detection_disabled(self) -> None:
        """Test that privacy detection can be disabled via configuration."""

        content = """
def unused_function():
    pass
"""
        module = astroid.parse(content)

        # Mock linter with privacy detection disabled
        mock_linter = Mock()
        mock_linter.config.enable_privacy_detection = False

        with patch.object(self.checker, "linter", mock_linter):
            with self.assertNoMessages():
                self.checker.visit_module(module)

    def test_custom_public_api_patterns(self) -> None:
        """Test that custom public API patterns are used in privacy detection."""
        from unittest.mock import Mock, patch

        content = """
def handler():
    pass

def processor():
    pass
"""
        module = astroid.parse(content)

        # Mock linter with custom public API patterns
        mock_linter = Mock()
        mock_linter.config.enable_privacy_detection = True
        mock_linter.config.public_api_patterns = ["handler", "processor"]
        mock_linter.current_file = "/test/module.py"

        with patch.object(self.checker, "linter", mock_linter):
            with patch.object(self.checker, "_get_project_root") as mock_project_root:
                mock_project_root.return_value = Path("/test")

                with patch(
                    "pylint_sort_functions.utils.should_function_be_private"
                ) as mock_should_private:
                    mock_should_private.return_value = False

                    with self.assertNoMessages():
                        self.checker.visit_module(module)

                    # Verify should_function_be_private was called with custom patterns
                    assert mock_should_private.call_count == 2
                    call_args = mock_should_private.call_args_list[0]
                    # Check the fourth argument (public_patterns)
                    assert call_args[0][3] == {"handler", "processor"}

    def test_decorator_exclusions_configuration(self) -> None:
        """Test that decorator exclusions configuration is properly defined."""
        # Verify ignore-decorators option is defined
        options_dict = {opt[0]: opt[1] for opt in self.checker.options}

        assert "ignore-decorators" in options_dict
        decorator_option = options_dict["ignore-decorators"]
        assert decorator_option["type"] == "csv"
        assert decorator_option["default"] == []
        assert "decorator patterns" in decorator_option["help"].lower()

    def test_decorator_exclusions_functions(self) -> None:
        """Test that functions with excluded decorators are not flagged for sorting."""

        content = """
@app.route('/users')
def zebra_route():
    pass

@app.route('/users/<int:id>')
def alpha_route():
    pass

def alpha_function():
    pass

def zebra_function():
    pass
"""
        module = astroid.parse(content)

        # Mock linter with decorator exclusions configured
        mock_linter = Mock()
        mock_linter.config.ignore_decorators = ["@app.route"]
        mock_linter.config.enable_privacy_detection = (
            False  # Disable to focus on sorting
        )

        with patch.object(self.checker, "linter", mock_linter):
            # Should NOT report unsorted functions because:
            # - Decorated functions @app.route are excluded from sorting
            # - Regular functions are properly sorted (alpha_function, zebra_function)
            with self.assertNoMessages():
                self.checker.visit_module(module)

    def test_decorator_exclusions_methods(self) -> None:
        """Test that methods with excluded decorators are not flagged for sorting."""

        content = """
class APIHandler:
    @app.route('/api/users')
    def zebra_route(self):
        pass

    @app.route('/api/users/<int:id>')
    def alpha_route(self):
        pass

    def alpha_method(self):
        pass

    def zebra_method(self):
        pass
"""
        module = astroid.parse(content)
        class_node = module.body[0]
        assert isinstance(class_node, nodes.ClassDef)

        # Mock linter with decorator exclusions configured
        mock_linter = Mock()
        mock_linter.config.ignore_decorators = ["@app.route"]

        with patch.object(self.checker, "linter", mock_linter):
            # Should NOT report unsorted methods because:
            # - Decorated methods @app.route are excluded from sorting
            # - Regular methods are properly sorted (alpha_method, zebra_method)
            with self.assertNoMessages():
                self.checker.visit_classdef(class_node)

    def test_all_functions_excluded_no_message(self) -> None:
        """Test that when all functions are excluded, no message is issued."""

        content = """
@app.route('/users')
def zebra_route():
    pass

@app.route('/admin')
def alpha_route():
    pass
"""
        module = astroid.parse(content)

        # Mock linter excluding all functions
        mock_linter = Mock()
        mock_linter.config.ignore_decorators = ["@app.route"]
        mock_linter.config.enable_privacy_detection = False

        with patch.object(self.checker, "linter", mock_linter):
            # No functions are sortable, so no sorting violation should be reported
            with self.assertNoMessages():
                self.checker.visit_module(module)

    def test_privacy_configuration_options(self) -> None:
        """Test that privacy-specific configuration options are properly defined."""
        # Test privacy-exclude-dirs option
        exclude_dirs_option = self.checker.options[3]
        assert exclude_dirs_option[0] == "privacy-exclude-dirs"
        assert exclude_dirs_option[1]["type"] == "csv"
        assert exclude_dirs_option[1]["default"] == []

        # Test privacy-exclude-patterns option
        exclude_patterns_option = self.checker.options[4]
        assert exclude_patterns_option[0] == "privacy-exclude-patterns"
        assert exclude_patterns_option[1]["type"] == "csv"
        assert exclude_patterns_option[1]["default"] == []

        # Test privacy-additional-test-patterns option
        additional_patterns_option = self.checker.options[5]
        assert additional_patterns_option[0] == "privacy-additional-test-patterns"
        assert additional_patterns_option[1]["type"] == "csv"
        assert additional_patterns_option[1]["default"] == []

        # Test privacy-update-tests option
        update_tests_option = self.checker.options[6]
        assert update_tests_option[0] == "privacy-update-tests"
        assert update_tests_option[1]["type"] == "yn"
        assert update_tests_option[1]["default"] is False

        # Test privacy-override-test-detection option
        override_option = self.checker.options[7]
        assert override_option[0] == "privacy-override-test-detection"
        assert override_option[1]["type"] == "yn"
        assert override_option[1]["default"] is False

    def test_get_privacy_config_method(self) -> None:
        """Test that _get_privacy_config extracts configuration correctly."""

        # Mock linter config with privacy settings
        mock_linter = Mock()
        mock_linter.config.privacy_exclude_dirs = ["tests", "qa"]
        mock_linter.config.privacy_exclude_patterns = ["test_*.py", "*_spec.py"]
        mock_linter.config.privacy_additional_test_patterns = ["scenario_*.py"]
        mock_linter.config.privacy_update_tests = True
        mock_linter.config.privacy_override_test_detection = False

        with patch.object(self.checker, "linter", mock_linter):
            config = self.checker._get_privacy_config()

            assert config["exclude_dirs"] == ["tests", "qa"]
            assert config["exclude_patterns"] == ["test_*.py", "*_spec.py"]
            assert config["additional_test_patterns"] == ["scenario_*.py"]
            assert config["update_tests"] is True
            assert config["override_test_detection"] is False

    def test_get_privacy_config_with_defaults(self) -> None:
        """Test that _get_privacy_config handles missing configuration with defaults."""

        # Mock linter config without privacy settings
        mock_linter = Mock()
        # Remove privacy attributes to simulate default behavior
        del mock_linter.config.privacy_exclude_dirs
        del mock_linter.config.privacy_exclude_patterns
        del mock_linter.config.privacy_additional_test_patterns
        del mock_linter.config.privacy_update_tests
        del mock_linter.config.privacy_override_test_detection

        with patch.object(self.checker, "linter", mock_linter):
            config = self.checker._get_privacy_config()

            assert config["exclude_dirs"] == []
            assert config["exclude_patterns"] == []
            assert config["additional_test_patterns"] == []
            assert config["update_tests"] is False
            assert config["override_test_detection"] is False

    def test_get_privacy_config_exception_handling(self) -> None:
        """Test that _get_privacy_config handles exceptions gracefully."""

        # Create a mock that raises AttributeError when accessed
        class ExceptionMock:  # pylint: disable=too-few-public-methods
            """Mock class that raises AttributeError on attribute access."""

            def __getattr__(self, name: str) -> None:
                raise AttributeError(f"Mock attribute error for {name}")

        mock_linter = Mock()
        mock_linter.config = ExceptionMock()

        with patch.object(self.checker, "linter", mock_linter):
            # Should use defaults when exceptions occur
            config = self.checker._get_privacy_config()
            assert config["exclude_dirs"] == []
            assert config["exclude_patterns"] == []
            assert config["additional_test_patterns"] == []
            assert config["update_tests"] is False
            assert config["override_test_detection"] is False

        # Test TypeError handling as well
        class TypeErrorMock:  # pylint: disable=too-few-public-methods
            """Mock class that raises TypeError on getattr."""

            def __getattr__(self, name: str) -> None:
                raise TypeError(f"Mock type error for {name}")

        mock_linter_2 = Mock()
        mock_linter_2.config = TypeErrorMock()

        with patch.object(self.checker, "linter", mock_linter_2):
            # Should also use defaults when TypeError occurs
            config = self.checker._get_privacy_config()
            assert config["exclude_dirs"] == []
            assert config["additional_test_patterns"] == []
            assert config["update_tests"] is False
            assert config["override_test_detection"] is False
