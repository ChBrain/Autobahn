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
2. Open a PR - the PR template checklist must pass before merge
3. Merge to `main` via PR only
4. Create a GitHub release with a version tag to trigger the release workflow
5. The workflow zips every folder that contains `stack.md` and uploads the zip as a release asset

## Style

- Do not use em dashes (--). Use a hyphen (-) instead.

## File standards

Footer in place files: `v0.1.0 - KAI Worlds`
