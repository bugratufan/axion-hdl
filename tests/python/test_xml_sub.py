import sys
import os
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from axion_hdl.xml_input_parser import XMLInputParser

class TestXMLSubregisters(unittest.TestCase):
    def setUp(self):
        self.parser = XMLInputParser()
        self.xml_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '../xml/subregister_test.xml')
        )

    def test_xml_parsing(self):
        """Test that XML parser correctly handles subregisters and defaults."""
        
        # Parse the file
        module = self.parser.parse_file(self.xml_path)
        self.assertIsNotNone(module)
        
        print(f"DEBUG: Keys in module: {module.keys()}")
        if 'packed_registers' in module:
            print(f"DEBUG: Packed registers found: {len(module['packed_registers'])}")
            for pr in module['packed_registers']:
                print(f"  Packed Reg: {pr['name']} (Default: 0x{pr.get('default_value', 0):X})")
                for f in pr['fields']:
                    print(f"    Field: {f['name']} [{f['bit_high']}:{f['bit_low']}] Default: {f['default_value']}")
        
        # Verify packed_registers key exists
        self.assertIn('packed_registers', module)
        self.assertEqual(len(module['packed_registers']), 2)
        
        # Verify status_reg (RO)
        status_reg = next((r for r in module['packed_registers'] if r['name'] == 'status_reg'), None)
        self.assertIsNotNone(status_reg)
        self.assertEqual(status_reg['access_mode'], 'RO')
        self.assertEqual(len(status_reg['fields']), 5)
        
        # Verify fields in status_reg
        ready = next((f for f in status_reg['fields'] if f['name'] == 'ready'), None)
        self.assertIsNotNone(ready)
        self.assertEqual(ready['bit_low'], 0)
        self.assertEqual(ready['width'], 1)
        
        count = next((f for f in status_reg['fields'] if f['name'] == 'count'), None)
        self.assertIsNotNone(count)
        self.assertEqual(count['bit_low'], 8)
        self.assertEqual(count['width'], 8)
        
        # Verify control_reg (RW) with defaults
        control_reg = next((r for r in module['packed_registers'] if r['name'] == 'control_reg'), None)
        self.assertIsNotNone(control_reg)
        self.assertEqual(control_reg['access_mode'], 'RW')
        
        # Verify defaults
        # enable: bit 0, default 1
        # mode: bit 1, default 0
        # irq_mask: bits 7:4, default 0xF (15)
        # timeout: bits 15:8, default 100
        
        # Combined default calculation:
        # enable   (1) << 0  = 0x01
        # mode     (0) << 1  = 0x00
        # irq_mask (15)<< 4  = 0xF0
        # timeout  (100)<<8  = 0x6400
        # Total              = 0x64F1
        
        self.assertEqual(control_reg['default_value'], 0x64F1)
        
        enable = next((f for f in control_reg['fields'] if f['name'] == 'enable'), None)
        self.assertEqual(enable['default_value'], 1)
        
        timeout = next((f for f in control_reg['fields'] if f['name'] == 'timeout'), None)
        self.assertEqual(timeout['default_value'], 100)

if __name__ == '__main__':
    unittest.main()
