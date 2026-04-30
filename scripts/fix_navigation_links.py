#!/usr/bin/env python3
"""Fix navigation link placement: move from ## Shown to ## Holds.

This script automates the fix for the 51 files that have neighbour links
in ## Shown instead of ## Holds.

Pattern to find and move: "- <distance> km <direction>: [...](...md)"

Strategy:
  1. Parse file line-by-line into sections
  2. Extract neighbour links from Shown
  3. Insert them into Holds after the kilometerstein line
  4. Rewrite the file with fixed sections

Usage:
  scripts/fix_navigation_links.py            # fixes all 51 files
  scripts/fix_navigation_links.py FILE...    # fixes only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# Regex for a neighbour link
NEIGHBOUR_LINK_RE = re.compile(
    r"^-\s+[\d.]+\s+km\s+\w+:\s+\[.+?\]\(place_[^)]+\.md\).*$",
    re.MULTILINE,
)


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def parse_sections(text: str) -> dict[str, list[str]]:
    """Parse file into sections. Each section is a list of lines (no newlines)."""
    sections: dict[str, list[str]] = {}
    lines = text.split('\n')
    current_section: str | None = None
    current_lines: list[str] = []
    
    for line in lines:
        if line.startswith("## "):
            # Save previous section
            if current_section is not None:
                sections[current_section] = current_lines
            # Start new section
            current_section = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    
    # Save last section
    if current_section is not None:
        sections[current_section] = current_lines
    
    return sections


def fix(path: Path) -> bool:
    """Move navigation links from Shown to Holds. Returns True if changed."""
    text = path.read_text(encoding="utf-8")
    sections = parse_sections(text)
    
    if "Shown" not in sections or "Holds" not in sections:
        return False
    
    shown_lines = sections["Shown"]
    holds_lines = sections["Holds"]
    
    # Find neighbour links in Shown
    neighbour_links: list[str] = []
    shown_fixed: list[str] = []
    
    for line in shown_lines:
        if NEIGHBOUR_LINK_RE.match(line):
            neighbour_links.append(line)
        else:
            shown_fixed.append(line)
    
    if not neighbour_links:
        return False  # No changes needed
    
    # Clean up empty lines at end of shown
    while shown_fixed and shown_fixed[-1].strip() == "":
        shown_fixed.pop()
    
    # Find the kilometerstein line in Holds and insert after it
    holds_fixed: list[str] = []
    for i, line in enumerate(holds_lines):
        holds_fixed.append(line)
        if line.startswith("[km ") and "](piece_the_kilometerstein.md)" in line:
            # Insert neighbour links after kilometerstein
            holds_fixed.extend(neighbour_links)
    
    # Reconstruct the file
    parts: list[str] = []
    
    # Header (everything before first ##)
    header_lines: list[str] = []
    lines = text.split('\n')
    for line in lines:
        if line.startswith("## "):
            break
        header_lines.append(line)
    
    parts.append('\n'.join(header_lines).rstrip())
    
    # Add sections in order
    section_order = ["Owner", "Shown", "Holds", "Offers", "Withheld"]
    for section_name in section_order:
        if section_name in sections:
            if section_name == "Shown":
                section_content = shown_fixed
            elif section_name == "Holds":
                section_content = holds_fixed
            else:
                section_content = sections[section_name]
            
            parts.append(f"\n## {section_name}")
            parts.append('\n'.join(section_content))
    
    # Add footer and other sections not in our order
    remaining_sections = [s for s in sections if s not in section_order]
    for section_name in remaining_sections:
        parts.append(f"\n## {section_name}")
        parts.append('\n'.join(sections[section_name]))
    
    new_text = '\n'.join(parts)
    
    # Add back the trailing newline and any final content after Withheld
    if text.endswith('\n'):
        new_text += '\n'
    
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)
    
    fixed = 0
    for path in targets:
        # Check if file has violations before trying to fix
        text = path.read_text(encoding="utf-8")
        sections = parse_sections(text)
        if "Shown" in sections:
            shown_text = '\n'.join(sections["Shown"])
            if NEIGHBOUR_LINK_RE.search(shown_text):
                if fix(path):
                    fixed += 1
                    print(f"FIXED {path}")
    
    print(f"\nFixed {fixed} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
