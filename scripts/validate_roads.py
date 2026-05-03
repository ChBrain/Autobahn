#!/usr/bin/env python3
"""Road architecture validation for place_*.md files in the Autobahn world.

Checks compliance with ARCHITECTURE.md ## Roads:
  - Every file Owner block contains `- Project: Autobahn`
  - Road node files: Owner must contain
      `- Place: [Road](place_road.md) in [Bundesland](place_bundesland.md)`
  - Road index files: Owner must NOT contain a `- Place:` line
  - Road index files: Must have all 5 required sections
      (Owner, Shown, Holds, Offers, Withheld)
  - Road index files: Must NOT contain forbidden sections
      (Status, Planned Route, Plan, Future, TODO)
  - Road index Holds: State subsections must have backreferences
      (### StateName (place_state.md))

File classification by path. Every road has its own folder at
`roads/<road>/`. The road index file lives in that folder alongside its
nodes; everything else `place_*.md` in the folder is a node.

  roads/<road>/place_<road>.md         -> road index
  roads/<road>/place_the_<road>.md     -> road index (legacy form)
  roads/<road>/place_*.md (other)      -> road node
  states/place_*.md                    -> bundesland (not checked here)

Read-only. Emits Issue records; orchestration is validate.py's job.

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_roads.py            # walks the repo
  scripts/validate_roads.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue

# `\r?\n` so the regex still matches if a file slipped in with CRLF endings.
OWNER_BLOCK_RE = re.compile(r"## Owner\r?\n(.*?)(?=\r?\n##|\Z)", re.DOTALL)
PLACE_LINE_RE = re.compile(
    r"^\s*-\s*Place:\s*\[.+?\]\(place_[^)]+\.md\)\s+in\s+\[.+?\]\(place_[^)]+\.md\)",
    re.MULTILINE,
)
HOLDS_SECTION_RE = re.compile(r"## Holds\r?\n(.*?)(?=\r?\n##|\Z)", re.DOTALL)
STATE_SUBSECTION_RE = re.compile(r"^###\s+(\w+(?:\s+\w+)*)\s*(?:\((.*?)\))?\s*$", re.MULTILINE)
SECTION_RE = re.compile(r"^## (.+)$", re.MULTILINE)

REQUIRED_SECTIONS = ["Owner", "Shown", "Holds", "Offers", "Withheld"]
FORBIDDEN_SECTIONS = ["Status", "Planned Route", "Plan", "Future", "TODO"]


def classify(path: Path, root: Path) -> str:
    """Return 'road_index', 'road_node', 'bundesland', or 'other'."""
    path = path.resolve()
    root = root.resolve()
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "other"
    parts = rel.parts
    if parts[0] == "states":
        return "bundesland"
    if parts[0] == "roads" and len(parts) >= 3:
        road = parts[1]
        stem = path.stem
        if stem == f"place_{road}" or stem == f"place_the_{road}":
            return "road_index"
        return "road_node"
    return "other"


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path, root: Path) -> list[Issue]:
    issues: list[Issue] = []

    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        # General layer reports encoding failures; nothing useful to add here.
        return []

    owner_match = OWNER_BLOCK_RE.search(text)
    owner_text = owner_match.group(1) if owner_match else ""

    if "- Project: Autobahn" not in owner_text:
        issues.append(Issue(
            error="Owner block missing `- Project: Autobahn`",
            verdict="insert `- Project: Autobahn` as a bullet under `## Owner`",
        ))

    kind = classify(path, root)
    has_place_line = bool(PLACE_LINE_RE.search(owner_text))

    if kind == "road_node" and not has_place_line:
        # Road derivable from path; bundesland needs lookup the validator doesn't have.
        issues.append(Issue(
            error="road node Owner missing `- Place: [Road](place_road.md) in [Bundesland](place_bundesland.md)`",
            verdict=None,  # bundesland mapping not known to the validator
        ))
    elif kind == "road_index" and has_place_line:
        issues.append(Issue(
            error="road index Owner must not contain a `- Place:` line",
            verdict="remove the `- Place:` line from the Owner block",
        ))

    # Validate state backreferences in road index files
    if kind == "road_index":
        holds_match = HOLDS_SECTION_RE.search(text)
        if holds_match:
            holds_text = holds_match.group(1)
            # Find all state subsections (lines starting with ###)
            state_subsections = STATE_SUBSECTION_RE.findall(holds_text)
            for state_name, backreference in state_subsections:
                if not backreference:
                    issues.append(Issue(
                        error=f"state subsection '{state_name}' missing mandatory backreference",
                        verdict=f"change `### {state_name}` to `### {state_name} (place_state.md)`",
                    ))
                elif not backreference.startswith("place_") or not backreference.endswith(".md"):
                    issues.append(Issue(
                        error=f"state subsection '{state_name}' has invalid backreference format: `({backreference})`",
                        verdict=f"backreference must be `(place_state.md)` format",
                    ))
        
        # Check for forbidden sections
        found_sections = set(SECTION_RE.findall(text))
        for forbidden in FORBIDDEN_SECTIONS:
            if forbidden in found_sections:
                issues.append(Issue(
                    error=f"road index contains forbidden section `## {forbidden}`",
                    verdict=f"merge {forbidden} content into Shown or Holds section; do not create custom sections",
                ))
        
        # Check for missing required sections (road indexes must have them all)
        for required in REQUIRED_SECTIONS:
            if required not in found_sections:
                issues.append(Issue(
                    error=f"road index missing required section `## {required}`",
                    verdict=f"add `## {required}` section following architecture pattern",
                ))

    return issues


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    failed = 0
    for path in targets:
        issues = validate(path, root)
        if issues:
            failed += 1
            print(f"FAIL {path}")
            for issue in issues:
                print(f"  - {issue.error}")
                if issue.verdict:
                    print(f"    verdict: {issue.verdict}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed road architecture validation")
        return 1
    print(f"OK: {total} files passed road architecture validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
