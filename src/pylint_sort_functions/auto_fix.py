"""Auto-fix functionality for sorting functions and methods."""
# pylint: disable=too-many-lines

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import utils
from pylint_sort_functions.utils.categorization import CategoryConfig, categorize_method


@dataclass
class FunctionSpan:
    """Represents a function with its complete text span in the source file."""

    node: nodes.FunctionDef
    start_line: int
    end_line: int
    text: str  # Complete source text from start_line to end_line (inclusive)
    name: str


@dataclass
class AutoFixConfig:  # pylint: disable=too-many-instance-attributes
    """Configuration for the automatic function sorting tool.

    Controls how the auto-fix feature behaves when reordering functions
    and methods in Python source files.

    Note: Comment preservation is always enabled as it's essential for
    maintaining code intent and documentation during reorganization.
    """

    dry_run: bool = False  # Show what would be changed without modifying files
    backup: bool = True  # Create .bak files before making changes
    ignore_decorators: Optional[List[str]] = (
        None  # Decorator patterns to exclude from sorting
    )

    # Section header configuration
    add_section_headers: bool = False  # Add section headers during sorting
    public_header: str = "# Public functions"  # Header text for public functions
    private_header: str = "# Private functions"  # Header text for private functions
    public_method_header: str = "# Public methods"  # Header text for public methods
    private_method_header: str = "# Private methods"  # Header text for private methods

    # Section header detection configuration
    additional_section_patterns: Optional[List[str]] = (
        None  # Extra patterns to detect as headers
    )
    section_header_case_sensitive: bool = False  # Case sensitivity for header detection

    # Multi-category system integration
    category_config: Optional[CategoryConfig] = None  # Use new categorization system
    enable_multi_category_headers: bool = False  # Enable multi-category section headers


