#!/usr/bin/env python3
"""Runner: executes all Autobahn validators in sequence.

Runs validation pipeline:
  1. validate_general.py - encoding, section order, footer
  2. validate_roads.py → validate_roads_km.py → validate_roads_km_math.py
     (Road validation chain: architecture → km format → km math)
  3. validate_states.py - state architecture compliance

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
import validate_roads
import validate_states
import validate_navigation_links


def main() -> int:
    root = HERE.parent

    if len(sys.argv) > 1:
        files = [Path(f) for f in sys.argv[1:] if Path(f).name.startswith("place_")]
    else:
        files = validate_general.find_place_files(root)

    # Pipeline: general → roads (with chain) → states → navigation
    print("=== General validation ===")
    result = validate_general.main(["validate_general"] + [str(f) for f in files])
    if result != 0:
        return result
    
    print()
    print("=== Road validation chain ===")
    result = validate_roads.main(["validate_roads"] + [str(f) for f in files])
    if result != 0:
        return result
    
    print()
    print("=== State architecture validation ===")
    result = validate_states.main(["validate_states"] + [str(f) for f in files])
    if result != 0:
        return result
    
    print()
    print("=== Navigation link placement validation ===")
    result = validate_navigation_links.main(["validate_navigation_links"] + [str(f) for f in files])
    return result


if __name__ == "__main__":
    sys.exit(main())
