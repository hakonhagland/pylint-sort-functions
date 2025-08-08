#!/usr/bin/env python3
"""
PyPI Publishing Script

Consolidates the publish-to-pypi Makefile targets into a single script that:
1. Bumps version (patch/minor/major)
2. Prepares changelog for release
3. Commits changes using safe-commit.sh workflow
4. Builds and uploads to PyPI
5. Creates and pushes git tag

Usage:
    python scripts/publish-to-pypi.py patch
    python scripts/publish-to-pypi.py minor
    python scripts/publish-to-pypi.py major
"""

import argparse
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path


def run_command(
    cmd: str, description: str, check: bool = True
) -> subprocess.CompletedProcess:
    """Run a shell command with error handling."""
    print(f"📋 {description}")
    print(f"   Running: {cmd}")

    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)

    if check and result.returncode != 0:
        print(f"❌ Error: {description} failed with exit code {result.returncode}")
        sys.exit(1)

    return result


def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def main():
    parser = argparse.ArgumentParser(description="Publish package to PyPI")
    parser.add_argument(
        "version_type",
        choices=["patch", "minor", "major"],
        help="Type of version bump to perform",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually doing it",
    )

    args = parser.parse_args()

    if args.dry_run:
        print(
            f"🔍 DRY RUN: Would publish to PyPI with {args.version_type} version bump"
        )
        return

    print(f"🚀 Publishing to PyPI with {args.version_type} version bump...")

    # Step 1: Bump version
    run_command(
        f"python scripts/bump-version.py --no-commit {args.version_type}",
        f"Bumping version ({args.version_type})",
    )

    # Step 2: Prepare changelog for release
    print("📝 Preparing changelog for release...")
    run_command(
        "python scripts/prepare-release-changelog.py",
        "Preparing changelog for release",
        check=False,  # Script may return non-zero but continue
    )

    # Step 3: Get new version for commit message
    new_version = get_current_version()
    commit_message = f"chore: bump version to {new_version} and prepare changelog"

    # Step 4: Stage all changes and commit using safe-commit workflow
    run_command("git add -A", "Staging version bump and changelog changes")

    # Use safe-commit.sh to handle pre-commit hooks properly
    run_command(
        f"bash scripts/safe-commit.sh '{commit_message}'",
        "Committing version bump and changelog with safe-commit workflow",
    )

    # Step 5: Clean old builds
    print("🧹 Cleaning old builds...")
    if Path("dist").exists():
        shutil.rmtree("dist")

    # Step 6: Build package
    run_command("uv build", "Building package")

    # Step 7: Upload to PyPI
    run_command(
        f"twine upload dist/pylint_sort_functions-{new_version}*", "Uploading to PyPI"
    )

    # Step 8: Create and push git tag
    tag_name = f"v{new_version}"
    run_command(
        f"git tag -a {tag_name} -m 'Release {tag_name}'", f"Creating git tag {tag_name}"
    )

    run_command(f"git push origin {tag_name}", f"Pushing git tag {tag_name}")

    print(f"✅ Successfully published version {new_version} to PyPI!")
    print(
        f"📦 Package URL: https://pypi.org/project/pylint-sort-functions/{new_version}/"
    )
    print(f"🏷️  Git tag: {tag_name}")
    print("🤖 GitHub Actions will create a release automatically from the pushed tag.")


if __name__ == "__main__":
    main()
