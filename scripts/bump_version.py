#!/usr/bin/env python3
"""
Version bumping script for crypto-powerdata-mcp.

This script helps increment version numbers in pyproject.toml and other files.
"""

import re
import sys
from pathlib import Path
from typing import Tuple

def get_current_version() -> str:
    """Get current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        raise FileNotFoundError("pyproject.toml not found")
    
    content = pyproject_path.read_text()
    match = re.search(r'version = "([^"]+)"', content)
    if not match:
        raise ValueError("Version not found in pyproject.toml")
    
    return match.group(1)

def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse version string into major, minor, patch."""
    parts = version.split('.')
    if len(parts) != 3:
        raise ValueError(f"Invalid version format: {version}")
    
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        raise ValueError(f"Invalid version format: {version}")

def bump_version(version: str, bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(version)
    
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

def update_version_in_file(file_path: Path, old_version: str, new_version: str):
    """Update version in a specific file."""
    if not file_path.exists():
        print(f"Warning: {file_path} not found, skipping")
        return
    
    content = file_path.read_text()
    
    # Different patterns for different files
    patterns = [
        (r'version = "([^"]+)"', f'version = "{new_version}"'),  # pyproject.toml
        (r"version='([^']+)'", f"version='{new_version}'"),      # CLI help
        (r'crypto-powerdata-mcp ([0-9.]+)', f'crypto-powerdata-mcp {new_version}'),  # CLI version
    ]
    
    updated = False
    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            updated = True
    
    if updated:
        file_path.write_text(content)
        print(f"✅ Updated version in {file_path}")
    else:
        print(f"⚠️  No version pattern found in {file_path}")

def main():
    """Main version bumping workflow."""
    if len(sys.argv) != 2:
        print("Usage: python scripts/bump_version.py <major|minor|patch>")
        sys.exit(1)
    
    bump_type = sys.argv[1].lower()
    if bump_type not in ["major", "minor", "patch"]:
        print("Error: bump type must be 'major', 'minor', or 'patch'")
        sys.exit(1)
    
    try:
        # Get current version
        current_version = get_current_version()
        print(f"Current version: {current_version}")
        
        # Calculate new version
        new_version = bump_version(current_version, bump_type)
        print(f"New version: {new_version}")
        
        # Confirm with user
        confirm = input(f"Bump version from {current_version} to {new_version}? (y/N): ")
        if confirm.lower() != 'y':
            print("Version bump cancelled")
            sys.exit(0)
        
        # Update version in files
        files_to_update = [
            Path("pyproject.toml"),
            Path("src/cli.py"),
        ]
        
        for file_path in files_to_update:
            update_version_in_file(file_path, current_version, new_version)
        
        print(f"\n🎉 Version bumped successfully!")
        print(f"Next steps:")
        print(f"1. Review changes: git diff")
        print(f"2. Commit changes: git add -A && git commit -m 'Bump version to {new_version}'")
        print(f"3. Create tag: git tag v{new_version}")
        print(f"4. Push changes: git push && git push --tags")
        print(f"5. Create GitHub release to trigger PyPI publication")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
