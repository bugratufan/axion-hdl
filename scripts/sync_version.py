#!/usr/bin/env python3
"""
Version Sync Script for Axion-HDL

This script manages version synchronization across the project:
- Reads version from .version file (format: v<major>.<minor>.<patch>)
- Can auto-bump version based on branch name
- Updates pyproject.toml, setup.py, and axion_hdl/__init__.py

Usage:
    python scripts/sync_version.py                    # Sync current version
    python scripts/sync_version.py --bump minor      # Bump minor version
    python scripts/sync_version.py --bump patch      # Bump patch version
    python scripts/sync_version.py --check           # Check if files are in sync
"""

import argparse
import re
import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
VERSION_FILE = PROJECT_ROOT / ".version"
PYPROJECT_FILE = PROJECT_ROOT / "pyproject.toml"
SETUP_FILE = PROJECT_ROOT / "setup.py"
INIT_FILE = PROJECT_ROOT / "axion_hdl" / "__init__.py"


def parse_version(version_str: str) -> tuple:
    """Parse version string v<major>.<minor>.<patch> into tuple."""
    version_str = version_str.strip()
    if version_str.startswith('v'):
        version_str = version_str[1:]
    
    match = re.match(r'^(\d+)\.(\d+)\.(\d+)$', version_str)
    if not match:
        raise ValueError(f"Invalid version format: {version_str}")
    
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def format_version(major: int, minor: int, patch: int, with_v: bool = True) -> str:
    """Format version tuple to string."""
    version = f"{major}.{minor}.{patch}"
    return f"v{version}" if with_v else version


def read_version() -> str:
    """Read version from .version file."""
    if not VERSION_FILE.exists():
        raise FileNotFoundError(f".version file not found at {VERSION_FILE}")
    
    return VERSION_FILE.read_text().strip()


def write_version(version: str):
    """Write version to .version file."""
    VERSION_FILE.write_text(version + "\n")


def bump_version(bump_type: str) -> str:
    """Bump version based on type (major, minor, patch)."""
    current = read_version()
    major, minor, patch = parse_version(current)
    
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        major = major
        minor += 1
        patch = 0
    elif bump_type == "patch":
        major = major
        minor = minor
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")
    
    new_version = format_version(major, minor, patch)
    write_version(new_version)
    return new_version


def update_pyproject(version: str):
    """Update version in pyproject.toml."""
    # Remove 'v' prefix for pyproject.toml
    version_num = version[1:] if version.startswith('v') else version
    
    content = PYPROJECT_FILE.read_text()
    new_content = re.sub(
        r'^version\s*=\s*"[^"]*"',
        f'version = "{version_num}"',
        content,
        flags=re.MULTILINE
    )
    
    if content != new_content:
        PYPROJECT_FILE.write_text(new_content)
        return True
    return False


def update_setup(version: str):
    """Update version in setup.py."""
    # Remove 'v' prefix for setup.py
    version_num = version[1:] if version.startswith('v') else version
    
    content = SETUP_FILE.read_text()
    new_content = re.sub(
        r"version\s*=\s*['\"][^'\"]*['\"]",
        f"version='{version_num}'",
        content,
        count=1  # Only replace first occurrence
    )
    
    if content != new_content:
        SETUP_FILE.write_text(new_content)
        return True
    return False


def update_init(version: str):
    """Update __version__ in __init__.py."""
    # Remove 'v' prefix for Python __version__
    version_num = version[1:] if version.startswith('v') else version
    
    content = INIT_FILE.read_text()
    new_content = re.sub(
        r'^__version__\s*=\s*"[^"]*"',
        f'__version__ = "{version_num}"',
        content,
        flags=re.MULTILINE
    )
    
    if content != new_content:
        INIT_FILE.write_text(new_content)
        return True
    return False


def get_current_versions() -> dict:
    """Get current version from all files."""
    versions = {}
    
    # .version file
    try:
        versions['.version'] = read_version()
    except FileNotFoundError:
        versions['.version'] = None
    
    # pyproject.toml
    content = PYPROJECT_FILE.read_text()
    match = re.search(r'^version\s*=\s*"([^"]*)"', content, re.MULTILINE)
    versions['pyproject.toml'] = match.group(1) if match else None
    
    # setup.py
    content = SETUP_FILE.read_text()
    match = re.search(r"version\s*=\s*['\"]([^'\"]*)['\"]\s*,", content)
    versions['setup.py'] = match.group(1) if match else None
    
    # __init__.py
    content = INIT_FILE.read_text()
    match = re.search(r'^__version__\s*=\s*"([^"]*)"', content, re.MULTILINE)
    versions['__init__.py'] = match.group(1) if match else None
    
    return versions


def check_sync() -> bool:
    """Check if all version files are in sync."""
    versions = get_current_versions()
    
    # Normalize .version (remove 'v' prefix)
    version_file = versions['.version']
    if version_file and version_file.startswith('v'):
        version_file = version_file[1:]
    
    all_same = (version_file == versions['pyproject.toml'] == versions['setup.py'] == versions['__init__.py'])
    
    print("Current versions:")
    for file, ver in versions.items():
        status = "✓" if ver else "✗"
        print(f"  {status} {file}: {ver}")
    
    if all_same:
        print("\n✓ All versions are in sync")
    else:
        print("\n✗ Versions are NOT in sync")
    
    return all_same


def sync_all():
    """Sync version from .version to all files."""
    version = read_version()
    print(f"Syncing version: {version}")
    
    pyproject_updated = update_pyproject(version)
    setup_updated = update_setup(version)
    init_updated = update_init(version)
    
    if pyproject_updated:
        print(f"  ✓ Updated pyproject.toml")
    else:
        print(f"  - pyproject.toml already up to date")
    
    if setup_updated:
        print(f"  ✓ Updated setup.py")
    else:
        print(f"  - setup.py already up to date")
    
    if init_updated:
        print(f"  ✓ Updated __init__.py")
    else:
        print(f"  - __init__.py already up to date")
    
    return pyproject_updated or setup_updated or init_updated


def main():
    parser = argparse.ArgumentParser(description="Version sync tool for Axion-HDL")
    parser.add_argument('--bump', choices=['major', 'minor', 'patch'],
                        help='Bump version before syncing')
    parser.add_argument('--check', action='store_true',
                        help='Check if versions are in sync (no changes)')
    parser.add_argument('--version', action='store_true',
                        help='Print current version and exit')
    
    args = parser.parse_args()
    
    if args.version:
        print(read_version())
        return 0
    
    if args.check:
        return 0 if check_sync() else 1
    
    if args.bump:
        new_version = bump_version(args.bump)
        print(f"Bumped version to: {new_version}")
    
    changes_made = sync_all()
    
    if args.bump or changes_made:
        print("\n✓ Version sync complete")
        return 0
    else:
        print("\n- No changes needed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
