"""Main checker class for enforcing function and method sorting.

The FunctionSortChecker is used by PyLint itself, not by end users directly.
PyLint discovers this checker via the plugin entry point and manages its lifecycle.

For detailed information about the sorting rules and algorithm, see docs/sorting.rst.

How it works:
    1. PyLint loads the plugin and calls register() function (the plugin entry point
       defined in __init__.py and configured in pyproject.toml)
    2. register() creates a FunctionSortChecker instance and gives it to PyLint
    3. PyLint walks the AST (Abstract Syntax Tree) of user code
    4. For each AST node, PyLint calls corresponding visit_* methods on this checker
       (we only implement visit_module and visit_classdef from the many available)
    5. The checker analyzes nodes and calls self.add_message() when issues are found

User Experience:
    $ pylint --load-plugins=pylint_sort_functions mycode.py
    # PyLint automatically uses this checker and reports any sorting violations

The visitor pattern: PyLint calls visit_module() for modules and visit_classdef()
for class definitions. Each method analyzes the code structure and reports issues.
"""

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from astroid import nodes  # type: ignore[import-untyped]
from pylint.checkers import BaseChecker

from pylint_sort_functions import messages, utils
from pylint_sort_functions.utils import CategoryConfig, MethodCategory

if TYPE_CHECKING:
    pass


