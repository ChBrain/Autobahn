# Autobahn - Copilot Instructions

## Git workflow

**Before any file edit:**
1. Run `git branch --show-current` to confirm the current branch
2. If on `main`, stop and create a feature branch first
3. Only edit files when on a feature branch

Never commit or edit directly on `main`.

## Branch naming

- `feat/<name>` - new road, new node, new world content
- `fix/<name>` - corrections to existing content
- `chore/<name>` - infrastructure, scaffolding, housekeeping

## Release procedure

1. Work on a feature branch
2. Run `python scripts/validate.py FILE...` on changed files - all must pass before opening a PR
3. Run `python scripts/deploy.py --check <manifest>` on any manifest you touched - it must pass strict mode before opening a PR
4. For minor or major releases only: run `python scripts/bump_version.py --minor` (or `--major`) and commit the result. Skip for patch releases.
5. Open a PR - the PR template checklist must pass before merge
6. Merge to `main` via PR only
7. Create a GitHub release with a version tag to trigger the release workflow
8. The workflow runs `scripts/deploy.py` on every manifest (`autobahn.md`, every `roads/*/place_*.md`, every `bundeslaender/place_*.md`) and uploads each resulting zip as a release asset

## Versioning

- **File footer patch** - LLM increments per file during content edits, by editing the footer in place. No release needed. `bump_version.py` does not offer this; it is per-file.
- **Patch release** - user-triggered GitHub tag bump only. No file footer changes.
- **Minor release** - user-triggered. Run `bump_version.py --minor` to update all file footers, then PR + tag.
- **Major release** - user-triggered. Run `bump_version.py --major` for structural changes, then PR + tag.

Never run `bump_version.py` unless the user explicitly asks for a release.

## Deployment

The world deploys flat to Claude.ai. `scripts/deploy.py <manifest>` builds a flat zip from a manifest file (any `*.md` whose links enumerate the bundle). The bundle is exactly the manifest plus every `*.md` it links to - single-hop closure, no transitive walk. The author owns the cut.

Manifests:

- `autobahn.md` at the repo root - the all-bundle.
- `roads/<road>/place_<road>.md` - per-road bundle.
- `bundeslaender/place_<bundesland>.md` - per-Bundesland bundle.

If a manifest needs the world frame (`instructions.md`, `stack.md`, the engine pieces, personas, vehicles, props), it must link to them. Frame is a choice.

Adding a road, a Bundesland, or a frame piece means linking it from the manifest(s) that should ship it. New deployment scope = new manifest file at the appropriate path.

Single author-facing rule: **every file basename in the world is unique.**

## Style

- Do not use em dashes anywhere in this repository (place files, ARCHITECTURE, README, copilot-instructions, anything else). Use a hyphen (`-`) or rephrase.

## File standards

Footer in place files: `vX.Y.Z - KAI Worlds`, where `X.Y.Z` is the current world version (set by `scripts/bump_version.py` on release, or per-file by an LLM during a content edit).
