import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock
from axion_hdl.source_modifier import SourceModifier

class TestSmartPreservation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.vhdl_path = os.path.join(self.test_dir, "test_module.vhd")
        
        # Create a sample VHDL file with specific formatting
        with open(self.vhdl_path, 'w') as f:
            f.write("""library IEEE;
use IEEE.std_logic_1164.all;

entity test_module is
end entity;

architecture rtl of test_module is
    -- Existing signal with custom spacing
    -- My custom description
    signal my_reg   : std_logic_vector(31 downto 0) := (others => '0'); -- @axion: access=RW
    
    -- Signal with custom attributes
    signal special_reg : std_logic_vector(31 downto 0) := (others => '0'); -- @axion: access=RW my_flag custom_val=10
begin
end architecture;
""")
        
        # Mock Axion instance
        self.mock_axion = MagicMock()
        self.mock_axion.analyzed_modules = [{
            'name': 'test_module',
            'file': self.vhdl_path,
            'registers': [
                {
                    'reg_name': 'my_reg',
                    'signal_name': 'my_reg',
                    'width': 32,
                    'default_value': 0,
                    'access_mode': 'RW'
                },
                {
                    'reg_name': 'special_reg',
                    'signal_name': 'special_reg',
                    'width': 32,
                    'default_value': 0,
                    'access_mode': 'RW'
                }
            ]
        }]
        
        self.modifier = SourceModifier(self.mock_axion)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_update_metadata_only_obeys_spacing(self):
        """Test that updating only metadata (access) preserves original spacing."""
        new_regs = [{
            'name': 'my_reg',
            'width': 32,
            'default_value': 0,
            'access': 'RO',        # Changed from RW
            'read_strobe': True,   # Added strobe
            'description': 'Updated description',
        }]
        
        content, _ = self.modifier.get_modified_content('test_module', new_regs)
        
        # Check that the signal declaration part is preserved EXACTLY
        expected_signal_part = "    signal my_reg   : std_logic_vector(31 downto 0) := (others => '0');"
        self.assertIn(expected_signal_part, content)
        
        # Check that tag is updated and uses SHORT format
        self.assertIn("-- @axion: RO R_STROBE", content)
        # Check explicit exclusion of access=RO
        self.assertNotIn("access=RO", content)
        
        # Check that description comment is NOT duplicated
        self.assertIn("-- My custom description", content)
        self.assertNotIn("-- Updated description", content)

    def test_update_width_regenerates_line(self):
        """Test that updating structural property (width) regenerates the line."""
        new_regs = [{
            'name': 'my_reg',
            'width': 16,           # Changed from 32
            'default_value': 0,
            'access': 'RW'
        }]
        
        content, _ = self.modifier.get_modified_content('test_module', new_regs)
        self.assertIn("signal my_reg : std_logic_vector(15 downto 0) := (others => '0');", content)

    def test_custom_attribute_retention(self):
        """Test that custom attributes are preserved when updating."""
        new_regs = [{
            'name': 'special_reg',
            'width': 32,
            'default_value': 0,
            'access': 'WO' # Changed Access
        }]
        
        content, _ = self.modifier.get_modified_content('test_module', new_regs)
        
        # Access should be updated
        self.assertIn("WO", content)
        
        # Custom attributes should be retained
        # Note: Order might change depending on dictionary iteration, but they should be present
        self.assertIn("MY_FLAG", content) # Assuming boolean flags are uppercased
        self.assertIn("custom_val=10", content)

if __name__ == '__main__':
    unittest.main()
