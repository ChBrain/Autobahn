#!/usr/bin/env python3
"""Bump every `vX.Y.Z - KAI Worlds` footer across the repo.

This exists for minor and major releases (run by the user when a release is
requested), not for ordinary content edits. For per-file patch bumps an LLM
edits the footer in place when it edits the file.

Usage:
  scripts/bump_version.py --minor       # X.Y.Z -> X.(Y+1).0
  scripts/bump_version.py --major       # X.Y.Z -> (X+1).0.0

Never invoked unless the user has explicitly asked for a release.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FOOTER_RE = re.compile(
    r"(v)(\d+)\.(\d+)\.(\d+)(\s*-\s*KAI Worlds)"
)
ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "scripts", ".github", "dist"}


def find_world_files() -> list[Path]:
    """Every *.md in the world. The footer regex filters which actually
    get rewritten; files without a footer (README, ARCHITECTURE, etc.)
    are visited but left alone."""
    out: list[Path] = []
    for p in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return sorted(out)


def bump_footer(text: str, kind: str) -> tuple[str, bool]:
    changed = False

    def repl(m: re.Match) -> str:
        nonlocal changed
        major, minor, patch = int(m.group(2)), int(m.group(3)), int(m.group(4))
        if kind == "major":
            major, minor, patch = major + 1, 0, 0
        elif kind == "minor":
            minor, patch = minor + 1, 0
        elif kind == "patch":
            patch += 1
        else:
            raise ValueError(f"unknown kind: {kind}")
        changed = True
        return f"{m.group(1)}{major}.{minor}.{patch}{m.group(5)}"

    new = FOOTER_RE.sub(repl, text)
    return new, changed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--patch", action="store_const", dest="kind", const="patch")
    g.add_argument("--minor", action="store_const", dest="kind", const="minor")
    g.add_argument("--major", action="store_const", dest="kind", const="major")
    args = ap.parse_args(argv[1:])

    files = find_world_files()
    bumped = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        new, changed = bump_footer(text, args.kind)
        if changed:
            p.write_text(new, encoding="utf-8")
            bumped += 1
    print(f"bumped {bumped}/{len(files)} files ({args.kind})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
