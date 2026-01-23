"""
Cocotb Test Configuration for Axion-HDL

This file provides pytest fixtures and configuration for cocotb tests.
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Environment setup for cocotb
os.environ.setdefault('SIM', 'ghdl')
os.environ.setdefault('TOPLEVEL_LANG', 'vhdl')


def pytest_configure(config):
    """Configure pytest for cocotb tests"""
    config.addinivalue_line(
        "markers", "cocotb: mark test as a cocotb simulation test"
    )


def pytest_collection_modifyitems(config, items):
    """Add cocotb marker to all tests in this directory"""
    for item in items:
        if "cocotb" in str(item.fspath):
            item.add_marker("cocotb")
