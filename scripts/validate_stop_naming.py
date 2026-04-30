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

# Files that fail: standalone (no road prefix)
STANDALONE_RE = {
    "service":   re.compile(r"^place_service_[a-z_]+\.md$"),
    "rest":      re.compile(r"^place_rest_[a-z_]+\.md$"),
    "roadhouse": re.compile(r"^place_roadhouse_[a-z_]+\.md$"),
    "rasthof":   re.compile(r"^place_rasthof_[a-z_]+\.md$"),
}


def find_place_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("place_*.md") if ".git" not in p.parts)


def validate(path: Path) -> list[Issue]:
    basename = path.name
    for kind, regex in STANDALONE_RE.items():
        if regex.match(basename):
            return [Issue(
                error=f"standalone {kind} file missing road prefix",
                verdict=None,  # rule names the type, not which road owns it
            )]
    return []


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
