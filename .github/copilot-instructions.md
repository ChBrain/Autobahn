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
3. For minor or major releases only: run `python scripts/bump_version.py --minor` (or `--major`) and commit the result. Skip for patch releases.
4. Open a PR - the PR template checklist must pass before merge
5. Merge to `main` via PR only
6. Create a GitHub release with a version tag to trigger the release workflow
7. The workflow zips every folder that contains `stack.md` and uploads the zip as a release asset

## Versioning

- **File footer patch** - LLM increments per file during content edits. No release needed.
- **Patch release** - user-triggered GitHub tag bump only. No file footer changes.
- **Minor release** - user-triggered. Run `bump_version.py --minor` to update all file footers, then PR + tag.
- **Major release** - user-triggered. Run `bump_version.py --major` for structural changes, then PR + tag.

Never run `bump_version.py` unless the user explicitly asks for a release.

## Style

- Do not use em dashes (--). Use a hyphen (-) instead.

## File standards

Footer in place files: `v0.1.0 - KAI Worlds`
