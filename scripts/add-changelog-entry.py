#!/usr/bin/env python3
"""Script to add entries to the CHANGELOG.md file."""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional


def get_changelog_path() -> Path:
    """Get the path to CHANGELOG.md."""
    # Try current directory first, then parent
    for base in [Path.cwd(), Path.cwd().parent]:
        changelog = base / "CHANGELOG.md"
        if changelog.exists():
            return changelog
    raise FileNotFoundError("CHANGELOG.md not found")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Add an entry to the CHANGELOG.md file"
    )
    parser.add_argument(
        "type",
        choices=["added", "changed", "deprecated", "removed", "fixed", "security"],
        help="Type of change (following Keep a Changelog format)",
    )
    parser.add_argument(
        "message",
        help="Description of the change",
    )
    parser.add_argument(
        "--pr",
        type=int,
        help="Pull request number (optional)",
    )
    parser.add_argument(
        "--issue",
        type=int,
        help="Issue number (optional)",
    )
    parser.add_argument(
        "--breaking",
        action="store_true",
        help="Mark as a breaking change",
    )
    return parser.parse_args()


def ensure_unreleased_section(content: str) -> str:
    """Ensure the changelog has an [Unreleased] section."""
    if "[Unreleased]" in content:
        return content

    # Find the first version header
    version_pattern = r"^## \[\d+\.\d+\.\d+\]"
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if re.match(version_pattern, line):
            # Insert [Unreleased] section before the first version
            unreleased = [
                "## [Unreleased]",
                "",
                "### Added",
                "",
                "### Changed",
                "",
                "### Deprecated",
                "",
                "### Removed",
                "",
                "### Fixed",
                "",
                "### Security",
                "",
            ]
            lines[i:i] = unreleased
            return "\n".join(lines)

    # No version found, add at the end of the header
    header_end = content.find("\n## ")
    if header_end == -1:
        # Just append to the end
        unreleased_template = (
            "\n\n## [Unreleased]\n\n### Added\n\n### Changed\n\n"
            "### Deprecated\n\n### Removed\n\n### Fixed\n\n### Security\n"
        )
        return content + unreleased_template

    return content


