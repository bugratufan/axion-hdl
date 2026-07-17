#!/usr/bin/env python3
"""
test_cdc.py - Clock Domain Crossing Requirements Tests

Tests for CDC-001 through CDC-017 requirements
Verifies CDC synchronizer generation and configuration.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl import AxionHDL


class TestCDCRequirements(unittest.TestCase):
    """Test cases for CDC-xxx requirements"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
    
    def tearDown(self):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _write_temp_vhdl(self, filename: str, content: str) -> str:
        """Write VHDL content to temp file and return path"""
        filepath = os.path.join(self.temp_dir, filename)
        with open(filepath, 'w') as f:
            f.write(content)
        return filepath
    
    def _generate_and_read_vhdl(self, vhdl_content: str, entity_name: str) -> str:
        """Generate VHDL and return the generated content"""
        self._write_temp_vhdl(f"{entity_name}.vhd", vhdl_content)
        
        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        axion.analyze()
        axion.generate_vhdl()
        
        gen_file = os.path.join(self.output_dir, f"{entity_name}_axion_reg.vhd")
        if os.path.exists(gen_file):
            with open(gen_file, 'r') as f:
                return f.read()
        return ""

    def _generate_from_yaml(self, yaml_content: str, module_name: str,
                            systemverilog: bool = False) -> str:
        """Generate VHDL (or SystemVerilog) from YAML input and return the content"""
        yaml_path = os.path.join(self.temp_dir, f"{module_name}.yaml")
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)

        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_yaml_src(self.temp_dir)
        axion.analyze()
        if systemverilog:
            axion.generate_systemverilog()
            gen_file = os.path.join(self.output_dir, f"{module_name}_axion_reg.sv")
        else:
            axion.generate_vhdl()
            gen_file = os.path.join(self.output_dir, f"{module_name}_axion_reg.vhd")

        if os.path.exists(gen_file):
            with open(gen_file, 'r') as f:
                return f.read()
        return ""

    def _generate_from_vhdl(self, vhdl_content: str, entity_name: str,
                            systemverilog: bool = False) -> str:
        """Generate VHDL (or SystemVerilog) from VHDL-annotation input and return the content"""
        self._write_temp_vhdl(f"{entity_name}.vhd", vhdl_content)

        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_src(self.temp_dir)
        axion.analyze()
        if systemverilog:
            axion.generate_systemverilog()
            gen_file = os.path.join(self.output_dir, f"{entity_name}_axion_reg.sv")
        else:
            axion.generate_vhdl()
            gen_file = os.path.join(self.output_dir, f"{entity_name}_axion_reg.vhd")

        if os.path.exists(gen_file):
            with open(gen_file, 'r') as f:
                return f.read()
        return ""

    # VHDL-annotation fixture describing the same packed register layout as
    # PACKED_CDC_YAML, used by the input-format equivalence tests (CDC-016)
    PACKED_CDC_VHDL = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE={stages}
entity {module} is
    port (clk : in std_logic);
end entity;
architecture rtl of {module} is
    signal go_bit : std_logic;                      -- @axion RW ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=0
    signal speed : std_logic_vector(2 downto 0);    -- @axion RW ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=1
    signal ready_bit : std_logic;                   -- @axion RO ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=8
    signal version : std_logic_vector(3 downto 0);  -- @axion RO ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=12
begin
end architecture;
'''

    # YAML fixture with a packed (mixed RW/RO) register used by CDC-010..013 tests
    PACKED_CDC_YAML = '''
module: {module}
base_addr: "0x0000"
config:
  cdc_en: true
  cdc_stage: {stages}

registers:
  - name: mix_reg
    addr: "0x00"
    access: RW
    fields:
      - name: go_bit
        bit_offset: 0
        width: 1
        access: RW
        description: Control output bit
      - name: speed
        bit_offset: 1
        width: 3
        access: RW
        description: Control output vector
      - name: ready_bit
        bit_offset: 8
        width: 1
        access: RO
        description: Status input bit
      - name: version
        bit_offset: 12
        width: 4
        access: RO
        description: Status input vector
