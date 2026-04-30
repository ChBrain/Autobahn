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
  - place_rasthof_holmmoor.md → place_a7_roadhouse_holmmoor.md

Usage:
  scripts/fix_stop_naming.py

The script:
1. Uses git mv to rename the files
2. Updates references in road index files (place_<road>.md)
3. Updates references in state files (bundeslaender/place_*.md)
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
    "place_rasthof_holmmoor.md": "place_a7_roadhouse_holmmoor.md",
}

# Files that reference these stops and need updates
FILES_WITH_REFERENCES = [
    "roads/a7/place_a7.md",
    "bundeslaender/place_schleswig_holstein.md",
]


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


def update_references(old_basename: str, new_basename: str) -> list[str]:
    """Update references in files that link to the renamed file."""
    updated: list[str] = []
    
    for ref_file in FILES_WITH_REFERENCES:
        path = Path(ref_file)
        if not path.exists():
            continue
        
        content = path.read_text(encoding="utf-8")
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
            
            # Update references
            updated_files = update_references(old_name, new_name)
            if updated_files:
                print(f"  Updated references in: {', '.join(updated_files)}")
            
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
                ["git", "commit", "-m", f"fix: add road prefix to {fixed} stop files\n\n- place_service_aalbek → place_a7_service_aalbek\n- place_service_brokenlande → place_a7_service_brokenlande\n- place_service_huettener_berge → place_a7_service_huettener_berge\n- place_rasthof_holmmoor → place_a7_roadhouse_holmmoor\n\nAll stop files now follow convention: place_{{road}}_{{type}}_{{name}}"],
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
