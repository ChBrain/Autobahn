#!/usr/bin/env python3
"""Road architecture validation for place_*.md files in the Autobahn world.

Checks compliance with ARCHITECTURE.md ## Roads:
  - Every file Owner block contains `- Project: Autobahn`
  - Road node files  (roads/<road>/place_*.md):
      Owner must contain `- Place: [Road](place_road.md) in [Bundesland](place_bundesland.md)`
  - Road index files (roads/place_*.md):
      Owner must NOT contain a `- Place:` line

File classification by path:
  roads/place_*.md              -> road index
  roads/<road>/place_*.md       -> road node
  bundeslaender/place_*.md      -> bundesland (not checked here - see future validate_bundeslaender.py)

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_roads.py            # walks the repo
  scripts/validate_roads.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

OWNER_BLOCK_RE = re.compile(r"## Owner\n(.*?)(?=\n##|\Z)", re.DOTALL)
PLACE_LINE_RE = re.compile(
    r"^\s*-\s*Place:\s*\[.+?\]\(place_[^)]+\.md\)\s+in\s+\[.+?\]\(place_[^)]+\.md\)",
    re.MULTILINE,
)


def classify(path: Path, root: Path) -> str:
    """Return 'road_index', 'road_node', 'bundesland', or 'other'."""
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "other"
    parts = rel.parts
    if parts[0] == "bundeslaender":
        return "bundesland"
    if parts[0] == "roads":
        if len(parts) == 2:
            return "road_index"
        if len(parts) >= 3:
            return "road_node"
    return "other"


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path, root: Path) -> list[str]:
    errors: list[str] = []

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ["could not read file as UTF-8 - run validate_general.py first"]

    owner_match = OWNER_BLOCK_RE.search(text)
    owner_text = owner_match.group(1) if owner_match else ""

    if "- Project: Autobahn" not in owner_text:
        errors.append("Owner block missing `- Project: Autobahn`")

    kind = classify(path, root)
    has_place_line = bool(PLACE_LINE_RE.search(owner_text))

    if kind == "road_node" and not has_place_line:
        errors.append(
            "road node Owner missing `- Place: [Road](place_road.md) in [Bundesland](place_bundesland.md)`"
        )
    elif kind == "road_index" and has_place_line:
        errors.append("road index Owner must not contain a `- Place:` line")

    return errors


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

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
        print(f"\n{failed}/{total} files failed road architecture validation")
        return 1
    print(f"OK: {total} files passed road architecture validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
