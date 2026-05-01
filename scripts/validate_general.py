#!/usr/bin/env python3
"""General validation for all place_*.md files in the Autobahn world.

Checks each file for:
  - Filename format: underscores only, no hyphens
  - UTF-8 encoding with no byte-order mark
  - No Unicode replacement character (U+FFFD)
  - No literal Unicode escape sequences
  - Required sections present in order: Owner, Shown, Holds, Offers, Withheld
  - Trailing version footer: `vX.Y.Z - KAI Worlds`

Read-only. Emits Issue records with verdicts where the rule determines
the fix. The orchestrator (validate.py) is responsible for sequencing.

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

from findings import Issue

REQUIRED_SECTIONS = ["Owner", "Shown", "Holds", "Offers", "Withheld"]
FOOTER_RE = re.compile(r"v\d+\.\d+\.\d+\s*[-–—]\s*KAI Worlds")
SECTION_RE = re.compile(r"^## (.+?)\s*$", re.MULTILINE)


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[Issue]:
    issues: list[Issue] = []

    # Check filename: no hyphens allowed, only underscores
    if "-" in path.name:
        issues.append(Issue(
            error="filename contains hyphen: use underscore instead",
            verdict=f"rename to {path.name.replace('-', '_')}",
        ))

    raw = path.read_bytes()

    if raw.startswith(b"\xef\xbb\xbf"):
        issues.append(Issue(
            error="starts with UTF-8 BOM",
            verdict="strip the leading 3 bytes (EF BB BF)",
        ))

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        return [Issue(
            error=f"not valid UTF-8: {exc}",
            verdict=None,  # encoding repair needs human - original bytes ambiguous
        )]

    if "�" in text:
        issues.append(Issue(
            error="contains U+FFFD replacement character",
            verdict=None,  # original character is lost - human must restore
        ))

    if re.search(r"\\u[0-9a-fA-F]{4}", text):
        issues.append(Issue(
            error="contains literal Unicode escape sequences",
            verdict="decode each `\\uXXXX` to its UTF-8 character",
        ))

    headings = SECTION_RE.findall(text)
    seen = [h for h in headings if h in REQUIRED_SECTIONS]
    if seen != REQUIRED_SECTIONS:
        issues.append(Issue(
            error=f"sections out of order or missing: got {seen}, expected {REQUIRED_SECTIONS}",
            verdict=f"reorder sections to: {', '.join(REQUIRED_SECTIONS)}",
        ))

    if not FOOTER_RE.search(text):
        issues.append(Issue(
            error="missing or malformed `vX.Y.Z - KAI Worlds` footer",
            verdict="append `vX.Y.Z - KAI Worlds` (X.Y.Z = current world version)",
        ))

    return issues


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    failed = 0
    for path in targets:
        issues = validate(path)
        if issues:
            failed += 1
            print(f"FAIL {path}")
            for issue in issues:
                print(f"  - {issue.error}")
                if issue.verdict:
                    print(f"    verdict: {issue.verdict}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed general validation")
        return 1
    print(f"OK: {total} files passed general validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
