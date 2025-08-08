#!/usr/bin/env python3
"""Version bumping utility for PyPI publishing.

This script automatically increments the version number in pyproject.toml
and creates a git commit with the version bump.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple


def get_current_version(pyproject_path: Path) -> str:
    """Extract current version from pyproject.toml.

    :param pyproject_path: Path to pyproject.toml file
    :type pyproject_path: Path
    :returns: Current version string
    :rtype: str
    :raises: ValueError if version not found
    """
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    return match.group(1)


def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version string into components.

    :param version: Version string like "1.2.3"
    :type version: str
    :returns: Tuple of (major, minor, patch)
    :rtype: Tuple[int, int, int]
    :raises: ValueError if version format is invalid
    """
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid version format: {version}. Expected: major.minor.patch"
        )

    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError as e:
        raise ValueError(
            f"Invalid version format: {version}. All parts must be integers"
        ) from e


def bump_version(version: str, bump_type: str) -> str:
    """Bump version according to semantic versioning.

    :param version: Current version string
    :type version: str
    :param bump_type: Type of bump (major, minor, patch)
    :type bump_type: str
    :returns: New version string
    :rtype: str
    """
    major, minor, patch = parse_version(version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}. Use: major, minor, patch")


def update_pyproject_version(pyproject_path: Path, new_version: str) -> None:
    """Update version in pyproject.toml file.

    :param pyproject_path: Path to pyproject.toml file
    :type pyproject_path: Path
    :param new_version: New version string
    :type new_version: str
    """
    content = pyproject_path.read_text(encoding="utf-8")
    updated_content = re.sub(
        r'^version\s*=\s*"[^"]+"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE,
    )
    pyproject_path.write_text(updated_content, encoding="utf-8")


def git_commit_version(version: str) -> None:
    """Create git commit for version bump.

    Pre-commit hooks may modify files (like uv.lock when rebuilding the plugin),
    so we stage all changes after the initial commit attempt.

    :param version: New version string
    :type version: str
    """
    # Stage the version file first
    subprocess.run(["git", "add", "pyproject.toml"], check=True)

    commit_message = f"""chore: bump version to {version}

Automated version bump for PyPI release.

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"""

    try:
        # Try initial commit
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
    except subprocess.CalledProcessError:
        # Pre-commit hooks may have modified files (e.g., uv.lock)
        # Stage all changes and retry commit
        print("Pre-commit hooks modified files, staging all changes and retrying...")
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)


def check_git_status() -> None:
    """Check if git working directory is clean.

    :raises: RuntimeError if there are uncommitted changes
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, check=True
    )

    if result.stdout.strip():
        # Allow CHANGELOG.md changes from prepare-release-changelog.py
        changes = result.stdout.strip().split("\n")
        non_changelog_changes = [c for c in changes if "CHANGELOG.md" not in c]

        if non_changelog_changes:
            raise RuntimeError(
                "Git working directory is not clean. "
                "Please commit or stash changes first."
            )


def main() -> None:
    """Main entry point for version bumping script."""
    parser = argparse.ArgumentParser(
        description="Bump version in pyproject.toml and create git commit"
    )
    parser.add_argument(
        "bump_type", choices=["major", "minor", "patch"], help="Type of version bump"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Update version but don't create git commit",
    )

    args = parser.parse_args()

    # Find pyproject.toml
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found in current directory", file=sys.stderr)
        sys.exit(1)

    try:
        # Check git status (unless dry run or no commit)
        if not args.dry_run and not args.no_commit:
            check_git_status()

        # Get current version and calculate new version
        current_version = get_current_version(pyproject_path)
        new_version = bump_version(current_version, args.bump_type)

        print(f"Current version: {current_version}")
        print(f"New version: {new_version}")

        if args.dry_run:
            print("Dry run - no changes made")
            return

        # Update pyproject.toml
        update_pyproject_version(pyproject_path, new_version)
        print(f"Updated pyproject.toml with version {new_version}")

        # Create git commit
        if not args.no_commit:
            git_commit_version(new_version)
            print(f"Created git commit for version {new_version}")

    except (ValueError, RuntimeError, subprocess.CalledProcessError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
