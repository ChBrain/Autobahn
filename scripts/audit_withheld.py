#!/usr/bin/env python3
"""Audit random Withheld blocks for factual accuracy and close-paraphrase risk.

Picks N random in-scope `## Withheld` blocks (deterministic per --seed), runs
each through Claude Sonnet 4.6 with the web_search server tool, and emits a
markdown report scoring each block as clean / minor / issues.

This codifies the manual spot-check workflow (extract claims -> web-search ->
write up) into a reproducible script. It does NOT gate CI - the report is a
human-review aid.

Cost: roughly $0.50-2.00 per run with --count 5 and effort=medium.

Requires:
  ANTHROPIC_API_KEY  - the API key for the Anthropic SDK.
  PR_NUMBER          - optional; used as the random seed in CI.
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent

# In-scope roads = SH/HH/MV roads. Out-of-scope (development) regions like A40,
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


class Claim(BaseModel):
    text: str = Field(description="The factual claim, briefly stated")
    category: Literal["year", "person", "place", "quantity", "event", "status"]
    verification: Literal["verified", "contradicted", "inconclusive"]
    source_url: str | None = Field(
        default=None,
        description="URL of the source consulted, if any",
    )
    note: str = Field(
        default="",
        description="Brief explanation, especially when contradicted or inconclusive",
    )


class ParaphraseFlag(BaseModel):
    level: Literal["none", "low", "medium", "high"]
    sentence: str | None = Field(
        default=None,
        description="The sentence in the Withheld that closely paraphrases a public source",
    )
    likely_source: str | None = Field(
        default=None,
        description="URL of the suspected source",
    )
    rationale: str = Field(default="")


class WithheldAudit(BaseModel):
    claims: list[Claim]
    paraphrase: ParaphraseFlag
    verdict: Literal["clean", "minor", "issues"]
    summary: str = Field(description="One-sentence summary of the audit result")


SYSTEM_PROMPT = """You are an audit agent for the Autobahn world project, a content world about German motorways deployed to Claude.ai.

Your job: verify factual claims in a `## Withheld` section against authoritative web sources, and flag any close paraphrasing of public sources (especially Wikipedia).

For each Withheld passage:
1. Identify every distinct factual claim - years, named persons, places, quantities, specific events, status claims like "still standing".
2. Use web_search to verify each claim against authoritative sources: Wikipedia, official municipal/historical sites, autobahn.de, BASt, autobahnatlas-online, local newspapers.
3. Report each claim with: text, category, verification status (verified / contradicted / inconclusive), source URL, brief note.
4. To detect close paraphrase: pick the most distinctive sentence from the Withheld and search for a verbatim or near-verbatim substring. If a top result shares more than ~7 consecutive non-trivial words with the Withheld sentence, flag it as paraphrase risk.
5. Final verdict:
   - "clean"  - all claims verified, no paraphrase risk
   - "minor"  - at most one minor date imprecision or unsourceable detail
   - "issues" - clear factual error OR medium/high paraphrase risk

Be honest about inconclusive results. Do not guess. Cite real URLs from your searches. The author's working principle is "facts are not copyrightable; expression is" - your job is to flag drift in either direction."""


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


def make_schema_strict(schema):
    """Walk the schema and set additionalProperties=False on every object node.

    The Anthropic structured-output API requires this on every object. Pydantic
    v2 doesn't emit it by default, so we patch the generated tree before sending.
    """
    if isinstance(schema, dict):
        if schema.get("type") == "object":
            schema["additionalProperties"] = False
        for v in schema.values():
            make_schema_strict(v)
    elif isinstance(schema, list):
        for v in schema:
            make_schema_strict(v)
    return schema


