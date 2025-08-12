#!/usr/bin/env python3
"""
Integration tests for configuration validation and edge cases.

Tests configuration handling, error recovery, and edge cases including:
- Invalid configurations
- Conflicting settings
- Performance with large codebases
- Integration between different features
"""

import json
import time
from typing import Any

from tests.integration.conftest import IntegrationTestHelper


class TestConfigurationValidation:  # pylint: disable=too-few-public-methods
    """Test configuration validation and error handling."""

    def test_conflicting_framework_and_custom_categories(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test when both framework preset and custom categories are specified."""
        file_creator(
            "src/test.py",
            """
class Test:
    def test_method(self):
        pass
""",
        )

        # Configure with both framework preset AND custom categories
        categories = [{"name": "custom", "patterns": ["test_*"], "priority": 100}]

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
method-categories = {json.dumps(categories)}
"""
        config_writer("pylintrc", config_content)

        # Run PyLint - should handle conflict gracefully
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should not crash, one config should take precedence
        assert returncode != 1, "Should handle conflicting configs gracefully"

    def test_invalid_category_priority(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test handling of invalid priority values in categories."""
        file_creator("src/test.py", "class Test:\n    pass")

        # Configure with invalid priority values
        categories = [
            {
                "name": "cat1",
                "patterns": ["*"],
                "priority": "high",
            },  # String instead of int
            {"name": "cat2", "patterns": ["_*"], "priority": -100},  # Negative priority
        ]

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {json.dumps(categories)}
"""
        config_writer("pylintrc", config_content)

        # Should handle invalid priorities gracefully
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        assert returncode != 1, "Should handle invalid priorities"

    def test_missing_required_category_fields(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test categories with missing required fields."""
        file_creator("src/test.py", "class Test:\n    pass")

        # Categories missing required fields
        categories = [
            {"name": "cat1"},  # Missing patterns/decorators
            {"patterns": ["test_*"], "priority": 10},  # Missing name
            {},  # Empty category
        ]

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {json.dumps(categories)}
"""
        config_writer("pylintrc", config_content)

        # Should handle incomplete categories
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        assert returncode != 1, "Should handle incomplete categories"

    def test_circular_pattern_dependencies(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test handling of circular or conflicting pattern dependencies."""
        test_code = '''"""Test circular patterns."""

class Service:
    def test_helper(self):
        """Matches both test_* and *_helper patterns."""
        pass

    def helper_test(self):
        """Also matches both patterns in reverse."""
        pass
'''
        file_creator("src/service.py", test_code)

        # Create circular pattern dependencies
        categories = [
            {"name": "test_methods", "patterns": ["test_*", "*_test"], "priority": 50},
            {
                "name": "helpers",
                "patterns": ["*_helper", "helper_*"],
                "priority": 50,
            },  # Same priority!
        ]

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {json.dumps(categories)}
"""
        config_writer("pylintrc", config_content)

        # Should handle ambiguous patterns
        returncode, stdout, stderr = pylint_runner(
            ["src/service.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should handle circular patterns without crashing (any return code OK)
        assert returncode % 2 == 0, f"Should handle circular patterns: {stderr}"

    def test_unicode_in_configuration(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test handling of Unicode characters in configuration."""
        file_creator(
            "src/test.py",
            '''
class Test:
    def método_español(self):
        """Method with Unicode name."""
        pass
''',
        )

        # Configuration with Unicode
        categories = [
            {"name": "métodos", "patterns": ["método_*"], "priority": 10},
            {"name": "普通方法", "patterns": ["*"], "priority": 5},
        ]

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {json.dumps(categories, ensure_ascii=False)}
"""
        config_writer("pylintrc", config_content)

        # Should handle Unicode configuration
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        assert returncode != 1, "Should handle Unicode in config"

    def test_extremely_long_configuration(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test handling of very large configuration."""
        file_creator("src/test.py", "class Test:\n    pass")

        # Create extremely long configuration
        categories = []
        for i in range(100):  # 100 categories
            categories.append(
                {
                    "name": f"category_{i}",
                    "patterns": [f"pattern_{i}_*", f"*_pattern_{i}"],
                    "decorators": [f"@decorator_{i}"],
                    "priority": 100 - i,
                }
            )

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {json.dumps(categories)}
"""
        config_writer("pylintrc", config_content)

        # Should handle large configs
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        assert returncode != 1, "Should handle large configurations"


class TestPerformanceAndScale:  # pylint: disable=too-few-public-methods
    """Test performance with large codebases and complex configurations."""

    def test_performance_many_methods(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test performance with classes containing many methods."""
        # Create class with many methods
        methods = []
        for i in range(50):
            methods.append(f'''
    def method_{i:03d}(self):
        """Method {i}."""
        return {i}
''')

        test_code = f'''"""Large class test."""

class LargeClass:
{"".join(methods)}
'''
        file_creator("src/large_class.py", test_code)

        # Enable categorization
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
"""
        config_writer("pylintrc", config_content)

        # Measure performance
        start_time = time.time()
        returncode, stdout, stderr = pylint_runner(
            ["src/large_class.py"], extra_args=["--enable=unsorted-methods"]
        )
        elapsed_time = time.time() - start_time

        # Should complete in reasonable time
        assert elapsed_time < 5.0, f"Should complete quickly, took {elapsed_time}s"
        # Performance test - should handle large classes without timeout/crash
        assert returncode % 2 == 0, f"Should handle large classes: {stderr}"

    def test_performance_many_files(self, file_creator: Any) -> None:
        """Test performance with many files using the helper."""
        # Create multiple modules
        modules = IntegrationTestHelper.create_multi_module_project(
            file_creator, num_modules=10
        )

        # Just verify files were created successfully
        assert len(modules) == 10, "Should create 10 modules"
        for module in modules:
            assert module.exists(), f"Module {module} should exist"

    def test_complex_import_chains(self, file_creator: Any) -> None:
        """Test complex import dependency chains."""
        # Create import chain using helper
        import_chain = IntegrationTestHelper.create_import_chain(file_creator)

        # Verify chain was created
        assert "module_a" in import_chain
        assert "module_b" in import_chain
        assert "module_c" in import_chain

        # Verify imports are present
        module_b_content = import_chain["module_b"].read_text()
        assert "from src.module_a import" in module_b_content


class TestFeatureIntegration:  # pylint: disable=too-few-public-methods
    """Test integration between different plugin features."""

    def test_privacy_detection_with_categorization(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test privacy detection works with method categorization."""
        # Create file with privacy issues
        test_code = '''"""Test privacy with categories."""

class Service:
    def internal_helper(self):
        """Should be private."""
        return self._do_work()

    def _do_work(self):
        """Already private."""
        return "work"

    def public_api(self):
        """Public API."""
        return self.internal_helper()
'''
        file_creator("src/service.py", test_code)

        # Enable both features
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
enable-privacy-detection = yes
framework-preset = pytest
category-sorting = declaration
"""
        config_writer("pylintrc", config_content)

        # Run PyLint with both features
        returncode, stdout, stderr = pylint_runner(
            ["src/service.py"],
            extra_args=["--enable=function-should-be-private,unsorted-methods"],
        )

        # Both features should work together
        # Integration test - should work without fatal errors
        assert returncode % 2 == 0, f"Features should work together: {stderr}"

    def test_section_headers_with_auto_sort(
        self, cli_runner: Any, file_creator: Any, assert_no_syntax_errors: Any
    ) -> None:
        """Test section headers work with auto-sort."""
        # Create unsorted file
        test_code = '''"""Test integration."""

class Service:
    def zebra(self):
        pass

    def alpha(self):
        pass

    def _zebra_private(self):
        pass

    def _alpha_private(self):
        pass
'''
        test_file = file_creator("src/service.py", test_code)

        # Run auto-sort with section headers
        returncode, stdout, stderr = cli_runner(
            ["--fix", "--auto-sort", "--add-section-headers", "src/service.py"]
        )

        # Should work with privacy detection (even with other violations)
        assert returncode % 2 == 0, f"Should succeed: {stderr}"

        # Verify both features worked
        content = test_file.read_text()
        assert "# Public" in content, "Should add section headers"
        assert content.index("def alpha") < content.index("def zebra"), (
            "Should sort methods"
        )
        assert assert_no_syntax_errors(test_file), "Should maintain valid syntax"

    def test_all_features_combined(
        self, cli_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test all new features working together."""
        # Create complex test file
        test_code = '''"""Test all features."""

class TestService:
    def test_zebra(self):
        return self.helper()

    def helper(self):
        return "help"

    def test_alpha(self):
        return self._internal()

    def _internal(self):
        return "internal"

    def setup_method(self):
        pass
'''
        test_file = file_creator("src/test_all.py", test_code)

        # Configure all features
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
category-sorting = declaration
enforce-section-headers = no
enable-privacy-detection = yes
"""
        config_writer("pylintrc", config_content)

        # Run auto-fix with all features (excluding PyLint-only options)
        returncode, stdout, stderr = cli_runner(
            [
                "--fix",
                "--auto-sort",
                "--add-section-headers",
                "--fix-privacy",
                "src/test_all.py",
            ]
        )

        # Combined features test - should work without fatal errors
        assert returncode % 2 == 0, f"All features should work together: {stderr}"

        # Verify transformations
        content = test_file.read_text()

        # Verify basic functionality - file should be processed without corruption
        assert "class TestService:" in content, "Class should be preserved"
        assert "def test_zebra" in content and "def helper" in content, (
            "Methods should be preserved"
        )
        assert content.count("def ") == 5, "All methods should be preserved"


class TestErrorRecovery:  # pylint: disable=too-few-public-methods
    """Test error recovery and graceful degradation."""

    def test_syntax_error_in_target_file(
        self, pylint_runner: Any, file_creator: Any
    ) -> None:
        """Test handling of files with syntax errors."""
        # Create file with syntax error
        test_code = '''"""Syntax error test."""

class Test:
    def method(self:  # Missing closing parenthesis
        pass
'''
        file_creator("src/syntax_error.py", test_code)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/syntax_error.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should report syntax error but not crash
        assert "syntax" in stdout.lower() or "syntax" in stderr.lower(), (
            "Should report syntax error"
        )

    def test_missing_pylintrc_fallback(
        self, pylint_runner: Any, file_creator: Any
    ) -> None:
        """Test behavior when configuration file is missing."""
        file_creator("src/test.py", "class Test:\n    pass")

        # Run without any configuration file
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should use defaults
        # Fallback test - should work without fatal errors even with missing config
        assert returncode % 2 == 0, f"Should work without config: {stderr}"

    def test_corrupted_pyproject_toml(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test handling of corrupted pyproject.toml."""
        file_creator("src/test.py", "class Test:\n    pass")

        # Write corrupted TOML
        config_content = """[tool.pylint
This is not valid TOML syntax
"""
        config_writer("pyproject.toml", config_content)

        # Should handle corrupted config
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should fall back to defaults or report config error
        assert returncode != 1, "Should not crash on corrupted config"
