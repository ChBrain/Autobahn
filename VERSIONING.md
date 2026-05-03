# Versioning Workflow with Intent Declaration

*v0.2.4 - KAI Worlds*

## Overview

Every commit has an **implicit release intent**: patch, minor, or major. We make this explicit:

1. **Declare** intent upfront with `.bump-type` file
2. **Validate** all commits match the declared intent (pre-commit hook)
3. **Merge** to main via PR
4. **Release** via GitHub tag (minor/major only; patch bumps merge automatically)

This protects against scope creep and ensures you know what you're committing.

## Workflow

### Step 1: Create Feature Branch

```bash
git checkout -b feat/my-change
```

### Step 2: Declare Intent with `.bump-type`

Determine what kind of change this is:

- **PATCH** - Fix, typo, small improvement. No new features. `x.y.z → x.y.(z+1)`
- **MINOR** - New feature, new road, new node. Backward compatible. `x.y.z → x.(y+1).0`
- **MAJOR** - Restructure, schema change, breaking change. `x.y.z → (x+1).0.0`

Then create the file:

```bash
echo "PATCH" > .bump-type
git add .bump-type
git commit -m "chore: declare bump type"
```

### Step 3: (Optional) Get Ministerial Review

Ask the Federal Minister if your declared scope is reasonable:

```bash
python scripts/minister_review.py
```

The minister will give feedback. If they slap your hand, reconsider the scope.

### Step 4: Make Changes and Bump Version

Make your content changes:

```bash
# Edit some files
nano roads/a20/place_a20.md
```

Bump the version to match your declared intent:

```bash
# For PATCH or MINOR (automatic detection from .bump-type):
python scripts/bump_version.py --patch  # if declared PATCH
python scripts/bump_version.py --minor  # if declared MINOR

# For MAJOR:
python scripts/bump_version.py --major
```

Commit with your changes and version bump:

```bash
git add -A
git commit -m "feat: add new road"
```

**The pre-commit hook will:**
- ✓ Verify version bump matches declared type
- ✗ Reject if you declared PATCH but bumped to MINOR (scope creep)
- ✗ Reject if you forgot to bump version

### Step 5: Open PR and Merge

```bash
git push -u origin feat/my-change
```

Open a PR. CI will:
- Validate version bump is in the right range
- Run all content validation
- Check that `.bump-type` matches actual version change

Once approved, merge to main.

### Step 6: (For MINOR/MAJOR) Create Release

For patch bumps, you're done - version is already bumped and merged.

For **minor or major releases**, create a GitHub release:

```bash
# Create release v0.3.0 (if currently v0.2.0)
# The release workflow will sync versions and deploy
```

## Examples

### Example 1: Patch Fix

```bash
# Branch and declare
git checkout -b fix/typo-in-a1
echo "PATCH" > .bump-type
git add .bump-type && git commit -m "chore: declare patch bump"

# Make change
nano roads/a1/place_a1.md
python scripts/bump_version.py --patch  # v0.2.0 → v0.2.1

# Commit
git add -A && git commit -m "fix: typo in A1 description"

# Output:
# ✓ Version bump validated
#   Type:    PATCH
#   Version: v0.2.0 → v0.2.1
```

### Example 2: Minor Feature

```bash
# Branch and declare
git checkout -b feat/a20-expansion
echo "MINOR" > .bump-type
git add .bump-type && git commit -m "chore: declare minor bump"

# Make changes
nano roads/a20/place_a20.md
python scripts/bump_version.py --minor  # v0.2.0 → v0.3.0

# Multiple commits are OK (all must stay within MINOR):
git add -A && git commit -m "feat: add 10 new A20 exits"
nano roads/a20/place_a20_01.md
git add -A && git commit -m "docs: add details to A20 node"

# Output:
# ✓ Version bump validated
#   Type:    MINOR
#   Version: v0.2.0 → v0.3.0
```

### Example 3: Scope Creep (Rejected)

```bash
# Declared PATCH
git checkout -b fix/typo
echo "PATCH" > .bump-type
git add .bump-type && git commit -m "chore: declare patch bump"

# But then did a MINOR bump
python scripts/bump_version.py --minor  # v0.2.0 → v0.3.0
git add -A && git commit -m "fix: typo"

# Output:
# ✗ VALIDATION FAILED
#   Declared: PATCH
#   Actual:   MINOR
#   Version:  v0.2.0 → v0.3.0
# 
# Your bump doesn't match your declaration!
# This is a scope violation. Fix it:
#   You declared PATCH but are bumping MINOR (scope creep)
```

## Files

- `.bump-type` - Declare PATCH/MINOR/MAJOR for this branch (created by you per-branch)
- `.bump-type.example` - Template/reference
- `.githooks/pre-commit` - Hook that validates version bumps match declared type
- `scripts/bump_version.py` - Bump version files to match intent
- `scripts/minister_review.py` - Get ministerial feedback on declared scope
- `scripts/setup-hooks.sh` - Install the pre-commit hook

## Setup

First time only:

```bash
bash scripts/setup-hooks.sh
git config core.hooksPath .githooks
```

Then every feature branch:

```bash
git checkout -b feat/my-change
echo "PATCH" > .bump-type  # Change to MINOR or MAJOR as needed
git add .bump-type && git commit -m "chore: declare bump type"
```

## Why This Works

1. **Intent is declared upfront** - You commit to a scope before making changes
2. **Hook enforces consistency** - You can't accidentally scope-creep from PATCH to MINOR
3. **Version is always in sync** - Version bump = content change (no separate automation)
4. **PR shows intent** - `.bump-type` file is first commit, intent is visible
5. **Minister provides oversight** - Arbitrary authority can slap your hand if scope is wrong
6. **Simple and auditable** - All version history is in git, nothing hidden

## Minister's Authority

The minister has final say on whether your declared scope is appropriate. If they reject it:

```bash
# Edit .bump-type with the suggested level
echo "PATCH" > .bump-type
git add .bump-type && git commit --amend
```

Then continue. The minister's review is advisory but respected.
