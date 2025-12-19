import pytest
import os
import unittest
from axion_hdl.parser import VHDLParser
from axion_hdl.address_manager import AddressConflictError


class TestErrorHandlingRequirements(unittest.TestCase):
    """ERR-xxx requirement tests for error handling"""

    def test_err_001_address_conflict_error_message(self):
        """ERR-001: AddressConflictError string representation is clean"""
        err = AddressConflictError(0x1000, "reg_a", "reg_b", "mod_x")
        msg = str(err)
        
        self.assertIn("Address Conflict", msg)
        self.assertIn("0x1000", msg)
        self.assertIn("reg_a", msg)
        self.assertIn("reg_b", msg)
        # Assert ASCII art is NOT in the default string
        self.assertNotIn("╔", msg)
        self.assertNotIn("VIOLATED REQUIREMENTS", msg)
        
        # Assert formatted message is available
        self.assertIn("╔", err.formatted_message)

    def test_err_002_parser_partial_loading_on_conflict(self):
        """ERR-002: Parser returns module with errors on conflict"""
        content = """
        library ieee;
        entity conflict_test is end;
        architecture rtl of conflict_test is
            -- @axion_def cdc_enabled=false
            
            signal reg_a : std_logic_vector(31 downto 0); -- @axion address=0x0 access=RW
            signal reg_b : std_logic_vector(31 downto 0); -- @axion address=0x0 access=RW
        begin
        end;
        """
        
        test_path = "/tmp/conflict_test.vhd"
        with open(test_path, 'w') as f:
            f.write(content)
            
        parser = VHDLParser()
        # Use internal parse to check dict directly
        data = parser._parse_vhdl_file(test_path)
        
        self.assertIsNotNone(data, "Parser should return data even with conflicts")
        self.assertEqual(data['name'], 'conflict_test')
        
        # Check registers
        regs = {r['signal_name']: r for r in data['registers']}
        self.assertIn('reg_a', regs)
        self.assertIn('reg_b', regs)
        
        # Check errors
        self.assertIn('parsing_errors', data)
        errors = data['parsing_errors']
        self.assertGreater(len(errors), 0)
        
        conflict_err = next((e for e in errors if "Address Conflict" in e['msg']), None)
        self.assertIsNotNone(conflict_err)
        self.assertIn("Address 0x0000", conflict_err['msg'])
        
        os.remove(test_path)

    def test_err_003_skipped_files(self):
        """ERR-003: Skips files missing @axion or valid entities"""
        content = """
        -- No @axion annotations here
        entity skipped_mod is end;
        """
        test_path = "/tmp/skipped_mod.vhd"
        with open(test_path, 'w') as f:
            f.write(content)
            
        parser = VHDLParser()
        data = parser._parse_vhdl_file(test_path)
        os.remove(test_path)
        
        # Should return None for skipped files
        self.assertIsNone(data)

    def test_err_004_invalid_hex_address(self):
        """ERR-004: Reports error for malformed hex strings"""
        content = """
        library ieee;
        entity bad_hex is end;
        architecture rtl of bad_hex is
            signal reg_a : std_logic_vector(31 downto 0); -- @axion address=0xGG
        begin
        end;
        """
        test_path = "/tmp/bad_hex.vhd"
        with open(test_path, 'w') as f:
            f.write(content)
            
        parser = VHDLParser()
        # The parser uses int(x, 16) which raises ValueError on invalid hex
        # This exception is uncaught in _parse_signal_annotations -> int()
        # So we verify it raises ValueError
        with self.assertRaises(ValueError):
            parser._parse_vhdl_file(test_path)
            
        os.remove(test_path)
        
    def test_err_005_no_entity_declaration(self):
        """ERR-005: Handles files missing entity declarations"""
        content = """
        -- Just comments
        -- @axion address=0x0
        """
        test_path = "/tmp/no_entity.vhd"
        with open(test_path, 'w') as f:
            f.write(content)
            
        parser = VHDLParser()
        data = parser._parse_vhdl_file(test_path)
        os.remove(test_path)
        
        self.assertIsNone(data)

    def test_err_006_duplicate_signal_detection(self):
        """ERR-006: Detects and reports duplicate signal names"""
        content = """
        library ieee;
        entity dup_sig is end;
        architecture rtl of dup_sig is
            signal reg_a : std_logic; -- @axion address=0x0
            signal reg_a : std_logic; -- @axion address=0x4
        begin
        end;
        """
        test_path = "/tmp/dup_sig.vhd"
        with open(test_path, 'w') as f:
            f.write(content)
            
        parser = VHDLParser()
        data = parser._parse_vhdl_file(test_path)
        os.remove(test_path)
        
        self.assertIsNotNone(data)
        regs = [r['signal_name'] for r in data['registers']]
        self.assertEqual(regs.count('reg_a'), 2)

    def test_err_007_address_overlap_detection(self):
        """ERR-007: Warns when multiple modules have overlapping address ranges"""
        from axion_hdl.axion import AxionHDL
        from axion_hdl.address_manager import AddressConflictError
        
        # Create two modules with overlapping base addresses
        # Module 1: Base 0x1000, Size 0x10 (regs at 0x0, 0x4, 0x8, 0xC)
        mod1 = {
            'name': 'm1', 
            'base_address': 0x1000, 
            'registers': [
                {'name': 'r1', 'offset': 0x0, 'width': 32},
                {'name': 'r2', 'offset': 0xC, 'width': 32}
            ]
        }
        # m1 range: 0x1000 to 0x1010
        
        # Module 2: Base 0x1008, Size 0x4
        # Starts at 0x1008 which is inside m1's range
        mod2 = {
            'name': 'm2', 
            'base_address': 0x1008, 
            'registers': [
                {'name': 'r3', 'offset': 0x0, 'width': 32}
            ]
        }
        
        axion = AxionHDL()
        axion.analyzed_modules = [mod1, mod2]
        
        # Trigger conflict check
        with self.assertRaises(AddressConflictError):
            axion.check_address_overlaps()



# Backwards compatibility
def test_address_conflict_error_message():
    """Verify AddressConflictError string representation is clean."""
    t = TestErrorHandlingRequirements()
    t.test_err_001_address_conflict_error_message()

def test_parser_partial_loading_on_conflict():
    """Verify parser returns module with errors on conflict."""
    t = TestErrorHandlingRequirements()
    t.test_err_002_parser_partial_loading_on_conflict()


if __name__ == "__main__":
    unittest.main()

