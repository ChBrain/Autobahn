#!/usr/bin/env python3
"""Road architecture validation for place_*.md files in the Autobahn world.

Checks compliance with ARCHITECTURE.md ## Roads:
  - Every file Owner block contains `- Project: Autobahn`
  - Road node files: Owner must contain
      `- Place: [Road](place_road.md) in [Bundesland](place_bundesland.md)`
  - Road index files: Owner must NOT contain a `- Place:` line

File classification by path. Every road has its own folder at
`roads/<road>/`. The road index file lives in that folder alongside its
nodes; everything else `place_*.md` in the folder is a node.

  roads/<road>/place_<road>.md         -> road index
  roads/<road>/place_the_<road>.md     -> road index (legacy form)
  roads/<road>/place_*.md (other)      -> road node
  states/place_*.md                    -> state (checked by validate_states.py)

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

# `\r?\n` so the regex still matches if a file slipped in with CRLF endings.
OWNER_BLOCK_RE = re.compile(r"## Owner\r?\n(.*?)(?=\r?\n##|\Z)", re.DOTALL)
PLACE_LINE_RE = re.compile(
    r"^\s*-\s*Place:\s*\[.+?\]\(place_[^)]+\.md\)\s+in\s+\[.+?\]\(place_[^)]+\.md\)",
    re.MULTILINE,
)


def classify(path: Path, root: Path) -> str:
    """Return 'road_index', 'road_node', 'state', or 'other'.

    A file inside `roads/<road>/` is the road index iff its basename is
    `place_<road>.md` or the legacy `place_the_<road>.md`. Anything else
    matching `place_*.md` in that folder is a node.
    """
    path = path.resolve()
    root = root.resolve()
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "other"
    parts = rel.parts
    if parts[0] == "states":
        return "state"
    if parts[0] == "roads" and len(parts) >= 3:
        road = parts[1]
        stem = path.stem
        if stem == f"place_{road}" or stem == f"place_the_{road}":
            return "road_index"
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

    # Skip state files - they are checked by validate_states.py
    if kind == "state":
        return []

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
    
    # Pass to state validator
    print()
    import validate_states
    return validate_states.main(["validate_states"] + [str(f) for f in targets])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
