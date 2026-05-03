#!/usr/bin/env python3
"""Validate version bumps in pull requests.

Rules:
- Regular PRs (work): patch bumps only (x.y.z → x.y.(z+1))
- Release PRs: major/minor/patch bumps allowed (x.y.z → (x+1).0.0 or x.(y+1).0)
- Release PRs detected by: release tag on HEAD or PR title containing version

Exit codes:
  0 = valid version bump
  1 = invalid bump (minor/major in regular PR)
  2 = no version change
  3 = version parse error
  4 = cannot determine current version
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

FOOTER_RE = re.compile(
    r"v(\d+)\.(\d+)\.(\d+)\s*-\s*KAI Worlds"
)
ROOT = Path(__file__).resolve().parent.parent


def parse_version(s: str) -> tuple[int, int, int] | None:
    """Parse 'vX.Y.Z' or just 'X.Y.Z'."""
    m = re.search(r"v?(\d+)\.(\d+)\.(\d+)", s)
    if m:
        return (int(m.group(1)), int(m.group(2)), int(m.group(3)))
    return None


def get_current_version() -> tuple[int, int, int] | None:
    """Get version from main branch."""
    try:
        # Check autobahn.md first (root file with version)
        result = subprocess.run(
            ["git", "show", "origin/main:autobahn.md"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            match = FOOTER_RE.search(result.stdout)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except Exception:
        pass
    return None


def get_pr_version() -> tuple[int, int, int] | None:
    """Get version from PR branch (HEAD)."""
    try:
        for p in ROOT.rglob("*.md"):
            if ".git" in p.parts or "scripts" in p.parts or ".github" in p.parts:
                continue
            text = p.read_text(encoding="utf-8")
            match = FOOTER_RE.search(text)
            if match:
                return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    except Exception:
        pass
    return None


def is_release_pr() -> bool:
    """Detect if this is a release PR.
    
    Checks:
    - HEAD is tagged with release tag (v*.*.*)
    - PR title contains version (from GITHUB_HEAD_REF or git branch)
    """
    # Check if HEAD has a release tag
    try:
        result = subprocess.run(
            ["git", "describe", "--exact-match", "--tags", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            if parse_version(tag):
                return True
    except Exception:
        pass
    
    # Check PR title from GitHub Actions env
    pr_title = os.getenv("GITHUB_EVENT_PATH", "")
    if pr_title:
        try:
            import json
            with open(pr_title) as f:
                event = json.load(f)
                title = event.get("pull_request", {}).get("title", "")
                if parse_version(title):
                    return True
        except Exception:
            pass
    
    return False


def detect_bump_type(
    current: tuple[int, int, int],
    new: tuple[int, int, int],
) -> str:
    """Detect bump type: major, minor, patch."""
    curr_major, curr_minor, curr_patch = current
    new_major, new_minor, new_patch = new
    
    if new_major > curr_major:
        return "major"
    elif new_minor > curr_minor:
        return "minor"
    elif new_patch > curr_patch:
        return "patch"
    else:
        return "none"


def main(argv: list[str]) -> int:
    current = get_current_version()
    if not current:
        print("ERROR: Could not detect current version from origin/main", file=sys.stderr)
        return 4

    new = get_pr_version()
    if not new:
        print("ERROR: Could not detect new version from PR branch", file=sys.stderr)
        return 3

    bump_type = detect_bump_type(current, new)

    if bump_type == "none":
        print(f"ℹ No version change (currently v{current[0]}.{current[1]}.{current[2]})")
        return 0

    is_release = is_release_pr()
    
    print(f"Current: v{current[0]}.{current[1]}.{current[2]}")
    print(f"New:     v{new[0]}.{new[1]}.{new[2]}")
    print(f"Bump:    {bump_type}")
    print(f"Release: {is_release}")

    # Validation logic
    if is_release:
        print(f"✓ Release PR: {bump_type} bump allowed")
        return 0
    else:
        # Regular PR: only patch allowed
        if bump_type == "patch":
            print(f"✓ Work PR: patch bump allowed")
            return 0
        else:
            print(
                f"✗ Work PR: {bump_type} bump not allowed (only patch bumps allowed in regular PRs)",
                file=sys.stderr,
            )
            print(
                f"  Hint: Use minor/major bumps only in release PRs",
                file=sys.stderr,
            )
            return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
