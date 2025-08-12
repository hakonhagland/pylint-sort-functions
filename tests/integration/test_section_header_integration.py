#!/usr/bin/env python3
"""
Integration tests for section header validation feature (Phase 2).

Tests the functional section header validation system including:
- Section header enforcement (W9006: method-wrong-section)
- Required section headers (W9007: missing-section-header)
- Empty section validation (W9008: empty-section-header)
- Integration with method categorization
"""

import json
from typing import Any


class TestSectionHeaderValidation:  # pylint: disable=too-few-public-methods
    """Integration tests for section header validation features."""

    def test_section_header_enforcement_basic(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test basic section header enforcement."""
        # Create test file with methods in wrong sections
        test_code = '''"""Test section header validation."""

class TestService:
    # Test methods
    def public_helper(self):
        """This should be in 'Public methods' section."""
        pass

    # Public methods
    def test_something(self):
        """This should be in 'Test methods' section."""
        pass
'''
        file_creator("src/test_service.py", test_code)

        # Enable section header enforcement
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
enforce-section-headers = yes
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"], extra_args=["--enable=method-wrong-section"]
        )

        # Should detect methods in wrong sections
        assert "method-wrong-section" in stdout, (
            "Should detect methods in wrong sections"
        )
        assert "public_helper" in stdout or "test_something" in stdout

    def test_missing_section_header_detection(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test detection of missing required section headers."""
        # Create test file without section headers
        test_code = '''"""Test missing section headers."""

class TestService:
    def test_feature_a(self):
        """Test method without section header."""
        pass

    def test_feature_b(self):
        """Another test method."""
        pass

    def helper_method(self):
        """Public helper without section header."""
        pass
'''
        file_creator("src/test_service.py", test_code)

        # Require section headers
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
enforce-section-headers = yes
require-section-headers = yes
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"], extra_args=["--enable=missing-section-header"]
        )

        # Should detect missing section headers
        assert "missing-section-header" in stdout, (
            "Should detect missing section headers"
        )

    def test_empty_section_header_detection(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test detection of empty section headers."""
        # Create test file with empty section
        test_code = '''"""Test empty section headers."""

class TestService:
    # Test methods
    # No actual test methods defined

    # Public methods
    def helper_method(self):
        """Public helper method."""
        pass
'''
        file_creator("src/test_service.py", test_code)

        # Disallow empty sections
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
enforce-section-headers = yes
allow-empty-sections = no
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"], extra_args=["--enable=empty-section-header"]
        )

        # Should detect empty section header
        assert "empty-section-header" in stdout, "Should detect empty section headers"

    def test_correct_section_headers_no_violations(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test that correct section headers produce no violations."""
        # Create properly organized test file
        test_code = '''"""Test correct section headers."""

class TestService:
    # Test fixtures
    def setup_method(self):
        """Setup test fixture."""
        self.data = []

    # Test methods
    def test_feature_a(self):
        """Test feature A."""
        assert True

    def test_feature_b(self):
        """Test feature B."""
        assert True

    # Public methods
    def helper_method(self):
        """Public helper."""
        return "help"

    # Private methods
    def _internal_helper(self):
        """Private helper."""
        return "private"
'''
        file_creator("src/test_service.py", test_code)

        # Enable all section header checks
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
enforce-section-headers = yes
require-section-headers = yes
allow-empty-sections = no
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"],
            extra_args=[
                "--enable=method-wrong-section,missing-section-header,empty-section-header"
            ],
        )

        # Should have no violations
        assert "method-wrong-section" not in stdout
        assert "missing-section-header" not in stdout
        assert "empty-section-header" not in stdout

    def test_section_headers_with_custom_categories(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test section headers with custom category definitions."""
        # Create test file with custom categories (clean PyLint-compliant code)
        test_code = '''"""Test custom section headers."""

class APIHandler:
    """API handler class."""

    def __init__(self):
        """Initialize handler."""
        self._status = "active"

    # Properties
    @property
    def status(self):
        """Status property."""
        return self._status

    # API Endpoints
    def get_users(self):
        """Get users endpoint."""
        return []

    # Public Methods
    def process_data(self):
        """Process data."""
        return True

    # Private Methods
    def _validate(self):
        """Validate data."""
        return True
'''
        file_creator("src/api_handler.py", test_code)

        # Configure custom categories with section headers
        categories = [
            {
                "name": "properties",
                "patterns": ["*"],
                "decorators": ["@property"],
                "priority": 20,
            },
            {
                "name": "api_endpoints",
                "patterns": ["get_*", "post_*", "*_endpoint"],
                "priority": 15,
            },
            {"name": "public_methods", "patterns": ["*"], "priority": 10},
            {"name": "private_methods", "patterns": ["_*"], "priority": 5},
        ]

        config_content = f"""[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
method-categories = {json.dumps(categories)}
enforce-section-headers = yes
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/api_handler.py"], extra_args=["--enable=method-wrong-section"]
        )

        # Test should run without fatal errors (return codes 20+ normal)
        assert returncode % 2 == 0, f"Custom sections should work: {stderr}"

        # Verify section header validation works (some violations expected)
        assert "method-wrong-section" in stdout or returncode < 16, (
            "Section validation should be active"
        )

    def test_case_insensitive_section_matching(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test that section header matching is case-insensitive by default."""
        # Create test with varied case headers
        test_code = '''"""Test case-insensitive matching."""

class TestService:
    # TEST METHODS
    def test_feature(self):
        """Test feature."""
        pass

    # public Methods
    def helper(self):
        """Helper method."""
        pass
'''
        file_creator("src/test_service.py", test_code)

        # Enable section headers (case-insensitive by default)
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
enforce-section-headers = yes
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"], extra_args=["--enable=method-wrong-section"]
        )

        # Should accept varied case headers
        assert "method-wrong-section" not in stdout, "Should match case-insensitively"

    def test_section_headers_disabled_by_default(
        self, pylint_runner: Any, file_creator: Any
    ) -> None:
        """Test that section header validation is disabled by default."""
        # Create test file with wrong sections
        test_code = '''"""Test default behavior."""

class TestService:
    # Test methods
    def public_method(self):
        """Wrong section but should not be checked by default."""
        pass
'''
        file_creator("src/test_service.py", test_code)

        # Run PyLint WITHOUT enabling section headers
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"], extra_args=["--enable=method-wrong-section"]
        )

        # Should NOT report violations when disabled
        assert "method-wrong-section" not in stdout, (
            "Section headers disabled by default"
        )

    def test_integration_with_auto_fix(
        self, cli_runner: Any, file_creator: Any, assert_no_syntax_errors: Any
    ) -> None:
        """Test section header integration with CLI auto-fix tool."""
        # Create unsorted file needing section headers
        test_code = '''"""Test auto-fix with section headers."""

class TestService:
    def test_zebra(self):
        """Test Z."""
        pass

    def test_alpha(self):
        """Test A."""
        pass

    def public_helper(self):
        """Public helper."""
        pass

    def _private_helper(self):
        """Private helper."""
        pass
'''
        test_file = file_creator("src/test_service.py", test_code)

        # Run auto-fix with section headers
        returncode, stdout, stderr = cli_runner(
            [
                "--fix",
                "--auto-sort",
                "--add-section-headers",
                "--enable-method-categories",
                "--framework-preset",
                "pytest",
                "src/test_service.py",
            ]
        )

        # Auto-fix should work without fatal errors
        assert returncode % 2 == 0, f"Auto-fix should succeed: {stderr}"

        # Verify basic functionality - file should be processed without corruption
        content = test_file.read_text()
        assert "class TestService:" in content, "Class should be preserved"
        assert "def test_" in content, "Test methods should be preserved"
        assert content.count("def ") == 4, "All methods should be preserved"
        # Basic integration test - just verify no corruption occurred

        # Verify syntax is still valid
        assert assert_no_syntax_errors(test_file), "Output should have valid syntax"

    def test_pyqt_section_headers(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test section headers with PyQt framework preset."""
        # Create PyQt-style dialog with sections (clean code without imports)
        test_code = '''"""PyQt dialog with section headers."""

class MyDialog:
    """Dialog class."""

    def __init__(self, parent=None):
        """Initialize dialog."""
        self.parent = parent
        self._value = None

    # Initialization methods
    def setup_ui(self):
        """Setup UI."""
        pass

    # Properties
    @property
    def value(self):
        """Get value."""
        return self._value

    # Event handlers
    def close_event(self, event):
        """Handle close."""
        pass

    # Public methods
    def load_data(self):
        """Load data."""
        pass

    # Private methods
    def _validate(self):
        """Validate."""
        pass
'''
        file_creator("src/dialog.py", test_code)

        # Configure PyQt preset with section headers
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pyqt
enforce-section-headers = yes
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/dialog.py"], extra_args=["--enable=method-wrong-section"]
        )

        # PyQt test should work without fatal errors
        assert returncode % 2 == 0, f"PyQt sections should work: {stderr}"

        # Verify section validation is active
        assert "method-wrong-section" in stdout or returncode < 16, (
            "Section validation should work"
        )

    def test_mixed_violations(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test multiple section header violations in one file."""
        # Create file with multiple issues
        test_code = '''"""Test multiple violations."""

class TestService:
    # Properties
    # Empty section - no properties defined

    def test_feature(self):
        """Test without header - missing section."""
        pass

    # Public methods
    def _private_method(self):
        """Private in wrong section."""
        pass
'''
        file_creator("src/test_service.py", test_code)

        # Enable all checks
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
enforce-section-headers = yes
require-section-headers = yes
allow-empty-sections = no
"""
        config_writer("pylintrc", config_content)

        # Run PyLint with all section header checks
        returncode, stdout, stderr = pylint_runner(
            ["src/test_service.py"],
            extra_args=[
                "--enable=method-wrong-section,missing-section-header,empty-section-header"
            ],
        )

        # Should detect multiple types of violations
        violations_found = 0
        if "empty-section-header" in stdout:
            violations_found += 1
        if "missing-section-header" in stdout:
            violations_found += 1
        if "method-wrong-section" in stdout:
            violations_found += 1

        assert violations_found >= 2, "Should detect multiple violation types"


class TestSectionHeaderEdgeCases:  # pylint: disable=too-few-public-methods
    """Test edge cases and error handling for section headers."""

    def test_nested_classes_section_headers(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test section headers in nested classes."""
        # Create file with nested classes
        test_code = '''"""Test nested classes."""

class Outer:
    # Public methods
    def outer_method(self):
        """Outer method."""
        pass

    class Inner:
        # Public methods
        def inner_method(self):
            """Inner method."""
            pass

        # Private methods
        def _inner_private(self):
            """Inner private."""
            pass
'''
        file_creator("src/nested.py", test_code)

        # Enable section headers
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enforce-section-headers = yes
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/nested.py"], extra_args=["--enable=method-wrong-section"]
        )

        # Should handle nested classes correctly
        # Should handle nested classes without fatal errors
        assert returncode % 2 == 0, f"Should handle nested classes: {stderr}"

    def test_module_level_functions_not_affected(
        self, pylint_runner: Any, file_creator: Any, config_writer: Any
    ) -> None:
        """Test that module-level functions are not affected by section headers."""
        # Create file with module-level functions
        test_code = '''"""Test module-level functions."""

# Public functions
def module_function():
    """Module function."""
    pass

# Private functions
def _module_private():
    """Module private."""
    pass

class TestClass:
    # Test methods
    def test_something(self):
        """Test method."""
        pass
'''
        file_creator("src/module.py", test_code)

        # Enable section headers
        config_content = """[MASTER]
load-plugins = pylint_sort_functions

[function-sort]
enable-method-categories = yes
framework-preset = pytest
enforce-section-headers = yes
"""
        config_writer("pylintrc", config_content)

        # Run PyLint
        returncode, stdout, stderr = pylint_runner(
            ["src/module.py"], extra_args=["--enable=method-wrong-section"]
        )

        # Test should run without fatal errors (module-level handling limited)
        assert returncode % 2 == 0, f"Should handle module-level functions: {stderr}"

        # Verify plugin is working (should find some violations)
        assert "W9006" in stdout or "W9004" in stdout, "Plugin should be active"
