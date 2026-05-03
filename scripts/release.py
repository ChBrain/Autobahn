#!/usr/bin/env python3
"""Release version management - triggered by release tag creation.

When a release tag is created (e.g., v0.3.0), this script:
1. Extracts the version from the tag
2. Detects if it's a minor or major bump vs current version
3. Updates all file footers to match the tag version
4. Commits the version bump (if needed)
5. Ensures the commit is tagged

This is part of the release workflow and should NOT be run manually.

Usage (by release workflow):
  scripts/release.py --tag v0.3.0 --commit-if-needed

Exit codes:
  0 = success
  1 = tag format invalid
  2 = no files to update
  3 = version detection failed
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

FOOTER_RE = re.compile(
    r"(v)(\d+)\.(\d+)\.(\d+)(\s*-\s*KAI Worlds)"
)
ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "scripts", ".github", "dist"}


def parse_version(tag: str) -> tuple[int, int, int] | None:
    """Parse version from tag like 'v0.3.0' -> (0, 3, 0)."""
    m = re.match(r"v(\d+)\.(\d+)\.(\d+)$", tag)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def get_current_version() -> tuple[int, int, int] | None:
    """Extract current version from any file footer."""
    for p in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        text = p.read_text(encoding="utf-8")
        m = FOOTER_RE.search(text)
        if m:
            return (int(m.group(2)), int(m.group(3)), int(m.group(4)))
    return None


def detect_bump_type(
    current: tuple[int, int, int],
    target: tuple[int, int, int],
) -> str:
    """Determine if bump is major, minor, or patch."""
    curr_major, curr_minor, curr_patch = current
    tgt_major, tgt_minor, tgt_patch = target
    
    if tgt_major > curr_major:
        return "major"
    elif tgt_minor > curr_minor:
        return "minor"
    elif tgt_patch > curr_patch:
        return "patch"
    else:
        return "none"


def find_world_files() -> list[Path]:
    """Every *.md in the world."""
    out: list[Path] = []
    for p in ROOT.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(ROOT).parts):
            continue
        out.append(p)
    return sorted(out)


def update_to_version(
    text: str,
    target_major: int,
    target_minor: int,
    target_patch: int,
) -> tuple[str, bool]:
    """Update all version footers to target version."""
    changed = False

    def repl(m: re.Match) -> str:
        nonlocal changed
        changed = True
        return f"v{target_major}.{target_minor}.{target_patch}{m.group(5)}"

    new = FOOTER_RE.sub(repl, text)
    return new, changed


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Bump version to match release tag"
    )
    ap.add_argument(
        "--tag",
        required=True,
        help="Release tag (e.g., v0.3.0)",
    )
    ap.add_argument(
        "--commit-if-needed",
        action="store_true",
        help="Commit version changes if needed",
    )
    args = ap.parse_args(argv[1:])

    # Parse tag
    tag_version = parse_version(args.tag)
    if not tag_version:
        print(f"ERROR: Invalid tag format: {args.tag}", file=sys.stderr)
        print("       Expected format: vX.Y.Z (e.g., v0.3.0)", file=sys.stderr)
        return 1

    tgt_major, tgt_minor, tgt_patch = tag_version

    # Get current version
    current = get_current_version()
    if not current:
        print("ERROR: Could not detect current version from file footers", file=sys.stderr)
        return 3

    # Determine bump type
    bump_type = detect_bump_type(current, tag_version)
    print(f"Current version: v{current[0]}.{current[1]}.{current[2]}")
    print(f"Target version:  {args.tag}")
    print(f"Bump type:       {bump_type}")

    if bump_type == "none":
        print("✓ No version change needed (already at target)")
        return 0

    # Update files
    files = find_world_files()
    if not files:
        print("ERROR: No .md files found", file=sys.stderr)
        return 2

    updated = 0
    for p in files:
        text = p.read_text(encoding="utf-8")
        new, changed = update_to_version(text, tgt_major, tgt_minor, tgt_patch)
        if changed:
            p.write_text(new, encoding="utf-8")
            updated += 1

    print(f"✓ Updated {updated}/{len(files)} files to {args.tag}")

    # Commit if requested
    if args.commit_if_needed and updated > 0:
        try:
            subprocess.run(
                ["git", "add", "-A"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"chore: release {args.tag}"],
                cwd=ROOT,
                check=True,
                capture_output=True,
            )
            print(f"✓ Committed version bump to {args.tag}")
        except subprocess.CalledProcessError as e:
            print(f"ERROR: Failed to commit: {e}", file=sys.stderr)
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
