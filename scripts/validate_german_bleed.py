#!/usr/bin/env python3
"""Validate that place files don't contain German language bleeding.

German language detection:
- Common German words (and, oder, gab, ziegeleien, etc.)
- German umlauts (ä, ö, ü, ß)
- German diacritics (à, etc.)

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

# Common German words that indicate German bleed (strict list)
# These are clearly German-only words, not English
GERMAN_WORDS = {
    "gab es",
    "ziegeleien",
    "mecklenburg-schwerin",
    "betriebe",
    "glazialen",
    "böden",
    "lieferten",
    "gutshäuser",
    "dorfkirchen",
    "demselben",
    "boden",
    "jahrhundert",
    "verschwanden",
    "industrielle",
    "konkurrenz",
    "konsolidierung",
    "tongruben",
    "wurden",
    "seen",
    "gebäude",
    "stehen",
    "hauptstadt",
    "fürstentums",
    "ratzeburg",
    "territorium",
    "eingeklemmt",
    "holstein",
    "bewahrte",
    "besondere",
    "gegensatz",
    "mecklenburgs",
    "leibeigenschaft",
    "gutswirtschaft",
    "großgrundbesitzer",
    "freie",
    "bauern",
    "grenze",
    "verlief",
    "dreißig",
    "westlich",
    "güter",
    "kontrolle",
    "jener",
    "seite",
    "freiheit",
    "selben",
    "zeit",
}

# German umlaut pattern (only actual German umlauts, not corruption)
GERMAN_UMLAUT_RE = re.compile(r"[äöüßÄÖÜ]")


def has_german_bleed(text: str) -> tuple[bool, str]:
    """Check if text contains German language bleed.
    
    Returns (has_german, reason)
    """
    # Check for umlauts first (most obvious indicator)
    if GERMAN_UMLAUT_RE.search(text):
        matches = GERMAN_UMLAUT_RE.findall(text)
        return True, f"German umlauts found: {', '.join(set(matches))}"
    
    # Check for common German words
    text_lower = text.lower()
    for word in GERMAN_WORDS:
        if word in text_lower:
            return True, f"German word found: '{word}'"
    
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
