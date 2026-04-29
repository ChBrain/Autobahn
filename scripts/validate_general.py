#!/usr/bin/env python3
"""General validation for all place_*.md files in the Autobahn world.

Checks each file for:
  - UTF-8 encoding with no byte-order mark
  - No Unicode replacement character (U+FFFD)
  - Required sections present in order: Owner, Shown, Holds, Offers, Withheld
  - Trailing version footer: `vX.Y.Z - KAI Worlds`

Then calls validate_roads, which calls validate_roads_km.

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_general.py            # walks the repo
  scripts/validate_general.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

REQUIRED_SECTIONS = ["Owner", "Shown", "Holds", "Offers", "Withheld"]
FOOTER_RE = re.compile(r"v\d+\.\d+\.\d+\s*[-\u2013\u2014]\s*KAI Worlds")
SECTION_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    raw = path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("starts with UTF-8 BOM")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [f"not valid UTF-8: {exc}"]

    if "\ufffd" in text:
        errors.append("contains U+FFFD replacement character")

    headings = SECTION_RE.findall(text)
    seen = [h for h in headings if h in REQUIRED_SECTIONS]
    if seen != REQUIRED_SECTIONS:
        errors.append(
            f"sections out of order or missing: got {seen}, expected {REQUIRED_SECTIONS}"
        )

    if not FOOTER_RE.search(text):
        errors.append("missing or malformed `vX.Y.Z - KAI Worlds` footer")

    return errors


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    failed = 0
    for path in targets:
        errors = validate(path)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for err in errors:
                print(f"  - {err}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed general validation")
        return 1
    print(f"OK: {total} files passed general validation")
    
    # Pass to next validator
    print()
    import validate_roads
    return validate_roads.main(["validate_roads"] + [str(f) for f in targets])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
