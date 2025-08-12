#!/usr/bin/env python3
"""
Shared pytest fixtures for integration tests.

This module provides common test infrastructure to eliminate duplication
across integration test files and ensure consistent test setup.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Generator, List, Optional, Tuple

import pytest


@pytest.fixture
def assert_no_syntax_errors() -> Callable[[Path], bool]:
    """
    Provide a helper function to verify Python syntax.

    Returns:
        Callable: Function that checks if content has valid Python syntax
    """

    def check_syntax(file_path: Path) -> bool:
        """
        Check if a Python file has valid syntax.

        Args:
            file_path: Path to Python file to check

        Returns:
            bool: True if syntax is valid, False otherwise
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            compile(content, str(file_path), "exec")
            return True
        except SyntaxError:
            return False

    return check_syntax


# Helper class for complex test scenarios

# Cleanup is handled automatically by tmp_path fixture


@pytest.fixture
def cli_runner(test_project: Path) -> Callable[[List[str]], Tuple[int, str, str]]:
    """
    Factory fixture for running CLI commands in the test project.

    Args:
        test_project: The test project fixture

    Returns:
        Callable: A function that runs CLI commands and returns results
    """
    # Find the pylint-sort-functions CLI module
    project_root = Path(__file__).parent.parent.parent
    cli_module = str(project_root / "src" / "pylint_sort_functions" / "cli.py")
    python_executable = sys.executable

    def run_command(
        args: List[str], cwd: Optional[Path] = None, use_project_root: bool = True
    ) -> Tuple[int, str, str]:
        """
        Run pylint-sort-functions CLI command and return results.

        Args:
            args: Command line arguments to pass to the CLI
            cwd: Working directory for command execution (defaults to test_project)
            use_project_root: Whether to use test_project as cwd (default: True)

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        # Set up environment
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)

        # Determine working directory
        if cwd is None and use_project_root:
            cwd = test_project

        # Build command
        cmd = [python_executable, cli_module] + args

        # Execute command
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, env=env, check=False
        )

        return result.returncode, result.stdout, result.stderr

    return run_command


@pytest.fixture
def config_writer(test_project: Path) -> Callable[[str, str], Path]:
    """
    Factory fixture for creating PyLint configuration files.

    Args:
        test_project: The test project fixture

    Returns:
        Callable: A function that creates .pylintrc or pyproject.toml configs
    """

    def write_config(config_type: str, content: str) -> Path:
        """
        Write a PyLint configuration file.

        Args:
            config_type: Either "pylintrc" or "pyproject.toml"
            content: Configuration content

        Returns:
            Path: The created configuration file
        """
        if config_type == "pylintrc":
            config_path = test_project / ".pylintrc"
        elif config_type == "pyproject.toml":
            config_path = test_project / "pyproject.toml"
        else:
            raise ValueError(f"Unknown config type: {config_type}")

        config_path.write_text(content, encoding="utf-8")
        return config_path

    return write_config


@pytest.fixture
def file_creator(test_project: Path) -> Callable[[str, str], Path]:
    """
    Factory fixture for creating test files within the project.

    Args:
        test_project: The test project fixture

    Returns:
        Callable: A function that creates files with given content
    """

    def create_file(relative_path: str, content: str) -> Path:
        """
        Create a test file with specified content.

        Args:
            relative_path: Path relative to project root (e.g., "src/module.py")
            content: Content to write to the file

        Returns:
            Path: The created file's absolute path
        """
        file_path = test_project / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    return create_file


@pytest.fixture
def pylint_runner(
    test_project: Path,
) -> Callable[[List[str], Optional[List[str]]], Tuple[int, str, str]]:
    """
    Factory fixture for running PyLint with the plugin loaded.

    Args:
        test_project: The test project fixture

    Returns:
        Callable: A function that runs PyLint with the plugin
    """

    def run_pylint(
        files: List[str],
        extra_args: Optional[List[str]] = None,
        cwd: Optional[Path] = None,
    ) -> Tuple[int, str, str]:
        """
        Run PyLint with pylint-sort-functions plugin loaded.

        Args:
            files: List of files to check (relative to project root)
            extra_args: Additional PyLint arguments
            cwd: Working directory (defaults to test_project)

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        if cwd is None:
            cwd = test_project

        # Build PyLint command
        cmd = [
            sys.executable,
            "-m",
            "pylint",
            "--load-plugins=pylint_sort_functions",
        ]

        if extra_args:
            cmd.extend(extra_args)

        cmd.extend(files)

        # Set up environment
        env = os.environ.copy()
        project_root = Path(__file__).parent.parent.parent
        env["PYTHONPATH"] = str(project_root)

        # Execute command
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, env=env, check=False
        )

        return result.returncode, result.stdout, result.stderr

    return run_pylint


