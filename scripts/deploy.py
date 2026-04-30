#!/usr/bin/env python3
"""Build a deployable bundle for the Autobahn world.

A bundle is the manifest file plus every `*.md` file it links to. Single-hop
closure: if a linked file in turn links to other files, those are not pulled
in unless the manifest also links them. The author owns the cut.

The bundle is flat: all files end up in one folder and every internal link
is rewritten to its bare basename. Output is a zip ready to upload as a
Claude.ai project.

Usage:
  scripts/deploy.py <manifest>           # build dist/<basename>.zip
  scripts/deploy.py <manifest> --check   # validate without writing
  scripts/deploy.py <manifest> --strict  # fail on cross-bundle links
  scripts/deploy.py <manifest> --out PATH

Typical manifests:
  - autobahn.md                            # all-bundle (world manifest)
  - roads/<road>/place_<road>.md           # per-road bundle
  - states/place_<state>.md    # per-state bundle

Cross-bundle links (a bundled file linking to a target outside the bundle)
are warned by default; `--strict` upgrades the warning to a failure. The
manifest's own dangling links always fail.
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path

LINK_RE = re.compile(r"\]\(([^)]+\.md)(#[^)]*)?\)")
ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "scripts", ".github", "dist"}


def repo_md_index(root: Path) -> dict[str, list[Path]]:
    """Map basename -> list of paths for every *.md in the repo."""
    index: dict[str, list[Path]] = {}
    for p in root.rglob("*.md"):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        index.setdefault(p.name, []).append(p)
    return index


def parse_links(text: str) -> list[str]:
    """Return every markdown link target ending in .md (anchors not stripped)."""
    return [m.group(1) for m in LINK_RE.finditer(text)]


def resolve_link(target: str, source: Path, basenames: dict[str, list[Path]]) -> Path | None:
    """Resolve a link target either by relative path or by repo-wide basename."""
    if "/" in target:
        candidate = (source.parent / target).resolve()
        return candidate if candidate.is_file() else None
    paths = basenames.get(target)
    return paths[0] if paths else None


def collect_bundle(manifest: Path, basenames: dict[str, list[Path]]) -> tuple[set[Path], list[str]]:
    """Return ({manifest} U {resolved manifest links}, errors)."""
    errors: list[str] = []
    bundle: set[Path] = {manifest.resolve()}
    text = manifest.read_text(encoding="utf-8")
    for target in parse_links(text):
        resolved = resolve_link(target, manifest, basenames)
        if resolved is None:
            errors.append(f"manifest link does not resolve: {target}")
            continue
        bundle.add(resolved.resolve())
    return bundle, errors


def check_basename_uniqueness(bundle: set[Path]) -> list[str]:
    seen: dict[str, list[Path]] = {}
    for p in bundle:
        seen.setdefault(p.name, []).append(p)
    return [
        f"basename collision: {name!r} appears at " + ", ".join(str(p.relative_to(ROOT)) for p in paths)
        for name, paths in seen.items()
        if len(paths) > 1
    ]


def check_inner_links(bundle: set[Path], manifest: Path) -> list[str]:
    """List every link inside non-manifest bundle files whose target is not in the bundle."""
    bundle_names = {p.name for p in bundle}
    manifest_resolved = manifest.resolve()
    issues: list[str] = []
    for path in sorted(bundle):
        if path == manifest_resolved:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for target in parse_links(text):
            basename = Path(target.split("#", 1)[0]).name
            if basename not in bundle_names:
                issues.append(f"{path.relative_to(ROOT)} -> {target}")
    return issues


def rewrite_links_to_basenames(text: str) -> str:
    """Rewrite every [label](path/to/file.md[#anchor]) -> [label](file.md[#anchor])."""
    def repl(m: re.Match) -> str:
        target = m.group(1)
        anchor = m.group(2) or ""
        return f"]({Path(target).name}{anchor})"
    return LINK_RE.sub(repl, text)


def build_zip(bundle: set[Path], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle):
            flat = rewrite_links_to_basenames(path.read_text(encoding="utf-8"))
            zf.writestr(path.name, flat.encode("utf-8"))


def default_out_path(manifest: Path) -> Path:
    """Map a manifest filename to a release-friendly zip name in dist/."""
    stem = manifest.stem
    if stem == "autobahn":
        name = "autobahn"
    elif stem.startswith("place_the_"):
        name = "autobahn-" + stem[len("place_the_"):]
    elif stem.startswith("place_"):
        name = "autobahn-" + stem[len("place_"):]
    else:
        name = "autobahn-" + stem
    return ROOT / "dist" / f"{name}.zip"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Build a deployable Autobahn bundle from a manifest")
    parser.add_argument("manifest", type=Path, help="Manifest file (any *.md whose links enumerate the bundle)")
    parser.add_argument("--check", action="store_true", help="Validate without writing the zip")
    parser.add_argument("--strict", action="store_true", help="Fail on cross-bundle links from inside the bundle")
    parser.add_argument("--out", type=Path, default=None, help="Output zip path (default: dist/<derived>.zip)")
    args = parser.parse_args(argv[1:])

    if not args.manifest.is_file():
        print(f"manifest not found: {args.manifest}", file=sys.stderr)
        return 2

    basenames = repo_md_index(ROOT)

    bundle, errors = collect_bundle(args.manifest, basenames)
    if errors:
        for e in errors:
            print(f"FAIL {e}")
        return 1

    collisions = check_basename_uniqueness(bundle)
    if collisions:
        for c in collisions:
            print(f"FAIL {c}")
        return 1

    cross = check_inner_links(bundle, args.manifest)
    for c in cross:
        print(f"WARN cross-bundle link: {c}")
    if cross and args.strict:
        print(f"\n--strict: {len(cross)} cross-bundle link(s) failed validation")
        return 1

    print(f"OK: {len(bundle)} files in bundle ({args.manifest.name})")
    if args.check:
        return 0

    out_path = args.out if args.out else default_out_path(args.manifest)
    build_zip(bundle, out_path)
    print(f"Wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
