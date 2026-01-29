import pytest
import os
from pathlib import Path
from axion_hdl.xml_input_parser import XMLInputParser

def test_xml_subregisters():
    """Test that XML parser correctly handles subregisters and defaults."""
    parser = XMLInputParser()
    xml_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../xml/subregister_test.xml')
    )
    
    module = parser.parse_file(xml_path)
    assert module is not None
    assert 'packed_registers' in module
    assert len(module['packed_registers']) == 2
    
    # 1. Verify status_reg (RO)
    status_reg = next(r for r in module['packed_registers'] if r['name'] == 'status_reg')
    assert status_reg['access_mode'] == 'RO'
    assert len(status_reg['fields']) == 5
    
    ready = next(f for f in status_reg['fields'] if f['name'] == 'ready')
    assert ready['bit_low'] == 0
    assert ready['width'] == 1
    
    # 2. Verify control_reg (RW) with defaults
    control_reg = next(r for r in module['packed_registers'] if r['name'] == 'control_reg')
    assert control_reg['access_mode'] == 'RW'
    
    # Combined default calculation:
    # enable(1)<<0 | mode(0)<<1 | irq_mask(15)<<4 | timeout(100)<<8 = 0x64F1
    assert control_reg['default_value'] == 0x64F1
    
    enable = next(f for f in control_reg['fields'] if f['name'] == 'enable')
    assert enable['default_value'] == 1
    
    timeout = next(f for f in control_reg['fields'] if f['name'] == 'timeout')
    assert timeout['default_value'] == 100
