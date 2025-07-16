#!/usr/bin/env python3
"""
Pre-publication checks for crypto-powerdata-mcp package.

This script performs various checks before publishing to ensure package quality.
"""

import subprocess
import sys
import os
from pathlib import Path
import json

def run_command(cmd, check=True):
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
    if check and result.returncode != 0:
        print(f"❌ Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    return result

def check_pyproject_toml():
    """Check pyproject.toml for required fields."""
    print("\n📋 Checking pyproject.toml...")

    try:
        with open("pyproject.toml", "r") as f:
            content = f.read()

        required_fields = [
            "name =",
            "version =",
            "description =",
            "authors =",
            "license =",
            "requires-python =",
            "[project.scripts]"
        ]

        missing_fields = []
        for field in required_fields:
            if field not in content:
                missing_fields.append(field)

        if missing_fields:
            print(f"❌ Missing required fields in pyproject.toml: {missing_fields}")
            return False
        else:
            print("✅ pyproject.toml looks good")
            return True

    except FileNotFoundError:
        print("❌ pyproject.toml not found")
        return False

def check_readme():
    """Check README.md exists and has content."""
    print("\n📖 Checking README.md...")

    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()

        if len(content) < 500:
            print("❌ README.md seems too short")
            return False

        required_sections = ["# Crypto PowerData MCP", "## 🚀 Quick Start with uvx (Recommended)", "## Installation"]
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)

        if missing_sections:
            print(f"❌ Missing sections in README.md: {missing_sections}")
            return False
        else:
            print("✅ README.md looks good")
            return True

    except FileNotFoundError:
        print("❌ README.md not found")
        return False

def check_license():
    """Check LICENSE file exists."""
    print("\n📄 Checking LICENSE...")

    if Path("LICENSE").exists():
        print("✅ LICENSE file found")
        return True
    else:
        print("❌ LICENSE file not found")
        return False

def check_source_structure():
    """Check source code structure."""
    print("\n🏗️  Checking source structure...")

    required_files = [
        "src/__init__.py",
        "src/main.py",
        "src/cli.py",
        "src/data_provider.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing source files: {missing_files}")
        return False
    else:
        print("✅ Source structure looks good")
        return True

def check_dependencies():
    """Check if all dependencies are properly specified."""
    print("\n📦 Checking dependencies...")

    try:
        result = run_command("uv tree", check=False)
        if result and result.returncode == 0:
            print("✅ Dependencies resolved successfully")
            return True
        else:
            print("❌ Dependency resolution failed")
            return False
    except Exception:
        print("❌ Could not check dependencies")
        return False

def main():
    """Main check workflow."""
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🔍 Running pre-publication checks for crypto-powerdata-mcp")

    checks = [
        ("pyproject.toml", check_pyproject_toml),
        ("README.md", check_readme),
        ("LICENSE", check_license),
        ("Source structure", check_source_structure),
        ("Dependencies", check_dependencies),
    ]

    results = []
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ Error in {check_name} check: {e}")
            results.append((check_name, False))

    print("\n" + "="*50)
    print("📊 CHECK RESULTS")
    print("="*50)

    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check_name}")
        if not passed:
            all_passed = False

    print("="*50)

    if all_passed:
        print("🎉 All checks passed! Ready for publication.")
        print("\nNext steps:")
        print("1. Run: python scripts/publish.py")
        print("2. Or manually: uv run python -m build && uv run twine upload dist/*")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues before publishing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
