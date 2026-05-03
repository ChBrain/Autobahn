#!/usr/bin/env python3
"""Validate that place files don't contain German language bleeding.

German language detection (content, not proper nouns):
- Common German verb phrases (gab es, lieferten, wurden, etc.)
- German-specific words (ziegeleien, konkurrenz, konsolidierung, etc.)
- Note: German proper names (Eigenname) and place names are allowed

Exit codes:
  0 = no German detected
  1 = German text found
  2 = error reading files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# German language bleed detection
# Only phrases and constructions that are UNAMBIGUOUSLY German
# (to avoid false positives from English words that happen to match)
GERMAN_PHRASES = {
    "gab es",           # "there was/were" - distinctly German construction
    "ziegeleien",       # brick factories - German-only word
    "betriebe",         # operations - typically German in this context
    "lieferten",        # supplied - German past tense
    "wurden",           # became/were - German past tense marker
    "tongruben",        # clay pits - German compound
    "gebäude",          # buildings - German word
    "verschwanden",     # vanished - German past tense
    "konkurrenz",       # competition - German-specific term
    "konsolidierung",   # consolidation - German-specific term
    "eingeklemmt",      # wedged - German adjective
    "bewahrte",         # maintained - German past tense
    "gegensatz",        # contrast - German-specific term
    "leibeigenschaft",  # serfdom - German-specific term
    "gutswirtschaft",   # manor economy - German-specific term
    "großgrundbesitzer",# large landowners - German-specific term
    "glazialen",        # glacial - German adjective form
}

# English words that shouldn't be flagged (homonyms or common words)
# "zeit", "grenze", "seite", "seen", "freie", "bauern", "stehen", "jener", 
# "kontrolle", "freiheit", "selben", "zeit", "jahrhundert" - often appear in legitimate contexts



def has_german_bleed(text: str) -> tuple[bool, str]:
    """Check if text contains German language bleed.
    
    Returns (has_german, reason)
    Only detects unambiguous German phrases, not common words that appear in English.
    """
    text_lower = text.lower()
    for phrase in GERMAN_PHRASES:
        if phrase in text_lower:
            return True, f"German phrase found: '{phrase}'"
    
    return False, ""


def main() -> int:
    """Check all place files for German bleed."""
    findings = []
    
    try:
        for place_file in sorted(ROOT.rglob("place_*.md")):
            if ".git" in place_file.parts:
                continue
            
            try:
                text = place_file.read_text(encoding="utf-8")
                has_german, reason = has_german_bleed(text)
                
                if has_german:
                    findings.append({
                        "file": place_file.relative_to(ROOT),
                        "reason": reason,
                    })
            except Exception as e:
                print(f"Error reading {place_file}: {e}", file=sys.stderr)
                return 2
    except Exception as e:
        print(f"Error scanning files: {e}", file=sys.stderr)
        return 2
    
    if findings:
        print(f"German language bleed detected in {len(findings)} file(s):\n")
        for finding in findings:
            print(f"  {finding['file']}: {finding['reason']}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
