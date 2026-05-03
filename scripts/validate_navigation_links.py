#!/usr/bin/env python3
"""Navigation link placement validation for place_*.md files.

Enforces the rule from ARCHITECTURE.md:
  - Shown: what the driver sees from the carriageway
  - Holds: kilometerstein position AND navigation links to adjacent stops

Neighbour links (`- 3.4 km north: [Name](...md)`) must appear in `## Holds`,
not in `## Shown`.

Read-only. The fix is determined by the rule, so the verdict is concrete.

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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue

NEIGHBOUR_LINK_RE = re.compile(
    r"^-\s+[\d.]+\s+km\s+[\w/-]+:\s+\[.+?\]\(place_[^)]+\.md\)",
    re.MULTILINE,
)

SECTION_RE = re.compile(r"^## (\w+)\r?\n(.*?)(?=^##|\Z)", re.MULTILINE | re.DOTALL)


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[Issue]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    sections = {name: content for name, content in SECTION_RE.findall(text)}
    if "Shown" not in sections:
        return []

    shown_links = NEIGHBOUR_LINK_RE.findall(sections["Shown"])
    if not shown_links:
        return []

    return [Issue(
        error=(f"{len(shown_links)} neighbour link(s) in ## Shown:\n"
               + "\n".join(f"      {link}" for link in shown_links)),
        verdict="move neighbour links from ## Shown to ## Holds (after the kilometerstein line)",
    )]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    failed = 0
    for path in targets:
        issues = validate(path)
        if issues:
            failed += 1
            print(f"FAIL {path}")
            for issue in issues:
                print(f"  - {issue.error}")
                if issue.verdict:
                    print(f"    verdict: {issue.verdict}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed navigation link validation")
        return 1
    print(f"OK: {total} files passed navigation link validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