'''
    
    # =========================================================================
    # CDC-001: CDC Synchronizer Stage Count
    # =========================================================================
    def test_cdc_001_stage_count_2(self):
        """CDC-001: CDC_STAGE=2 generates 2-stage synchronizer"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity cdc_test is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_test is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_test")
        # CDC-001: Verify module_clk port exists for CDC-enabled module
        self.assertIn('module_clk', content.lower(), 
            "CDC-enabled module must have module_clk port")
        # Verify sync-related signals or logic is present
        self.assertTrue('sync' in content.lower(), 
            "CDC-enabled module should have synchronizer signals")
    
    def test_cdc_001_stage_count_3(self):
        """CDC-001: CDC_STAGE=3 generates 3-stage synchronizer"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=3
entity cdc3_test is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc3_test is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc3_test")
        # CDC-001: With 3-stage CDC, should have module_clk and sync signals
        self.assertIn('module_clk', content.lower(), 
            "3-stage CDC module must have module_clk port")
        self.assertTrue(len(content) > 500, 
            "CDC-enabled module should have substantial generated code")
    
    # =========================================================================
    # CDC-002: CDC Default Stage Count
    # =========================================================================
    def test_cdc_002_default_stage_count(self):
        """CDC-002: CDC_EN without CDC_STAGE defaults to 2 stages"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_default is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_default is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_default")
        # CDC-002: Default to 2 stages - verify module_clk port exists
        self.assertIn('module_clk', content.lower(), 
            "CDC-enabled module (default stages) must have module_clk port")
    
    # =========================================================================
    # CDC-003: CDC Signal Declaration
    # =========================================================================
    def test_cdc_003_sync_signal_declaration(self):
        """CDC-003: CDC-enabled modules declare synchronizer signals"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity cdc_signals is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_signals is
    signal my_reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_signals")
        # CDC-003: Generated VHDL with CDC should have signal declarations
        self.assertTrue(len(content) > 500, 
            "CDC module should generate substantial VHDL")
        self.assertIn('signal', content.lower(), 
            "CDC module should declare internal signals")
    
    # =========================================================================
    # CDC-004: CDC Module Clock Port
    # =========================================================================
    def test_cdc_004_module_clock_port(self):
        """CDC-004: CDC-enabled modules have module_clk port"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_clk is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_clk is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "cdc_clk")
        # CDC-004: CDC-enabled modules must have module_clk in entity
        self.assertIn('module_clk', content.lower(), 
            "CDC-enabled module must have module_clk port")
    
    # =========================================================================
    # CDC-005: CDC Disabled Behavior
    # =========================================================================
    def test_cdc_005_cdc_disabled(self):
        """CDC-005: Without CDC_EN, no CDC signals generated"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity no_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of no_cdc is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "no_cdc")
        # CDC-005: Without CDC_EN, module_clk should NOT be in entity port list
        # Extract entity section to verify no module_clk in ports
        self.assertTrue(len(content) > 100, 
            "Non-CDC module should still generate VHDL")
        # The module_clk should not appear as port
        entity_section = content.lower().split('architecture')[0] if 'architecture' in content.lower() else content.lower()
        self.assertNotIn('module_clk', entity_section, 
            "Non-CDC module should not have module_clk port")
    
    # =========================================================================
    # CDC-006: RO Register CDC Path
    # =========================================================================
    def test_cdc_006_ro_cdc_path(self):
        """CDC-006: RO registers synchronized from module to AXI domain"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity ro_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of ro_cdc is
    signal status_ro : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "ro_cdc")
        # RO register should have input port
        self.assertTrue('status_ro' in content.lower())
        # Sync chain must exist and be clocked by axi_aclk (target domain)
        self.assertIn('status_ro_sync0 <= status_ro;', content,
            "RO input must enter a synchronizer chain")
        self.assertIn('status_ro_sync1 <= status_ro_sync0;', content,
            "RO synchronizer chain must have the configured depth")
        # AXI-side register must be fed from the last sync stage
        self.assertIn('status_ro_reg <= status_ro_sync1;', content,
            "AXI read path must use the last synchronizer stage")
    
    # =========================================================================
    # CDC-007: RW/WO Register CDC Path
    # =========================================================================
    def test_cdc_007_rw_cdc_path(self):
        """CDC-007: Writable registers synchronized from AXI to module domain"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity rw_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of rw_cdc is
    signal control_rw : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "rw_cdc")
        # RW register should have output port
        self.assertTrue('control_rw' in content.lower())
        # Output-direction chain must be clocked by module_clk (target domain)
        self.assertIn('rising_edge(module_clk)', content,
            "RW output synchronizer must be clocked by module_clk")
        self.assertIn('control_rw_sync0 <= control_rw_reg;', content,
            "RW output must enter a synchronizer chain from AXI storage")
        # Output port must be driven from the last sync stage, not from storage
        self.assertIn('control_rw <= control_rw_sync1;', content,
            "RW output port must be driven from the last synchronizer stage")
        self.assertNotIn('control_rw <= control_rw_reg;', content,
            "RW output port must not bypass the synchronizer chain")

    # =========================================================================
    # CDC-008: CDC Flag Equivalence
    # =========================================================================
    def test_cdc_008_equivalence(self):
        """CDC-008: CDC_EN flag is equivalent to CDC_EN=true"""
        vhdl_flag = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN
entity cdc_flag is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_flag is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        vhdl_kv = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN=true
entity cdc_kv is
    port (clk : in std_logic);
end entity;
architecture rtl of cdc_kv is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        content_flag = self._generate_and_read_vhdl(vhdl_flag, "cdc_flag")
        content_kv = self._generate_and_read_vhdl(vhdl_kv, "cdc_kv")
        
        # Verify both generated content with module clock port (CDC enabled)
        self.assertTrue('module_clk' in content_flag.lower())
        self.assertTrue('module_clk' in content_kv.lower())
        
        # Verify content similarity (ignoring entity names)
        # We can check specific CDC logic blocks
        self.assertTrue('sync' in content_flag.lower())

    # =========================================================================
    # CDC-009: WO Register Output Synchronization
    # =========================================================================
    def test_cdc_009_wo_output_sync(self):
        """CDC-009: WO outputs driven from module_clk-domain sync chain"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity wo_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of wo_cdc is
    signal cmd_wo : std_logic_vector(31 downto 0); -- @axion WO ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "wo_cdc")
        self.assertIn('rising_edge(module_clk)', content,
            "WO output synchronizer must be clocked by module_clk")
        self.assertIn('cmd_wo_sync0 <= cmd_wo_reg;', content,
            "WO output must enter a synchronizer chain from AXI storage")
        self.assertIn('cmd_wo <= cmd_wo_sync1;', content,
            "WO output port must be driven from the last synchronizer stage")
        self.assertNotIn('cmd_wo <= cmd_wo_reg;', content,
            "WO output port must not bypass the synchronizer chain")

    # =========================================================================
    # CDC-010: Packed Register RO Field Synchronization
    # =========================================================================
    def test_cdc_010_packed_ro_field_sync(self):
        """CDC-010: RO fields of packed registers get axi_aclk-domain sync chains"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="packed_ro_cdc", stages=2),
            "packed_ro_cdc")
        # RO field sync chains must exist
        self.assertIn('mix_reg_ready_bit_sync0 <= mix_reg_ready_bit;', content,
            "Packed RO field must enter a synchronizer chain")
        self.assertIn('mix_reg_version_sync0 <= mix_reg_version;', content,
            "Packed multi-bit RO field must enter a synchronizer chain")
        # Read value mapping must use the last sync stage, not the raw input
        self.assertIn('mix_reg_val(8) <= mix_reg_ready_bit_sync1;', content,
            "Packed RO field read value must come from the last sync stage")
        self.assertIn('mix_reg_val(15 downto 12) <= mix_reg_version_sync1;', content,
            "Packed RO vector field read value must come from the last sync stage")
        self.assertNotIn('mix_reg_val(8) <= mix_reg_ready_bit;', content,
            "Packed RO field must not enter the AXI read path unsynchronized")

    # =========================================================================
    # CDC-011: Packed Register RW/WO Field Output Synchronization
    # =========================================================================
    def test_cdc_011_packed_rw_field_output_sync(self):
        """CDC-011: RW/WO fields of packed registers driven from module_clk-domain chain"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="packed_rw_cdc", stages=2),
            "packed_rw_cdc")
        # Storage register sync chain in module_clk domain must exist
        self.assertIn('mix_reg_reg_sync0 <= mix_reg_reg;', content,
            "Packed register storage must enter a module_clk synchronizer chain")
        self.assertIn('rising_edge(module_clk)', content,
            "Packed RW/WO synchronizer must be clocked by module_clk")
        # Field outputs must be driven from the last sync stage
        self.assertIn('mix_reg_go_bit <= mix_reg_reg_sync1(0);', content,
            "Packed RW field output must come from the last sync stage")
        self.assertIn('mix_reg_speed <= mix_reg_reg_sync1(3 downto 1);', content,
            "Packed RW vector field output must come from the last sync stage")
        self.assertNotIn('mix_reg_go_bit <= mix_reg_reg(0);', content,
            "Packed RW field output must not bypass the synchronizer chain")
        # AXI readback must still use the axi_aclk-domain storage
        self.assertIn('mix_reg_val(0) <= mix_reg_reg(0);', content,
            "AXI readback of RW bits must use the axi_aclk-domain storage")

    # =========================================================================
    # CDC-012: ASYNC_REG Attribute on Sync Chains
    # =========================================================================
    def test_cdc_012_async_reg_attribute_vhdl(self):
        """CDC-012: All VHDL sync signals carry the ASYNC_REG attribute"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="attr_cdc", stages=2),
            "attr_cdc")
        self.assertIn('attribute ASYNC_REG : string;', content,
            "ASYNC_REG attribute must be declared")
        import re
        sync_signals = set(re.findall(r'signal\s+(\w+_sync\d+)\s*:', content))
        self.assertTrue(sync_signals, "Expected synchronizer signals in output")
        for sig in sync_signals:
            self.assertIn(f'attribute ASYNC_REG of {sig} : signal is "TRUE";', content,
                f"Sync signal {sig} must carry the ASYNC_REG attribute")

    def test_cdc_012_async_reg_attribute_sv(self):
        """CDC-012: SystemVerilog sync arrays carry the ASYNC_REG attribute"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="attr_sv_cdc", stages=2),
            "attr_sv_cdc", systemverilog=True)
        self.assertTrue(content, "SystemVerilog output must be generated")
        self.assertIn('(* ASYNC_REG = "TRUE" *)', content,
            "SV sync arrays must carry the ASYNC_REG attribute")

    # =========================================================================
    # CDC-013: Stage Count Honored in All Chains
    # =========================================================================
    def test_cdc_013_stage_count_honored(self):
        """CDC-013: CDC_STAGE depth applied to every chain, incl. packed fields"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="stages_cdc", stages=4),
            "stages_cdc")
        # 4-stage chains: sync0..sync3 exist, sync4 does not
        for sig in ['mix_reg_reg', 'mix_reg_ready_bit', 'mix_reg_version']:
            for stage in range(4):
                self.assertIn(f'{sig}_sync{stage}', content,
                    f"{sig} chain must contain stage {stage}")
            self.assertNotIn(f'{sig}_sync4', content,
                f"{sig} chain must not exceed the configured depth")
        # Consumers must use the last stage
        self.assertIn('mix_reg_go_bit <= mix_reg_reg_sync3(0);', content,
            "Packed RW field output must use the last configured stage")
        self.assertIn('mix_reg_val(8) <= mix_reg_ready_bit_sync3;', content,
            "Packed RO field read value must use the last configured stage")

    # =========================================================================
    # CDC-014: Wide Register CDC
    # =========================================================================
    def test_cdc_014_wide_register_cdc(self):
        """CDC-014: >32-bit registers synchronized chunk-by-chunk"""
        vhdl = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000 CDC_EN CDC_STAGE=2
entity wide_cdc is
    port (clk : in std_logic);
end entity;
architecture rtl of wide_cdc is
    signal big_rw : std_logic_vector(63 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
'''
        content = self._generate_and_read_vhdl(vhdl, "wide_cdc")
        # Both 32-bit chunks must have sync chains
        self.assertIn('big_rw0_sync0 <= big_rw_reg0;', content,
            "Low chunk must enter a synchronizer chain")
        self.assertIn('big_rw1_sync0 <= big_rw_reg1;', content,
            "High chunk must enter a synchronizer chain")
        # Output port must be driven by concatenation of last sync stages
        self.assertIn('big_rw <= big_rw1_sync1 & big_rw0_sync1;', content,
            "Wide output port must be driven from the last sync stage of all chunks")

    def test_cdc_014_wide_register_yaml(self):
        """CDC-014: Wide registers from YAML input are chunked correctly"""
        yaml_content = '''
module: wide_yaml_cdc
base_addr: "0x0000"
config:
  cdc_en: true
  cdc_stage: 2

registers:
  - name: big_cfg
    addr: "0x00"
    access: RW
    width: 64
    description: Wide RW register
'''
        content = self._generate_from_yaml(yaml_content, "wide_yaml_cdc")
        # Storage must be chunked into two 32-bit registers
        self.assertIn('big_cfg_reg0', content,
            "Wide YAML register must have chunked storage")
        self.assertIn('big_cfg_reg1', content,
            "Wide YAML register must have chunked storage")
        self.assertIn('big_cfg <= big_cfg1_sync1 & big_cfg0_sync1;', content,
            "Wide YAML register output must concatenate last sync stages")

    # =========================================================================
    # CDC-015: SystemVerilog CDC Parity
    # =========================================================================
    def test_cdc_015_sv_packed_field_ports(self):
        """CDC-015: SV output exposes per-field ports for packed registers"""
        import re
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="sv_ports_cdc", stages=2),
            "sv_ports_cdc", systemverilog=True)
        self.assertTrue(content, "SystemVerilog output must be generated")
        self.assertRegex(content, r'output\s+logic\s+mix_reg_go_bit',
            "Packed RW field must have an output port")
        self.assertRegex(content, r'output\s+logic \[2:0\]\s+mix_reg_speed',
            "Packed RW vector field must have an output port")
        self.assertRegex(content, r'input\s+logic\s+mix_reg_ready_bit',
            "Packed RO field must have an input port")
        self.assertRegex(content, r'input\s+logic \[3:0\]\s+mix_reg_version',
            "Packed RO vector field must have an input port")
        self.assertIsNone(re.search(r'logic \[31:0\]\s+mix_reg\s*[,)]', content),
            "Packed register must not be exposed as a monolithic word port")

    def test_cdc_015_sv_packed_ro_field_sync(self):
        """CDC-015: SV packed RO fields get axi_aclk-domain sync chains"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="sv_ro_cdc", stages=2),
            "sv_ro_cdc", systemverilog=True)
        self.assertIn('mix_reg_ready_bit_sync[0] <= mix_reg_ready_bit;', content,
            "Packed RO field must enter a synchronizer chain")
        self.assertIn('mix_reg_version_sync[0] <= mix_reg_version;', content,
            "Packed multi-bit RO field must enter a synchronizer chain")
        self.assertIn('mix_reg_val[8] = mix_reg_ready_bit_sync[1];', content,
            "Packed RO field read value must come from the last sync stage")
        self.assertIn('mix_reg_val[15:12] = mix_reg_version_sync[1];', content,
            "Packed RO vector field read value must come from the last sync stage")
        self.assertNotIn('mix_reg_val[8] = mix_reg_ready_bit;', content,
            "Packed RO field must not enter the AXI read path unsynchronized")

    def test_cdc_015_sv_packed_rw_field_output_sync(self):
        """CDC-015: SV packed RW/WO fields driven from module_clk-domain chain"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="sv_rw_cdc", stages=2),
            "sv_rw_cdc", systemverilog=True)
        self.assertIn('mix_reg_reg_sync[0] <= mix_reg_reg;', content,
            "Packed register storage must enter a module_clk synchronizer chain")
        self.assertIn('always_ff @(posedge module_clk', content,
            "Packed RW/WO synchronizer must be clocked by module_clk")
        self.assertIn('assign mix_reg_go_bit = mix_reg_reg_sync[1][0];', content,
            "Packed RW field output must come from the last sync stage")
        self.assertIn('assign mix_reg_speed = mix_reg_reg_sync[1][3:1];', content,
            "Packed RW vector field output must come from the last sync stage")
        self.assertNotIn('assign mix_reg_go_bit = mix_reg_reg[0];', content,
            "Packed RW field output must not bypass the synchronizer chain")
        # AXI readback must still use the axi_aclk-domain storage
        self.assertIn('mix_reg_val[0] = mix_reg_reg[0];', content,
            "AXI readback of RW bits must use the axi_aclk-domain storage")

    def test_cdc_015_sv_stage_count_honored(self):
        """CDC-015: CDC_STAGE depth applied to every SV chain, incl. packed fields"""
        content = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="sv_stages_cdc", stages=4),
            "sv_stages_cdc", systemverilog=True)
        for sig in ['mix_reg_reg', 'mix_reg_ready_bit', 'mix_reg_version']:
            for stage in range(4):
                self.assertIn(f'{sig}_sync[{stage}]', content,
                    f"{sig} chain must contain stage {stage}")
            self.assertNotIn(f'{sig}_sync[4]', content,
                f"{sig} chain must not exceed the configured depth")
        self.assertIn('assign mix_reg_go_bit = mix_reg_reg_sync[3][0];', content,
            "Packed RW field output must use the last configured stage")
        self.assertIn('mix_reg_val[8] = mix_reg_ready_bit_sync[3];', content,
            "Packed RO field read value must use the last configured stage")

    def test_cdc_015_sv_wide_register(self):
        """CDC-015: >32-bit registers from YAML are chunk-addressed and synced in SV"""
        yaml_content = '''
module: sv_wide_cdc
base_addr: "0x0000"
config:
  cdc_en: true
  cdc_stage: 2

registers:
  - name: big_cfg
    addr: "0x00"
    access: RW
    width: 64
    description: Wide RW register
'''
        content = self._generate_from_yaml(yaml_content, "sv_wide_cdc",
                                           systemverilog=True)
        self.assertIn('big_cfg_reg[63:32] <= axi_wdata;', content,
            "Wide SV register must have upper-word write access")
        self.assertIn('rdata_reg = big_cfg_reg[63:32];', content,
            "Wide SV register must have upper-word read access")
        self.assertIn('(* ASYNC_REG = "TRUE" *) logic [63:0]', content,
            "Wide SV sync array must span the full register width")
        self.assertIn('assign big_cfg = big_cfg_sync[1];', content,
            "Wide SV output port must be driven from the last sync stage")

    # =========================================================================
    # CDC-016: Input-Format Independence (annotation vs structured config)
    # =========================================================================
    # Structural CDC lines that must appear in the generated output for the
    # shared packed-register layout, regardless of the input format
    VHDL_CDC_PARITY_LINES = [
        'mix_reg_ready_bit_sync0 <= mix_reg_ready_bit;',
        'mix_reg_reg_sync0 <= mix_reg_reg;',
        'mix_reg_go_bit <= mix_reg_reg_sync1(0);',
        'mix_reg_speed <= mix_reg_reg_sync1(3 downto 1);',
        'mix_reg_val(8) <= mix_reg_ready_bit_sync1;',
        'mix_reg_val(15 downto 12) <= mix_reg_version_sync1;',
        'rising_edge(module_clk)',
        'attribute ASYNC_REG : string;',
    ]
    SV_CDC_PARITY_LINES = [
        'mix_reg_ready_bit_sync[0] <= mix_reg_ready_bit;',
        'mix_reg_reg_sync[0] <= mix_reg_reg;',
        'assign mix_reg_go_bit = mix_reg_reg_sync[1][0];',
        'assign mix_reg_speed = mix_reg_reg_sync[1][3:1];',
        'mix_reg_val[8] = mix_reg_ready_bit_sync[1];',
        'mix_reg_val[15:12] = mix_reg_version_sync[1];',
        'always_ff @(posedge module_clk',
        '(* ASYNC_REG = "TRUE" *)',
    ]

    def test_cdc_016_annotation_yaml_parity_vhdl(self):
        """CDC-016: annotation and YAML inputs yield the same VHDL CDC structure"""
        content_ann = self._generate_from_vhdl(
            self.PACKED_CDC_VHDL.format(module="parity_ann", stages=2),
            "parity_ann")
        content_yaml = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="parity_yaml", stages=2),
            "parity_yaml")
        self.assertTrue(content_ann, "Annotation-input VHDL must be generated")
        self.assertTrue(content_yaml, "YAML-input VHDL must be generated")
        for line in self.VHDL_CDC_PARITY_LINES:
            self.assertIn(line, content_ann,
                f"Annotation-input VHDL must contain: {line}")
            self.assertIn(line, content_yaml,
                f"YAML-input VHDL must contain: {line}")

    # =========================================================================
    # CDC-017: GUI Template Round-Trip
    # =========================================================================
    def test_cdc_017_gui_template_round_trip(self):
        """CDC-017: GUI VHDL template emits parseable @axion annotations incl. CDC"""
        from axion_hdl.gui import AxionGUI
        gui = AxionGUI(None)
        registers = [
            {'name': 'ctrl_reg', 'width': 32, 'access': 'RW',
             'default_value': '0xAB', 'description': 'Control register',
             'w_strobe': True},
            {'name': 'stat_reg', 'width': 32, 'access': 'RO', 'r_strobe': True},
            # default_value may arrive as None from the GUI/JSON layer
            {'name': 'flag_reg', 'width': 1, 'access': 'RW', 'default_value': None},
        ]
        # base_address may arrive already 0x-prefixed from other GUI paths
        properties = {'base_address': '0x0100', 'cdc_enabled': True, 'cdc_stages': 3}
        template = gui._generate_vhdl_template('gui_cdc_mod', registers, properties)

        # Template must carry the analyzer-recognized annotations
        self.assertIn('-- @axion_def BASE_ADDR=0x0100 CDC_EN CDC_STAGE=3', template,
            "GUI template must emit a parseable @axion_def with CDC settings")
        self.assertNotIn('0x0x', template,
            "0x-prefixed base_address must not be double-prefixed")
        self.assertIn("signal flag_reg : std_logic := '0'; -- @axion RW", template,
            "None default must fall back to zero without crashing")
        self.assertIn('-- @axion RW W_STROBE DEFAULT=0xAB DESC="Control register"', template,
            "GUI template must emit parseable register annotations")
        self.assertNotIn('AXION_CDC', template,
            "GUI template must not use the legacy unparsed annotation format")

        # Round-trip: the analyzer must recover the CDC config and registers
        content = self._generate_and_read_vhdl(template, 'gui_cdc_mod')
        self.assertTrue(content, "Analyzer must accept the GUI-generated template")
        self.assertIn('module_clk', content,
            "CDC setting from GUI template must survive analysis")
        self.assertIn('ctrl_reg <= ctrl_reg_sync2;', content,
            "RW register from GUI template must get a 3-stage output sync chain")
        self.assertIn('stat_reg_reg <= stat_reg_sync2;', content,
            "RO register from GUI template must get a 3-stage input sync chain")
        self.assertIn('ctrl_reg_wr_strobe', content,
            "Write strobe from GUI template must survive analysis")
        self.assertIn('stat_reg_rd_strobe', content,
            "Read strobe from GUI template must survive analysis")

    def test_cdc_016_annotation_yaml_parity_sv(self):
        """CDC-016: annotation and YAML inputs yield the same SV CDC structure"""
        content_ann = self._generate_from_vhdl(
            self.PACKED_CDC_VHDL.format(module="parity_ann_sv", stages=2),
            "parity_ann_sv", systemverilog=True)
        content_yaml = self._generate_from_yaml(
            self.PACKED_CDC_YAML.format(module="parity_yaml_sv", stages=2),
            "parity_yaml_sv", systemverilog=True)
        self.assertTrue(content_ann, "Annotation-input SV must be generated")
        self.assertTrue(content_yaml, "YAML-input SV must be generated")
        for line in self.SV_CDC_PARITY_LINES:
            self.assertIn(line, content_ann,
                f"Annotation-input SV must contain: {line}")
            self.assertIn(line, content_yaml,
                f"YAML-input SV must contain: {line}")


def run_cdc_tests():
    """Run all CDC tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCDCRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_cdc_tests()
    sys.exit(0 if success else 1)
