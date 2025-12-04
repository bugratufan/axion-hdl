#!/usr/bin/env python3
"""
Address Conflict Detection Test

This test verifies that Axion-HDL correctly detects and reports address conflicts
when two or more registers are assigned to the same address.

Test Requirements:
- AXION-006: Each register must have a unique address
- AXION-007: Address offsets must be correctly calculated
- AXION-008: No address overlap allowed within a module

Expected Behavior:
- When parsing a VHDL file with duplicate addresses, Axion should raise
  AddressConflictError with detailed information about the conflict.
- If no error is raised, the test FAILS.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from axion_hdl import AxionHDL, AddressConflictError


def test_address_conflict_detection():
    """
    Test that address conflicts are properly detected.
    
    Uses tests/vhdl/address_conflict_test.vhd which intentionally has
    two registers assigned to the same address (0x00).
    
    Returns:
        bool: True if test passes (conflict detected), False otherwise
    """
    print("=" * 70)
    print("ADDRESS CONFLICT DETECTION TEST")
    print("=" * 70)
    print()
    print("Test File: tests/vhdl/address_conflict_test.vhd")
    print("Expected: AddressConflictError should be raised")
    print()
    print("-" * 70)
    
    # Get the path to the test VHDL file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    test_vhdl_dir = os.path.join(project_root, "tests", "vhdl", "error_cases")
    conflict_file = os.path.join(test_vhdl_dir, "address_conflict_test.vhd")
    
    # Verify test file exists
    if not os.path.exists(conflict_file):
        print(f"ERROR: Test file not found: {conflict_file}")
        return False
    
    # Create a temporary directory for this specific test
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy only the conflict test file to temp directory
        import shutil
        temp_vhdl = os.path.join(temp_dir, "address_conflict_test.vhd")
        shutil.copy(conflict_file, temp_vhdl)
        
        # Initialize Axion
        axion = AxionHDL()
        axion.add_src(temp_dir)
        axion.set_output_dir(os.path.join(temp_dir, "output"))
        
        # Try to analyze - should raise AddressConflictError
        try:
            axion.analyze()
            
            # If we get here, no exception was raised - TEST FAILS
            print()
            print("!" * 70)
            print("TEST FAILED: No AddressConflictError was raised!")
            print("!" * 70)
            print()
            print("The parser should have detected that reg_alpha and reg_beta")
            print("are both assigned to address 0x00, but it didn't.")
            print()
            print("This violates:")
            print("  - AXION-006: Each register must have a unique address")
            print("  - AXION-007: Address offsets must be correctly calculated")
            print("  - AXION-008: No address overlap allowed within a module")
            print()
            return False
            
        except AddressConflictError as e:
            # This is the expected behavior - TEST PASSES
            print()
            print("AddressConflictError was correctly raised!")
            print()
            print("Error details:")
            print(str(e))
            print()
            print("-" * 70)
            print("TEST PASSED: Address conflict was properly detected")
            print("-" * 70)
            
            # Verify error contains expected information
            error_msg = str(e)
            checks = [
                ("Address mentioned", "0x0000" in error_msg or "0x00" in error_msg),
                ("Existing register mentioned", "reg_alpha" in error_msg),
                ("Conflicting register mentioned", "reg_beta" in error_msg),
                ("Module name mentioned", "address_conflict_test" in error_msg),
                ("AXION-006 requirement", "AXION-006" in error_msg),
                ("AXION-007 requirement", "AXION-007" in error_msg),
                ("AXION-008 requirement", "AXION-008" in error_msg),
            ]
            
            print()
            print("Error message validation:")
            all_passed = True
            for check_name, check_result in checks:
                status = "✓" if check_result else "✗"
                print(f"  {status} {check_name}: {'PASS' if check_result else 'FAIL'}")
                if not check_result:
                    all_passed = False
            
            return all_passed
            
        except Exception as e:
            # Some other exception was raised - unexpected
            print()
            print("!" * 70)
            print(f"TEST FAILED: Unexpected exception type: {type(e).__name__}")
            print("!" * 70)
            print()
            print(f"Exception: {e}")
            print()
            print("Expected: AddressConflictError")
            print(f"Got: {type(e).__name__}")
            return False


def test_no_conflict_when_addresses_differ():
    """
    Test that no error is raised when addresses are unique.
    
    Uses a subset of the normal test files that have valid addresses.
    
    Returns:
        bool: True if test passes (no conflict), False otherwise
    """
    print()
    print("=" * 70)
    print("NO CONFLICT WITH UNIQUE ADDRESSES TEST")
    print("=" * 70)
    print()
    
    # Create a valid VHDL content
    valid_vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity valid_module is
    port (clk : in std_logic);
end entity;

architecture rtl of valid_module is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
    signal reg_c : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x08
begin
end architecture;
'''
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write valid VHDL file
        vhdl_file = os.path.join(temp_dir, "valid_module.vhd")
        with open(vhdl_file, 'w') as f:
            f.write(valid_vhdl)
        
        # Initialize Axion
        axion = AxionHDL()
        axion.add_src(temp_dir)
        axion.set_output_dir(os.path.join(temp_dir, "output"))
        
        try:
            axion.analyze()
            print("No error raised with unique addresses - PASS")
            return True
        except AddressConflictError as e:
            print(f"Unexpected AddressConflictError: {e}")
            print("TEST FAILED: False positive conflict detection")
            return False
        except Exception as e:
            print(f"Unexpected error: {e}")
            return False


def test_wide_signal_address_overlap():
    """
    Test that address conflicts are detected when a wide signal overlaps
    with another register.
    
    A 64-bit signal at 0x00 occupies 0x00-0x07 (2 registers).
    If another register is placed at 0x04, it should conflict.
    
    Returns:
        bool: True if test passes (conflict detected), False otherwise
    """
    print()
    print("=" * 70)
    print("WIDE SIGNAL ADDRESS OVERLAP TEST")
    print("=" * 70)
    print()
    
    # Create VHDL with wide signal overlap
    overlap_vhdl = '''
library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity wide_overlap_test is
    port (clk : in std_logic);
end entity;

architecture rtl of wide_overlap_test is
    -- 64-bit signal occupies 0x00-0x03 (REG0) and 0x04-0x07 (REG1)
    signal wide_reg : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x00
    -- This 32-bit register at 0x04 conflicts with wide_reg's second chunk
    signal conflict_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04
begin
end architecture;
'''
    
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        vhdl_file = os.path.join(temp_dir, "wide_overlap_test.vhd")
        with open(vhdl_file, 'w') as f:
            f.write(overlap_vhdl)
        
        axion = AxionHDL()
        axion.add_src(temp_dir)
        axion.set_output_dir(os.path.join(temp_dir, "output"))
        
        try:
            axion.analyze()
            print("TEST FAILED: Wide signal overlap was not detected!")
            return False
        except AddressConflictError as e:
            print("Wide signal address overlap correctly detected!")
            print()
            print("Error details (abbreviated):")
            # Print first few lines of error
            error_lines = str(e).split('\n')[:10]
            for line in error_lines:
                print(line)
            print("...")
            print()
            print("TEST PASSED")
            return True
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            return False


def main():
    """Run all address conflict tests."""
    print()
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "    AXION-HDL ADDRESS CONFLICT DETECTION TEST SUITE".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print()
    
    results = []
    
    # Test 1: Basic address conflict detection
    results.append(("Basic Address Conflict Detection", test_address_conflict_detection()))
    
    # Test 2: No false positives
    results.append(("No Conflict With Unique Addresses", test_no_conflict_when_addresses_differ()))
    
    # Test 3: Wide signal overlap detection
    results.append(("Wide Signal Address Overlap", test_wide_signal_address_overlap()))
    
    # Summary
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print()
    
    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        symbol = "✓" if passed else "✗"
        print(f"  {symbol} {test_name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    print("-" * 70)
    if all_passed:
        print("ALL TESTS PASSED")
        print("-" * 70)
        return 0
    else:
        print("SOME TESTS FAILED")
        print("-" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
