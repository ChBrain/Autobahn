#!/usr/bin/env python3
"""Bump every `vX.Y.Z - KAI Worlds` footer across the repo.

**Patch bumps only.** Triggered automatically by CI on every push to main.
Cannot be invoked manually - enforced by checking for CI environment.

Minor and major releases are handled exclusively by the release process
(scripts/release.py), which is triggered by GitHub release tags.

Usage (CI only):
  scripts/bump_version.py --patch       # X.Y.Z -> X.Y.(Z+1)
  
Exit codes:
  0 = success
  1 = attempted manual patch bump (not in CI)
  2 = no files to bump
  3 = argument parsing error
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

FOOTER_RE = re.compile(
    r"(v)(\d+)\.(\d+)\.(\d+)(\s*-\s*KAI Worlds)"
)
ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "scripts", ".github", "dist"}


def is_ci_environment() -> bool:
    """Detect if running in GitHub Actions CI."""
    return os.getenv("GITHUB_ACTIONS") == "true"


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
    """Bump version footer. Only 'patch' is supported."""
    if kind != "patch":
        raise ValueError(f"unsupported version bump: {kind} (only 'patch' allowed)")
    
    changed = False

    def repl(m: re.Match) -> str:
        nonlocal changed
        major, minor, patch = int(m.group(2)), int(m.group(3)), int(m.group(4))
        # Patch bump only
        patch += 1
        changed = True
        return f"{m.group(1)}{major}.{minor}.{patch}{m.group(5)}"

    new = FOOTER_RE.sub(repl, text)
    return new, changed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Bump patch version in file footers (CI only)"
    )
    ap.add_argument(
        "--patch",
        action="store_true",
        required=True,
        help="Bump patch version (X.Y.Z -> X.Y.Z+1). Only option allowed."
    )
    
    try:
        args = ap.parse_args(argv[1:])
    except SystemExit as e:
        return 3 if e.code != 0 else 0

    # Guard: only allow in CI environment
    if not is_ci_environment():
        print("", file=sys.stderr)
        print("ERROR: bump_version.py is CI-ONLY and cannot run locally.", file=sys.stderr)
        print("", file=sys.stderr)
        print("This script is part of the CI/CD pipeline and should never be invoked", file=sys.stderr)
        print("outside of GitHub Actions.", file=sys.stderr)
        print("", file=sys.stderr)
        print("CORRECT WORKFLOW:", file=sys.stderr)
        print("  1. Create .bump-type file: echo 'PATCH' > .bump-type", file=sys.stderr)
        print("  2. Commit it: git add .bump-type && git commit -m 'chore: declare bump type'", file=sys.stderr)
        print("  3. Make content changes", file=sys.stderr)
        print("  4. Commit changes: git add -A && git commit -m 'your message'", file=sys.stderr)
        print("  5. Push and open PR - CI will validate and bump version on merge", file=sys.stderr)
        print("", file=sys.stderr)
        print("DO NOT run bump_version.py locally.", file=sys.stderr)
        print("", file=sys.stderr)
        return 1

    files = find_world_files()
    if not files:
        print("No .md files found to bump")
        return 2
    
    bumped = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        new, changed = bump_footer(text, "patch")
        if changed:
            p.write_text(new, encoding="utf-8")
            bumped += 1
    
    if bumped == 0:
        print(f"No version footers found to bump (visited {len(files)} files)")
        return 2
    
    print(f"✓ bumped {bumped}/{len(files)} files (patch)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