@pytest.fixture
def sample_test_class() -> dict[str, str]:
    """
    Provide sample test class code for framework preset testing.

    Returns:
        dict: Dictionary with sample code for different frameworks
    """
    return {
        "pytest": '''"""Test module using pytest."""

class TestExample:
    def setup_method(self):
        """Setup test fixtures."""
        self.data = []

    def teardown_method(self):
        """Cleanup after test."""
        self.data.clear()

    def test_feature_a(self):
        """Test feature A."""
        assert True

    def test_feature_b(self):
        """Test feature B."""
        assert True

    def helper_method(self):
        """Public helper for tests."""
        return "help"

    def _private_helper(self):
        """Private test helper."""
        return "private"
''',
        "unittest": '''"""Test module using unittest."""

import unittest

class TestExample(unittest.TestCase):
    def setUp(self):
        """Setup test fixtures."""
        self.data = []

    def tearDown(self):
        """Cleanup after test."""
        self.data.clear()

    def test_feature_a(self):
        """Test feature A."""
        self.assertTrue(True)

    def test_feature_b(self):
        """Test feature B."""
        self.assertTrue(True)

    def assert_custom(self, value):
        """Custom assertion helper."""
        self.assertIsNotNone(value)

    def _create_fixture(self):
        """Private fixture creator."""
        return {"test": "data"}
''',
        "pyqt": '''"""PyQt dialog example."""

from PyQt5.QtWidgets import QDialog

class ExampleDialog(QDialog):
    def __init__(self, parent=None):
        """Initialize dialog."""
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        """Setup user interface."""
        self.setWindowTitle("Example")

    @property
    def current_value(self):
        """Get current value."""
        return self._value

    @current_value.setter
    def current_value(self, value):
        """Set current value."""
        self._value = value

    def closeEvent(self, event):
        """Handle close event."""
        event.accept()

    def keyPressEvent(self, event):
        """Handle key press."""
        super().keyPressEvent(event)

    def load_data(self):
        """Load data into dialog."""
        pass

    def save_data(self):
        """Save dialog data."""
        pass

    def _validate_input(self):
        """Validate user input."""
        return True

    def _update_display(self):
        """Update display elements."""
        pass
''',
    }


@pytest.fixture
def test_project(tmp_path: Any) -> Generator[Path, None, None]:
    """
    Create a temporary Python project structure for testing.

    Creates a project with:
    - test_project/ root directory
    - test_project/src/ package directory
    - test_project/src/__init__.py package marker

    Yields:
        Path: The project root directory path
    """
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create standard Python package structure
    src_dir = project_root / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").touch()

    yield project_root


class IntegrationTestHelper:
    """Helper class with utilities for integration testing."""

    @staticmethod
    def create_import_chain(
        file_creator: Callable[[str, str], Path],
    ) -> dict[str, Path]:
        """
        Create modules with import dependencies for testing.

        Args:
            file_creator: The file_creator fixture

        Returns:
            dict: Dictionary mapping module names to paths
        """
        # Module A (base module)
        module_a = file_creator(
            "src/module_a.py",
            '''"""Module A."""

def public_api():
    """Public API function."""
    return _internal_helper()

def _internal_helper():
    """Internal helper."""
    return "help"
''',
        )

        # Module B (imports from A)
        module_b = file_creator(
            "src/module_b.py",
            '''"""Module B."""

from src.module_a import public_api

def use_module_a():
    """Use module A's API."""
    return public_api()
''',
        )

        # Module C (imports from B)
        module_c = file_creator(
            "src/module_c.py",
            '''"""Module C."""

from src.module_b import use_module_a

def final_usage():
    """Final usage in chain."""
    return use_module_a()
''',
        )

        return {"module_a": module_a, "module_b": module_b, "module_c": module_c}

    @staticmethod
    def create_multi_module_project(
        file_creator: Callable[[str, str], Path], num_modules: int = 3
    ) -> List[Path]:
        """
        Create a project with multiple interdependent modules.

        Args:
            file_creator: The file_creator fixture
            num_modules: Number of modules to create

        Returns:
            List[Path]: List of created module paths
        """
        modules = []
        for i in range(num_modules):
            content = f'''"""Module {i}."""

def public_function_{i}():
    """Public API function."""
    return helper_{i}()

def helper_{i}():
    """Helper function."""
    return "help {i}"

def _private_{i}():
    """Private function."""
    return "private {i}"
'''
            module_path = file_creator(f"src/module_{i}.py", content)
            modules.append(module_path)

        return modules
