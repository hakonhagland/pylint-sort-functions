#!/usr/bin/env python3
"""Script to validate CHANGELOG.md format."""

import re
import sys
from pathlib import Path


def get_changelog_path() -> Path:
    """Get the path to CHANGELOG.md."""
    for base in [Path.cwd(), Path.cwd().parent]:
        changelog = base / "CHANGELOG.md"
        if changelog.exists():
            return changelog
    raise FileNotFoundError("CHANGELOG.md not found")


def validate_changelog() -> bool:
    """Validate the changelog format."""
    try:
        changelog_path = get_changelog_path()
        content = changelog_path.read_text()

        errors = []

        # Check for Keep a Changelog format
        if "Keep a Changelog" not in content:
            errors.append("Missing reference to Keep a Changelog format")

        if "Semantic Versioning" not in content:
            errors.append("Missing reference to Semantic Versioning")

        # Check for valid version headers
        version_pattern = r"^## \[(Unreleased|\d+\.\d+\.\d+)\]"
        versions = re.findall(version_pattern, content, re.MULTILINE)

        if not versions:
            errors.append("No version headers found")

        # Check for valid section headers
        # Allow standard ones + custom for major releases
        standard_sections = [
            "Added",
            "Changed",
            "Deprecated",
            "Removed",
            "Fixed",
            "Security",
        ]
        allowed_custom_sections = [
            "Features",
            "Technical",
            "Documentation",
            "Quality",
            "Performance",
        ]
        valid_sections = standard_sections + allowed_custom_sections

        section_pattern = r"^### (\w+)"
        sections = re.findall(section_pattern, content, re.MULTILINE)

        for section in sections:
            if section not in valid_sections:
                allowed = ", ".join(standard_sections)
                errors.append(f"Invalid section header: {section} (allowed: {allowed})")

        # Check for proper date format in version headers
        date_pattern = r"## \[\d+\.\d+\.\d+\] - (\d{4}-\d{2}-\d{2})"
        dates = re.findall(date_pattern, content)

        for date in dates:
            # Basic date validation
            year, month, day = date.split("-")
            if not (1900 <= int(year) <= 2100):
                errors.append(f"Invalid year in date: {date}")
            if not (1 <= int(month) <= 12):
                errors.append(f"Invalid month in date: {date}")
            if not (1 <= int(day) <= 31):
                errors.append(f"Invalid day in date: {date}")

        # Check for duplicate versions
        if len(versions) != len(set(versions)):
            errors.append("Duplicate version entries found")

        # Check that versions are in descending order (newest first)
        numeric_versions = []
        for v in versions:
            if v != "Unreleased":
                parts = v.split(".")
                numeric_versions.append(tuple(int(p) for p in parts))

        for i in range(1, len(numeric_versions)):
            if numeric_versions[i] > numeric_versions[i - 1]:
                msg = "Versions not in descending order: "
                msg += f"{versions[i]} comes after {versions[i - 1]}"
                errors.append(msg)

        if errors:
            print("❌ Changelog validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False

        print("✅ Changelog validation passed")
        return True

    except Exception as e:
        print(f"❌ Error validating changelog: {e}")
        return False


def main() -> None:
    """Main entry point."""
    success = validate_changelog()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
