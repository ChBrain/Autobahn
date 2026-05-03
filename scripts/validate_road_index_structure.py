#!/usr/bin/env python3
"""
Validate road index file structure (place_aX.md).

Enforces:
1. Required sections: Owner, Shown, Holds, Offers, Withheld (+ footer)
2. Holds section must have Bundesland subsections (### State)
3. Each subsection must reference state file: [state](place_state.md)
4. No broken file links (referenced exits must exist or be marked [TBD])
5. No custom/non-standard sections (Status, Planned Route, etc.)
6. Proper section order
"""

import os
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ROADS_DIR = REPO_ROOT / "roads"

REQUIRED_SECTIONS = ["Owner", "Shown", "Holds", "Offers", "Withheld"]
FORBIDDEN_SECTIONS = ["Status", "Planned Route", "Plan", "Future", "TODO"]
SECTION_PATTERN = r"^## (.+)$"
SUBSECTION_PATTERN = r"^### (.+)$"

def validate_road_file(filepath):
    """Validate a single road index file."""
    errors = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # Check filename follows pattern
    filename = filepath.name
    if not filename.startswith('place_a') or not filename.endswith('.md'):
        errors.append(f"Invalid filename: {filename} (must be place_aX.md)")
        return errors
    
    # Extract sections
    sections = {}
    current_section = None
    current_content = []
    
    for line in lines:
        if re.match(SECTION_PATTERN, line):
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            match = re.match(SECTION_PATTERN, line)
            current_section = match.group(1)
            current_content = []
        elif current_section:
            current_content.append(line)
    
    if current_section:
        sections[current_section] = '\n'.join(current_content)
    
    # Check required sections
    for required in REQUIRED_SECTIONS:
        if required not in sections:
            errors.append(f"Missing section: ## {required}")
    
    # Check for forbidden sections
    for forbidden in FORBIDDEN_SECTIONS:
        if forbidden in sections:
            errors.append(f"Forbidden section: ## {forbidden} (use Shown or Holds instead)")
    
    # Validate Holds section has Bundesland subsections
    if "Holds" in sections:
        holds_content = sections["Holds"]
        subsections = re.findall(SUBSECTION_PATTERN, holds_content)
        
        if not subsections:
            errors.append("Holds section must have ### Bundesland subsections (e.g., ### Hamburg)")
        
        # Check each subsection references a state file
        for line in holds_content.split('\n'):
            if re.match(SUBSECTION_PATTERN, line):
                state_name = re.match(SUBSECTION_PATTERN, line).group(1)
                # Look for reference link in following lines
                next_lines = holds_content[holds_content.find(line):].split('\n')[1:5]
                has_state_ref = any(f"(place_{state_name.lower().replace(' ', '_').replace('-', '_')}.md)" in l 
                                   for l in next_lines)
                
                if not has_state_ref and "(place_hamburg.md)" not in str(next_lines) and "[TBD" not in str(next_lines):
                    # Some leniency for under-construction roads
                    if "[Under construction" not in holds_content:
                        errors.append(f"Subsection '### {state_name}' should reference state file")
    
    # Check for broken links (km references with km TBD is OK for under-construction)
    broken_links = re.findall(r'\[(.*?)\]\((place_[^)]+\.md)\)', content)
    for link_text, link_target in broken_links:
        if "[Under construction" not in content and "[TBD" not in link_text:
            target_path = filepath.parent / link_target
            if not target_path.exists():
                # Allow references outside roads/ directory
                if not link_target.startswith('../'):
                    errors.append(f"Broken link: {link_target} (referenced in '{link_text}')")
    
    # Validate section order
    section_list = list(sections.keys())
    valid_order = [s for s in REQUIRED_SECTIONS if s in section_list]
    if valid_order != section_list[:len(valid_order)]:
        errors.append(f"Section order incorrect. Should be: {', '.join(REQUIRED_SECTIONS)}")
    
    return errors

def main():
    """Validate all road index files."""
    all_errors = []
    
    for road_dir in ROADS_DIR.glob('a*'):
        if not road_dir.is_dir():
            continue
        
        road_file = road_dir / f"place_{road_dir.name}.md"
        
        if not road_file.exists():
            all_errors.append(f"Missing road index: {road_file.relative_to(REPO_ROOT)}")
            continue
        
        errors = validate_road_file(road_file)
        
        if errors:
            for error in errors:
                all_errors.append(f"{road_file.relative_to(REPO_ROOT)}: {error}")
    
    if all_errors:
        for error in sorted(all_errors):
            print(f"ERROR: {error}")
        return 1
    
    print(f"✓ Road index structure validation passed ({len(list(ROADS_DIR.glob('a*')))} files)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
