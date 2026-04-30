#!/usr/bin/env python3
"""Validate state place_*.md files for basic compliance.

Checks each state file for:
  - UTF-8 encoding with no byte-order mark
  - Required sections present in order: Owner, Shown, Holds, Offers, Withheld
  - Trailing version footer: `vX.Y.Z - KAI Worlds`

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_states.py            # walks states folder
  scripts/validate_states.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import validate_general

REQUIRED_SECTIONS = ["Owner", "Shown", "Holds", "Offers", "Withheld"]


def find_state_files(root: Path) -> list[Path]:
    """Find all state place_*.md files."""
    return sorted(p for p in (root / "states").rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[str]:
    """Validate a state file using general validation."""
    return validate_general.validate(path)


def main(argv: list[str]) -> int:
    root = HERE.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_state_files(root)
    
    if not targets:
        print("OK: no state files to validate")
        return 0
    
    failed = 0
    for path in targets:
        errors = validate(path)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for err in errors:
                print(f"  - {err}")
    
    passed = len(targets) - failed
    if failed:
        print(f"\n{failed}/{len(targets)} state files failed validation")
        return 1
    
    print(f"OK: {passed} state files passed validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
