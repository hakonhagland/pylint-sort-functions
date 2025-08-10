"""Command-line interface for pylint-sort-functions auto-fix.

This module provides the standalone CLI tool that users invoke via:
    $ pylint-sort-functions [options] <paths>

The entry point is configured in pyproject.toml and maps the 'pylint-sort-functions'
command to the main() function in this module. This provides auto-fix functionality
independent of the PyLint plugin integration.

Usage examples:
    $ pylint-sort-functions --fix src/
    $ pylint-sort-functions --dry-run --verbose myproject/
    $ pylint-sort-functions --fix --no-backup --ignore-decorators "@app.route" src/
"""

# Using argparse (stdlib) instead of click to maintain zero external dependencies.
# This lightweight approach is sufficient for our flat argument structure.
# Future: If subcommands are added, consider migrating to click for better UX.
import argparse
import sys
from pathlib import Path
from typing import List, Optional

import astroid  # type: ignore[import-untyped]
from astroid import nodes

from pylint_sort_functions import auto_fix, utils
from pylint_sort_functions.auto_fix import AutoFixConfig  # Class - direct import OK
from pylint_sort_functions.privacy_fixer import (  # Classes - direct import OK
    PrivacyFixer,
    RenameCandidate,
)

# Public functions


def main() -> int:  # pylint: disable=too-many-return-statements,too-many-branches,too-many-locals,too-many-statements
    """Main CLI entry point for pylint-sort-functions tool.

    Provides a complete workflow for auto-fixing function and method sorting:
    1. Parse and validate command-line arguments
    2. Resolve and validate input paths (files/directories)
    3. Discover Python files recursively in directories
    4. Configure auto-fix settings from CLI arguments
    5. Process files with function/method sorting and comment preservation
    6. Report results with optional verbose output

    The tool operates in different modes:
    - Check-only: Default mode, shows help and exits
    - Dry-run: Shows what would be changed without modifying files
    - Fix: Actually modifies files with optional backup creation

    Exit codes:
    - 0: Success (files processed successfully, or check-only mode)
    - 1: Error (invalid paths, processing failures, user interruption)

    Error handling:
    - Provides user-friendly error messages instead of stack traces
    - Handles filesystem errors, permission issues, and processing failures
    - Graceful handling of keyboard interruption (Ctrl+C)

    Side effects:
    - May modify Python files when --fix is used
    - May create .bak backup files unless --no-backup is specified
    - Outputs progress and results to stdout

    :returns: Exit code (0 for success, 1 for error)
    :rtype: int
    """
    parser = argparse.ArgumentParser(
        prog="pylint-sort-functions",
        description="Auto-fix function and method sorting in Python files",
    )
    _add_parser_arguments(parser)

    args = parser.parse_args()

    # Validate arguments
    if (
        not args.fix
        and not args.dry_run
        and not args.fix_privacy
        and not args.privacy_dry_run
    ):
        print(
            "Note: Running in check-only mode. Use --fix, --dry-run, "
            "--fix-privacy, or --privacy-dry-run to make changes."
        )
        print("Use 'pylint-sort-functions --help' for more options.")
        return 0

    # Check for conflicting privacy options
    if args.fix_privacy and args.privacy_dry_run:
        print("Error: Cannot use both --fix-privacy and --privacy-dry-run together.")
        return 1

    # Convert paths and find Python files
    try:
        paths = [Path(p).resolve() for p in args.paths]
        for path in paths:
            if not path.exists():
                print(f"Error: Path does not exist: {path}")
                return 1

        python_files = _find_python_files_from_paths(paths)
        if not python_files:
            print("No Python files found in the specified paths.")
            return 0

    # Catch broad exceptions for CLI robustness - path operations can fail in
    # many OS-specific ways, and we want clean error messages not stacktraces
    except Exception as e:  # pragma: no cover  # pylint: disable=broad-exception-caught
        print(f"Error processing paths: {e}")
        return 1

    # Configure auto-fix
    config = AutoFixConfig(
        dry_run=args.dry_run,
        backup=not args.no_backup,
        ignore_decorators=args.ignore_decorators or [],
        add_section_headers=args.add_section_headers,
        public_header=args.public_header,
        private_header=args.private_header,
        public_method_header=args.public_method_header,
        private_method_header=args.private_method_header,
        additional_section_patterns=args.additional_section_patterns,
        section_header_case_sensitive=args.section_headers_case_sensitive,
    )

    if args.verbose:  # pragma: no cover
        print(f"Processing {len(python_files)} Python files...")
        if config.ignore_decorators:
            print(f"Ignoring decorators: {', '.join(config.ignore_decorators)}")
        if config.add_section_headers:
            print("Section headers enabled:")
            print(f"  Public functions: '{config.public_header}'")
            print(f"  Private functions: '{config.private_header}'")
            print(f"  Public methods: '{config.public_method_header}'")
            print(f"  Private methods: '{config.private_method_header}'")
            if config.additional_section_patterns:
                patterns = config.additional_section_patterns
                print(f"  Additional detection patterns: {patterns}")
            if config.section_header_case_sensitive:
                print("  Case-sensitive detection enabled")

    # Process files based on mode
    try:
        # Privacy fixing mode
        if args.fix_privacy or args.privacy_dry_run:
            return _handle_privacy_fixing(args, python_files, paths)

        # Regular sorting mode
        files_processed, files_modified = auto_fix.sort_python_files(
            python_files, config
        )

        if args.verbose or files_modified > 0:  # pragma: no cover
            if config.dry_run:
                print(f"Would modify {files_modified} of {files_processed} files")
            else:
                print(f"Modified {files_modified} of {files_processed} files")
                if config.backup and files_modified > 0:
                    print("Backup files created with .bak extension")

        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error during processing: {e}")
        return 1