def add_entry_to_section(
    content: str,
    section: str,
    entry: str,
    pr: Optional[int] = None,
    issue: Optional[int] = None,
) -> str:
    """Add an entry to the specified section in [Unreleased]."""
    # Build the full entry with PR/issue links
    full_entry = f"- {entry}"

    refs = []
    if pr:
        refs.append(
            f"[#{pr}](https://github.com/hakonhagland/pylint-sort-functions/pull/{pr})"
        )
    if issue:
        refs.append(
            f"[#{issue}](https://github.com/hakonhagland/pylint-sort-functions/issues/{issue})"
        )

    if refs:
        full_entry += f" ({', '.join(refs)})"

    # Find the section header in [Unreleased]
    unreleased_start = content.find("## [Unreleased]")
    if unreleased_start == -1:
        raise ValueError("[Unreleased] section not found")

    # Find the next version section (to know where [Unreleased] ends)
    next_version_match = re.search(
        r"^## \[\d+\.\d+\.\d+\]", content[unreleased_start + 15 :], re.MULTILINE
    )

    if next_version_match:
        unreleased_end = unreleased_start + 15 + next_version_match.start()
    else:
        unreleased_end = len(content)

    unreleased_content = content[unreleased_start:unreleased_end]

    # Find the specific subsection
    section_header = f"### {section.capitalize()}"
    section_start = unreleased_content.find(section_header)

    if section_start == -1:
        # Section doesn't exist, add it
        # Find a good place to insert it (maintain order)
        sections_order = [
            "Added",
            "Changed",
            "Deprecated",
            "Removed",
            "Fixed",
            "Security",
        ]
        section_cap = section.capitalize()

        insert_pos = None
        for i, sec in enumerate(sections_order):
            if sec == section_cap:
                # Find where to insert based on order
                for j in range(i + 1, len(sections_order)):
                    next_sec = f"### {sections_order[j]}"
                    next_pos = unreleased_content.find(next_sec)
                    if next_pos != -1:
                        insert_pos = next_pos
                        break
                break

        if insert_pos is None:
            # Add at the end of [Unreleased]
            unreleased_content = (
                unreleased_content.rstrip() + f"\n\n{section_header}\n\n{full_entry}\n"
            )
        else:
            # Insert before the next section
            before = unreleased_content[:insert_pos].rstrip()
            after = unreleased_content[insert_pos:]
            unreleased_content = (
                f"{before}\n\n{section_header}\n\n{full_entry}\n\n{after}"
            )
    else:
        # Section exists, add entry to it
        # Find the next section or end
        next_section_match = re.search(
            r"^### ",
            unreleased_content[section_start + len(section_header) :],
            re.MULTILINE,
        )

        if next_section_match:
            section_end = (
                section_start + len(section_header) + next_section_match.start()
            )
        else:
            section_end = len(unreleased_content)

        section_content = unreleased_content[section_start:section_end].rstrip()

        # Check if section is empty (just has the header)
        if section_content.strip() == section_header:
            # Empty section, add the entry with proper spacing
            section_content = f"{section_header}\n\n{full_entry}\n"
        else:
            # Section has entries, append to it with proper spacing
            section_content = f"{section_content}\n{full_entry}\n"

        # Ensure proper spacing after the section if there's content following
        after_section = unreleased_content[section_end:]
        if after_section.strip() and not section_content.endswith("\n\n"):
            # Add extra newline if there's content after and no double newline
            section_content = section_content.rstrip() + "\n\n"

        unreleased_content = (
            unreleased_content[:section_start] + section_content + after_section
        )

    # Replace the [Unreleased] section in the original content
    return content[:unreleased_start] + unreleased_content + content[unreleased_end:]


def clean_empty_sections(content: str) -> str:
    """Remove empty sections from [Unreleased] but keep at least one."""
    # Only clean within [Unreleased] section
    unreleased_start = content.find("## [Unreleased]")
    if unreleased_start == -1:
        return content

    # Find the next version section
    next_version_match = re.search(
        r"^## \[\d+\.\d+\.\d+\]", content[unreleased_start + 15 :], re.MULTILINE
    )

    if next_version_match:
        unreleased_end = unreleased_start + 15 + next_version_match.start()
    else:
        unreleased_end = len(content)

    unreleased_content = content[unreleased_start:unreleased_end]

    # Remove empty sections (but keep the one we just added to)
    # Only match empty sections that are completely within the [Unreleased] section
    sections = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
    for section in sections:
        # Updated pattern: only match empty sections followed by subsection (###)
        # or at the end of the [Unreleased] section (not version headers ##)
        pattern = f"### {section}\n\n(?=###|$)"
        unreleased_content = re.sub(pattern, "", unreleased_content)

    # Clean up any trailing empty lines before the end of [Unreleased] section
    unreleased_content = unreleased_content.rstrip() + "\n"

    return content[:unreleased_start] + unreleased_content + content[unreleased_end:]


def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        changelog_path = get_changelog_path()

        # Read the current changelog
        content = changelog_path.read_text()

        # Ensure [Unreleased] section exists
        content = ensure_unreleased_section(content)

        # Add BREAKING prefix if needed
        message = args.message
        if args.breaking:
            message = f"**BREAKING**: {message}"

        # Add the entry
        content = add_entry_to_section(content, args.type, message, args.pr, args.issue)

        # Clean up empty sections
        content = clean_empty_sections(content)

        # Write back
        changelog_path.write_text(content)

        print(f"✅ Added {args.type} entry to CHANGELOG.md")
        if args.breaking:
            print("⚠️  Marked as BREAKING change")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
