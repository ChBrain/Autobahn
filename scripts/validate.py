#!/usr/bin/env python3
"""Autobahn validator orchestrator.

Schedules validation as a DAG over (file, layer) pairs:

                 general
                    │
        ┌───────────┼───────────┬──────────────┐
       roads      states    navigation    stop_naming
        │
      roads_km
        │
   roads_km_math

Roads run independently of each other. Inside a road, the index gates its
nodes: if `general(index)`, `roads(index)`, or `roads_km(index)` fail, the
nodes are not worth validating - the parent's contradiction propagates.
The runner records the gate failure and skips the nodes with an explicit
reason.

The validators are read-only. Each Issue carries a `verdict` when the
architecture's hierarchy determines the answer (road km > exit km), or
None when human engagement is required (no parent to arbitrate).

Exit status:
  0 if every file passes, 1 if any fail.

Usage:
  scripts/validate.py              # audit - validates every place_*.md
  scripts/validate.py FILE...      # validates the given files (CI mode)
  scripts/validate.py --json       # machine-readable findings
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from findings import Issue
import validate_general
import validate_roads
import validate_roads_km
import validate_roads_km_math
import validate_states
import validate_navigation_links
import validate_stop_naming

ROOT = HERE.parent


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Finding:
    path: Path
    layer: str
    issue: Issue
    implicit: bool = False  # surfaced from a file pulled in for gating, not in the user's scope


@dataclass(frozen=True)
class Skip:
    path: Path
    layer: str
    reason: str


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(path: Path) -> tuple[str, str | None]:
    """Return (kind, road) where kind is one of:
       'road_index', 'road_node', 'state', 'other'.
    """
    try:
        rel = path.resolve().relative_to(ROOT.resolve())
    except ValueError:
        return ("other", None)
    parts = rel.parts
    if parts[0] == "states":
        return ("state", None)
    if parts[0] == "roads" and len(parts) >= 3:
        road = parts[1]
        stem = path.stem
        if stem == f"place_{road}" or stem == f"place_the_{road}":
            return ("road_index", road)
        return ("road_node", road)
    return ("other", None)


def find_all_place_files() -> list[Path]:
    return sorted(p for p in ROOT.rglob("place_*.md") if ".git" not in p.parts)


def road_index_path(road: str) -> Path | None:
    for stem in (f"place_{road}", f"place_the_{road}"):
        p = ROOT / "roads" / road / f"{stem}.md"
        if p.is_file():
            return p
    return None


# ---------------------------------------------------------------------------
# Per-road gating
# ---------------------------------------------------------------------------

GATE_LAYERS = ("general", "roads", "roads_km")


def run_index_gate(index: Path) -> list[Finding]:
    """Run the structural gate on a road index file.

    Order matters: if `general` fails, the file might not parse correctly
    for the later layers, so we stop after the first gate-layer failure
    AT THE INDEX LEVEL. That's a per-file short-circuit, not a batch one.
    """
    findings: list[Finding] = []

    for issue in validate_general.validate(index):
        findings.append(Finding(index, "general", issue))
    if any(f.layer == "general" for f in findings):
        return findings

    for issue in validate_roads.validate(index, ROOT):
        findings.append(Finding(index, "roads", issue))
    if any(f.layer == "roads" for f in findings):
        return findings

    for issue in validate_roads_km.validate(index, ROOT):
        findings.append(Finding(index, "roads_km", issue))

    return findings


def run_index_siblings(index: Path) -> list[Finding]:
    """Sibling checks that don't gate the road but apply to the index."""
    out: list[Finding] = []
    for issue in validate_navigation_links.validate(index):
        out.append(Finding(index, "navigation", issue))
    for issue in validate_stop_naming.validate(index):
        out.append(Finding(index, "stop_naming", issue))
    return out


def run_node(node: Path) -> list[Finding]:
    """All applicable layers for a road node, with per-file short-circuit on general."""
    findings: list[Finding] = []
    general_issues = validate_general.validate(node)
    for issue in general_issues:
        findings.append(Finding(node, "general", issue))
    if general_issues:
        return findings  # later layers can't trust the file's structure

    for issue in validate_roads.validate(node, ROOT):
        findings.append(Finding(node, "roads", issue))
    for issue in validate_roads_km_math.validate(node, ROOT):
        findings.append(Finding(node, "roads_km_math", issue))
    for issue in validate_navigation_links.validate(node):
        findings.append(Finding(node, "navigation", issue))
    for issue in validate_stop_naming.validate(node):
        findings.append(Finding(node, "stop_naming", issue))
    return findings


