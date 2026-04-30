#!/usr/bin/env python3
"""Road-tied stop naming validation.

Enforces the rule from ARCHITECTURE.md:
  - Motorway Service Area: `place_{road}[_{NN}]_service_{name}.md`
  - Motorway Rest Area:    `place_{road}[_{NN}]_rest_{name}.md`
  - Roadhouse:             `place_{road}[_{NN}]_roadhouse_{name}.md`

All road-tied stops MUST carry a road prefix. Exit number (NN) is optional,
included only when the stop has an official AS-number.

Read-only. The rule names the type but not the road, so when a violating
file is found the verdict cannot determine which road owns it - human
engagement required.

Exit status:
  0 if every file passes, 1 otherwise.

Usage:
  scripts/validate_stop_naming.py            # walks the repo
  scripts/validate_stop_naming.py FILE...    # validates only the given files
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue

# Type infix anywhere in the basename. Files containing this MUST follow
# the strict pattern below; otherwise the name is malformed regardless of
# whether the missing piece is the road, the type spelling, or punctuation.
TYPE_INFIX_RE = re.compile(r"_(service|rest|roadhouse|rasthof)_")

# Strict architecture form: place_<road>[_<NN>]_<type>_<name>.md
# - road: a + digits (e.g., a1, a226)
# - optional exit number: 1-3 digits + optional letter (e.g., 5, 12, 2a)
# - type: service / rest / roadhouse (rasthof is legacy, see below)
STRICT_STOP_RE = re.compile(
    r"^place_a\d+(?:_\d{1,3}[a-z]?)?_(service|rest|roadhouse)_[a-z_]+\.md$"
)


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[Issue]:
    basename = path.name
    m = TYPE_INFIX_RE.search(basename)
    if not m:
        return []
    if STRICT_STOP_RE.match(basename):
        return []

    type_word = m.group(1)
    if type_word == "rasthof":
        # Architecturally rasthof is a roadhouse; the rename is determined.
        return [Issue(
            error="`_rasthof_` infix in filename",
            verdict="rename `_rasthof_` to `_roadhouse_` (rasthof is a type of roadhouse)",
        )]
    return [Issue(
        error=(f"road-tied stop name does not match "
               f"`place_<road>[_<NN>]_{type_word}_<name>.md`"),
        verdict=None,  # rule names the type, not which road owns it
    )]


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    failed = 0
    for path in targets:
        issues = validate(path)
        if issues:
            failed += 1
            print(f"FAIL {path}")
            for issue in issues:
                print(f"  - {issue.error}")
                if issue.verdict:
                    print(f"    verdict: {issue.verdict}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed road-tied stop naming validation")
        return 1
    print(f"OK: {total} files passed road-tied stop naming validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
