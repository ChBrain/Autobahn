#!/usr/bin/env python3
"""Invoke Federal Minister for Transport to review declared bump type.

Usage: python scripts/minister_review.py

The minister will evaluate whether your declared bump type (PATCH/MINOR/MAJOR)
is appropriate for the scope of work you've declared.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUMP_TYPE_FILE = ROOT / ".bump-type"


def get_bump_type() -> str | None:
    """Get declared bump type from .bump-type file."""
    if BUMP_TYPE_FILE.exists():
        content = BUMP_TYPE_FILE.read_text().strip()
        if content in ("PATCH", "MINOR", "MAJOR"):
            return content
    return None


def main() -> int:
    bump_type = get_bump_type()
    
    if not bump_type:
        print("✗ No .bump-type file found or invalid format")
        print("Must be PATCH, MINOR, or MAJOR")
        return 1
    
    # Get git branch name as context
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    except subprocess.CalledProcessError:
        branch = "unknown"
    
    # Build prompt for minister
    prompt = f"""You are the Federal Minister for Transport (Bundesminister für Verkehr).

A developer is working on branch: {branch}
They have declared their work scope as: {bump_type}

Your role: Evaluate this declaration. Is it appropriate? Is the scope clear?
- PATCH: Small fixes, typos, minor corrections. No new features.
- MINOR: New features, new roads/exits, backward compatible additions.
- MAJOR: Restructuring, schema changes, breaking changes.

Respond as the minister would - authoritatively, with precision. Point out if the scope seems unclear or if they're being overly cautious/ambitious. Then either approve it or suggest a correction.

Keep it brief (2-3 sentences). Tone: bureaucratic but fair."""
    
    # Invoke via git ask command if available, otherwise just show the prompt
    print(f"📋 Minister Review: {bump_type} scope on branch '{branch}'")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    print("\n(Minister response would appear here via AI consultation)")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
