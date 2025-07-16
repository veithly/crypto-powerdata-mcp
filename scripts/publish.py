#!/usr/bin/env python3
"""
Publishing script for crypto-powerdata-mcp package.

This script helps build and publish the package to PyPI.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        sys.exit(1)
    return result

def main():
    """Main publishing workflow."""
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🚀 Starting publication process for crypto-powerdata-mcp")
    
    # Clean previous builds
    print("\n📦 Cleaning previous builds...")
    run_command("rm -rf dist/ build/ *.egg-info/", check=False)
    
    # Install build dependencies
    print("\n🔧 Installing build dependencies...")
    run_command("uv add --dev build twine")
    
    # Run tests (optional, but recommended)
    print("\n🧪 Running tests...")
    result = run_command("uv run pytest", check=False)
    if result.returncode != 0:
        print("⚠️  Tests failed, but continuing with build...")
    
    # Build the package
    print("\n🏗️  Building package...")
    run_command("uv run python -m build")
    
    # Check the built package
    print("\n🔍 Checking package...")
    run_command("uv run twine check dist/*")
    
    # Ask for confirmation before uploading
    print("\n📋 Package built successfully!")
    print("Files in dist/:")
    run_command("ls -la dist/")
    
    upload_choice = input("\n🚀 Upload to PyPI? (y/N): ").strip().lower()
    
    if upload_choice == 'y':
        # Upload to PyPI
        print("\n📤 Uploading to PyPI...")
        print("You'll need to enter your PyPI credentials or API token.")
        run_command("uv run twine upload dist/*")
        print("\n✅ Package published successfully!")
        print("\nUsers can now install with:")
        print("  uvx crypto-powerdata-mcp")
        print("  # or")
        print("  pip install crypto-powerdata-mcp")
    else:
        print("\n⏸️  Upload cancelled. You can upload later with:")
        print("  uv run twine upload dist/*")
        print("\nOr upload to test PyPI first:")
        print("  uv run twine upload --repository testpypi dist/*")

if __name__ == "__main__":
    main()
