#!/usr/bin/env python3
"""
test_axion.py - Test script for Axion HDL Register Generator

This script demonstrates how to use Axion to analyze VHDL files
and generate AXI register interfaces.
"""

import os
import sys

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from axion_hdl import AxionHDL

def main():
    print("="*80)
    print("Axion HDL Register Generator - Test Script")
    print("="*80)
    
    # Determine paths relative to project root
    tests_vhdl_dir = os.path.join(project_root, "tests", "vhdl")
    output_dir = os.path.join(project_root, "output")
    
    # Step 1: Create Axion instance with output directory
    print("\n[1] Initializing Axion...")
    axion = AxionHDL(output_dir=output_dir)
    print(f"    Output directory: {output_dir}")
    
    # Step 2: Add source directories
    print("\n[2] Adding source directories...")
    axion.add_src(tests_vhdl_dir)
    
    # Exclude error test cases (intentionally broken files for testing)
    print("\n[2.1] Excluding error test cases...")
    axion.exclude("error_cases")
    
    # List all added source directories
    print("\n[3] Source directories:")
    axion.list_src()
    
    # Step 3: Analyze VHDL files
    print("\n[4] Analyzing VHDL files...")
    if not axion.analyze():
        print("    ERROR: Analysis failed!")
        return 1
    
    # Step 4: Generate outputs
    print("\n[5] Generating outputs...")
    
    # Generate VHDL register modules
    print("\n    [5.1] Generating VHDL modules...")
    axion.generate_vhdl()
    
    # Generate documentation
    print("\n    [5.2] Generating documentation...")
    axion.generate_documentation(format="md")
    
    # Generate XML register map
    print("\n    [5.3] Generating XML register map...")
    axion.generate_xml()
    
    # Generate C header files
    print("\n    [5.4] Generating C header files...")
    axion.generate_c_header()
    
    print("\n" + "="*80)
    print("Test completed successfully!")
    print("="*80)
    print(f"\nGenerated files can be found in: {output_dir}/")
    print("\nNext steps:")
    print("  1. Review the analysis output above")
    print("  2. Check generated VHDL files in ./output/")
    print("  3. Review documentation in ./output/register_map.md")
    print("  4. Check C headers in ./output/")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    exit(main())
