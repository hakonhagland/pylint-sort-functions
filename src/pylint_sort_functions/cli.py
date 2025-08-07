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
from typing import List

from pylint_sort_functions import auto_fix
from pylint_sort_functions.auto_fix import AutoFixConfig  # Class - direct import OK

# Public functions


def main() -> int:  # pylint: disable=too-many-return-statements,too-many-branches
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
    if not args.fix and not args.dry_run:
        print(
            "Note: Running in check-only mode. Use --fix or --dry-run to make changes."
        )
        print("Use 'pylint-sort-functions --help' for more options.")
        return 0

    # Convert paths and find Python files
    try:
        paths = [Path(p).resolve() for p in args.paths]
        for path in paths:
            if not path.exists():
                print(f"Error: Path does not exist: {path}")
                return 1

        python_files = _find_python_files(paths)
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
    )

    if args.verbose:  # pragma: no cover
        print(f"Processing {len(python_files)} Python files...")
        if config.ignore_decorators:
            print(f"Ignoring decorators: {', '.join(config.ignore_decorators)}")
        if config.add_section_headers:
            print(f"Section headers enabled:")
            print(f"  Public functions: '{config.public_header}'")
            print(f"  Private functions: '{config.private_header}'")
            print(f"  Public methods: '{config.public_method_header}'")
            print(f"  Private methods: '{config.private_method_header}'")

    # Process files
    try:
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

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")


def _find_python_files(paths: List[Path]) -> List[Path]:
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


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
