#!/usr/bin/env python3
"""Road-tied stop naming validation.

Enforces the rule from ARCHITECTURE.md:
  - Motorway Service Area: `place_{road}[_{NN}]_service_{name}.md`
  - Motorway Rest Area: `place_{road}[_{NN}]_rest_{name}.md`
  - Roadhouse: `place_{road}[_{NN}]_roadhouse_{name}.md`

All road-tied stops MUST have a road prefix. Exit number (NN) is optional,
included only if an official AS-number exists for that stop.

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

# Regex patterns for road-tied stops WITHOUT proper road prefix
# These FAIL: place_service_*, place_rest_*, place_roadhouse_* (standalone, no road)
STANDALONE_SERVICE_RE = re.compile(r"^place_service_[a-z_]+\.md$")
STANDALONE_REST_RE = re.compile(r"^place_rest_[a-z_]+\.md$")
STANDALONE_ROADHOUSE_RE = re.compile(r"^place_roadhouse_[a-z_]+\.md$")
STANDALONE_RASTHOF_RE = re.compile(r"^place_rasthof_[a-z_]+\.md$")

# Regex pattern for CORRECT road-tied stops WITH road prefix
# Pattern: place_<road>[_<NN>]_<type>_<name>.md
CORRECT_STOP_RE = re.compile(
    r"^place_a\d+(?:_\d{2})?_(service|rest|roadhouse)_[a-z_]+\.md$"
)


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[str]:
    """Check that road-tied stops have the road prefix."""
    errors: list[str] = []
    basename = path.name

    # Check for standalone service/rest/roadhouse/rasthof files (FAIL)
    if STANDALONE_SERVICE_RE.match(basename):
        errors.append(
            f"standalone service file missing road prefix; should be `place_{{road}}_service_...`"
        )
    elif STANDALONE_REST_RE.match(basename):
        errors.append(
            f"standalone rest area file missing road prefix; should be `place_{{road}}_rest_...`"
        )
    elif STANDALONE_ROADHOUSE_RE.match(basename):
        errors.append(
            f"standalone roadhouse file missing road prefix; should be `place_{{road}}_roadhouse_...`"
        )
    elif STANDALONE_RASTHOF_RE.match(basename):
        errors.append(
            f"standalone rasthof file missing road prefix; should be `place_{{road}}_roadhouse_...` (rasthof is a type of roadhouse)"
        )

    return errors


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) for a in argv[1:]] if len(argv) > 1 else find_place_files(root)

    failed = 0
    for path in targets:
        errors = validate(path)
        if errors:
            failed += 1
            print(f"FAIL {path}")
            for err in errors:
                print(f"  - {err}")

    total = len(targets)
    if failed:
        print(f"\n{failed}/{total} files failed road-tied stop naming validation")
        return 1
    print(f"OK: {total} files passed road-tied stop naming validation")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
