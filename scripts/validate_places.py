#!/usr/bin/env python3
"""Validate place_*.md files in the Autobahn world.

Checks each file for:
  - UTF-8 source with no byte-order mark
  - No Unicode replacement character (U+FFFD), which signals decode mojibake
  - Required sections in order: Owner, Shown, Holds, Offers, Withheld
    (additional `## ` headings before Owner are allowed, e.g. epigraphs)
  - Trailing version footer of the form `vX.Y.Z - KAI Worlds`
    (hyphen, en-dash, or em-dash separator)

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_places.py            # walks the repo
  scripts/validate_places.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = ["Owner", "Shown", "Holds", "Offers", "Withheld"]
FOOTER_RE = re.compile(r"v\d+\.\d+\.\d+\s*[-–—]\s*KAI Worlds")
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

    if "�" in text:
        errors.append("contains U+FFFD replacement character (decode mojibake)")

    headings = SECTION_RE.findall(text)
    seen = [h for h in headings if h in REQUIRED_SECTIONS]
    if seen != REQUIRED_SECTIONS:
        errors.append(
            f"required sections out of order or missing: got {seen}, "
            f"expected {REQUIRED_SECTIONS}"
        )

    if not FOOTER_RE.search(text):
        errors.append("missing or malformed `vX.Y.Z - KAI Worlds` footer")

    return errors


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        targets = [Path(a) for a in argv[1:]]
    else:
        targets = find_place_files(Path(__file__).resolve().parent.parent)

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
        print(f"\n{failed}/{total} files failed validation")
        return 1
    print(f"OK: {total} files validated")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
