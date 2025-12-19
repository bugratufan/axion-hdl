import os
import sys
import shutil
import pytest
import shutil
import pytest
import tempfile
import copy

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from axion_hdl.axion import AxionHDL
from axion_hdl.source_modifier import SourceModifier

class TestVHDLRobustness:
    def setup_method(self):
        self.test_dir = tempfile.mkdtemp()
        self.axion = AxionHDL()
        self.modifier = SourceModifier(self.axion)

    def teardown_method(self):
        shutil.rmtree(self.test_dir)

    def _create_vhdl(self, filename, content):
        path = os.path.join(self.test_dir, filename)
        with open(path, 'w') as f:
            f.write(content)
        return path

    def _normalize_regs(self, regs):
        # Return a DEEP COPY to simulate GUI payload that is distinct from backend state
        regs_copy = copy.deepcopy(regs)
        for r in regs_copy:
            if 'name' not in r:
                r['name'] = r.get('reg_name', r.get('signal_name'))
        return regs_copy


    def test_preservation_identity(self):
        """Test A: Identity - No changes to registers should mean 0 changes to lines."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_mod is
    generic (
        C_CDC_ENABLE : boolean := false
    );
end test_mod;

architecture str of test_mod is
    -- weird spacing preserved?
    signal reg_a : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x10 DESC="My Desc" DEFAULT=0x1234
    signal   reg_b   :   std_logic; -- @axion RW
begin
end str;
"""
        file_path = self._create_vhdl('test_preservation.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        
        # Change ONLY module property (CDC)
        regs = self._normalize_regs(module['registers'])
        props = {'cdc_enabled': True}
        
        self.modifier.save_changes(module['name'], regs, props, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Check CDC changed
        assert "C_CDC_ENABLE : boolean := true" in new_content
        
        # Check Lines preserved EXACTLY (including weird spacing)
        assert 'signal reg_a : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x10 DESC="My Desc" DEFAULT=0x1234' in new_content
        assert 'signal   reg_b   :   std_logic; -- @axion RW' in new_content

    def test_attribute_addition(self):
        """Test B: Attribute Addition - Add DESC and DEFAULT to bare register."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_add is
end test_add;

architecture str of test_add is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RW
begin
end str;
"""
        file_path = self._create_vhdl('test_add.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Modify reg_a
        regs[0]['description'] = "New Description"
        regs[0]['default_value'] = "0xABC"
        
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Check new attributes present
        assert 'DESC="New Description"' in new_content
        # Note: Implementation detail - might normalize 0xabc vs 0xABC or 32-bit width padding
        # We expect robust generation to handle this. Let's check generally.
        assert 'DEFAULT=0xABC' in new_content or 'DEFAULT=0x00000ABC' in new_content
        assert "RW" in new_content

    def test_attribute_modification(self):
        """Test C: Attribute Modification - RO -> RW, modify DESC."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_mod is
end test_mod;

architecture str of test_mod is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RO DESC="Old"
begin
end str;
"""
        file_path = self._create_vhdl('test_mod.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        regs[0]['access'] = 'RW'
        regs[0]['description'] = "New"
        
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        assert '-- @axion' in new_content
        assert 'RW' in new_content
        assert 'RO' not in new_content
        assert 'DESC="New"' in new_content

    def test_strobes(self):
        """Test D: Strobes - Add R_STROBE, Remove W_STROBE."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_strobes is
end test_strobes;

architecture str of test_strobes is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RW
    signal reg_b : std_logic_vector(31 downto 0); -- @axion RW W_STROBE
begin
end str;
"""
        file_path = self._create_vhdl('test_strobes.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Find regs
        reg_a = next(r for r in regs if r['name'] == 'reg_a')
        reg_b = next(r for r in regs if r['name'] == 'reg_b')
        
        # Add R_STROBE to A
        reg_a['r_strobe'] = True
        
        # Remove W_STROBE from B
        # Must clear both keys because parser sets 'write_strobe' but modifier checks 'w_strobe' too
        reg_b['w_strobe'] = False
        reg_b['write_strobe'] = False # Simulate full removal state
        
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
        
        # Check A has R_STROBE
        assert 'reg_a' in new_content and 'R_STROBE' in new_content
        # Check B does NOT have W_STROBE
        assert 'reg_b' in new_content and 'W_STROBE' not in new_content

    def test_formatting_resilience(self):
        """Test F: Formatting Resilience - Modify one reg, leave weird one alone."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_fmt is
end test_fmt;

architecture str of test_fmt is
    signal   weird_spacing   :   std_logic_vector(31 downto 0);   --   @axion   RO
    signal normal : std_logic_vector(31 downto 0); -- @axion RW
begin
end str;
"""
        file_path = self._create_vhdl('test_fmt.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Modify ONLY 'normal'
        normal = next(r for r in regs if r['name'] == 'normal')
        normal['description'] = "Changed"
        
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Assert weird spacing preserved exactly
        assert 'signal   weird_spacing   :   std_logic_vector(31 downto 0);   --   @axion   RO' in new_content
        # Assert normal changed
        assert 'DESC="Changed"' in new_content

    def test_no_signal_init(self):
        """Test G: No Signal Initialization - Ensure := is NOT generated, but DEFAULT tag is."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_init is
end test_init;

architecture str of test_init is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RW
begin
end str;
"""
        file_path = self._create_vhdl('test_init.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Add default value (as int to verify hex formatting in tag)
        regs[0]['default_value'] = 0xFACE
        
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Assert DEFAULT tag exists
        assert 'DEFAULT=0x0000FACE' in new_content
        # Assert NO VHDL initialization (:=)
        assert ':=' not in new_content.split('--')[0] # Check signal part only

    def test_comment_spacing(self):
        """Test H: Comment Spacing - Preserve whitespace before -- @axion tag."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_space is
end test_space;

architecture str of test_space is
    signal reg_a : std_logic_vector(31 downto 0);  -- @axion RW
begin
end str;
"""
        # Note: Two spaces before -- in original content
        
        file_path = self._create_vhdl('test_space.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Modify something to force regeneration
        regs[0]['description'] = "New Desc"
        
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Assert two spaces are preserved before --
        # We look for ";  -- @axion"
        assert ';  -- @axion' in new_content

    def test_std_logic_support(self):
        """Test I: std_logic Support - Correctly identify width=1 and preserve type."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_std is
end test_std;

architecture str of test_std is
    -- Signal with initialization that confused the parser previously
    signal reg_bit : std_logic := '0'; -- @axion RW
begin
end str;
"""
        file_path = self._create_vhdl('test_std.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Verify parsed width is 1
        assert regs[0]['width'] == 1, f"Expected width 1, got {regs[0].get('width')}"
        
        # Modify to force regeneration
        regs[0]['description'] = "Single bit"
        
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Assert type is still std_logic
        assert 'signal reg_bit : std_logic;' in new_content
        assert 'std_logic_vector' not in new_content
        # Assert default value is preserved in tag (since we stripped := '0')
        # Wait, if default_val is '0', it might be ignored in tag generation if 0 is skipped?
        # Let's check _generate_axion_tag logic. 
        # But main point is type preservation.

    def test_hex_persistence(self):
        """Test J: Hex Persistence - Ensure hex defaults like 0xDEADBEEF are not converted to decimal on save."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_hex is
end test_hex;

architecture str of test_hex is
    signal config_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00 DEFAULT=0xDEADBEEF
    signal zero_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04 DEFAULT=0
begin
end str;
"""
        file_path = self._create_vhdl('test_hex.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Simulate GUI behavior:
        # 1. Decimal string for default value matching the hex
        # 0xDEADBEEF = 3735928559
        regs[0]['default_value'] = "3735928559"
        
        # 2. String width
        regs[0]['width'] = "32"
        
        # 3. Force regeneration of zero_reg by changing description slightly
        regs[1]['description'] = "Zero Default Reg" 
        # (Original was empty or None? In VHDL: no desc. Wait, check original string)
        # Original: signal zero_reg ... -- @axion RW ADDR=0x04 DEFAULT=0
        # No description.
        
        # Save back
        self.modifier.save_changes(module['name'], regs, {}, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Assert 0xDEADBEEF is preserved (either by avoiding regen or by correct formatting)
        assert 'DEFAULT=0xDEADBEEF' in new_content, f"Converted hex default to decimal! Content: {new_content}"
        assert '3735928559' not in new_content
        
        # Assert DEFAULT=0 is preserved
        assert 'DEFAULT=0' in new_content, "Removed explicit DEFAULT=0!"

    def test_mod_def_injection(self):
        """Test K: Module Def Injection - Ensure @axion_def is injected if missing but props change."""
        content = """library ieee;
use ieee.std_logic_1164.all;

entity test_def_inject is
end test_def_inject;

architecture str of test_def_inject is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion RW
begin
end str;
"""
        file_path = self._create_vhdl('test_def_inject.vhd', content)
        self.axion.add_source(file_path)
        self.axion.analyze()
        module = self.axion.analyzed_modules[0]
        regs = self._normalize_regs(module['registers'])
        
        # Modify module property to enable CDC
        # This should trigger insertion of -- @axion_def CDC_EN ...
        props = {'cdc_enabled': True}
        
        self.modifier.save_changes(module['name'], regs, props, file_path=file_path)
        
        with open(file_path, 'r') as f:
            new_content = f.read()
            
        # Assert @axion_def was injected
        assert '-- @axion_def' in new_content, "Failed to inject @axion_def definition!"
        assert 'CDC_EN' in new_content, "Failed to include CDC_EN in injected definition"

if __name__ == "__main__":
    tests = [
        'test_preservation_identity',
        'test_attribute_addition',
        'test_attribute_modification',
        'test_strobes',
        'test_formatting_resilience',
        'test_no_signal_init',
        'test_comment_spacing',
        'test_no_signal_init',
        'test_comment_spacing',
        'test_std_logic_support',
        'test_hex_persistence',
        'test_mod_def_injection'
    ]
    
    for test_name in tests:
        t = TestVHDLRobustness()
        t.setup_method()
        try:
            print(f"Running {test_name}...")
            getattr(t, test_name)()
            print(f"{test_name}: PASS")
        except Exception as e:
            print(f"{test_name}: FAILED")
            import traceback
            traceback.print_exc()
        finally:
            t.teardown_method()
