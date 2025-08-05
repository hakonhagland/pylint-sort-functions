"""Auto-fix functionality for sorting functions and methods."""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import utils


@dataclass
class FunctionSpan:
    """Represents a function with its complete text span in the source file."""

    node: nodes.FunctionDef
    start_line: int
    end_line: int
    text: str  # Complete source text from start_line to end_line (inclusive)
    name: str


@dataclass
class AutoFixConfig:
    """Configuration for the automatic function sorting tool.

    Controls how the auto-fix feature behaves when reordering functions
    and methods in Python source files.
    """

    dry_run: bool = False  # Show what would be changed without modifying files
    backup: bool = True  # Create .bak files before making changes
    ignore_decorators: Optional[List[str]] = (
        None  # Decorator patterns to exclude from sorting
    )
    preserve_comments: bool = True  # Keep comments with their associated functions


# Note: This class intentionally has only one public method as it encapsulates
# the configuration state and provides a clean interface for file processing.
class FunctionSorter:  # pylint: disable=too-few-public-methods
    """Main class for auto-fixing function sorting.

    This class provides the core functionality for automatically reordering
    functions and methods in Python source files to comply with sorting rules.

    Usage:
        Used by the CLI tool (cli.py) and can be used programmatically:

        config = AutoFixConfig(dry_run=True, backup=True)
        sorter = FunctionSorter(config)
        was_modified = sorter.sort_file(Path("my_file.py"))
    """

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

            if self.config.dry_run:
                print(f"Would modify: {file_path}")
                return True

            # Create backup if requested
            if self.config.backup:
                backup_path = file_path.with_suffix(f"{file_path.suffix}.bak")
                shutil.copy2(file_path, backup_path)

            # Write the sorted content
            file_path.write_text(new_content, encoding="utf-8")
            return True

        # Broad exception catch ensures tool never crashes when modifying user files
        except (
            Exception
        ) as e:  # pragma: no cover  # pylint: disable=broad-exception-caught
            print(f"Error processing {file_path}: {e}")
            return False

    def _file_needs_sorting(self, content: str) -> bool:
        """Check if a file needs function sorting.

        :param content: File content as string
        :type content: str
        :returns: True if file needs sorting
        :rtype: bool
        """
        try:
            # Parse with astroid for consistency with the checker
            module = astroid.parse(content)

            # Check module-level functions
            functions = utils.get_functions_from_node(module)
            if functions and not utils.are_functions_sorted_with_exclusions(
                functions, self.config.ignore_decorators
            ):
                return True

            # Check class methods
            for node in module.body:
                if isinstance(node, nodes.ClassDef):
                    methods = utils.get_methods_from_class(node)
                    if methods and not utils.are_methods_sorted_with_exclusions(
                        methods, self.config.ignore_decorators
                    ):
                        return True

            return False

        except Exception:  # pylint: disable=broad-exception-caught
            return False

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

    def _sort_class_methods(  # pylint: disable=unused-argument
        self, content: str, module: nodes.Module, lines: List[str]
    ) -> str:
        """Sort methods within classes.

        :param content: File content
        :type content: str
        :param module: Parsed module
        :type module: nodes.Module
        :param lines: Content split into lines
        :type lines: List[str]
        :returns: Content with sorted class methods
        :rtype: str
        """
        # For now, focus on module-level functions
        # Class method sorting can be added in a future iteration
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
        if utils.are_functions_sorted_with_exclusions(  # pragma: no cover
            functions, self.config.ignore_decorators
        ):
            return content

        # Extract function spans
        function_spans = self._extract_function_spans(functions, lines)

        # Sort the functions
        sorted_spans = self._sort_function_spans(function_spans)

        # Reconstruct content
        return self._reconstruct_content_with_sorted_functions(
            content, function_spans, sorted_spans
        )

    def _extract_function_spans(
        self, functions: List[nodes.FunctionDef], lines: List[str]
    ) -> List[FunctionSpan]:
        """Extract function text spans from the source.

        :param functions: List of function nodes
        :type functions: List[nodes.FunctionDef]
        :param lines: Source file lines
        :type lines: List[str]
        :returns: List of function spans with text
        :rtype: List[FunctionSpan]
        """
        spans = []

        for i, func in enumerate(functions):
            start_line = func.lineno - 1  # Convert to 0-based indexing

            # Find the end line (start of next function or end of file)
            if i + 1 < len(functions):
                # Find decorators of next function
                next_func = functions[i + 1]
                if hasattr(next_func, "decorators") and next_func.decorators:
                    # Next function has decorators, use the first decorator's line
                    end_line = next_func.decorators.lineno - 1
                else:
                    # No decorators, use the function definition line
                    end_line = next_func.lineno - 1
            else:
                # Last function, use end of file
                end_line = len(lines)

            # Include decorators in the span
            actual_start = start_line
            if hasattr(func, "decorators") and func.decorators:
                actual_start = func.decorators.lineno - 1

            # Extract the text
            text = "".join(lines[actual_start:end_line])

            spans.append(
                FunctionSpan(
                    node=func,
                    start_line=actual_start,
                    end_line=end_line,
                    text=text,
                    name=func.name,
                )
            )

        return spans

    def _sort_function_spans(self, spans: List[FunctionSpan]) -> List[FunctionSpan]:
        """Sort function spans according to the plugin rules.

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
        # For now, use a simple approach: public sorted + private sorted + excluded
        # Future enhancement: Preserve relative positions of excluded functions
        return sortable_public + sortable_private + excluded

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

        # Add sorted functions
        for i, span in enumerate(sorted_spans):
            if i > 0:
                # Add blank line between functions if not already present
                if not span.text.startswith("\n"):
                    new_lines.append("\n")
            new_lines.append(span.text)

        # Add everything after the last function
        if last_func_end < len(lines):  # pragma: no cover
            new_lines.extend(lines[last_func_end:])

        return "".join(new_lines)


def sort_python_file(file_path: Path, config: AutoFixConfig) -> bool:
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
