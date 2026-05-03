#!/usr/bin/env python3
"""Road kilometre marker validation for road index files.

Companion to validate_roads.py. Checks km values in Holds sections of road
index files (place_<road>.md or place_the_<road>.md):
  - Holds entries follow format: `* [km X.X](piece_the_kilometerstein.md): [Name](...)`
  - km values are in strictly ascending order
  - No duplicate km values
  - All values are valid floats

Read-only. The index has no parent in the architecture's hierarchy, so most
issues here cannot be auto-resolved - the validator can only state the
contradiction and ask for human engagement.

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

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue

HOLDS_BLOCK_RE = re.compile(r"^## Holds\r?\n(.*?)(?=\r?\n## |\Z)", re.MULTILINE | re.DOTALL)
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


def validate(path: Path, root: Path) -> list[Issue]:
    """Validate km values inside a road index. No-op for non-index files."""
    if classify(path, root) != "road_index":
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    issues: list[Issue] = []

    holds_match = HOLDS_BLOCK_RE.search(text)
    if not holds_match:
        return [Issue(error="no Holds section found", verdict=None)]

    holds_text = holds_match.group(1)
    km_matches = KM_ENTRY_RE.findall(holds_text)

    if not km_matches:
        return [Issue(error="Holds section has no km entries", verdict=None)]

    km_values: list[float] = []
    for i, km_str in enumerate(km_matches):
        try:
            km_values.append(float(km_str))
        except ValueError:
            issues.append(Issue(
                error=f"entry {i+1}: km value '{km_str}' is not a valid float",
                verdict=None,
            ))
            km_values.append(float("nan"))

    # Strict-ascending: same value triggers ascending error AND duplicate. Report once.
    seen_at: dict[float, int] = {}
    for i, km in enumerate(km_values):
        if km != km:  # NaN from earlier failure
            continue
        if km in seen_at:
            issues.append(Issue(
                error=f"duplicate km {km} at entries {seen_at[km]+1} and {i+1}",
                verdict=None,
            ))
        else:
            seen_at[km] = i

    for i in range(1, len(km_values)):
        prev, curr = km_values[i-1], km_values[i]
        if prev != prev or curr != curr:
            continue
        if curr < prev:
            issues.append(Issue(
                error=f"entry {i+1} (km {curr}) is before entry {i} (km {prev})",
                verdict=None,
            ))
        # equal case already covered by duplicate check above

    return issues


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    targets = [p for p in targets if classify(p, root) == "road_index"]
    if not targets:
        print("OK: no road index files in scope")
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
        print(f"\n{failed}/{total} files failed km validation")
        return 1
    print(f"OK: {total} files passed km validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
