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
    """Per-state checks. Today: nothing beyond the general layer.

    Kept as a distinct sibling so future state-specific rules have an
    obvious home and the DAG continues to express the layered shape.
    """
    if not is_state_file(path, root):
        return []
    return []


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