# Note: This class intentionally has only one public method as it encapsulates
# the configuration state and provides a clean interface for file processing.
class FunctionSorter:  # pylint: disable=too-many-public-methods,too-few-public-methods
    """Main class for auto-fixing function sorting.

    This class provides the core functionality for automatically reordering
    functions and methods in Python source files to comply with sorting rules.

    Supports both traditional binary public/private sorting and the new
    multi-category system with flexible section headers.

    Basic Usage:
        Used by the CLI tool (cli.py) and can be used programmatically:

        config = AutoFixConfig(dry_run=True, backup=True)
        sorter = FunctionSorter(config)
        was_modified = sorter.sort_file(Path("my_file.py"))

    Multi-Category Usage:
        Enhanced functionality with custom categories and section headers:

        from pylint_sort_functions.utils import CategoryConfig, MethodCategory

        # Define custom categories
        category_config = CategoryConfig(
            enable_categories=True,
            categories=[
                MethodCategory(name="test_methods", patterns=["test_*"],
                             section_header="# Test methods"),
                MethodCategory(name="properties", decorators=["@property"],
                             section_header="# Properties"),
                MethodCategory(name="public_methods", patterns=["*"],
                             section_header="# Public methods"),
                MethodCategory(name="private_methods", patterns=["_*"],
                             section_header="# Private methods"),
            ]
        )

        # Configure auto-fix with multi-category support
        config = AutoFixConfig(
            add_section_headers=True,
            enable_multi_category_headers=True,
            category_config=category_config
        )

        sorter = FunctionSorter(config)
        was_modified = sorter.sort_file(Path("my_file.py"))
    """

    # Public methods

    def __init__(self, config: AutoFixConfig):
        """Initialize the function sorter.

        :param config: Configuration for auto-fix behavior
        :type config: AutoFixConfig
        """
        self.config = config
        if self.config.ignore_decorators is None:
            self.config.ignore_decorators = []

    def sort_file(self, file_path: Path) -> bool:
        """Auto-sort functions in a Python file.

        :param file_path: Path to the Python file to sort
        :type file_path: Path
        :returns: True if file was modified, False otherwise
        :rtype: bool
        """
        try:
            # Read the original file
            original_content = file_path.read_text(encoding="utf-8")

            # Check if file needs sorting
            if not self._file_needs_sorting(original_content):
                return False

            # Extract and sort functions
            new_content = self._sort_functions_in_content(original_content)

            if new_content == original_content:  # pragma: no cover
                return False

            # CRITICAL FIX: Validate syntax after transformation
            validated_content = self._validate_syntax_and_rollback(
                file_path, original_content, new_content
            )

            # If validation rolled back to original, no changes were made
            if validated_content == original_content:
                return False

            if self.config.dry_run:
                print(f"Would modify: {file_path}")
                return True

            # Create backup if requested
            if self.config.backup:
                backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
                shutil.copy2(file_path, backup_path)

            # Write the validated sorted content
            file_path.write_text(validated_content, encoding="utf-8")
            return True

        # Broad exception catch ensures tool never crashes when modifying user files
        except (
            Exception
        ) as e:  # pragma: no cover  # pylint: disable=broad-exception-caught
            print(f"Error processing {file_path}: {e}")
            return False

    # Private methods

    def _add_multi_category_section_headers_to_functions(
        self, sorted_spans: List[FunctionSpan], is_methods: bool = False
    ) -> List[str]:
        """Add multi-category section headers to sorted function spans.

        This enhanced version supports the new categorization system with multiple
        categories beyond just public/private. Each category gets its own section
        header based on the CategoryConfig.

        :param sorted_spans: Function spans in sorted order by category
        :type sorted_spans: List[FunctionSpan]
        :param is_methods: True if these are class methods, False for module functions
        :type is_methods: bool
        :returns: List of text lines with category headers and functions
        :rtype: List[str]
        """
        if (
            not self.config.enable_multi_category_headers
            or not self.config.category_config
        ):
            # Fall back to original binary public/private headers
            return self._add_section_headers_to_functions(sorted_spans, is_methods)

        if not self.config.add_section_headers:
            # If section headers are disabled, just return function texts
            result = []
            for i, span in enumerate(sorted_spans):
                result.append(span.text)
                if i < len(sorted_spans) - 1 and not span.text.endswith("\n\n"):
                    if not span.text.endswith("\n"):
                        result.append("\n")
                    result.append("\n")
            return result

        result_lines: list[str] = []
        current_category = None

        for span in sorted_spans:
            # Determine the category for this function/method
            category = categorize_method(span.node, self.config.category_config)

            # Add section header if we're entering a new category
            if current_category != category:
                # Add blank line before section header (except at the very beginning)
                if result_lines:
                    result_lines.append("\n")

                # Find the category definition to get section header text
                category_def = None
                for cat in self.config.category_config.categories:
                    if cat.name == category:
                        category_def = cat
                        break

                # Add section header if category has one defined
                if category_def and category_def.section_header:
                    result_lines.append(f"{category_def.section_header}\n\n")
                else:
                    # Fallback to generic header based on category name
                    header_text = category.replace("_", " ").title()
                    result_lines.append(f"# {header_text}\n\n")

                current_category = category

            # Add the function text
            result_lines.append(span.text)

        return result_lines

    def _add_section_headers_to_functions(  # pylint: disable=too-many-branches
        self, sorted_spans: List[FunctionSpan], is_methods: bool = False
    ) -> List[str]:
        """Add section headers to sorted function spans.

        Creates a list of lines that includes both section headers and function text,
        organized with public functions first, then private functions.

        :param sorted_spans: Function spans in sorted order (public first, then private)
        :type sorted_spans: List[FunctionSpan]
        :param is_methods: True if these are class methods, False for module functions
        :type is_methods: bool
        :returns: List of text lines with headers and functions
        :rtype: List[str]
        """
        if not self.config.add_section_headers:
            # If section headers are disabled, just return function texts with spacing
            result = []
            for i, span in enumerate(sorted_spans):
                result.append(span.text)
                # Ensure proper spacing between functions if not already included
                if i < len(sorted_spans) - 1 and not span.text.endswith("\n\n"):
                    if not span.text.endswith("\n"):
                        result.append("\n")
                    result.append("\n")
            return result

        if not self._has_mixed_visibility_functions(sorted_spans):
            # Only add headers when both public and private functions exist
            # Still ensure proper spacing between functions
            result = []
            for i, span in enumerate(sorted_spans):
                result.append(span.text)
                # Ensure proper spacing between functions if not already included
                if i < len(sorted_spans) - 1 and not span.text.endswith("\n\n"):
                    if not span.text.endswith("\n"):
                        result.append("\n")  # pragma: no cover
                    result.append("\n")
            return result

        result_lines: list[str] = []
        current_visibility = None  # Track whether we're in public or private section

        # Get appropriate header texts based on function type
        if is_methods:
            public_header = self.config.public_method_header
            private_header = self.config.private_method_header
        else:
            public_header = self.config.public_header
            private_header = self.config.private_header

        for i, span in enumerate(sorted_spans):
            is_private = utils.is_private_function(span.node)
            section_visibility = "private" if is_private else "public"

            # Add section header if we're entering a new section
            if current_visibility != section_visibility:
                # Add blank line before section header (except at the very beginning)
                if result_lines:
                    result_lines.append("\n")

                # Add appropriate section header
                if section_visibility == "public":
                    result_lines.append(f"{public_header}\n\n")
                else:
                    result_lines.append(f"{private_header}\n\n")

                current_visibility = section_visibility

            # Add the function text
            result_lines.append(span.text)

        return result_lines

    def _extract_function_spans(
        self, functions: List[nodes.FunctionDef], lines: List[str], module: nodes.Module
    ) -> List[FunctionSpan]:
        """Extract function text spans from the source.

        :param functions: List of function nodes
        :type functions: List[nodes.FunctionDef]
        :param lines: Source file lines
        :type lines: List[str]
        :param module: Module containing the functions
        :type module: nodes.Module
        :returns: List of function spans with text
        :rtype: List[FunctionSpan]
        """
        spans = []

        # First pass: determine where each function (including comments) starts
        function_boundaries = []
        for func in functions:
            start_line = func.lineno - 1  # Convert to 0-based indexing

            # Include decorators in the span
            actual_start = start_line
            if hasattr(func, "decorators") and func.decorators:
                actual_start = func.decorators.lineno - 1

            # Include comments above the function/decorators
            comment_start = self._find_comments_above_function(lines, actual_start)
            function_boundaries.append((func, comment_start))

        # Second pass: create spans using the boundaries
        for i, (func, comment_start) in enumerate(function_boundaries):
            # Find the end line (start of next function or end of file)
            if i + 1 < len(function_boundaries):
                # End where the next function's comments start
                end_line = function_boundaries[i + 1][1]
            else:
                # Last function, find the actual end using AST boundary detection
                end_line = self._find_function_end(lines, func, module)

            # Extract the text including comments
            text = "".join(lines[comment_start:end_line])

            spans.append(
                FunctionSpan(
                    node=func,
                    start_line=comment_start,
                    end_line=end_line,
                    text=text,
                    name=func.name,
                )
            )

        return spans

    def _extract_method_spans(
        self,
        methods: List[nodes.FunctionDef],
        lines: List[str],
        class_node: nodes.ClassDef,
    ) -> List[FunctionSpan]:
        """Extract method text spans from a class.

        :param methods: List of method nodes from the class
        :type methods: List[nodes.FunctionDef]
        :param lines: Source file lines
        :type lines: List[str]
        :param class_node: The class containing these methods
        :type class_node: nodes.ClassDef
        :returns: List of method spans with text
        :rtype: List[FunctionSpan]
        """
        spans = []

        # First pass: determine where each method (including comments) starts
        method_boundaries = []
        for method in methods:
            start_line = method.lineno - 1  # Convert to 0-based indexing

            # Include decorators in the span
            actual_start = start_line
            if hasattr(method, "decorators") and method.decorators:
                actual_start = method.decorators.lineno - 1

            # Include comments above the method/decorators
            comment_start = self._find_comments_above_function(lines, actual_start)
            method_boundaries.append((method, comment_start))

        # Second pass: create spans using the boundaries
        for i, (method, comment_start) in enumerate(method_boundaries):
            # Find the end line (start of next method or end of class)
            if i + 1 < len(method_boundaries):
                # End where the next method's comments start
                end_line = method_boundaries[i + 1][1]
            else:
                # Last method in class, find end of class
                end_line = (
                    class_node.end_lineno
                    if hasattr(class_node, "end_lineno")
                    else len(lines)
                )

            # Extract the text including comments
            text = "".join(lines[comment_start:end_line])

            spans.append(
                FunctionSpan(
                    node=method,
                    start_line=comment_start,
                    end_line=end_line,
                    text=text,
                    name=method.name,
                )
            )

        return spans

    def _file_needs_sorting(self, content: str) -> bool:
        """Check if a file needs function sorting.

        :param content: File content as string
        :type content: str
        :returns: True if file needs sorting
        :rtype: bool
        """
        try:  # pylint: disable=too-many-nested-blocks
            # Parse with astroid for consistency with the checker
            module = astroid.parse(content)

            # Check module-level functions
            functions = utils.get_functions_from_node(module)
            if functions:
                sorted_result = utils.are_functions_sorted_with_exclusions(
                    functions, self.config.ignore_decorators
                )
                if not sorted_result:
                    return True
                # Even if sorted, check if we need to add section headers
                if self.config.add_section_headers:
                    function_spans = self._extract_function_spans(
                        functions, content.splitlines(), module
                    )
                    if self._has_mixed_visibility_functions(function_spans):
                        return True

            # Check class methods
            for node in module.body:
                if isinstance(node, nodes.ClassDef):
                    methods = utils.get_methods_from_class(node)
                    if methods:
                        if not utils.are_methods_sorted_with_exclusions(
                            methods, self.config.ignore_decorators
                        ):
                            return True
                        # Even if sorted, check if we need to add section headers
                        if self.config.add_section_headers:
                            method_spans = self._extract_method_spans(
                                methods, content.splitlines(), node
                            )
                            if self._has_mixed_visibility_functions(method_spans):
                                return True

            return False

        except Exception:  # pylint: disable=broad-exception-caught
            return False

    def _find_comments_above_function(
        self, lines: List[str], function_start_line: int
    ) -> int:
        """Find comments that belong to a function and return the start line.

        Scans backwards from the function definition to find associated comments.
        Excludes section header comments that should remain at section boundaries.

        :param lines: Source file lines
        :type lines: List[str]
        :param function_start_line: The line where the function starts (0-based)
        :type function_start_line: int
        :returns: The line number where comments start, or function_start_line
        :rtype: int
        """
        comment_start_line = function_start_line

        # Scan backwards from the function start to find comments
        current_line = function_start_line - 1
        found_function_comments = []

        while current_line >= 0:
            line = lines[current_line].strip()

            # If we find a comment line, this could be part of the function's comments
            if line.startswith("#"):
                # Check if this is a section header comment
                if self._is_section_header_comment(line):
                    # Section headers should not move with functions
                    # Stop including comments here
                    break

                # This is a function-specific comment
                found_function_comments.append(current_line)
                comment_start_line = current_line
                current_line -= 1
                continue

            # If we find an empty line, continue scanning (comments might be separated)
            if line == "":
                current_line -= 1
                continue

            # If we find any other content, stop scanning
            break

        return comment_start_line

    def _find_existing_section_headers(self, lines: List[str]) -> Dict[str, int]:
        """Find existing section headers in the source lines.

        Returns a mapping of header types to their line numbers (0-based).
        This helps avoid duplicating headers during automatic insertion.

        :param lines: Source file lines
        :type lines: List[str]
        :returns: Dictionary mapping header type to line number
        :rtype: dict[str, int]
        """
        headers = {}

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue

            # Check if this matches any of our configured header patterns
            lower_line = stripped.lower()

            # Check for public function headers
            if any(
                keyword in lower_line
                for keyword in ["public functions", "public function"]
            ):
                headers["public_functions"] = i
            # Check for private function headers
            elif any(
                keyword in lower_line
                for keyword in ["private functions", "private function"]
            ):
                headers["private_functions"] = i
            # Check for public method headers
            elif any(
                keyword in lower_line for keyword in ["public methods", "public method"]
            ):
                headers["public_methods"] = i
            # Check for private method headers
            elif any(
                keyword in lower_line
                for keyword in ["private methods", "private method"]
            ):
                headers["private_methods"] = i

        return headers

    def _find_function_end(
        self, lines: List[str], func: nodes.FunctionDef, module: nodes.Module
    ) -> int:
        """Find the actual end line of a function using AST-based boundary detection.

        This method uses the module's AST to properly detect where module-level
        constructs (assignments, if statements, other functions/classes) begin,
        providing accurate boundaries without hardcoded pattern matching.

        :param lines: Source file lines
        :type lines: List[str]
        :param func: Function node
        :type func: nodes.FunctionDef
        :param module: Module containing the function
        :type module: nodes.Module
        :returns: Line number where function ends (exclusive)
        :rtype: int
        """
        func_end = func.end_lineno

        # Find the next module-level construct after this function
        next_construct_line = None
        for node in module.body:
            if node.lineno > func_end:
                # This is the first construct after our function
                next_construct_line = node.lineno
                break

        # If no module-level constructs follow, scan forward for trailing content
        if next_construct_line is None:
            # Look forward to include trailing comments/blank lines
            i = func_end
            while i < len(lines):
                line = lines[i].strip()
                # Include blank lines and comments that follow the function
                if line == "" or line.startswith("#"):
                    i += 1
                    continue
                # Stop at any non-empty, non-comment content
                break  # pragma: no cover
            return int(i)

        # We have a next construct - scan up to it, including preceding comments
        i = func_end
        while i < next_construct_line and i < len(lines):
            line = lines[i].strip()

            # Include blank lines and comments
            if line == "" or line.startswith("#"):
                i += 1
                continue

            # Stop if we hit content that belongs to the next construct
            # (e.g., assignment statements, other code)
            break

        return int(i)

    def _has_mixed_visibility_functions(self, spans: List[FunctionSpan]) -> bool:
        """Check if spans contain both public and private functions.

        Only add section headers when there are both public and private functions,
        as per the requirement in issue #9.

        :param spans: List of function spans to analyze
        :type spans: List[FunctionSpan]
        :returns: True if both public and private functions exist
        :rtype: bool
        """
        has_public = False
        has_private = False

        for span in spans:
            if utils.is_private_function(span.node):
                has_private = True
            else:
                has_public = True

            # Early exit if we've found both types
            if has_public and has_private:
                return True

        return False

    def _is_section_header_comment(self, comment_line: str) -> bool:
        """Check if a comment line is a section header.

        Section headers are comments that organize groups of functions/methods.
        This method uses configurable patterns and automatically includes
        the configured header texts from the AutoFixConfig.

        :param comment_line: The comment line to check (already stripped)
        :type comment_line: str
        :returns: True if this is likely a section header comment
        :rtype: bool
        """
        # Determine case sensitivity
        comparison_comment = (
            comment_line
            if self.config.section_header_case_sensitive
            else comment_line.lower()
        )

        # Build list of all patterns to check
        patterns_to_check = []

        # 1. Always include configured header texts (what we insert, we detect)
        configured_headers = [
            self.config.public_header,
            self.config.private_header,
            self.config.public_method_header,
            self.config.private_method_header,
        ]

        # 1a. Add multi-category headers if enabled
        if self.config.enable_multi_category_headers and self.config.category_config:
            for category in self.config.category_config.categories:
                if category.section_header:
                    configured_headers.append(category.section_header)

        for header in configured_headers:
            pattern = (
                header if self.config.section_header_case_sensitive else header.lower()
            )
            patterns_to_check.append(pattern)

        # 2. Add default fallback patterns for backward compatibility
        default_keywords = [
            "public functions",
            "private functions",
            "public methods",
            "private methods",
            "helper functions",
            "utility functions",
            "api functions",
            "internal functions",
            "exports",
            "imports",
        ]

        default_organizational = [
            "# functions",
            "# methods",
            "## functions",
            "## methods",
            "--- functions",
            "--- methods",
            "=== functions",
            "=== methods",
        ]

        # Apply case sensitivity to defaults
        if not self.config.section_header_case_sensitive:
            default_keywords = [kw.lower() for kw in default_keywords]
            default_organizational = [org.lower() for org in default_organizational]

        patterns_to_check.extend(default_keywords)
        patterns_to_check.extend(default_organizational)

        # 3. Add user-configured additional patterns
        if self.config.additional_section_patterns:
            additional_patterns = self.config.additional_section_patterns[:]
            if not self.config.section_header_case_sensitive:
                additional_patterns = [
                    pattern.lower() for pattern in additional_patterns
                ]
            patterns_to_check.extend(additional_patterns)

        # Check if the comment matches any pattern
        for pattern in patterns_to_check:
            if pattern in comparison_comment:
                return True

        return False

    def _reconstruct_class_with_sorted_methods(
        self,
        content: str,
        original_spans: List[FunctionSpan],
        sorted_spans: List[FunctionSpan],
    ) -> str:
        """Reconstruct class content with sorted methods.

        :param content: Original file content
        :type content: str
        :param original_spans: Original method spans in order of appearance
        :type original_spans: List[FunctionSpan]
        :param sorted_spans: Method spans in sorted order
        :type sorted_spans: List[FunctionSpan]
        :returns: Reconstructed content with sorted methods
        :rtype: str
        """
        if not original_spans:  # pragma: no cover
            return content

        # Find the region that contains all methods within the class
        first_method_start = min(span.start_line for span in original_spans)
        last_method_end = max(span.end_line for span in original_spans)

        # Split content into lines for manipulation
        content_lines = content.splitlines(keepends=True)

        # Build new content
        new_lines = []

        # Add everything before the first method
        new_lines.extend(content_lines[:first_method_start])

        # Add sorted methods with optional section headers
        method_lines = self._add_multi_category_section_headers_to_functions(
            sorted_spans, is_methods=True
        )
        new_lines.extend(method_lines)

        # Add everything after the last method
        if last_method_end < len(content_lines):
            new_lines.extend(content_lines[last_method_end:])

        return "".join(new_lines)

    def _reconstruct_content_with_sorted_functions(
        self,
        original_content: str,
        original_spans: List[FunctionSpan],
        sorted_spans: List[FunctionSpan],
    ) -> str:
        """Reconstruct file content with sorted functions.

        Strategy:
        1. Preserve everything before the first function (imports, module docstrings)
        2. Replace the function block with sorted functions
        3. Preserve everything after the last function
        4. Add blank lines between functions if not already present

        This approach ensures non-function content (imports, constants, etc.)
        remains in its original position while only reordering functions.

        :param original_content: Original file content
        :type original_content: str
        :param original_spans: Original function spans in order of appearance
        :type original_spans: List[FunctionSpan]
        :param sorted_spans: Function spans in sorted order
        :type sorted_spans: List[FunctionSpan]
        :returns: Reconstructed content with sorted functions
        :rtype: str
        """
        if not original_spans:  # pragma: no cover
            return original_content

        lines = original_content.splitlines(keepends=True)

        # Find the region that contains all functions
        first_func_start = min(span.start_line for span in original_spans)
        last_func_end = max(span.end_line for span in original_spans)

        # Build new content
        new_lines = []

        # Add everything before the first function
        new_lines.extend(lines[:first_func_start])

        # Add sorted functions with optional section headers
        function_lines = self._add_multi_category_section_headers_to_functions(
            sorted_spans, is_methods=False
        )
        new_lines.extend(function_lines)

        # Add everything after the last function
        if last_func_end < len(lines):
            new_lines.extend(lines[last_func_end:])

        return "".join(new_lines)

    def _sort_class_methods(
        self, content: str, module: nodes.Module, lines: List[str]
    ) -> str:
        """Sort methods within classes using multi-class safe processing.

        CRITICAL FIX for GitHub issue #25: This method now processes all classes
        in a single pass to prevent line number corruption when multiple classes
        are present. The original implementation processed classes sequentially,
        which caused subsequent classes to extract methods from wrong positions
        after the content string was modified by earlier classes.

        :param content: File content
        :type content: str
        :param module: Parsed module
        :type module: nodes.Module
        :param lines: Content split into lines
        :type lines: List[str]
        :returns: Content with sorted class methods
        :rtype: str
        """
        # CRITICAL FIX: Extract ALL class information upfront before ANY
        # modifications. This prevents line number corruption that causes
        # class definitions to be lost
        class_info = []

        for node in module.body:
            if isinstance(node, nodes.ClassDef):
                methods = utils.get_methods_from_class(node)
                if methods:
                    methods_already_sorted = utils.are_methods_sorted_with_exclusions(
                        methods, self.config.ignore_decorators
                    )
                    # Process class if methods need sorting or adding section headers
                    if not methods_already_sorted or self.config.add_section_headers:
                        # Extract method spans NOW while lines array is still accurate
                        method_spans = self._extract_method_spans(methods, lines, node)
                        sorted_spans = self._sort_function_spans(method_spans)
                        class_info.append((node, method_spans, sorted_spans))

        if not class_info:
            return content

        # CRITICAL FIX: Process classes in REVERSE ORDER to preserve line numbers
        # When we modify a class at the end of the file first, the line numbers
        # for classes earlier in the file remain valid
        for _, original_spans, sorted_spans in reversed(class_info):
            # Reconstruct the class content with sorted methods
            content = self._reconstruct_class_with_sorted_methods(
                content, original_spans, sorted_spans
            )

        return content

    def _sort_function_spans(self, spans: List[FunctionSpan]) -> List[FunctionSpan]:
        """Sort function spans according to the plugin rules.

        :param spans: List of function spans to sort
        :type spans: List[FunctionSpan]
        :returns: Sorted list of function spans
        :rtype: List[FunctionSpan]
        """
        # Use multi-category sorting if enabled
        if self.config.enable_multi_category_headers and self.config.category_config:
            return self._sort_function_spans_by_categories(spans)

        # Fall back to original binary public/private sorting
        return self._sort_function_spans_binary(spans)

    def _sort_function_spans_binary(
        self, spans: List[FunctionSpan]
    ) -> List[FunctionSpan]:
        """Sort function spans using the original binary public/private system.

        :param spans: List of function spans to sort
        :type spans: List[FunctionSpan]
        :returns: Sorted list of function spans
        :rtype: List[FunctionSpan]
        """
        # Separate functions based on exclusions and visibility
        excluded = []
        sortable_public = []
        sortable_private = []

        for span in spans:
            if utils.function_has_excluded_decorator(
                span.node, self.config.ignore_decorators or []
            ):
                excluded.append(span)
            elif utils.is_private_function(span.node):
                sortable_private.append(span)
            else:
                sortable_public.append(span)

        # Sort the sortable functions alphabetically
        sortable_public.sort(key=lambda s: s.name)
        sortable_private.sort(key=lambda s: s.name)

        # Reconstruct the order: sortable public + sortable private + excluded
        return sortable_public + sortable_private + excluded

    def _sort_function_spans_by_categories(
        self, spans: List[FunctionSpan]
    ) -> List[FunctionSpan]:
        """Sort function spans using the multi-category system.

        :param spans: List of function spans to sort
        :type spans: List[FunctionSpan]
        :returns: Sorted list of function spans by categories
        :rtype: List[FunctionSpan]
        """
        if not self.config.category_config:
            return spans

        # Separate excluded functions
        excluded = []
        sortable = []

        for span in spans:
            if utils.function_has_excluded_decorator(
                span.node, self.config.ignore_decorators or []
            ):
                excluded.append(span)
            else:
                sortable.append(span)

        # Group functions by category
        categorized_functions: Dict[str, List[FunctionSpan]] = {}

        for span in sortable:
            category = categorize_method(span.node, self.config.category_config)
            if category not in categorized_functions:
                categorized_functions[category] = []
            categorized_functions[category].append(span)

        # Sort within each category if category_sorting is alphabetical
        if self.config.category_config.category_sorting == "alphabetical":
            for category_functions in categorized_functions.values():
                category_functions.sort(key=lambda s: s.name)

        # Reconstruct in category order
        result = []
        for category_def in self.config.category_config.categories:
            if category_def.name in categorized_functions:
                result.extend(categorized_functions[category_def.name])

        # Add any excluded functions at the end
        result.extend(excluded)

        return result

    def _sort_functions_in_content(self, content: str) -> str:
        """Sort functions in file content and return new content.

        :param content: Original file content
        :type content: str
        :returns: Content with sorted functions
        :rtype: str
        """
        try:
            module = astroid.parse(content)
            lines = content.splitlines(keepends=True)

            # Process module-level functions
            content = self._sort_module_functions(content, module, lines)

            # Process class methods
            content = self._sort_class_methods(content, module, lines)

            return content

        except (
            Exception
        ) as e:  # pragma: no cover  # pylint: disable=broad-exception-caught
            print(f"Error sorting content: {e}")
            return content

    def _sort_module_functions(
        self, content: str, module: nodes.Module, lines: List[str]
    ) -> str:
        """Sort module-level functions.

        :param content: File content
        :type content: str
        :param module: Parsed module
        :type module: nodes.Module
        :param lines: Content split into lines
        :type lines: List[str]
        :returns: Content with sorted module functions
        :rtype: str
        """
        functions = utils.get_functions_from_node(module)
        if not functions:  # pragma: no cover
            return content

        # Check if sorting is needed
        functions_already_sorted = utils.are_functions_sorted_with_exclusions(
            functions, self.config.ignore_decorators
        )

        # Even if functions are sorted, we might need to add section headers
        if functions_already_sorted and not self.config.add_section_headers:
            return content

        # Extract function spans
        function_spans = self._extract_function_spans(functions, lines, module)

        # Sort the functions
        sorted_spans = self._sort_function_spans(function_spans)

        # Reconstruct content
        return self._reconstruct_content_with_sorted_functions(
            content, function_spans, sorted_spans
        )

    def _validate_syntax_and_rollback(
        self, file_path: Path, original_content: str, new_content: str
    ) -> str:
        """Validate syntax after transformation, rollback if invalid.

        This is a critical safety measure to prevent the corruption described in
        GitHub issue #25. If auto-sort creates syntax errors, we automatically
        rollback to the original content to prevent data loss.

        :param file_path: Path to the file being processed (for error reporting)
        :type file_path: Path
        :param original_content: Original file content before transformation
        :type original_content: str
        :param new_content: New content after auto-sort transformation
        :type new_content: str
        :returns: Validated content (new_content if valid, original_content if invalid)
        :rtype: str
        """
        try:
            # Attempt to compile the new content to check for syntax errors
            compile(new_content, str(file_path), "exec")
            return new_content
        except SyntaxError as e:
            # Log the syntax error and rollback to prevent corruption
            print(f"WARNING: Auto-sort would create syntax error in {file_path}:")
            print(f"  Error: {e}")
            if hasattr(e, "lineno") and e.lineno:
                if e.text:
                    print(f"  Line {e.lineno}: {e.text}")
                else:
                    print(f"  Line {e.lineno}")  # pragma: no cover
            print("  Reverting to original content to prevent file corruption.")
            print("  This prevents the critical bug described in GitHub issue #25.")
            return original_content
        except Exception as e:  # pragma: no cover
            # pylint: disable=broad-exception-caught
            # For any other compilation errors, be conservative and rollback
            print(f"WARNING: Could not validate syntax for {file_path}: {e}")
            print("  Reverting to original content as safety precaution.")
            return original_content


