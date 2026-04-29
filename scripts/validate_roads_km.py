#!/usr/bin/env python3
"""Road kilometre marker validation for index files in the Autobahn world.

Companion to validate_roads.py. Checks km values in Holds sections of road
index files (place_<road>.md or place_the_<road>.md):
  - Holds entries follow format: `* [km X.X](piece_the_kilometerstein.md): [Name](...)`
  - km values are in strictly ascending order
  - No duplicate km values
  - All values are valid floats

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_roads_km.py            # walks the repo
  scripts/validate_roads_km.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Import the math validator
try:
    from validate_roads_km_math import main as validate_km_math
except ImportError:
    validate_km_math = None

HOLDS_BLOCK_RE = re.compile(r"^## Holds\r?\n(.*?)(?=\r?\n##|\Z)", re.MULTILINE | re.DOTALL)
KM_ENTRY_RE = re.compile(
    r"^\s*\*\s*\[km\s+([\d.]+)\]\(piece_the_kilometerstein\.md\):",
    re.MULTILINE,
)


def classify(path: Path, root: Path) -> str:
    """Return 'road_index' or 'other'."""
    path = path.resolve()
    root = root.resolve()
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "other"
    parts = rel.parts
    if parts[0] == "roads" and len(parts) >= 3:
        road = parts[1]
        stem = path.stem
        if stem == f"place_{road}" or stem == f"place_the_{road}":
            return "road_index"
    return "other"


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path, root: Path) -> list[str]:
    errors: list[str] = []
    
    kind = classify(path, root)
    if kind != "road_index":
        return []  # Only validate road index files

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ["could not read file as UTF-8"]

    holds_match = HOLDS_BLOCK_RE.search(text)
    if not holds_match:
        return ["no Holds section found"]

    holds_text = holds_match.group(1)
    km_matches = KM_ENTRY_RE.findall(holds_text)

    if not km_matches:
        return ["Holds section has no km entries"]

    km_values: list[float] = []
    for i, km_str in enumerate(km_matches):
        try:
            km = float(km_str)
            km_values.append(km)
        except ValueError:
            errors.append(f"entry {i+1}: km value '{km_str}' is not a valid float")
            continue

    # Check for ascending order
    for i in range(1, len(km_values)):
        if km_values[i] <= km_values[i - 1]:
            errors.append(
                f"km values not in ascending order: "
                f"entry {i} has {km_values[i]}, "
                f"entry {i+1} has {km_values[i-1]}"
            )

    # Check for duplicates
    seen = set()
    for i, km in enumerate(km_values):
        if km in seen:
            errors.append(f"entry {i+1}: duplicate km value {km}")
        seen.add(km)

    return errors


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    # Only validate road index files
    targets = [p for p in targets if classify(p, root) == "road_index"]

    if not targets:
        print("OK: no km checks needed (no road index files)")
    else:
        failed = 0
        for path in targets:
            errors = validate(path, root)
            if errors:
                failed += 1
                print(f"FAIL {path}")
                for err in errors:
                    print(f"  - {err}")

        total = len(targets)
        if failed:
            print(f"\n{failed}/{total} files failed km validation")
            return 1
        print(f"OK: {total} files passed km validation")

    # Cascade to km math validation
    if validate_km_math:
        return validate_km_math(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
