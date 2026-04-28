#!/usr/bin/env python3
"""Bump the version footer in all place_*.md files.

Reads the current highest version across all files, increments the requested
part, then rewrites every file's footer to the new version.

Usage:
  scripts/bump_version.py --patch    # 0.1.2 -> 0.1.3
  scripts/bump_version.py --minor    # 0.1.2 -> 0.2.0
  scripts/bump_version.py --major    # 0.1.2 -> 1.0.0
  scripts/bump_version.py --dry-run --minor   # preview without writing

Rules (ARCHITECTURE.md):
  --patch  LLM-level edit to a single file; this script applies it world-wide
  --minor  Release-level bump; resets patch to 0
  --major  Structural release; resets minor and patch to 0
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FOOTER_RE = re.compile(
    r"(v)(\d+)\.(\d+)\.(\d+)(\s*[-\u2013\u2014]\s*KAI Worlds)"
)
ROOT = Path(__file__).resolve().parent.parent


def find_place_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("place_*.md") if ".git" not in p.parts)


def current_max_version(files: list[Path]) -> tuple[int, int, int]:
    best = (0, 0, 0)
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        for m in FOOTER_RE.finditer(text):
            v = (int(m.group(2)), int(m.group(3)), int(m.group(4)))
            if v > best:
                best = v
    return best


def bump(version: tuple[int, int, int], part: str) -> tuple[int, int, int]:
    major, minor, patch = version
    if part == "major":
        return (major + 1, 0, 0)
    if part == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def apply_version(text: str, new: tuple[int, int, int]) -> str:
    new_str = f"v{new[0]}.{new[1]}.{new[2]}"

    def replace(m: re.Match) -> str:
        return f"{new_str}{m.group(5)}"

    return FOOTER_RE.sub(replace, text)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Bump version in all place_*.md files")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--patch", dest="part", action="store_const", const="patch")
    group.add_argument("--minor", dest="part", action="store_const", const="minor")
    group.add_argument("--major", dest="part", action="store_const", const="major")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing")
    args = parser.parse_args(argv[1:])

    files = find_place_files()
    current = current_max_version(files)
    new = bump(current, args.part)

    print(f"Bumping {args.part}: v{current[0]}.{current[1]}.{current[2]} -> v{new[0]}.{new[1]}.{new[2]}")
    if args.dry_run:
        print("Dry run - no files written.")
        return 0

    updated = 0
    skipped = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        new_text = apply_version(text, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            updated += 1
        else:
            skipped += 1

    print(f"Updated {updated} files, {skipped} had no matching footer (run validate.py to check).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
