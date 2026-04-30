#!/usr/bin/env python3
"""Navigation link placement validation for place_*.md files.

Enforces the rule from ARCHITECTURE.md:
  - Shown: what the driver sees from the carriageway
  - Holds: carries the kilometerstein position AND navigation links to adjacent stops

This validator checks that neighbour links (distance + direction markers like
"3.4 km north: [Name](...md)") appear in ## Holds, not in ## Shown.

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_navigation_links.py            # walks the repo
  scripts/validate_navigation_links.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Regex for a neighbour link: "- <number> km <direction>: [Name](...md)"
# Captures lines like:
#   - 3.4 km north: [Neumünster-Nord](place_a7_13_neumuenster_nord.md)
#   - 2 km south: [Exit](place_exit.md)
#   - 43 km south: [Heide-West](place_a23_02_heide_west.md) - where B5 becomes A23
NEIGHBOUR_LINK_RE = re.compile(
    r"^-\s+[\d.]+\s+km\s+\w+:\s+\[.+?\]\(place_[^)]+\.md\)",
    re.MULTILINE,
)

# Regex to extract sections: "## Section" followed by content until next ## or EOF
SECTION_RE = re.compile(r"^## (\w+)\r?\n(.*?)(?=^##|\Z)", re.MULTILINE | re.DOTALL)


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[str]:
    """Check that navigation links appear only in ## Holds, not in ## Shown."""
    errors: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ["could not read file as UTF-8"]

    # Extract all sections
    sections = {name: content for name, content in SECTION_RE.findall(text)}

    # Check for neighbour links in ## Shown
    if "Shown" in sections:
        shown_links = NEIGHBOUR_LINK_RE.findall(sections["Shown"])
        if shown_links:
            errors.append(
                f"found {len(shown_links)} neighbour link(s) in ## Shown; must move to ## Holds:\n"
                + "\n".join(f"    {link}" for link in shown_links)
            )

    return errors


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    failed = 0
    for path in targets:
        errors = validate(path)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for err in errors:
                print(f"  - {err}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed navigation link validation")
        return 1
    print(f"OK: {total} files passed navigation link validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
