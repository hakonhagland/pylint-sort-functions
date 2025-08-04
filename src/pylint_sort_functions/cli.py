"""Command-line interface for pylint-sort-functions auto-fix."""

import argparse
import sys
from pathlib import Path
from typing import List

from pylint_sort_functions.auto_fix import AutoFixConfig, sort_python_files


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


def main() -> int:  # pylint: disable=too-many-return-statements,too-many-branches
    """Main CLI entry point.

    :returns: Exit code (0 for success, 1 for error)
    :rtype: int
    """
    parser = argparse.ArgumentParser(
        prog="pylint-sort-functions",
        description="Auto-fix function and method sorting in Python files",
    )

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

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

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

    except Exception as e:  # pragma: no cover  # pylint: disable=broad-exception-caught
        print(f"Error processing paths: {e}")
        return 1

    # Configure auto-fix
    config = AutoFixConfig(
        dry_run=args.dry_run,
        backup=not args.no_backup,
        ignore_decorators=args.ignore_decorators or [],
        preserve_comments=True,
    )

    if args.verbose:  # pragma: no cover
        print(f"Processing {len(python_files)} Python files...")
        if config.ignore_decorators:
            print(f"Ignoring decorators: {', '.join(config.ignore_decorators)}")

    # Process files
    try:
        files_processed, files_modified = sort_python_files(python_files, config)

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


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
