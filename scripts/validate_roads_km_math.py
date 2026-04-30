#!/usr/bin/env python3
"""Validate km values and distances in road node files against the road index.

Hierarchy: the road index is authoritative. A node's km marker must match
the index; Shown distances must match the index-derived calculation. When
they don't, the verdict is determined: the node is wrong.

Strict format enforcement: place files must follow the format used in A24:
  - Holds must contain: `[km X.X](piece_the_kilometerstein.md): Place-Name.`
  - No asterisk, no "on [Road]" text, no variations
  - Shown distances must match calculated distances from index km values

Read-only. Emits Issue records with verdicts where the architecture
arbitrates. Orchestration is validate.py's job.

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_roads_km_math.py            # walks the repo
  scripts/validate_roads_km_math.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue

INDEX_KM_RE = re.compile(
    r"^\s*\*\s*\[km\s+([\d.]+)\]\(piece_the_kilometerstein\.md\):\s*\[([^\]]+)\]\(([^)]+\.md)\)",
    re.MULTILINE,
)

# Strict node km format: `[km X.X](piece_the_kilometerstein.md): ...`
PLACE_KM_RE = re.compile(
    r"^\s*\[km\s+([\d.]+)\]\(piece_the_kilometerstein\.md\):\s*",
    re.MULTILINE,
)

DISTANCE_RE = re.compile(
    r"^\s*-\s*([\d.]+)\s*km\s+\w+[:/]?\s*\[([^\]]+)\]\(([^)]+\.md)\)",
    re.MULTILINE,
)

HOLDS_BLOCK_RE = re.compile(r"^## Holds\r?\n(.*?)(?=\r?\n##|\Z)", re.MULTILINE | re.DOTALL)


def classify(path: Path, root: Path) -> str:
    """Return 'place_node' or 'other'."""
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
        if stem.startswith("place_") and stem not in (f"place_{road}", f"place_the_{road}"):
            return "place_node"
    return "other"


def find_place_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def get_index_km_map(root: Path, road: str) -> Dict[str, Tuple[str, float]]:
    """Read the road index. Map filename -> (display name, km)."""
    for stem in (f"place_{road}", f"place_the_{road}"):
        index_file = root / "roads" / road / f"{stem}.md"
        if index_file.exists():
            break
    else:
        return {}

    try:
        text = index_file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {}

    km_map: Dict[str, Tuple[str, float]] = {}
    for match in INDEX_KM_RE.finditer(text):
        km_str, name, link = match.groups()
        try:
            km_map[Path(link).name] = (name, float(km_str))
        except ValueError:
            continue
    return km_map


def extract_road_from_path(path: Path, root: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    parts = rel.parts
    if len(parts) >= 3 and parts[0] == "roads":
        return parts[1]
    return None


def validate(path: Path, root: Path) -> List[Issue]:
    if classify(path, root) != "place_node":
        return []

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []

    road = extract_road_from_path(path, root)
    if not road:
        return []

    km_map = get_index_km_map(root, road)
    if not km_map:
        return []

    filename = path.name
    if filename not in km_map:
        # Bridges and other off-chain nodes legitimately do not appear in
        # the index Holds. Skip silently rather than failing.
        return []

    _, index_km = km_map[filename]
    issues: List[Issue] = []

    holds_match = HOLDS_BLOCK_RE.search(text)
    if not holds_match:
        return [Issue(error="no Holds section found", verdict=None)]

    holds_text = holds_match.group(1)
    km_matches = PLACE_KM_RE.findall(holds_text)

    if not km_matches:
        return [Issue(
            error="Holds missing km marker",
            verdict="add `[km X.X](piece_the_kilometerstein.md): ...` to Holds "
                    f"with km {index_km} (from index)",
        )]

    if len(km_matches) > 1:
        return [Issue(
            error=f"multiple km markers in Holds ({len(km_matches)})",
            verdict=f"keep exactly one km marker, set to {index_km} (from index)",
        )]

    try:
        file_km = float(km_matches[0])
    except ValueError:
        return [Issue(
            error=f"km value '{km_matches[0]}' is not a valid float",
            verdict=f"set km marker to {index_km} (from index)",
        )]

    if abs(file_km - index_km) > 0.05:
        # Index wins by hierarchy - the node is wrong.
        issues.append(Issue(
            error=f"km mismatch: file has {file_km}, index has {index_km}",
            verdict=f"set node km to {index_km} (index is authoritative)",
        ))

    # Neighbour distances live in Holds per ARCHITECTURE.md (the strict A24
    # format). The legacy convention put them in Shown - that history is why
    # this check used to read Shown.
    for dist_match in DISTANCE_RE.finditer(holds_text):
        distance_str, neighbour_name, neighbour_link = dist_match.groups()
        try:
            distance = float(distance_str)
        except ValueError:
            issues.append(Issue(
                error=f"distance '{distance_str}' is not a valid float",
                verdict=None,
            ))
            continue

        neighbour_file = Path(neighbour_link).name
        if neighbour_file not in km_map:
            # Node references a file the index does not acknowledge.
            # Hierarchy says the node is wrong, but doesn't tell us what to
            # replace the link with.
            issues.append(Issue(
                error=f"neighbour link '{neighbour_file}' not in road index",
                verdict=None,
            ))
            continue

        _, neighbour_km = km_map[neighbour_file]
        actual = abs(neighbour_km - file_km)
        if abs(distance - actual) > 0.1:
            issues.append(Issue(
                error=(f"distance to {neighbour_name}: stated {distance} km, "
                       f"calculated {actual:.1f} km (km {file_km} to km {neighbour_km})"),
                verdict=f"set Holds distance to {actual:.1f} km (computed from index)",
            ))

    return issues


def main(argv: List[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a).resolve() for a in argv[1:]] if len(argv) > 1 else find_place_files(root)
    targets = [p for p in targets if classify(p, root) == "place_node"]

    if not targets:
        print("OK: no node files in scope")
        return 0

    failed = 0
    for path in targets:
        issues = validate(path, root)
        if issues:
            failed += 1
            try:
                display = path.relative_to(root)
            except ValueError:
                display = path
            print(f"FAIL {display}")
            for issue in issues:
                print(f"  - {issue.error}")
                if issue.verdict:
                    print(f"    verdict: {issue.verdict}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed km math validation")
        return 1
    print(f"OK: {total} files passed km math validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
