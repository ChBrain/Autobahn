#!/usr/bin/env python3
"""Fix road-tied stop naming: add missing road prefixes.

Renames files to follow the convention:
  - place_<road>[_<NN>]_service_<name>.md
  - place_<road>[_<NN>]_rest_<name>.md
  - place_<road>[_<NN>]_roadhouse_<name>.md

Target files (4 total):
  - place_service_aalbek.md → place_a7_service_aalbek.md
  - place_service_brokenlande.md → place_a7_service_brokenlande.md
  - place_service_huettener_berge.md → place_a7_service_huettener_berge.md
  - place_rasthof_holmmoor.md → place_a7_service_holmmoor.md

Usage:
  scripts/fix_stop_naming.py

The script:
1. Uses git mv to rename the files
2. Uses git grep to find ALL references across the codebase
3. Updates all files with references
4. Commits the changes
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Mapping of old names to new names
RENAMES = {
    "place_service_aalbek.md": "place_a7_service_aalbek.md",
    "place_service_brokenlande.md": "place_a7_service_brokenlande.md",
    "place_service_huettener_berge.md": "place_a7_service_huettener_berge.md",
    "place_rasthof_holmmoor.md": "place_a7_service_holmmoor.md",
}


def git_mv(old: str, new: str) -> bool:
    """Rename a file using git mv."""
    try:
        subprocess.run(
            ["git", "mv", old, new],
            cwd=".",
            check=True,
            capture_output=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: git mv {old} {new} failed: {e.stderr.decode()}")
        return False


def find_references_with_git_grep(old_basename: str) -> set[str]:
    """Find all files containing references to the old filename using git grep."""
    try:
        result = subprocess.run(
            ["git", "grep", "--files-with-matches", old_basename],
            cwd=".",
            capture_output=True,
            text=True,
        )
        # Only return files that actually exist (filter out deleted refs in index)
        files = set()
        for filepath in result.stdout.strip().split("\n"):
            if filepath and Path(filepath).exists():
                files.add(filepath)
        return files
    except subprocess.CalledProcessError:
        return set()


def update_references(old_basename: str, new_basename: str) -> list[str]:
    """Update references in all files that link to the renamed file."""
    updated: list[str] = []
    
    # Find all files containing the old reference
    ref_files = find_references_with_git_grep(old_basename)
    
    for ref_file in ref_files:
        path = Path(ref_file)
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        
        if old_basename not in content:
            continue
        
        new_content = content.replace(old_basename, new_basename)
        path.write_text(new_content, encoding="utf-8")
        updated.append(ref_file)
    
    return updated


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    original_cwd = Path.cwd()
    
    try:
        # Change to repo root
        root_path = root
        
        fixed = 0
        for old_name, new_name in RENAMES.items():
            # Find the file in roads/a7/
            old_path = root_path / "roads" / "a7" / old_name
            new_path = root_path / "roads" / "a7" / new_name
            
            if not old_path.exists():
                print(f"SKIP {old_name}: not found")
                continue
            
            # Rename using git mv
            print(f"Renaming: {old_name} → {new_name}")
            if not git_mv(str(old_path), str(new_path)):
                return 1
            
            # Update all references across the codebase
            updated_files = update_references(old_name, new_name)
            if updated_files:
                print(f"  Updated references in {len(updated_files)} files")
            
            fixed += 1
        
        if fixed > 0:
            # Stage all changes
            subprocess.run(
                ["git", "add", "-A"],
                cwd=str(root_path),
                check=True,
            )
            
            # Commit
            subprocess.run(
                ["git", "commit", "-m", f"fix: add road prefix to {fixed} stop files\n\n- place_service_aalbek → place_a7_service_aalbek\n- place_service_brokenlande → place_a7_service_brokenlande\n- place_service_huettener_berge → place_a7_service_huettener_berge\n- place_rasthof_holmmoor → place_a7_service_holmmoor\n\nAll stop files now follow convention: place_{{road}}_{{type}}_{{name}}"],
                cwd=str(root_path),
                check=True,
            )
            
            print(f"\nFixed {fixed} files. Changes committed.")
        
        return 0
    
    finally:
        # Return to original directory
        pass


if __name__ == "__main__":
    sys.exit(main())

