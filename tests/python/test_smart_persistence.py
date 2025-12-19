
import pytest
from axion_hdl.source_modifier import SourceModifier

class MockAxion:
    def __init__(self):
        self.analyzed_modules = []

def test_generate_axion_tag_smart_persistence():
    modifier = SourceModifier(MockAxion())
    
    # Case 1: Manual Address -> Should write ADDR
    reg_manual = {
        'name': 'control_reg',
        'access': 'RW',
        'address': '0x14', 
        'manual_address': True
    }
    tag_manual = modifier._generate_axion_tag(reg_manual)
    assert "ADDR=0x14" in tag_manual
    
    # Case 2: Auto Address (No manual flag) -> Should NOT write ADDR (assuming new)
    reg_auto = {
        'name': 'status_reg',
        'access': 'RO',
        'address': '0x18',
        'manual_address': False
    }
    tag_auto = modifier._generate_axion_tag(reg_auto)
    assert "ADDR=" not in tag_auto
    
    # Case 3: Auto Address but Existing Tag had ADDR -> Should Preserve
    reg_preserve = {
        'name': 'config_reg',
        'access': 'RW',
        'address': '0x20',
        'manual_address': False
    }
    existing_tag = "-- @axion RW ADDR=0x20"
    tag_preserve = modifier._generate_axion_tag(reg_preserve, existing_tag_content=existing_tag)
    assert "ADDR=0x20" in tag_preserve

    # Case 4: Manual Address override Existing -> Should update ADDR
    reg_override = {
        'name': 'timer_reg',
        'access': 'RW',
        'address': '0x40', # Changed from 0x30
        'manual_address': True
    }
    existing_tag_override = "-- @axion RW ADDR=0x30"
    tag_override = modifier._generate_axion_tag(reg_override, existing_tag_content=existing_tag_override)
    assert "ADDR=0x40" in tag_override
    assert "ADDR=0x30" not in tag_override

if __name__ == "__main__":
    # Quick self-test if run directly
    test_generate_axion_tag_smart_persistence()
    print("All tests passed!")
