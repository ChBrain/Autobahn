#!/usr/bin/env python3
"""State architecture validation for place_*.md files in the Autobahn world.

Checks compliance with ARCHITECTURE.md ## Federal States:
  - Every state file in states/ has Owner block with `- Project: Autobahn`
  - State index files Owner must NOT contain a `- Place:` line
  - Filename must be place_{state}.md

State files are the 16 federal state aggregators. Unlike roads, states do not
have child folders - all state files live directly at states/place_*.md.

  states/place_*.md                -> state index

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_states.py            # walks the repo
  scripts/validate_states.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# `\r?\n` so the regex still matches if a file slipped in with CRLF endings.
OWNER_BLOCK_RE = re.compile(r"## Owner\r?\n(.*?)(?=\r?\n##|\Z)", re.DOTALL)
PLACE_LINE_RE = re.compile(
    r"^\s*-\s*Place:\s*\[.+?\]\(place_[^)]+\.md\)",
    re.MULTILINE,
)


def classify(path: Path, root: Path) -> str:
    """Return 'state_index' or 'other'.

    A file in states/ with filename place_*.md is a state index.
    """
    path = path.resolve()
    root = root.resolve()
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "other"
    parts = rel.parts
    if parts[0] == "states" and len(parts) == 2:
        return "state_index"
    return "other"


def find_place_files(root: Path) -> list[Path]:
    """Find all place_*.md files in states/ folder."""
    states_dir = root / "states"
    if not states_dir.exists():
        return []
    return sorted(
        p for p in states_dir.glob("place_*.md")
        if ".git" not in p.parts
    )


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

    if kind == "state_index" and has_place_line:
        errors.append("state index Owner must not contain a `- Place:` line")

    return errors


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    # Filter to only states files
    targets = [t for t in targets if classify(t, root) == "state_index"]

    if not targets:
        print("OK: 0 state files to validate")
        return 0

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
        print(f"\n{failed}/{total} files failed state architecture validation")
        return 1
    print(f"OK: {total} files passed state architecture validation")
    
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