# Private functions


def _add_parser_arguments(parser: argparse.ArgumentParser) -> None:
    """Configure CLI argument parser with all supported options.

    :param parser: The argument parser to configure
    :type parser: argparse.ArgumentParser
    """
    parser.add_argument(
        "paths", nargs="+", type=Path, help="Python files or directories to process"
    )

    parser.add_argument(
        "--fix",
        action="store_true",
        help="Apply auto-fix to sort functions (default: check only)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backup files (.bak) when fixing",
    )

    parser.add_argument(
        "--ignore-decorators",
        action="append",
        metavar="PATTERN",
        help='Decorator patterns to ignore (e.g., "@app.route" "@*.command"). '
        + "Can be used multiple times.",
    )

    # Section header options
    parser.add_argument(
        "--add-section-headers",
        action="store_true",
        help="Add section header comments (e.g., '# Public functions') during sorting",
    )

    parser.add_argument(
        "--public-header",
        default="# Public functions",
        metavar="TEXT",
        help="Header text for public functions (default: '# Public functions')",
    )

    parser.add_argument(
        "--private-header",
        default="# Private functions",
        metavar="TEXT",
        help="Header text for private functions (default: '# Private functions')",
    )

    parser.add_argument(
        "--public-method-header",
        default="# Public methods",
        metavar="TEXT",
        help="Header text for public methods (default: '# Public methods')",
    )

    parser.add_argument(
        "--private-method-header",
        default="# Private methods",
        metavar="TEXT",
        help="Header text for private methods (default: '# Private methods')",
    )

    # Section header detection options
    parser.add_argument(
        "--additional-section-patterns",
        action="append",
        metavar="PATTERN",
        help="Additional patterns to detect as section headers "
        + "(e.g., '=== API ===' or '--- Helpers ---'). Can be used multiple times.",
    )

    parser.add_argument(
        "--section-headers-case-sensitive",
        action="store_true",
        help="Make section header detection case-sensitive (default: case-insensitive)",
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    # Privacy fixer options
    parser.add_argument(
        "--fix-privacy",
        action="store_true",
        help="Automatically rename functions that should be private "
        "(adds underscore prefix)",
    )

    parser.add_argument(
        "--privacy-dry-run",
        action="store_true",
        help="Show functions that would be renamed to private (standalone option)",
    )

    parser.add_argument(
        "--auto-sort",
        action="store_true",
        help="Automatically apply function sorting after privacy fixes",
    )


def _analyze_files_for_privacy(
    python_files: List[Path],
    privacy_fixer: PrivacyFixer,
    project_root: Path,
    verbose: bool = False,
) -> List[RenameCandidate]:
    """Analyze files and return privacy rename candidates.

    :param python_files: List of Python files to analyze
    :param privacy_fixer: PrivacyFixer instance to use for analysis
    :param project_root: Root directory of the project
    :param verbose: Whether to print verbose output
    :returns: List of rename candidates found across all files
    """
    all_candidates = []

    for file_path in python_files:
        try:
            # Parse the file
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            module = astroid.parse(content, module_name=str(file_path))

            # Find functions that should be private
            functions = utils.get_functions_from_node(module)
            for func in functions:
                candidate = _create_rename_candidate(
                    func, file_path, privacy_fixer, project_root
                )
                if candidate is not None:
                    all_candidates.append(candidate)

        except (
            Exception
        ) as e:  # pragma: no cover  # pylint: disable=broad-exception-caught
            if verbose:
                print(f"Warning: Could not analyze {file_path}: {e}")
            continue

    return all_candidates


def _apply_integrated_sorting(
    args: argparse.Namespace, python_files: List[Path]
) -> None:
    """Apply function sorting after privacy fixes.

    :param args: Parsed command-line arguments containing configuration
    :param python_files: List of Python files to sort
    """
    # Create sorting configuration from CLI args
    config = AutoFixConfig(
        dry_run=args.privacy_dry_run,  # Use privacy dry-run mode for sorting too
        backup=not args.no_backup,
        ignore_decorators=args.ignore_decorators or [],
        add_section_headers=args.add_section_headers,
        public_header=args.public_header,
        private_header=args.private_header,
        public_method_header=args.public_method_header,
        private_method_header=args.private_method_header,
        additional_section_patterns=args.additional_section_patterns,
        section_header_case_sensitive=args.section_headers_case_sensitive,
    )

    # Apply sorting
    files_processed, files_modified = auto_fix.sort_python_files(python_files, config)

    if config.dry_run:
        print(f"Would sort {files_modified} of {files_processed} files")
    else:
        print(f"Sorted {files_modified} of {files_processed} files")
        if config.backup and files_modified > 0:  # pragma: no cover
            print("Additional backup files created for sorting changes")


def _create_rename_candidate(
    func: nodes.FunctionDef,
    file_path: Path,
    privacy_fixer: PrivacyFixer,
    project_root: Path,
) -> Optional[RenameCandidate]:
    """Create and validate a single rename candidate.

    :param func: Function node to analyze
    :param file_path: Path to file containing the function
    :param privacy_fixer: PrivacyFixer instance for validation
    :param project_root: Root directory of the project
    :returns: Validated rename candidate or None if not suitable
    """
    # Use default public patterns plus common API patterns
    public_patterns = {
        "main",
        "run",
        "execute",
        "start",
        "stop",
        "setup",
        "teardown",
        "public_api",
    }

    if not utils.should_function_be_private(
        func, file_path, project_root, public_patterns
    ):
        return None

    # Parse the module to get references
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    module = astroid.parse(content, module_name=str(file_path))

    # Find all references to this function
    references = privacy_fixer.find_function_references(func.name, module)

    # Create initial candidate
    candidate = RenameCandidate(
        function_node=func,
        old_name=func.name,
        new_name=f"_{func.name}",
        references=references,
        test_references=[],  # Will be populated if needed
        is_safe=True,  # Will be validated next
        safety_issues=[],
    )

    # Validate safety
    is_safe, issues = privacy_fixer.is_safe_to_rename(candidate)
    return RenameCandidate(
        function_node=func,
        old_name=func.name,
        new_name=f"_{func.name}",
        references=references,
        test_references=[],  # Will be populated if needed
        is_safe=is_safe,
        safety_issues=issues,
    )


def _find_project_root(start_path: Path) -> Path:
    """Find the project root by looking for common project markers.

    :param start_path: Starting path to search from
    :type start_path: Path
    :returns: Project root path
    :rtype: Path
    """
    current = start_path.resolve()
    if current.is_file():
        current = current.parent

    # Look for common project root indicators
    markers = ["pyproject.toml", "setup.py", "setup.cfg", ".git", "requirements.txt"]

    while current != current.parent:
        for marker in markers:
            if (current / marker).exists():
                return current
        current = current.parent

    # Fallback to the original path's parent
    return start_path.parent if start_path.is_file() else start_path


def _find_python_files_from_paths(paths: List[Path]) -> List[Path]:
    """Find all Python files in the given paths.

    :param paths: List of file or directory paths
    :type paths: List[Path]
    :returns: List of Python file paths
    :rtype: List[Path]
    """
    python_files = []

    for path in paths:
        if path.is_file() and path.suffix == ".py":
            python_files.append(path)
        elif path.is_dir():
            # Recursively find Python files
            python_files.extend(path.rglob("*.py"))

    return python_files


def _handle_privacy_fixing(
    args: argparse.Namespace, python_files: List[Path], paths: List[Path]
) -> int:
    """Handle privacy fixing workflow.

    :param args: Parsed command-line arguments
    :param python_files: List of Python files to process
    :param paths: List of original paths provided
    :returns: Exit code
    """
    if args.verbose:  # pragma: no cover
        print("\n=== Privacy Fixing Mode ===")
        print(f"Analyzing {len(python_files)} Python files for privacy issues...")

    privacy_fixer = PrivacyFixer(
        dry_run=args.privacy_dry_run, backup=not args.no_backup
    )
    project_root = _find_project_root(paths[0])

    # Analyze all files and collect rename candidates
    all_candidates = _analyze_files_for_privacy(
        python_files, privacy_fixer, project_root, args.verbose
    )

    # Process results and apply fixes if requested
    return _process_privacy_results(
        all_candidates, args, python_files, paths, privacy_fixer
    )


def _process_privacy_results(  # pylint: disable=too-many-branches
    all_candidates: List[RenameCandidate],
    args: argparse.Namespace,
    python_files: List[Path],
    paths: List[Path],
    privacy_fixer: PrivacyFixer,
) -> int:
    """Handle privacy analysis results and apply fixes if requested.

    :param all_candidates: List of rename candidates found
    :param args: Parsed command-line arguments
    :param python_files: List of Python files being processed
    :param paths: List of original paths provided
    :param privacy_fixer: PrivacyFixer instance for applying renames
    :returns: Exit code
    """
    if all_candidates:
        report = privacy_fixer.generate_report(all_candidates)
        print(report)

        # Apply renames if not in dry-run mode
        if args.fix_privacy:
            # Determine project root from the provided paths
            test_project_root: Optional[Path] = None
            if paths:
                # Use the first path as project root, or its parent if it's a file
                first_path = paths[0]
                if first_path.is_dir():
                    test_project_root = first_path
                else:
                    test_project_root = first_path.parent

            result = privacy_fixer.apply_renames(all_candidates, test_project_root)
            print(f"\nRenamed {result['renamed']} functions.")
            if result["skipped"] > 0:  # pragma: no cover
                print(f"Skipped {result['skipped']} unsafe renames.")
            if result.get("errors"):  # pragma: no cover
                for error in result["errors"]:
                    print(f"Error: {error}")

            # Report test file updates
            if "test_files_updated" in result:
                if result["test_files_updated"] > 0:
                    print(f"Updated {result['test_files_updated']} test files.")
                if result.get("test_file_errors"):
                    print("\nTest file update errors:")
                    for error in result["test_file_errors"]:
                        print(f"  {error}")

            # Apply automatic sorting if requested
            if args.auto_sort and result["renamed"] > 0:
                print("\n=== Applying Automatic Sorting ===")
                _apply_integrated_sorting(args, python_files)
        # For dry-run mode with auto-sort, show what sorting would do
        if args.privacy_dry_run and args.auto_sort and all_candidates:
            print("\n=== Auto-Sort Preview ===")
            _apply_integrated_sorting(args, python_files)
    else:  # pragma: no cover
        print("No functions found that need privacy fixes.")

        # For dry-run mode with auto-sort on files with no privacy issues,
        # still show sorting preview
        if args.privacy_dry_run and args.auto_sort:
            print("\n=== Auto-Sort Preview ===")
            _apply_integrated_sorting(args, python_files)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
