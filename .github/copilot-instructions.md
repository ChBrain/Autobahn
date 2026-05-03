# Autobahn - Copilot Instructions

## Release Agent

For releases, use the `@autobahn-release` agent instead of the default agent. It enforces approval gates and prevents accidental bypasses:

```
/autobahn-release
@autobahn-release please release X.Y.Z
```

This agent requires explicit user approval before:
- Merging any PR
- Creating release tags
- Creating GitHub Releases

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
2. Make your changes and **include a patch version bump** in your commits:
   - Run `python scripts/bump_version.py --patch` to update all file footers
   - Include the bumped versions in your PR
3. Run `python scripts/validate.py FILE...` on changed files - all must pass before opening a PR
4. Run `python scripts/deploy.py --check <manifest>` on any manifest you touched - it must pass strict mode before opening a PR
5. Open a PR - CI validates:
   - That your version bump is patch-only (x.y.z → x.y.(z+1))
   - All files pass validation
6. Merge to `main` via PR only
7. For **major or minor releases** (user-initiated):
   - Create a GitHub release with version tag (e.g., `v0.3.0` for minor, `v1.0.0` for major)
   - Release workflow detects bump type and syncs file versions
   - Release workflow runs `scripts/deploy.py` on every manifest and uploads assets

## Versioning

- **Patch bumps** - Developer-driven, included in work PRs. CI validates that only patch bumps occur in regular PRs (x.y.z → x.y.(z+1)).
- **Release tag structure**:
  - Minor release: Create tag `vX.(Y+1).0` (e.g., `v0.3.0` from `v0.2.0`)
  - Major release: Create tag `(X+1).0.0` (e.g., `v1.0.0` from `v0.2.0`)
- **Release workflow**: Creates PR from tag, syncs versions, deploys assets

**Important:**
- Patch bumps must be included in every PR (CI enforces patch-only)
- Do NOT manually edit version footers - use `python scripts/bump_version.py --patch` on your branch
- Minor/major bumps are release-only (via GitHub release tags)

## Deployment

The world deploys flat to Claude.ai. `scripts/deploy.py <manifest>` builds a flat zip from a manifest file (any `*.md` whose links enumerate the bundle). The bundle is exactly the manifest plus every `*.md` it links to - single-hop closure, no transitive walk. The author owns the cut.

Manifests:

- `autobahn.md` at the repo root - the all-bundle.
- `roads/<road>/place_<road>.md` - per-road bundle.
- `states/place_<state>.md` - per-state bundle.

If a manifest needs the world frame (`instructions.md`, `stack.md`, the engine pieces, personas, vehicles, props), it must link to them. Frame is a choice.

Adding a road, a Bundesland, or a frame piece means linking it from the manifest(s) that should ship it. New deployment scope = new manifest file at the appropriate path.

Single author-facing rule: **every file basename in the world is unique.**

## Style

- Do not use em dashes anywhere in this repository (place files, ARCHITECTURE, README, copilot-instructions, anything else). Use a hyphen (`-`) or rephrase.

## File standards

Footer in place files: `vX.Y.Z - KAI Worlds`, where `X.Y.Z` is the current world version (set by `scripts/bump_version.py` on release, or per-file by an LLM during a content edit).
