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

**See [VERSIONING.md](../VERSIONING.md) for complete workflow with examples.**

Quick summary:

1. **Create feature branch**
   ```bash
   git checkout -b feat/my-change
   ```

2. **Declare intent upfront** with `.bump-type`:
   ```bash
   echo "PATCH" > .bump-type  # or MINOR/MAJOR
   git add .bump-type && git commit -m "chore: declare bump type"
   ```

3. **(Optional) Get ministerial review:**
   ```bash
   python scripts/minister_review.py
   ```

4. **Make changes and bump version**:
   ```bash
   # Edit files
   nano roads/a20/place_a20.md
   
   # Bump version to match declared type
   python scripts/bump_version.py --patch  # if declared PATCH
   
   # Commit
   git add -A && git commit -m "feat: add new road"
   ```

5. **Pre-commit hook validates**:
   - ✓ Version bump matches declared type (PATCH/MINOR/MAJOR)
   - ✓ No German language bleed detected
   - ✗ Rejects scope creep (declared PATCH, bumped MINOR)

6. **Open PR and merge**:
   ```bash
   git push -u origin feat/my-change
   ```
   CI validates version bump rules, no German language bleed, all tests pass, merge to main.

7. **(For MINOR/MAJOR only) Create GitHub release**:
   - Patch bumps are already done - version merged to main
   - Minor/major releases: create GitHub release with tag (v0.3.0)
   - Release workflow syncs versions and deploys

## Versioning

- **Intent-first model** - Every branch declares PATCH/MINOR/MAJOR upfront in `.bump-type` file
- **Pre-commit hook** - Validates version bumps match declared type (prevents scope creep)
- **CI validation** - Validates patch-only for work PRs, major/minor/patch for release PRs
- **Version merges with code** - Not separate automation, version is part of the commit
- **Minor/major via tags** - Only release tags trigger minor/major bumps and deployment

**Important:**
- Always declare `.bump-type` on first commit of feature branch
- Use `python scripts/bump_version.py --patch` (or --minor/--major) to bump
- Hook prevents scope creep: can't declare PATCH and bump MINOR
- CI validates: work PRs must be patch-only, release PRs can be major/minor
- Minor/major bumps are release-only (via GitHub release tags)

See [VERSIONING.md](../VERSIONING.md) for full details, examples, and minister reviews.

## Version Bumping is CI-Only

**CRITICAL:** Do not run `python scripts/bump_version.py` locally.

This script only runs in GitHub Actions CI on merge to main. Running it locally causes the pre-commit hook to reject your commit with confusing errors.

**Correct workflow:**
1. Create `.bump-type` file with PATCH/MINOR/MAJOR on first commit
2. Make content changes and commit normally (no manual version bump)
3. Push and open PR
4. CI validates `.bump-type` matches declared intent
5. Merge to main → GitHub Actions automatically bumps version

**If you accidentally ran bump_version.py locally:**
```bash
git reset HEAD
git checkout -- .
git add -A
git commit -m "your change"
git push -u origin <branch>
```
The pre-commit hook error message will guide recovery steps.

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

## Content standards

**Language:** All place files must be in English. German proper names (Eigenname) and place names are acceptable, but German language content (sentences, phrases, and German-specific terminology) is not.

Examples:
- ✓ Allowed: "Ratzeburg is a city on the border"
- ✓ Allowed: "Named after Friedrich Franz I"
- ✗ Not allowed: "1949 bis 1990 verlief die Grenze..." (German sentence)
- ✗ Not allowed: "Der Krieg hat die Stadt..." (German language content)

The validator (`scripts/validate_german_bleed.py`) detects German verb phrases and language-specific terms. It is run automatically on all PRs as part of CI validation.

## File standards

Footer in place files: `vX.Y.Z - KAI Worlds`, where `X.Y.Z` is the current world version (set by `scripts/bump_version.py` on release, or per-file by an LLM during a content edit).
