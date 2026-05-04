#!/usr/bin/env python3
"""Validate state place_*.md files for basic compliance.

Sibling layer to roads. Today the state-specific architecture is not yet
defined (see ARCHITECTURE.md "To document"), so this layer only delegates
to general structural checks. When state-specific rules land, add them
here.

Read-only. Emits Issue records; orchestration is validate.py's job.

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_states.py            # walks states folder
  scripts/validate_states.py FILE...    # validates only the given files
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue


def is_state_file(path: Path, root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return rel.parts and rel.parts[0] == "states"


def find_state_files(root: Path) -> list[Path]:
    return sorted(p for p in (root / "states").rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path, root: Path) -> list[Issue]:
    """Per-state checks: hierarchical Holds section structure.

    Validates that IF a state file uses hierarchical road headers 
    (- [RoadName](place_road.md) - description), then exits should be
    nested underneath with indentation.
    
    Flexible to support multiple formats during migration. Only flags
    inconsistent mixing of road headers with flat exit lists.
    """
    if not is_state_file(path, root):
        return []

    issues = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return [Issue(str(path), f"Failed to read: {e}")]

    # Find Holds section
    if "## Holds" not in text:
        return issues

    holds_start = text.find("## Holds")
    holds_end = text.find("\n## ", holds_start + 1)
    if holds_end == -1:
        holds_end = len(text)
    holds_section = text[holds_start:holds_end]

    lines = holds_section.split("\n")[1:]  # Skip "## Holds" header

    # Count structure patterns
    road_headers = 0
    nested_items = 0
    flat_exits = 0
    
    prev_was_road = False
    for line in lines:
        if not line.strip() or line.strip().startswith("#"):
            continue
            
        # Road header pattern: - [name](link) - description
        if (
            line.startswith("- [")
            and "](place_" in line
            and " - " in line
            and not line.startswith("  ")
        ):
            road_headers += 1
            prev_was_road = True
        # Nested item (indented - or *)
        elif (line.startswith("  ") or line.startswith("\t")) and line.lstrip().startswith(
            ("- ", "* ")
        ):
            nested_items += 1
            prev_was_road = False
        # Flat exit at top level (not indented)
        elif line.startswith("- [") and "](place_" in line and prev_was_road:
            flat_exits += 1

    # Only flag if clearly mixing: has road headers AND flat exits (no nesting)
    if road_headers > 0 and flat_exits > 0 and nested_items == 0:
        issues.append(
            Issue(
                str(path),
                "Holds mixes road headers with flat exit list. Either use flat format throughout, or nest exits under road headers.",
            )
        )

    return issues


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_state_files(root)
    targets = [p for p in targets if is_state_file(p, root)]

    if not targets:
        print("OK: no state files in scope")
        return 0

    failed = 0
    for path in targets:
        issues = validate(path, root)
        if issues:
            failed += 1
            print(f"FAIL {path}")
            for issue in issues:
                print(f"  - {issue.error}")
                if issue.verdict:
                    print(f"    verdict: {issue.verdict}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} state files failed validation")
        return 1
    print(f"OK: {total} state files passed validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
