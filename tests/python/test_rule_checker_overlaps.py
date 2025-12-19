import pytest
from axion_hdl.rule_checker import RuleChecker

def test_check_address_overlaps_double_addition():
    """
    Verify that rule checker does not double-add base address.
    
    Scenario:
    Module A: Base 0x1000. Reg at offset 0. Absolute Addr 0x1000.
    Module B: Base 0x2000. Reg at offset 0. Absolute Addr 0x2000.
    
    If RuleChecker adds Base to Absolute, Module A's Reg would range:
    Start: 0x1000? No, check_address_overlaps uses base_addr as start of module range.
    Endpoint calculation: base_addr + address_int + size
    If address_int is 0x1000 (absolute), then end = 0x1000 + 0x1000 + 4 = 0x2004.
    
    Module A range would be detected as 0x1000 - 0x2004.
    Module B starts at 0x2000.
    So they would essentially overlap because Module A's calculated end is pushed way out.
    """
    
    checker = RuleChecker()
    
    modules = [
        {
            'name': 'mod_a',
            'base_address': 0x1000,
            'registers': [
                {
                    'reg_name': 'reg_a',
                    'address_int': 0x1000, # Absolute address (Base + 0)
                    'width': 32
                }
            ]
        },
        {
            'name': 'mod_b',
            'base_address': 0x2000,
            'registers': [
                {
                    'reg_name': 'reg_b',
                    'address_int': 0x2000, # Absolute address (Base + 0)
                    'width': 32
                }
            ]
        }
    ]
    
    # Run checks
    checker.check_address_overlaps(modules)
    
    # There should conform NO errors. 0x1000-0x1003 and 0x2000-0x2003 are far apart.
    # If bug exists, Mod A end will be 0x2004, causing overlap with Mod B (0x2000).
    
    has_overlap_error = False
    for err in checker.errors:
        if err['type'] == "Address Overlap":
            has_overlap_error = True
            print(f"DEBUG: Found overlap error: {err['msg']}")
            
    assert not has_overlap_error, "Found unexpected address overlap! Double base address addition likely."

if __name__ == "__main__":
    test_check_address_overlaps_double_addition()
