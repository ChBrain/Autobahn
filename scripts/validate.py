#!/usr/bin/env python3
"""Runner: executes all Autobahn validators in sequence.

Runs validation pipeline:
  1. validate_general.py - encoding, section order, footer
  2. validate_roads.py - road architecture compliance
  3. validate_roads_km.py - kilometre marker ordering and format

Exit status:
  0 if all validators pass, 1 if any fail.

Usage:
  scripts/validate.py              # audit - validates all place_*.md files
  scripts/validate.py FILE...      # validates only the given files (CI mode)
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import validate_general


def main() -> int:
    root = HERE.parent

    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:] if Path(f).name.startswith("place_")]
    else:
        files = validate_general.find_place_files(root)

    # Start the validation pipeline
    print("=== General validation ===")
    return validate_general.main(["validate_general"] + [str(f) for f in files])


if __name__ == "__main__":
    sys.exit(main())