def run_state(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    general_issues = validate_general.validate(path)
    for issue in general_issues:
        findings.append(Finding(path, "general", issue))
    if general_issues:
        return findings
    for issue in validate_states.validate(path, ROOT):
        findings.append(Finding(path, "states", issue))
    for issue in validate_navigation_links.validate(path):
        findings.append(Finding(path, "navigation", issue))
    for issue in validate_stop_naming.validate(path):
        findings.append(Finding(path, "stop_naming", issue))
    return findings


def run_other(path: Path) -> list[Finding]:
    return [Finding(path, "general", i) for i in validate_general.validate(path)]


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def schedule(targets: list[Path]) -> tuple[list[Finding], list[Skip]]:
    """Schedule validation per the DAG. Returns (findings, skips).

    Roads are processed independently. Within each road the index gates
    its nodes: a structural failure on the index skips every node in that
    road with an explicit reason. Sibling checks (navigation, stop_naming)
    on the index still run - they don't depend on the gate.
    """
    findings: list[Finding] = []
    skips: list[Skip] = []

    # Group by road / state / other
    by_road: dict[str, dict[str, object]] = {}
    state_files: list[Path] = []
    other_files: list[Path] = []

    for path in targets:
        kind, road = classify(path)
        if kind in ("road_index", "road_node"):
            assert road is not None
            group = by_road.setdefault(road, {"index": None, "nodes": []})
            if kind == "road_index":
                group["index"] = path
            else:
                group["nodes"].append(path)  # type: ignore[union-attr]
        elif kind == "state":
            state_files.append(path)
        else:
            other_files.append(path)

    # When a node is in scope but the index isn't explicitly requested,
    # we still need to run the gate against the index so the node's km
    # math has something to compare against. Pull in the index implicitly.
    for road, group in by_road.items():
        if group["index"] is None and group["nodes"]:
            implicit = road_index_path(road)
            if implicit is not None:
                group["index"] = implicit
                group["_implicit"] = True

    # Per-road work, independent across roads (parallelizable; sequential here).
    for road in sorted(by_road):
        group = by_road[road]
        index = group["index"]  # type: ignore[assignment]
        nodes = group["nodes"]  # type: ignore[assignment]
        index_implicit = bool(group.get("_implicit"))

        gate_failed = False
        gate_reason = ""

        if index is not None:
            gate_findings = run_index_gate(index)  # type: ignore[arg-type]
            sibling_findings = run_index_siblings(index)  # type: ignore[arg-type]

            # Surface the index findings only if the index was requested or
            # if its failure caused us to skip nodes.
            structural = [f for f in gate_findings if f.layer in GATE_LAYERS]
            if structural:
                gate_failed = True
                gate_reason = (f"index {Path(index).name} failed gate: "  # type: ignore[arg-type]
                               + "; ".join(f.issue.error for f in structural))

            if not index_implicit:
                findings.extend(gate_findings)
                findings.extend(sibling_findings)
            elif gate_failed:
                # Mark these as implicit so the exit code is not influenced
                # by pre-existing brokenness in files the user did not touch.
                structural = [
                    Finding(f.path, f.layer, f.issue, implicit=True)
                    for f in structural
                ]
                # The user didn't ask about the index, but they need to know
                # why their node was skipped.
                findings.extend(structural)

        if gate_failed:
            for node in nodes:  # type: ignore[union-attr]
                skips.append(Skip(node, "roads", gate_reason))
            continue

        for node in nodes:  # type: ignore[union-attr]
            findings.extend(run_node(node))

    for path in state_files:
        findings.extend(run_state(path))

    for path in other_files:
        findings.extend(run_other(path))

    return findings, skips


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def render_text(findings: list[Finding], skips: list[Skip]) -> None:
    """Group output by road / state / other for readability."""
    by_road: dict[str, list[Finding]] = {}
    by_road_skips: dict[str, list[Skip]] = {}
    state_findings: list[Finding] = []
    other_findings: list[Finding] = []

    for f in findings:
        kind, road = classify(f.path)
        if kind in ("road_index", "road_node") and road:
            by_road.setdefault(road, []).append(f)
        elif kind == "state":
            state_findings.append(f)
        else:
            other_findings.append(f)

    for s in skips:
        _, road = classify(s.path)
        if road:
            by_road_skips.setdefault(road, []).append(s)

    def render_finding(f: Finding) -> None:
        try:
            display = f.path.relative_to(ROOT)
        except ValueError:
            display = f.path
        tag = "determined" if f.issue.verdict else "human"
        # `INFO` for implicit (pre-existing brokenness in a file the user did
        # not touch); `FAIL` when the file is in the user's scope.
        marker = "INFO" if f.implicit else "FAIL"
        print(f"  {marker} {display}  [{f.layer}] [{tag}]")
        print(f"    error:   {f.issue.error}")
        if f.issue.verdict:
            print(f"    verdict: {f.issue.verdict}")

    for road in sorted(set(list(by_road) + list(by_road_skips))):
        print(f"=== {road} ===")
        road_findings = by_road.get(road, [])
        road_skips = by_road_skips.get(road, [])

        if not road_findings and not road_skips:
            print("  OK")
            print()
            continue

        for f in road_findings:
            render_finding(f)
        if road_skips:
            print(f"  SKIP {len(road_skips)} node(s): {road_skips[0].reason}")
            for s in road_skips:
                try:
                    display = s.path.relative_to(ROOT)
                except ValueError:
                    display = s.path
                print(f"    - {display}")
        print()

    if state_findings:
        print("=== states ===")
        for f in state_findings:
            render_finding(f)
        print()

    if other_findings:
        print("=== other ===")
        for f in other_findings:
            render_finding(f)
        print()


def render_json(findings: list[Finding], skips: list[Skip]) -> None:
    out = {
        "findings": [
            {
                "path": str(f.path.relative_to(ROOT)) if f.path.is_relative_to(ROOT) else str(f.path),
                "layer": f.layer,
                "error": f.issue.error,
                "verdict": f.issue.verdict,
                "kind": f.issue.kind,
            }
            for f in findings
        ],
        "skips": [
            {
                "path": str(s.path.relative_to(ROOT)) if s.path.is_relative_to(ROOT) else str(s.path),
                "layer": s.layer,
                "reason": s.reason,
            }
            for s in skips
        ],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def render_checks(findings: list[Finding], skips: list[Skip]) -> None:
    """Output per-validator check results for GitHub workflow annotations."""
    # All validators that might run
    validators = [
        ("general", "Filename format, UTF-8, sections, footer"),
        ("roads", "Road structure validation"),
        ("roads_km", "Kilometer position format"),
        ("roads_km_math", "Kilometer math consistency"),
        ("states", "State file structure"),
        ("navigation", "Navigation link integrity"),
        ("stop_naming", "Stop naming conventions"),
    ]
    
    explicit_findings = [f for f in findings if not f.implicit]
    by_layer: dict[str, list[Finding]] = {}
    for f in explicit_findings:
        by_layer.setdefault(f.layer, []).append(f)
    
    print("::group::Validator Results")
    # Output status for each validator
    for validator, description in validators:
        issues = by_layer.get(validator, [])
        if issues:
            count = len(issues)
            files = len(set(f.path for f in issues))
            print(f"  ❌ {validator}: {description}")
            print(f"     → {count} issue(s) in {files} file(s)")
        else:
            print(f"  ✅ {validator}: {description}")
    print("::endgroup::")


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Autobahn place files.")
    parser.add_argument("files", nargs="*", type=Path, help="Files to validate (default: walk repo)")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON")
    parser.add_argument("--checks", action="store_true", help="Emit per-validator check results for workflow")
    args = parser.parse_args()

    if args.files:
        targets = [f for f in args.files if f.name.startswith("place_")]
    else:
        targets = find_all_place_files()

    findings, skips = schedule(targets)

    if args.json:
        render_json(findings, skips)
    elif args.checks:
        render_checks(findings, skips)
    else:
        render_text(findings, skips)
        explicit = [f for f in findings if not f.implicit]
        implicit = [f for f in findings if f.implicit]
        total_skip = len(skips)
        total_files = len(targets)
        determined = sum(1 for f in explicit if f.issue.verdict)
        human = len(explicit) - determined
        summary = (f"Summary: {total_files} file(s), "
                   f"{len(explicit)} finding(s) ({determined} determined / {human} human), "
                   f"{total_skip} skipped")
        if implicit:
            summary += f", {len(implicit)} info (pre-existing, out of scope)"
        print(summary)

    return 1 if any(not f.implicit for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
