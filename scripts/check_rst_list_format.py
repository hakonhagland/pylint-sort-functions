#!/usr/bin/env python3
"""
Check RST files for missing newlines before lists.

This script detects a common RST formatting issue where lists immediately
follow text ending with a colon without a blank line separator. This causes
the list to be rendered inline rather than as proper bullet points.

Examples of issues detected:
    Incorrect (missing blank line):
        **Some text**:
        - Item 1
        - Item 2

    Correct (with blank line):
        **Some text**:

        - Item 1
        - Item 2

Usage:
    python scripts/check_rst_list_format.py docs/*.rst
    python scripts/check_rst_list_format.py --recursive docs/

Exit codes:
    0: No issues found
    1: Formatting issues detected
    2: Error reading files
"""

import argparse
import re
import sys
from pathlib import Path
from typing import List, Tuple


class RSTListFormatChecker:
    """Check for missing newlines before lists in RST files."""

    def __init__(self, verbose: bool = False):
        """Initialize the checker.

        Args:
            verbose: Whether to print verbose output
        """
        self.verbose = verbose
        self.total_issues = 0
        self.files_with_issues = 0

    def check_content(self, content: str) -> List[Tuple[int, str, str]]:
        """Check RST content for missing newlines before lists.

        Args:
            content: The RST file content to check

        Returns:
            List of (line_number, error_type, context) tuples
        """
        issues = []
        lines = content.split("\n")

        # Patterns that indicate missing newlines before lists
        patterns = [
            # Text ending with colon, immediately followed by list marker
            (r"^(.+):\n([-*+]) ", "text-colon-list"),
            # Bold/strong text with colon, immediately followed by list
            (r"\*\*(.+)\*\*:\n([-*+]) ", "bold-colon-list"),
            # Italic/emphasis text with colon, immediately followed by list
            (r"\*([^*]+)\*:\n([-*+]) ", "italic-colon-list"),
            # Closing parenthesis with colon, immediately followed by list
            (r"\):\n([-*+]) ", "paren-colon-list"),
            # Literal/code text with colon, immediately followed by list
            (r"``(.+)``:\n([-*+]) ", "literal-colon-list"),
        ]

        for pattern_str, error_type in patterns:
            pattern = re.compile(pattern_str, re.MULTILINE)

            for match in pattern.finditer(content):
                line_num = content[: match.start()].count("\n") + 1

                # Get the line with the colon for context
                if 0 <= line_num - 1 < len(lines):
                    context_line = lines[line_num - 1].strip()
                    # Truncate long lines
                    if len(context_line) > 60:
                        context_line = context_line[:57] + "..."
                else:
                    context_line = "<line not found>"

                issues.append((line_num, error_type, context_line))

        # Remove duplicates (same line reported by multiple patterns)
        seen = set()
        unique_issues = []
        for line_num, error_type, context in issues:
            if line_num not in seen:
                seen.add(line_num)
                unique_issues.append((line_num, error_type, context))

        return sorted(unique_issues, key=lambda x: x[0])

    def check_file(self, filepath: Path) -> List[Tuple[int, str, str]]:
        """Check a single RST file for formatting issues.

        Args:
            filepath: Path to the RST file to check

        Returns:
            List of issues found
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            return self.check_content(content)
        except Exception as e:
            if self.verbose:
                print(f"Error reading {filepath}: {e}", file=sys.stderr)
            return []

    def check_files(self, files: List[Path]) -> int:
        """Check multiple RST files.

        Args:
            files: List of file paths to check

        Returns:
            Exit code (0 for success, 1 for issues found)
        """
        all_issues = {}

        for filepath in files:
            if not filepath.exists():
                print(f"Warning: {filepath} not found", file=sys.stderr)
                continue

            if filepath.suffix.lower() != ".rst":
                if self.verbose:
                    print(f"Skipping non-RST file: {filepath}", file=sys.stderr)
                continue

            issues = self.check_file(filepath)
            if issues:
                all_issues[filepath] = issues
                self.files_with_issues += 1
                self.total_issues += len(issues)

        # Print results
        if all_issues:
            for filepath, issues in all_issues.items():
                print(f"\n{filepath}:")
                for line_num, error_type, context in issues:
                    print(
                        f"  Line {line_num}: Missing blank line before list after: "
                        f"{context}"
                    )

            print(
                f"\n✗ Found {self.total_issues} issue(s) in "
                f"{self.files_with_issues} file(s)"
            )
            print(
                "\nTo fix: Add a blank line between text ending with ':' "
                "and the following list"
            )
            return 1
        else:
            if self.verbose or not files:
                print("✓ No RST list formatting issues found")
            return 0


def main():
    """Command-line interface."""
    parser = argparse.ArgumentParser(
        description="Check RST files for missing newlines before lists",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s docs/*.rst           # Check specific files
  %(prog)s --recursive docs/    # Check all RST files recursively
  %(prog)s -v docs/*.rst        # Verbose output
        """,
    )

    parser.add_argument(
        "paths", nargs="+", type=Path, help="RST files or directories to check"
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Recursively check directories for RST files",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    # Collect all files to check
    files_to_check = []
    for path in args.paths:
        if path.is_file():
            files_to_check.append(path)
        elif path.is_dir():
            if args.recursive:
                # Recursively find all .rst files
                files_to_check.extend(path.glob("**/*.rst"))
            else:
                # Only check .rst files in the directory (not subdirs)
                files_to_check.extend(path.glob("*.rst"))
        else:
            print(f"Warning: {path} not found", file=sys.stderr)

    if not files_to_check:
        print("No RST files found to check", file=sys.stderr)
        return 2

    # Run the checker
    checker = RSTListFormatChecker(verbose=args.verbose)
    return checker.check_files(sorted(set(files_to_check)))


if __name__ == "__main__":
    sys.exit(main())