# Public functions


# Public API function for sorting a single file
def sort_python_file(file_path: Path, config: AutoFixConfig) -> bool:  # pylint: disable=function-should-be-private
    """Sort functions in a Python file.

    :param file_path: Path to the Python file
    :type file_path: Path
    :param config: Auto-fix configuration
    :type config: AutoFixConfig
    :returns: True if file was modified
    :rtype: bool
    """
    return _sort_python_file(file_path, config)


def sort_python_files(file_paths: List[Path], config: AutoFixConfig) -> Tuple[int, int]:
    """Sort functions in multiple Python files.

    :param file_paths: List of Python file paths
    :type file_paths: List[Path]
    :param config: Auto-fix configuration
    :type config: AutoFixConfig
    :returns: Tuple of (files_processed, files_modified)
    :rtype: Tuple[int, int]
    """
    files_processed = 0
    files_modified = 0

    for file_path in file_paths:
        if file_path.suffix == ".py":
            files_processed += 1
            if _sort_python_file(file_path, config):
                files_modified += 1

    return files_processed, files_modified


# Private functions


def _sort_python_file(file_path: Path, config: AutoFixConfig) -> bool:
    """Sort functions in a Python file (private implementation).

    :param file_path: Path to the Python file
    :type file_path: Path
    :param config: Auto-fix configuration
    :type config: AutoFixConfig
    :returns: True if file was modified
    :rtype: bool
    """
    sorter = FunctionSorter(config)
    return sorter.sort_file(file_path)
