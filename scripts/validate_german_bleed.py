#!/usr/bin/env python3
"""Validate that place files don't contain German narrative prose.

The world deploys to Claude.ai as English-language content. State and
road-index files carry a single German subtitle by design (line 2,
"## Das Land, das blieb..."). Body sections (Shown, Holds, Offers,
Withheld) must be English; German function words and verb forms there
indicate language drift, usually from agentic generation that slipped
back into the source language.

Detection runs only against body sections (Shown / Holds / Offers /
Withheld), so the title, the deliberate German subtitle, and the
Owner-block place-name links never trigger.

A section fails when it contains:
  - any STRONG_PHRASES match (multi-word German constructions or
    German-only verb forms that have no English equivalent), OR
  - WEAK_TOKEN_THRESHOLD or more matches against WEAK_TOKENS
    (single German function words; one stray instance, e.g. inside a
    German book title, isn't enough).

Exit codes:
  0 = no German detected
  1 = German text found
  2 = error reading files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue

ROOT = HERE.parent

# Multi-word German constructions and German-only verb forms. Any single
# occurrence in a body section flags that section.
STRONG_PHRASES = [
    r"\bist ein\b", r"\bist eine\b", r"\bist heute\b",
    r"\bwar ein\b", r"\bwar eine\b", r"\bwar einmal\b",
    r"\bund das\b", r"\bund die\b", r"\bund der\b",
    r"\bund ein\b", r"\bund eine\b",
    r"\bnoch heute\b", r"\bnoch immer\b",
    r"\bnicht nur\b", r"\bnicht weil\b",
    r"\bkein Zufall\b", r"\bkein Unfall\b",
    r"\bim Mittelalter\b", r"\bim Jahr\b",
    r"\bdie DDR\b", r"\bdie Stadt\b", r"\bdie Kirche\b",
    r"\bder Ort\b", r"\bdas Dorf\b", r"\bdas Muster\b", r"\bdie Leere\b",
    r"\bgegründet\b", r"\bgehört\b",
    r"\bwurde geboren\b", r"\bwurde \d{4}\b", r"\b\d{4} wurde\b",
    r"\b\d{4} kamen\b",
    r"\bsind bis heute\b",
    r"\bvon \d{4} bis \d{4}\b",
    # Original 17-phrase list, kept for backward compatibility.
    r"\bgab es\b", r"\bziegeleien\b", r"\bbetriebe\b", r"\blieferten\b",
    r"\btongruben\b", r"\bgebäude\b", r"\bverschwanden\b",
    r"\bkonkurrenz\b", r"\bkonsolidierung\b", r"\beingeklemmt\b",
    r"\bbewahrte\b", r"\bgegensatz\b", r"\bleibeigenschaft\b",
    r"\bgutswirtschaft\b", r"\bgroßgrundbesitzer\b", r"\bglazialen\b",
]

# Single-word German function tokens. Need WEAK_TOKEN_THRESHOLD or more
# matches in the same section to flag - one stray match (e.g. a German
# book title quoted in English narrative) is not enough.
WEAK_TOKENS = [
    r"\bwurde\b", r"\bwurden\b",
    r"\bnicht\b", r"\bsich\b",
    r"\bkein\b", r"\bkeine\b",
    r"\bliegt\b", r"\bsteht\b", r"\bkommt\b", r"\bgibt\b",
    r"\bnoch\b", r"\bauch\b", r"\bdoch\b", r"\bschon\b",
    r"\bdamals\b", r"\bgleichzeitig\b",
]
WEAK_TOKEN_THRESHOLD = 3

SECTION_RE = re.compile(
    r"^##\s+(\S.*?)\r?\n(.*?)(?=^##\s+|\Z)",
    re.MULTILINE | re.DOTALL,
)
BODY_SECTIONS = {"Shown", "Holds", "Offers", "Withheld"}


def _section_findings(body: str) -> tuple[list[str], int]:
    strong: list[str] = []
    for pat in STRONG_PHRASES:
        for m in re.finditer(pat, body, re.IGNORECASE):
            strong.append(m.group(0))
    weak_count = 0
    for pat in WEAK_TOKENS:
        weak_count += len(re.findall(pat, body, re.IGNORECASE))
    return strong, weak_count


def has_german_bleed(text: str) -> tuple[bool, str]:
    """Return (flagged, reason) summarising any body-section German bleed."""
    for m in SECTION_RE.finditer(text):
        head_raw = m.group(1).strip()
        head = head_raw.split()[0] if head_raw else ""
        if head not in BODY_SECTIONS:
            continue
        body = m.group(2)
        strong, weak_count = _section_findings(body)
        if strong:
            sample = ", ".join(sorted({s.lower() for s in strong})[:3])
            return True, f"German prose in ## {head} (e.g. {sample})"
        if weak_count >= WEAK_TOKEN_THRESHOLD:
            return True, (
                f"German function tokens in ## {head} "
                f"({weak_count} hits, threshold {WEAK_TOKEN_THRESHOLD})"
            )
    return False, ""


def validate(path: Path) -> list[Issue]:
    """Per-file entry for the orchestrator. Returns at most one Issue."""
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    flagged, reason = has_german_bleed(text)
    if flagged:
        return [Issue(error=reason, verdict="rewrite the German passage in English")]
    return []


def main() -> int:
    """Walk the repo and report any place file with German bleed."""
    findings: list[dict] = []

    try:
        for place_file in sorted(ROOT.rglob("place_*.md")):
            if ".git" in place_file.parts:
                continue
            try:
                text = place_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading {place_file}: {e}", file=sys.stderr)
                return 2
            flagged, reason = has_german_bleed(text)
            if flagged:
                findings.append({
                    "file": place_file.relative_to(ROOT),
                    "reason": reason,
                })
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
