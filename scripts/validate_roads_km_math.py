#!/usr/bin/env python3
"""Validate km values and distances in place files against road index.

Strict format enforcement: place files must follow the format used in A24:
  - Holds must contain: `[km X.X](piece_the_kilometerstein.md): Place-Name.`
  - No asterisk, no "on [Road]" text, no variations
  - Shown distances must match calculated distances from index km values

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

# Extract km from road index Holds section
INDEX_KM_RE = re.compile(
    r"^\s*\*\s*\[km\s+([\d.]+)\]\(piece_the_kilometerstein\.md\):\s*\[([^\]]+)\]\(([^)]+\.md)\)",
    re.MULTILINE,
)

# STRICT: place file km format - exactly: [km X.X](piece_the_kilometerstein.md): ...
# No asterisk, no "on [Road]" variation
PLACE_KM_RE = re.compile(
    r"^\s*\[km\s+([\d.]+)\]\(piece_the_kilometerstein\.md\):\s*",
    re.MULTILINE,
)

# Extract distances from Shown: `- X km (direction): [Name](link)`
DISTANCE_RE = re.compile(
    r"^\s*-\s*([\d.]+)\s*km\s+\w+[:/]?\s*\[([^\]]+)\]\(([^)]+\.md)\)",
    re.MULTILINE,
)

HOLDS_BLOCK_RE = re.compile(r"^## Holds\r?\n(.*?)(?=\r?\n##|\Z)", re.MULTILINE | re.DOTALL)
SHOWN_BLOCK_RE = re.compile(r"^## Shown\r?\n(.*?)(?=\r?\n##|\Z)", re.MULTILINE | re.DOTALL)


def classify(path: Path, root: Path) -> str:
    """Return 'place_node' or 'other'."""
    path = path.resolve()
    root = root.resolve()
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "other"
    parts = rel.parts
    # place_node: place_<road>_<number>_*.md (not place_<road>.md)
    if parts[0] == "roads" and len(parts) >= 3:
        stem = path.stem
        if stem.startswith("place_") and stem.count("_") >= 2:
            # place_a24_01_hamburg_horn -> road_node
            # place_a24 -> not a node
            parts = stem.split("_")
            if len(parts) >= 3 and parts[2].isdigit():
                return "place_node"
    return "other"


def find_place_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def get_index_km_map(root: Path, road: str) -> Dict[str, Tuple[str, float]]:
    """Read road index and return map of filename -> (name, km)."""
    index_file = root / "roads" / road / f"place_{road}.md"
    if not index_file.exists():
        return {}
    
    try:
        text = index_file.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return {}
    
    km_map: Dict[str, Tuple[str, float]] = {}
    for match in INDEX_KM_RE.finditer(text):
        km_str, name, link = match.groups()
        try:
            km = float(km_str)
            filename = Path(link).name
            km_map[filename] = (name, km)
        except ValueError:
            continue
    
    return km_map


def extract_road_from_path(path: Path) -> str | None:
    """Extract road name from place_<road>_*.md"""
    stem = path.stem
    if stem.startswith("place_"):
        parts = stem.split("_")
        if len(parts) >= 3:
            return parts[1]  # e.g., "a24" from "place_a24_01_name"
    return None


def validate(path: Path, root: Path) -> List[str]:
    errors: List[str] = []
    
    kind = classify(path, root)
    if kind != "place_node":
        return []
    
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ["could not read file as UTF-8"]
    
    road = extract_road_from_path(path)
    if not road:
        return ["could not extract road name from filename"]
    
    # Get index km map
    km_map = get_index_km_map(root, road)
    if not km_map:
        return ["road index not found or has no km entries"]
    
    filename = path.name
    if filename not in km_map:
        return ["file not found in road index"]
    
    _, index_km = km_map[filename]
    
    # Check Holds section for km marker
    holds_match = HOLDS_BLOCK_RE.search(text)
    if not holds_match:
        return ["no Holds section found"]
    
    holds_text = holds_match.group(1)
    km_matches = PLACE_KM_RE.findall(holds_text)
    
    if not km_matches:
        errors.append("Holds missing km marker (must be: [km X.X](piece_the_kilometerstein.md): ...)")
        return errors
    
    # Strict format check: only one km line allowed
    if len(km_matches) > 1:
        errors.append(f"multiple km markers found ({len(km_matches)}), expected exactly 1")
        return errors
    
    try:
        file_km = float(km_matches[0])
    except ValueError:
        errors.append(f"km value '{km_matches[0]}' is not a valid float")
        return errors
    
    # Check km match with tolerance
    if abs(file_km - index_km) > 0.05:
        errors.append(
            f"km mismatch: file has {file_km}, index has {index_km}"
        )
    
    # Validate distances in Shown section
    shown_match = SHOWN_BLOCK_RE.search(text)
    if shown_match:
        shown_text = shown_match.group(1)
        for dist_match in DISTANCE_RE.finditer(shown_text):
            distance_str, neighbour_name, neighbour_link = dist_match.groups()
            
            try:
                distance = float(distance_str)
            except ValueError:
                errors.append(f"distance '{distance_str}' is not a valid float")
                continue
            
            neighbour_file = Path(neighbour_link).name
            if neighbour_file not in km_map:
                errors.append(f"referenced file '{neighbour_file}' not in road index")
                continue
            
            _, neighbour_km = km_map[neighbour_file]
            
            # Check distance accuracy
            actual_distance = abs(neighbour_km - file_km)
            if abs(distance - actual_distance) > 0.1:  # 100m tolerance (x.y precision)
                errors.append(
                    f"distance to {neighbour_name}: stated {distance} km, "
                    f"calculated {actual_distance:.1f} km (km {file_km} to km {neighbour_km})"
                )
    
    return errors


def main(argv: List[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    
    if len(argv) > 1:
        targets = [Path(a).resolve() for a in argv[1:]]
    else:
        targets = find_place_files(root)
    
    # Only validate place node files
    targets = [p for p in targets if classify(p, root) == "place_node"]
    
    if not targets:
        print("OK: no place node files to validate")
        return 0
    
    failed = 0
    for path in targets:
        errors = validate(path, root)
        if errors:
            failed += 1
            try:
                display_path = path.relative_to(root)
            except ValueError:
                display_path = path
            print(f"FAIL {display_path}")
            for err in errors:
                print(f"  - {err}")
    
    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed km math validation")
        return 1
    print(f"OK: {total} files passed km math validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
