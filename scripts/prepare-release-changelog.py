#!/usr/bin/env python3
"""Script to prepare CHANGELOG.md for a release."""

import re
import sys
import tomllib
from datetime import datetime
from pathlib import Path


def get_project_version() -> str:
    """Get the current version from pyproject.toml."""
    pyproject_path = Path.cwd() / "pyproject.toml"
    if not pyproject_path.exists():
        pyproject_path = Path.cwd().parent / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
        return data["project"]["version"]


def get_changelog_path() -> Path:
    """Get the path to CHANGELOG.md."""
    for base in [Path.cwd(), Path.cwd().parent]:
        changelog = base / "CHANGELOG.md"
        if changelog.exists():
            return changelog
    raise FileNotFoundError("CHANGELOG.md not found")


def prepare_changelog_for_release() -> bool:
    """Move [Unreleased] section to a versioned section."""
    try:
        changelog_path = get_changelog_path()
        content = changelog_path.read_text()

        # Check if there's an [Unreleased] section
        if "[Unreleased]" not in content:
            print("ℹ️  No [Unreleased] section found in CHANGELOG.md")
            return True

        # Check if [Unreleased] has any content
        unreleased_match = re.search(
            r"## \[Unreleased\](.*?)(?=## \[|\Z)", content, re.DOTALL
        )

        if not unreleased_match:
            print("ℹ️  Could not parse [Unreleased] section")
            return True

        unreleased_content = unreleased_match.group(1).strip()

        # Check if there's actual content (not just empty section headers)
        has_content = False
        for line in unreleased_content.split("\n"):
            if line.strip() and not line.startswith("###"):
                if line.strip() != "-":  # Ignore empty list items
                    has_content = True
                    break

        if not has_content:
            print("ℹ️  [Unreleased] section is empty, nothing to release")
            return True

        # Get version and date
        version = get_project_version()
        today = datetime.now().strftime("%Y-%m-%d")

        # Replace [Unreleased] with [version] - date
        new_content = content.replace("## [Unreleased]", f"## [{version}] - {today}")

        # Add a new [Unreleased] section at the top
        # Find where to insert it (after the header but before the first version)
        lines = new_content.split("\n")
        insert_index = None

        for i, line in enumerate(lines):
            if line.startswith(f"## [{version}]"):
                insert_index = i
                break

        if insert_index is not None:
            # Insert new [Unreleased] section
            new_unreleased = [
                "## [Unreleased]",
                "",
            ]
            lines[insert_index:insert_index] = new_unreleased
            new_content = "\n".join(lines)

        # Add the version link at the bottom
        # Check if there's already a links section
        if f"[{version}]:" not in new_content:
            # Add the link
            repo_url = "https://github.com/hakonhagland/pylint-sort-functions"
            version_link = f"[{version}]: {repo_url}/releases/tag/v{version}"

            # Find where to add it (at the end, before other version links)
            if re.search(r"^\[\d+\.\d+\.\d+\]:", new_content, re.MULTILINE):
                # Insert before the first version link
                match = re.search(r"^(\[\d+\.\d+\.\d+\]:)", new_content, re.MULTILINE)
                if match:
                    insert_pos = match.start()
                    new_content = (
                        new_content[:insert_pos]
                        + version_link
                        + "\n"
                        + new_content[insert_pos:]
                    )
            else:
                # Add at the end
                new_content = new_content.rstrip() + f"\n\n{version_link}\n"

        # Write back
        changelog_path.write_text(new_content)

        print(f"✅ Prepared CHANGELOG.md for version {version}")
        print(f"   Moved [Unreleased] → [{version}] - {today}")
        return True

    except Exception as e:
        print(f"⚠️  Warning: Could not prepare changelog: {e}")
        # Return True to not block the release process
        return True


def main() -> None:
    """Main entry point."""
    success = prepare_changelog_for_release()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
