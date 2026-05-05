#!/usr/bin/env python3
"""Sample N random Withheld blocks for human/LLM audit.

Picks random in-scope `## Withheld` blocks and prints them as a markdown
brief that includes the audit instructions and the sampled content. The
audit itself is performed by whoever runs the script — typically an LLM
session (Claude Code, ChatGPT) that already has web search.

No API key, no network call from the script.

Usage:
  python scripts/spotcheck_withheld.py [--count N] [--seed N] [--output FILE]

If $PR_NUMBER is set, it's used as the default seed (so two runs against
the same PR pick the same files).
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# In-scope = SH/HH/MV roads. Out-of-scope (development) regions like A40,
# A111, A115 are excluded.
IN_SCOPE_ROADS = [
    "a1", "a7", "a11", "a14", "a19", "a20", "a21", "a210",
    "a215", "a226", "a23", "a24", "a25", "a255", "a261",
]
IN_SCOPE_STATES = {
    "place_schleswig_holstein.md",
    "place_hamburg.md",
    "place_mecklenburg_vorpommern.md",
}

WITHHELD_RE = re.compile(
    r"^##\s+Withheld\s*\r?\n(.*?)(?=^---\s*$|\Z)",
    re.MULTILINE | re.DOTALL,
)

INSTRUCTIONS = """For each Withheld block below, do the following and write up one section per file.

1. **Extract claims.** Identify every distinct factual claim - years, named persons, places, quantities, specific events, status claims like "still standing".
2. **Verify each claim** against authoritative sources via web search. Preferred order: official sites (autobahn.de, bast.de, municipal/heritage pages) -> autobahnatlas-online.de -> Wikipedia -> local reporting. Mark each claim as **verified**, **contradicted**, or **inconclusive**, with a real source URL.
3. **Check for close paraphrase.** Pick the most distinctive sentence from the Withheld and search for a verbatim or near-verbatim match. If a top result shares more than ~7 consecutive non-trivial words, flag it - quote the sentence and link the likely source.
4. **Verdict per file:**
   - **clean** - all claims verified, no paraphrase risk.
   - **minor** - at most one minor date imprecision or unsourceable detail.
   - **issues** - clear factual error OR medium/high paraphrase risk.

Be honest about inconclusive results - don't guess. The author's working principle is "facts are not copyrightable; expression is" - flag drift in either direction."""


def find_in_scope_files() -> list[Path]:
    files: list[Path] = []
    for road in IN_SCOPE_ROADS:
        d = ROOT / "roads" / road
        if not d.exists():
            continue
        for f in d.glob("place_*.md"):
            if f.stem == f"place_{road}":
                continue  # skip road index
            files.append(f)
    for state_name in IN_SCOPE_STATES:
        f = ROOT / "states" / state_name
        if f.exists():
            files.append(f)
    return files


def extract_withheld(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    m = WITHHELD_RE.search(text)
    if not m:
        return None
    body = m.group(1).strip()
    return body or None


def render(samples: list[tuple[Path, str]], seed: int) -> str:
    parts: list[str] = [
        "# Withheld spot-check",
        "",
        f"_Random sample of {len(samples)} in-scope `## Withheld` blocks (seed `{seed}`)._",
        "",
        "## How to audit",
        "",
        INSTRUCTIONS,
        "",
        "---",
        "",
    ]
    for path, withheld in samples:
        rel = path.relative_to(ROOT)
        parts.append(f"## `{rel}`")
        parts.append("")
        parts.append("```")
        parts.append(withheld)
        parts.append("```")
        parts.append("")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5, help="number of files to sample")
    parser.add_argument(
        "--seed", type=int, default=None,
        help="random seed (default: $PR_NUMBER or 42)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="output file (default: stdout)",
    )
    args = parser.parse_args()

    seed = (
        args.seed
        if args.seed is not None
        else int(os.environ.get("PR_NUMBER") or 42)
    )
    rng = random.Random(seed)

    candidates: list[tuple[Path, str]] = []
    for path in find_in_scope_files():
        wh = extract_withheld(path)
        if wh and len(wh) >= 100:  # skip stub Withhelds
            candidates.append((path, wh))

    if not candidates:
        print("No in-scope Withheld blocks found.", file=sys.stderr)
        return 1

    sampled = rng.sample(candidates, min(args.count, len(candidates)))
    report = render(sampled, seed)

    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.output} ({len(sampled)} files, seed {seed})", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
