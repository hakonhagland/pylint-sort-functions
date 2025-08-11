#!/usr/bin/env python3
"""Validate TOML code blocks in RST documentation files.

This script extracts TOML code blocks from reStructuredText files and validates
their syntax to prevent rendering issues in documentation.
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path
from typing import List, Tuple


def extract_toml_blocks(content: str) -> List[Tuple[int, str]]:
    """Extract TOML code blocks from RST content.

    Args:
        content: RST file content

    Returns:
        List of tuples containing (line_number, toml_content)
    """
    blocks = []

    # Pattern to match TOML code blocks with their line numbers
    pattern = r"^\.\. code-block:: toml\n\n((?:(?:    .*)?\n)+)"

    for match in re.finditer(pattern, content, re.MULTILINE):
        line_num = content[: match.start()].count("\n") + 1
        block_content = match.group(1)

        # Remove RST indentation (4 spaces) from each line
        toml_lines = []
        for line in block_content.split("\n"):
            if line.startswith("    "):
                toml_lines.append(line[4:])
            elif line.strip() == "":
                toml_lines.append("")
            else:
                toml_lines.append(line)

        toml_content = "\n".join(toml_lines).strip()
        if toml_content:  # Only add non-empty blocks
            blocks.append((line_num, toml_content))

    return blocks


def validate_toml_block(toml_content: str) -> tuple[bool, str]:
    """Validate a TOML string.

    Args:
        toml_content: TOML content to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        tomllib.loads(toml_content)
        return True, ""
    except tomllib.TOMLDecodeError as e:
        return False, str(e)


def check_file(file_path: Path) -> List[str]:
    """Check all TOML blocks in an RST file.

    Args:
        file_path: Path to RST file

    Returns:
        List of error messages
    """
    if not file_path.exists():
        return [f"File not found: {file_path}"]

    try:
        content = file_path.read_text()
    except Exception as e:
        return [f"Error reading {file_path}: {e}"]

    blocks = extract_toml_blocks(content)
    errors = []

    for line_num, toml_content in blocks:
        is_valid, error_msg = validate_toml_block(toml_content)
        if not is_valid:
            prefix = f"{file_path}:{line_num}: Invalid TOML syntax in code block"
            error_message = f"{prefix} - {error_msg}"
            errors.append(error_message)

    return errors


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate TOML code blocks in RST documentation files"
    )
    parser.add_argument("files", nargs="+", type=Path, help="RST files to check")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show verbose output including valid blocks",
    )

    args = parser.parse_args()

    total_errors = []
    total_files = 0
    total_blocks = 0

    for file_path in args.files:
        if file_path.suffix != ".rst":
            print(f"Skipping non-RST file: {file_path}", file=sys.stderr)
            continue

        total_files += 1
        content = file_path.read_text()
        blocks = extract_toml_blocks(content)
        total_blocks += len(blocks)

        if args.verbose and blocks:
            print(f"Checking {len(blocks)} TOML block(s) in {file_path}")

        errors = check_file(file_path)
        total_errors.extend(errors)

    # Print results
    if total_errors:
        print("\n❌ TOML validation errors found:", file=sys.stderr)
        for error in total_errors:
            print(f"  {error}", file=sys.stderr)
        print(
            f"\nTotal: {len(total_errors)} error(s) in {total_files} file(s)",
            file=sys.stderr,
        )
        return 1
    else:
        if args.verbose or total_blocks > 0:
            print(
                f"✅ All {total_blocks} TOML blocks in {total_files} file(s) are valid!"
            )
        return 0


if __name__ == "__main__":
    sys.exit(main())
