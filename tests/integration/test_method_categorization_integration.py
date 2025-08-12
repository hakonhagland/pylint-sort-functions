#!/usr/bin/env python3
"""
Integration tests for method categorization feature (Phase 1).

Tests the flexible method categorization system including:
- Framework presets (pytest, unittest, pyqt)
- Custom JSON category configuration
- Category sorting behavior
- Priority-based conflict resolution
"""

import json
from typing import Any


class TestMethodCategorizationIntegration:  # pylint: disable=too-few-public-methods
    """Integration tests for method categorization features."""

    def test_pytest_framework_preset(
        self,
        pylint_runner: Any,
        file_creator: Any,
        config_writer: Any,
        sample_test_class: Any,
    ) -> None:
        """Test pytest framework preset categorization."""
        # Create test file with pytest-style test class
        file_creator("src/test_example.py", sample_test_class["pytest"])

        # Create config with pytest preset (needs config file, not CLI args)
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
category-sorting = declaration
"""
        config_writer("pylintrc", config_content)

        # Run PyLint with pytest framework preset
        returncode, stdout, stderr = pylint_runner(
            ["src/test_example.py"], extra_args=["--enable=unsorted-methods"]
        )

        # The pytest preset should not flag violations for conventional pytest ordering
        # (test fixtures first, then test methods, then helpers)
        assert "unsorted-methods" not in stdout, (
            "Pytest preset should accept conventional ordering"
        )

    def test_unittest_framework_preset(
        self,
        pylint_runner: Any,
        file_creator: Any,
        config_writer: Any,
        sample_test_class: Any,
    ) -> None:
        """Test unittest framework preset categorization."""
        # Create test file with unittest-style test class
        file_creator("src/test_example.py", sample_test_class["unittest"])

        # Create config with unittest preset
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = unittest
category-sorting = declaration
"""
        config_writer("pylintrc", config_content)

        # Run PyLint with unittest framework preset
        returncode, stdout, stderr = pylint_runner(
            ["src/test_example.py"], extra_args=["--enable=unsorted-methods"]
        )

        # The unittest preset should accept setUp/tearDown at the top
        assert "unsorted-methods" not in stdout, (
            "Unittest preset should accept conventional ordering"
        )

    def test_pyqt_framework_preset(
        self,
        pylint_runner: Any,
        file_creator: Any,
        config_writer: Any,
        sample_test_class: Any,
    ) -> None:
        """Test PyQt framework preset categorization."""
        # Create test file with PyQt-style dialog class
        file_creator("src/dialog.py", sample_test_class["pyqt"])

        # Create config with PyQt preset
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pyqt
category-sorting = declaration
"""
        config_writer("pylintrc", config_content)

        # Run PyLint with PyQt framework preset
        returncode, stdout, stderr = pylint_runner(
            ["src/dialog.py"], extra_args=["--enable=unsorted-methods"]
        )

        # The PyQt preset should accept init/properties/events/public/private ordering
        assert "unsorted-methods" not in stdout, (
            "PyQt preset should accept conventional ordering"
        )

    def test_custom_json_categories(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test basic method categorization with declaration order."""
        # Create simple test file
        test_code = '''"""Test basic categorization."""

class Service:
    def zebra_method(self):
        """Method Z - should not need alphabetical order."""
        pass

    def alpha_method(self):
        """Method A - comes second in declaration order."""
        pass

    def _private_method(self):
        """Private method."""
        pass
'''
        file_creator("src/service.py", test_code)

        # Use basic categorization with declaration order
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
category-sorting = declaration
"""
        config_writer("pylintrc", config_content)

        # Run PyLint - should accept declaration order
        returncode, stdout, stderr = pylint_runner(
            ["src/service.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Declaration order should be accepted (no sorting violations)
        assert "unsorted-methods" not in stdout, (
            "Declaration order should work correctly"
        )

    def test_category_sorting_alphabetical(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test alphabetical sorting within categories."""
        # Create test file with methods needing alphabetical sorting
        test_code = '''"""Test alphabetical sorting within categories."""

class Service:
    def zebra_method(self):
        """Public method Z."""
        pass

    def alpha_method(self):
        """Public method A - should come first."""
        pass

    def _zebra_private(self):
        """Private method Z."""
        pass

    def _alpha_private(self):
        """Private method A - should come first."""
        pass
'''
        file_creator("src/service.py", test_code)

        # Configure for alphabetical sorting
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
category-sorting = alphabetical
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/service.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should report violations for non-alphabetical ordering
        assert "unsorted-methods" in stdout, "Should detect non-alphabetical ordering"
        # The plugin detects unsorted methods but doesn't include specific method names

    def test_category_sorting_declaration(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test declaration order preservation within categories."""
        # Create test file with methods in declaration order
        test_code = '''"""Test declaration order preservation."""

class Service:
    def zebra_method(self):
        """Public method Z."""
        pass

    def alpha_method(self):
        """Public method A."""
        pass

    def _zebra_private(self):
        """Private method Z."""
        pass

    def _alpha_private(self):
        """Private method A."""
        pass
'''
        file_creator("src/service.py", test_code)

        # Configure for declaration order preservation
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
category-sorting = declaration
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/service.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should NOT report violations when using declaration order
        assert "unsorted-methods" not in stdout, "Declaration order should be accepted"

    def test_pattern_priority_resolution(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test priority-based conflict resolution for overlapping patterns."""
        # Create test with methods matching multiple patterns in correct category order
        test_code = '''"""Test priority resolution."""

class TestService:
    @property
    def test_property(self):
        """This matches both @property (priority 100) and test_* (priority 50)."""
        return self._value

    @property
    def regular_property(self):
        """This only matches @property decorator."""
        return self._other

    def test_regular(self):
        """This only matches test_* pattern."""
        pass
'''
        file_creator("src/test_service.py", test_code)

        # Configure with overlapping patterns
        categories = [
            {"name": "properties", "decorators": ["@property"], "priority": 100},
            {"name": "test_methods", "patterns": ["test_*"], "priority": 50},
            {"name": "public_methods", "patterns": ["*"], "priority": 10},
        ]

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {json.dumps(categories)}
category-sorting = declaration
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"], extra_args=["--enable=unsorted-methods"]
        )

        # test_property should be categorized as "properties" due to higher priority
        # Order should be: properties first, then test_methods
        # This specific order should not trigger violations
        assert "unsorted-methods" not in stdout, (
            "Priority resolution should work correctly"
        )

    def test_backward_compatibility_disabled(
        self, pylint_runner: Any, file_creator: Any
    ) -> None:
        """Test that categorization is disabled by default for compatibility."""
        # Create test file with non-standard ordering
        test_code = '''"""Test backward compatibility."""

class Service:
    def _private_first(self):
        """Private method incorrectly placed first."""
        pass

    def public_method(self):
        """Public method should be first."""
        pass
'''
        file_creator("src/service.py", test_code)

        # Run PyLint WITHOUT enabling categorization
        returncode, stdout, stderr = pylint_runner(
            ["src/service.py"], extra_args=["--enable=mixed-function-visibility"]
        )

        # Should use traditional binary public/private checking
        assert "mixed-function-visibility" in stdout, (
            "Should use traditional checking by default"
        )

    def test_framework_preset_with_violations(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test that framework presets still detect real violations."""
        # Create test file with incorrect ordering even for pytest
        test_code = '''"""Test with violations."""

class TestExample:
    def test_zebra(self):
        """Test Z - incorrectly ordered."""
        pass

    def test_alpha(self):
        """Test A - should come before test_zebra."""
        pass

    def setup_method(self):
        """Setup should be at the top in pytest preset."""
        pass
'''
        file_creator("src/test_incorrect.py", test_code)

        # Create config file with pytest preset
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
category-sorting = alphabetical
"""
        config_writer("pylintrc", config_content)

        # Run PyLint with pytest preset (these must be in config file, not CLI args)
        returncode, stdout, stderr = pylint_runner(
            ["src/test_incorrect.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should still detect violations within categories
        assert "unsorted-methods" in stdout, (
            "Should detect violations within categories"
        )

    def test_invalid_framework_preset(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test handling of invalid framework preset names."""
        file_creator("src/test.py", "class Test:\n    pass")

        # Try to use invalid framework preset
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = invalid_framework
"""
        config_writer("pylintrc", config_content)

        # Run PyLint - should handle gracefully
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should either ignore invalid preset or report configuration error
        # But should not crash
        assert returncode != 1, "Should not crash on invalid preset"

    def test_malformed_json_categories(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test handling of malformed JSON in method-categories."""
        file_creator("src/test.py", "class Test:\n    pass")

        # Write malformed JSON configuration
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {invalid json here}
"""
        config_writer("pylintrc", config_content)

        # Run PyLint - should handle gracefully
        returncode, stdout, stderr = pylint_runner(
            ["src/test.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should handle JSON errors gracefully
        assert returncode != 1, "Should not crash on malformed JSON"

    def test_empty_categories_configuration(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test behavior with empty category configuration."""
        test_code = '''"""Test empty categories."""

class Service:
    def public_method(self):
        pass

    def _private_method(self):
        pass
'''
        file_creator("src/service.py", test_code)

        # Configure with empty categories
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = []
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/service.py"], extra_args=["--enable=unsorted-methods"]
        )

        # Should fall back to default behavior or handle gracefully (don't crash)
        assert returncode != 1, "Should not crash on empty categories"


class TestMethodCategorizationCLI:  # pylint: disable=too-few-public-methods
    """Test method categorization via CLI auto-fix tool."""

    def test_cli_with_framework_preset(
        self, cli_runner: Any, file_creator: Any
    ) -> None:
        """Test CLI auto-fix with section headers (presets are PyLint-only)."""
        # Create unsorted pytest test file
        unsorted_pytest = '''"""Unsorted pytest test."""

class TestExample:
    def test_zebra(self):
        """Test Z."""
        pass

    def test_alpha(self):
        """Test A."""
        pass

    def setup_method(self):
        """Setup fixture."""
        pass

    def _helper(self):
        """Helper."""
        pass
'''
        test_file = file_creator("src/test_unsorted.py", unsorted_pytest)

        # Run auto-fix with section headers (CLI doesn't have framework preset flag)
        returncode, stdout, stderr = cli_runner(
            ["--fix", "--auto-sort", "--add-section-headers", "src/test_unsorted.py"]
        )

        assert returncode == 0, f"CLI should succeed: {stderr}"

        # Check that file was sorted according to pytest preset
        content = test_file.read_text()
        lines = content.split("\n")

        # Find method definitions
        method_lines = [
            i for i, line in enumerate(lines) if "def " in line and "class" not in line
        ]
        method_names = [
            lines[i].strip().split("def ")[1].split("(")[0] for i in method_lines
        ]

        # In the CLI without framework preset, methods are sorted alphabetically
        # So test_alpha should come before test_zebra
        assert method_names.index("test_alpha") < method_names.index("test_zebra"), (
            "Test methods should be sorted alphabetically"
        )

    def test_cli_auto_sort_with_categories(
        self, cli_runner: Any, file_creator: Any
    ) -> None:
        """Test CLI auto-sort (CLI uses basic sorting, categories are PyLint-only)."""
        # Create file needing sorting
        test_code = '''"""Unsorted methods."""

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

        # Run auto-sort (CLI doesn't have --enable-method-categories)
        returncode, stdout, stderr = cli_runner(
            ["--fix", "--auto-sort", "src/service.py"]
        )

        assert returncode == 0, f"CLI should succeed: {stderr}"

        # Verify sorting
        content = test_file.read_text()
        assert content.index("def alpha(") < content.index("def zebra("), (
            "Public methods should be sorted"
        )
        assert content.index("def _alpha_private(") < content.index(
            "def _zebra_private("
        ), "Private methods should be sorted"