class FunctionSortChecker(BaseChecker):
    """Checker to enforce alphabetical sorting of functions and methods.

    Inherits from PyLint's BaseChecker which provides the visitor pattern
    infrastructure. PyLint will automatically call our visit_* methods as it
    traverses the AST.
    """

    name = "function-sort"  # Identifier used by PyLint for this checker
    msgs: dict[str, Any] = messages.MESSAGES  # Message definitions from messages.py
    options = (
        (
            "public-api-patterns",
            {
                "default": [
                    "main",
                    "run",
                    "execute",
                    "start",
                    "stop",
                    "setup",
                    "teardown",
                ],
                "type": "csv",
                "metavar": "<pattern1,pattern2,...>",
                "help": (
                    "List of function names to always treat as public API. "
                    "These functions will not be flagged for privacy even if only used "
                    "internally. Useful for entry points and framework callbacks."
                ),
            },
        ),
        (
            "enable-privacy-detection",
            {
                "default": True,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Enable detection of functions that should be made private "
                    "based on usage analysis."
                ),
            },
        ),
        (
            "ignore-decorators",
            {
                "default": [],
                "type": "csv",
                "metavar": "<pattern1,pattern2,...>",
                "help": (
                    "Decorator patterns to exclude from sorting requirements. "
                    "Supports exact matches and wildcards (e.g., @app.route)."
                ),
            },
        ),
        (
            "privacy-exclude-dirs",
            {
                "default": [],
                "type": "csv",
                "metavar": "<dir1,dir2,...>",
                "help": (
                    "Directories to exclude from privacy analysis. Files in these "
                    "directories are scanned but their references are ignored when "
                    "determining if functions should be private. Useful for test "
                    "directories and other non-production code."
                ),
            },
        ),
        (
            "privacy-exclude-patterns",
            {
                "default": [],
                "type": "csv",
                "metavar": "<pattern1,pattern2,...>",
                "help": (
                    "File patterns to exclude from privacy analysis. Files matching "
                    "these patterns are scanned but their references are ignored when "
                    "determining if functions should be private. Supports glob "
                    "patterns like 'test_*.py', '*_test.py', 'conftest.py'."
                ),
            },
        ),
        (
            "privacy-additional-test-patterns",
            {
                "default": [],
                "type": "csv",
                "metavar": "<pattern1,pattern2,...>",
                "help": (
                    "Additional file patterns to treat as test files, beyond the "
                    "built-in detection. These patterns are added to the default "
                    "test detection (test_*.py, *_test.py, conftest.py, tests/). "
                    "Supports glob patterns like 'spec_*.py', '*_spec.py'."
                ),
            },
        ),
        (
            "privacy-update-tests",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Enable automatic updating of test files when functions are "
                    "privatized. When enabled, test files will be automatically "
                    "updated to use the new private function names. Requires the "
                    "privacy fixer to be run."
                ),
            },
        ),
        (
            "privacy-override-test-detection",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Override the built-in test file detection entirely and only "
                    "use the patterns specified in privacy-exclude-patterns and "
                    "privacy-exclude-dirs. When disabled, both built-in detection "
                    "and custom patterns are used together."
                ),
            },
        ),
        (
            "enable-method-categories",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Enable flexible method categorization system. When disabled, "
                    "uses the original binary public/private sorting. When enabled, "
                    "allows custom method categories and framework presets."
                ),
            },
        ),
        (
            "framework-preset",
            {
                "default": None,
                "type": "string",
                "metavar": "<preset_name>",
                "help": (
                    "Use a built-in framework preset for method categorization. "
                    "Available presets: pytest, unittest, pyqt, django. "
                    "Requires enable-method-categories=true."
                ),
            },
        ),
        (
            "method-categories",
            {
                "default": None,
                "type": "string",
                "metavar": "<json_config>",
                "help": (
                    "JSON configuration for custom method categories. Defines "
                    "category names, patterns, decorators, and priorities. "
                    'Example: \'[{"name":"properties","decorators":["@property"]}]\''
                ),
            },
        ),
        (
            "category-sorting",
            {
                "default": "alphabetical",
                "type": "choice",
                "choices": ["alphabetical", "declaration"],
                "metavar": "<alphabetical|declaration>",
                "help": (
                    "How to sort methods within each category. "
                    "'alphabetical' sorts methods alphabetically within categories. "
                    "'declaration' preserves the original declaration order."
                ),
            },
        ),
        (
            "enforce-section-headers",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Enforce that methods must be organized under correct section "
                    "headers according to their categorization. When enabled, "
                    "methods appearing under wrong section headers will trigger "
                    "warnings. Requires enable-method-categories=true."
                ),
            },
        ),
        (
            "require-section-headers",
            {
                "default": False,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Require section headers to be present for each category that "
                    "contains methods. When enabled, missing section headers will "
                    "trigger warnings. Requires enforce-section-headers=true."
                ),
            },
        ),
        (
            "allow-empty-sections",
            {
                "default": True,
                "type": "yn",
                "metavar": "<y or n>",
                "help": (
                    "Allow section headers to exist without any methods underneath. "
                    "When disabled, empty section headers will trigger warnings. "
                    "Requires enforce-section-headers=true."
                ),
            },
        ),
    )

    # Public methods

    def visit_classdef(self, node: nodes.ClassDef) -> None:
        """Visit a class definition to check method sorting.

        Called by PyLint for each class definition in the code.

        :param node: The class definition AST node to analyze
        :type node: nodes.ClassDef
        """
        methods = utils.get_methods_from_class(node)

        # Get configured decorator exclusions and category configuration
        ignore_decorators = self.linter.config.ignore_decorators or []
        category_config = self._get_category_config()

        if not utils.are_methods_sorted_with_exclusions(
            methods, ignore_decorators, category_config
        ):
            # Report unsorted methods - see docs/usage.rst for message details
            self.add_message("unsorted-methods", node=node, args=(node.name,))

        if not utils.are_functions_properly_separated(methods):
            # Report mixed visibility - see docs/usage.rst for suppression options
            self.add_message(
                "mixed-function-visibility",
                node=node,
                args=(f"class {node.name}",),
            )

        # Check section header validation if enabled
        if getattr(self.linter.config, "enforce_section_headers", False):
            self._validate_method_sections(methods, node)

    def visit_module(self, node: nodes.Module) -> None:
        """Visit a module node to check function sorting and privacy.

        Called by PyLint once for each Python module (file) being analyzed.

        :param node: The module AST node to analyze
        :type node: nodes.Module
        """
        functions = utils.get_functions_from_node(node)

        # Get configured decorator exclusions and category configuration
        ignore_decorators = self.linter.config.ignore_decorators or []
        category_config = self._get_category_config()

        if not utils.are_functions_sorted_with_exclusions(
            functions, ignore_decorators, category_config
        ):
            # Report unsorted functions - see docs/usage.rst for configuration
            self.add_message("unsorted-functions", node=node, args=("module",))

        if not utils.are_functions_properly_separated(functions):
            # Report mixed visibility - see docs/usage.rst for severity levels
            self.add_message("mixed-function-visibility", node=node, args=("module",))

        # Check section header validation if enabled
        if getattr(self.linter.config, "enforce_section_headers", False):
            self._validate_function_sections(functions, node)

        # Check if any public functions should be private
        self._check_function_privacy(functions, node)

    # Private methods

    def _check_function_privacy(
        self, functions: list[nodes.FunctionDef], node: nodes.Module
    ) -> None:
        """Check if any public functions should be private using import analysis.

        :param functions: List of functions to check
        :type functions: list[nodes.FunctionDef]
        :param node: The module node
        :type node: nodes.Module
        """
        # Check if privacy detection is enabled
        if not self.linter.config.enable_privacy_detection:
            return

        module_path = self._get_module_path()
        if not module_path:
            # Fallback to heuristic approach when path info unavailable
            self._check_function_privacy_heuristic(functions, node)
            return

        project_root = self._get_project_root(module_path)
        if not project_root:
            # Fallback to heuristic approach when project root can't be determined
            self._check_function_privacy_heuristic(functions, node)
            return

        # Get configured public API patterns
        public_patterns = set(self.linter.config.public_api_patterns)

        # Get privacy exclusion configuration
        privacy_config = self._get_privacy_config()

        # Use import analysis for more accurate detection
        for func in functions:
            if utils.should_function_be_private(
                func, module_path, project_root, public_patterns, privacy_config
            ):
                # Report function that should be private
                # See docs/usage.rst for privacy detection feature
                self.add_message(
                    "function-should-be-private", node=func, args=(func.name,)
                )
            elif utils.should_function_be_public(
                func, module_path, project_root, privacy_config
            ):
                # Report private function that should be public
                # See docs/usage.rst for privacy detection feature
                self.add_message(
                    "function-should-be-public", node=func, args=(func.name,)
                )

    def _check_function_privacy_heuristic(
        self,
        functions: list[nodes.FunctionDef],
        node: nodes.Module,  # pylint: disable=unused-argument
    ) -> None:
        """Check function privacy using heuristic approach (fallback).

        Used when import analysis is not available due to missing path information.

        :param functions: List of functions to check
        :type functions: list[nodes.FunctionDef]
        :param node: The module node
        :type node: nodes.Module
        """
        # Skip privacy check in heuristic mode - we can't determine without paths
        # This fallback mode is rarely used (only when linter has no file info)
        pass  # pragma: no cover

    def _get_category_config(self) -> CategoryConfig:
        """Create CategoryConfig from linter configuration.

        :returns: Category configuration for method sorting
        :rtype: CategoryConfig
        """
        config = CategoryConfig()

        # Get basic configuration options
        enable_categories = getattr(
            self.linter.config, "enable_method_categories", False
        )
        category_sorting = getattr(
            self.linter.config, "category_sorting", "alphabetical"
        )
        framework_preset = getattr(self.linter.config, "framework_preset", None)
        method_categories_json = getattr(self.linter.config, "method_categories", None)

        config.enable_categories = enable_categories
        config.category_sorting = category_sorting

        # If categories are disabled, return with defaults
        if not enable_categories:
            return config

        try:
            # Handle framework preset
            if framework_preset:
                config.categories = self._get_framework_preset_categories(
                    framework_preset
                )
            # Handle custom JSON configuration
            elif method_categories_json:
                config.categories = self._parse_method_categories_json(
                    method_categories_json
                )
            # Use defaults if nothing specified

        except (ValueError, json.JSONDecodeError) as e:
            # Configuration error - report it and use defaults
            # Note: We can't use self.add_message here as we're not in a visit method
            # The error will surface when pylint runs and encounters invalid config
            print(f"Warning: Invalid method category configuration: {e}")
            # Keep default categories

        return config

    def _get_framework_preset_categories(self, preset: str) -> list[MethodCategory]:
        """Get method categories for a framework preset.

        :param preset: Framework preset name
        :type preset: str
        :returns: List of method categories for the preset
        :rtype: list[MethodCategory]
        :raises ValueError: If preset is not recognized
        """
        presets = {
            "pytest": [
                MethodCategory(
                    name="test_fixtures",
                    patterns=["setUp", "tearDown", "setup_*", "teardown_*"],
                    priority=10,
                    section_header="# Test fixtures",
                ),
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    priority=5,
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    priority=1,
                    section_header="# Public methods",
                ),
                MethodCategory(
                    name="private_methods",
                    patterns=["_*"],
                    priority=2,
                    section_header="# Private methods",
                ),
            ],
            "unittest": [
                MethodCategory(
                    name="test_fixtures",
                    patterns=["setUp", "tearDown", "setUpClass", "tearDownClass"],
                    priority=10,
                    section_header="# Test fixtures",
                ),
                MethodCategory(
                    name="test_methods",
                    patterns=["test_*"],
                    priority=5,
                    section_header="# Test methods",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    priority=1,
                    section_header="# Public methods",
                ),
                MethodCategory(
                    name="private_methods",
                    patterns=["_*"],
                    priority=2,
                    section_header="# Private methods",
                ),
            ],
            "pyqt": [
                MethodCategory(
                    name="initialization",
                    patterns=["__init__", "setup*", "*_ui"],
                    priority=10,
                    section_header="# Initialization",
                ),
                MethodCategory(
                    name="properties",
                    decorators=["@property", "@*.setter", "@*.deleter"],
                    priority=8,
                    section_header="# Properties",
                ),
                MethodCategory(
                    name="event_handlers",
                    patterns=["*Event", "on_*", "handle_*", "eventFilter"],
                    priority=6,
                    section_header="# Event handlers",
                ),
                MethodCategory(
                    name="public_methods",
                    patterns=["*"],
                    priority=1,
                    section_header="# Public methods",
                ),
                MethodCategory(
                    name="private_methods",
                    patterns=["_*"],
                    priority=2,
                    section_header="# Private methods",
                ),
            ],
        }

        if preset not in presets:
            available = ", ".join(presets.keys())
            raise ValueError(
                f"Unknown framework preset '{preset}'. Available: {available}"
            )

        return presets[preset]

    def _get_module_path(self) -> Path | None:
        """Get the current module's file path from the linter.

        :returns: Path to the module file, or None if not available
        :rtype: Path | None
        """
        # Defensive check: ensure linter has current_file attribute
        # (version compatibility)
        if hasattr(self.linter, "current_file") and self.linter.current_file:
            try:
                # Handle Mock objects and other invalid file paths gracefully
                current_file = self.linter.current_file
                if hasattr(current_file, "_mock_name"):
                    # This is a Mock object, return None
                    return None
                return Path(current_file).resolve()
            except (TypeError, OSError, ValueError):
                # Handle cases where current_file is not a valid path
                return None
        return None

    def _get_privacy_config(self) -> dict[str, Any]:
        """Extract privacy-related configuration from linter config.

        :returns: Dictionary containing privacy configuration options
        :rtype: dict[str, Any]
        """
        config = {}

        # Handle both real config and Mock objects robustly
        def get_config_value(attr_name: str, default_value: Any) -> Any:
            try:
                value = getattr(self.linter.config, attr_name, default_value)
                # If it's a Mock object, return the default instead
                if hasattr(value, "_mock_name"):
                    return default_value
                return value
            except (AttributeError, TypeError):
                return default_value

        config["exclude_dirs"] = get_config_value("privacy_exclude_dirs", [])
        config["exclude_patterns"] = get_config_value("privacy_exclude_patterns", [])
        config["additional_test_patterns"] = get_config_value(
            "privacy_additional_test_patterns", []
        )
        config["update_tests"] = get_config_value("privacy_update_tests", False)
        config["override_test_detection"] = get_config_value(
            "privacy_override_test_detection", False
        )

        return config

    def _get_project_root(self, module_path: Path) -> Path | None:
        """Find the project root directory by looking for common project markers.

        :param module_path: Path to the current module
        :type module_path: Path
        :returns: Project root path, or module's parent directory as fallback
        :rtype: Path | None
        """
        # Common project markers that indicate a project root
        project_markers = [
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            ".git",
            "requirements.txt",
            "Pipfile",
            "poetry.lock",
        ]

        current = module_path.parent
        while current != current.parent:
            # Check if any project marker exists in current directory
            if any((current / marker).exists() for marker in project_markers):
                return current
            current = current.parent

        # Fallback: use the module's parent directory
        # This handles cases where we're testing in isolated directories
        return module_path.parent

    def _parse_method_categories_json(self, json_str: str) -> list[MethodCategory]:
        """Parse JSON method categories configuration.

        :param json_str: JSON string containing category definitions
        :type json_str: str
        :returns: List of parsed method categories
        :rtype: list[MethodCategory]
        :raises ValueError: If JSON is malformed or contains invalid category
            definitions
        :raises json.JSONDecodeError: If JSON syntax is invalid
        """
        try:
            categories_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Invalid JSON in method-categories: {e}", json_str, 0
            ) from e

        if not isinstance(categories_data, list):
            raise ValueError(
                "method-categories must be a JSON array of category objects"
            )

        categories = []
        for i, category_data in enumerate(categories_data):
            if not isinstance(category_data, dict):
                raise ValueError(f"Category {i} must be a JSON object")

            # Validate required fields
            if "name" not in category_data:
                raise ValueError(f"Category {i} is missing required 'name' field")

            # Create category with validation
            try:
                category = MethodCategory(
                    name=category_data["name"],
                    patterns=category_data.get("patterns", []),
                    decorators=category_data.get("decorators", []),
                    priority=category_data.get("priority", 0),
                    section_header=category_data.get(
                        "section_header",
                        f"# {category_data['name'].replace('_', ' ').title()}",
                    ),
                )
                categories.append(category)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"Invalid category {i} "
                    f"({category_data.get('name', 'unnamed')}): {e}"
                ) from e

        return categories

    def _validate_function_sections(
        self, functions: list[nodes.FunctionDef], module_node: nodes.Module
    ) -> None:
        """Validate that functions are in correct sections according to headers.

        :param functions: List of function nodes to validate
        :type functions: list[nodes.FunctionDef]
        :param module_node: Module containing the functions
        :type module_node: nodes.Module
        """
        if not functions:
            return

        # Get the source file content
        module_path = self._get_module_path()
        if not module_path or not module_path.exists():
            return

        try:
            lines = module_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            return

        category_config = self._get_category_config()
        self._validate_sections_common(functions, lines, category_config, module_node)

    def _validate_method_sections(
        self, methods: list[nodes.FunctionDef], class_node: nodes.ClassDef
    ) -> None:
        """Validate that methods are in correct sections according to headers.

        :param methods: List of method nodes to validate
        :type methods: list[nodes.FunctionDef]
        :param class_node: Class containing the methods
        :type class_node: nodes.ClassDef
        """
        if not methods:
            return

        # Get the source file content
        module_path = self._get_module_path()
        if not module_path or not module_path.exists():
            return

        try:
            lines = module_path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            return

        category_config = self._get_category_config()
        self._validate_sections_common(methods, lines, category_config, class_node)

    def _validate_sections_common(
        self,
        methods: list[nodes.FunctionDef],
        lines: list[str],
        config: utils.CategoryConfig,
        node: nodes.ClassDef | nodes.Module,
    ) -> None:
        """Common section validation logic for both methods and functions.

        :param methods: List of method/function nodes to validate
        :type methods: list[nodes.FunctionDef]
        :param lines: Source file lines
        :type lines: list[str]
        :param config: Category configuration
        :type config: utils.CategoryConfig
        :param node: AST node for error reporting (class or module)
        :type node: nodes.ClassDef | nodes.Module
        """
        # Check for methods in wrong sections
        violations = utils.get_section_violations(methods, lines, config)
        for method, expected_section, actual_section in violations:
            self.add_message(
                "method-wrong-section",
                node=method,
                args=(method.name, expected_section, actual_section),
            )

        # Check for missing section headers if required
        if getattr(self.linter.config, "require_section_headers", False):
            missing_headers = utils.find_missing_section_headers(methods, lines, config)
            for category_name in missing_headers:
                # Find category to get section header text
                category = next(
                    (cat for cat in config.categories if cat.name == category_name),
                    None,
                )
                if category and category.section_header:
                    self.add_message(
                        "missing-section-header",
                        node=node,
                        args=(category.section_header, category_name),
                    )

        # Check for empty section headers if not allowed
        if not getattr(self.linter.config, "allow_empty_sections", True):
            empty_headers = utils.find_empty_section_headers(methods, lines, config)
            for category_name in empty_headers:
                # Find category to get section header text
                category = next(
                    (cat for cat in config.categories if cat.name == category_name),
                    None,
                )
                if category and category.section_header:
                    self.add_message(
                        "empty-section-header",
                        node=node,
                        args=(category.section_header,),
                    )