def audit_one(
    client: anthropic.Anthropic,
    path: Path,
    withheld: str,
    schema: dict,
) -> WithheldAudit | None:
    rel = path.relative_to(ROOT)
    user_message = (
        f"File: `{rel}`\n\n"
        f"## Withheld\n\n{withheld}\n\n"
        "Audit this Withheld block per your instructions. Use web_search to verify "
        "each factual claim, then check for close paraphrase. Return structured JSON."
    )

    messages: list[dict] = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    # Cache the system prompt across the per-file audits in one
                    # run. Sonnet 4.6's cacheable-prefix minimum is 2048 tokens;
                    # this prompt is well below that, so the marker is harmless
                    # if no cache hit fires.
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            thinking={"type": "adaptive"},
            output_config={
                "effort": "medium",
                "format": {"type": "json_schema", "schema": schema},
            },
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            messages=messages,
        )

        # Server-side web_search hit its iteration limit; resume per
        # https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons
        if response.stop_reason == "pause_turn":
            messages = [
                *messages,
                {"role": "assistant", "content": response.content},
            ]
            continue
        break

    text = next((b.text for b in response.content if b.type == "text"), None)
    if not text:
        print(f"  [{rel}] no text in response", file=sys.stderr)
        return None
    try:
        return WithheldAudit.model_validate_json(text)
    except Exception as e:
        print(f"  [{rel}] schema validation failed: {e}", file=sys.stderr)
        return None


def render_markdown(results: list[tuple[Path, WithheldAudit]], seed: int) -> str:
    if not results:
        return f"# Withheld audit\n\n_No audits completed (seed `{seed}`)._\n"

    parts: list[str] = [
        "# Withheld audit",
        "",
        f"_Random spot-check of {len(results)} in-scope `## Withheld` blocks (seed `{seed}`)._",
        "",
        "Verdict legend: ✅ clean, ⚠️ minor issues, ❌ needs attention.",
    ]
    for path, audit in results:
        rel = path.relative_to(ROOT)
        emoji = {"clean": "✅", "minor": "⚠️", "issues": "❌"}.get(audit.verdict, "❓")
        parts.append("")
        parts.append(f"## {emoji} `{rel}` — {audit.verdict}")
        parts.append("")
        parts.append(audit.summary)
        parts.append("")
        parts.append("**Claims:**")
        parts.append("")
        for claim in audit.claims:
            ver = {"verified": "✓", "contradicted": "✗", "inconclusive": "?"}.get(
                claim.verification, "?"
            )
            parts.append(f"- {ver} _({claim.category})_ {claim.text}")
            if claim.source_url:
                parts.append(f"    - Source: <{claim.source_url}>")
            if claim.note:
                parts.append(f"    - {claim.note}")
        if audit.paraphrase.level not in (None, "none"):
            parts.append("")
            parts.append(
                f"**Close-paraphrase risk: {audit.paraphrase.level}** — "
                f"{audit.paraphrase.rationale}"
            )
            if audit.paraphrase.sentence:
                parts.append(f"  - Sentence: \"{audit.paraphrase.sentence}\"")
            if audit.paraphrase.likely_source:
                parts.append(f"  - Likely source: <{audit.paraphrase.likely_source}>")
    parts.append("")
    return "\n".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5, help="number of files to audit")
    parser.add_argument(
        "--seed", type=int, default=None,
        help="random seed (default: $PR_NUMBER or 42)",
    )
    parser.add_argument(
        "--output", type=Path, default=None,
        help="output file (default: stdout)",
    )
    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set", file=sys.stderr)
        return 2

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
    schema = make_schema_strict(WithheldAudit.model_json_schema())

    client = anthropic.Anthropic()
    results: list[tuple[Path, WithheldAudit]] = []
    for path, wh in sampled:
        rel = path.relative_to(ROOT)
        print(f"Auditing {rel} ...", file=sys.stderr)
        try:
            audit = audit_one(client, path, wh, schema)
        except anthropic.APIError as e:
            print(f"  [{rel}] API error: {e}", file=sys.stderr)
            continue
        if audit:
            results.append((path, audit))

    report = render_markdown(results, seed)
    if args.output:
        args.output.write_text(report, encoding="utf-8")
        print(f"Wrote {args.output}", file=sys.stderr)
    else:
        print(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
