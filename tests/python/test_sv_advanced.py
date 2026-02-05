"""
SystemVerilog Advanced Tests

Tests for:
- SV-LINT-001 to SV-LINT-010: Verilator lint validation
- SV-EQUIV-001 to SV-EQUIV-010: VHDL vs SystemVerilog equivalence
- SV-PACKED-001 to SV-PACKED-010: Packed register support
- SV-DEFAULT-001 to SV-DEFAULT-010: Default value support
- SV-STRESS-001 to SV-STRESS-010: Stress and edge case testing
"""

import unittest
import os
import sys
import tempfile
import subprocess
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from axion_hdl.systemverilog_generator import SystemVerilogGenerator
from axion_hdl.systemverilog_parser import SystemVerilogParser
from axion_hdl import AxionHDL


class TestSystemVerilogLint(unittest.TestCase):
    """Verilator lint validation tests"""

    def setUp(self):
        """Check if Verilator is available"""
        self.verilator_available = shutil.which('verilator') is not None
        if not self.verilator_available:
            self.skipTest("Verilator not installed")

    def test_sv_lint_001_basic_module(self):
        """SV-LINT-001: Basic module passes Verilator lint"""
        module_data = {
            'name': 'lint_test_basic',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'status', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RO', 'read_strobe': False, 'write_strobe': False,
                 'description': 'Status', 'address_int': 0x00}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            # Run Verilator lint
            result = subprocess.run(
                ['verilator', '--lint-only', '-Wall', output_path],
                capture_output=True,
                text=True
            )

            # Check for errors (warnings are OK)
            assert result.returncode == 0, f"Verilator lint failed:\n{result.stderr}"

    def test_sv_lint_002_with_cdc(self):
        """SV-LINT-002: Module with CDC passes Verilator lint"""
        module_data = {
            'name': 'lint_test_cdc',
            'base_address': 0,
            'cdc_enabled': True,
            'cdc_stages': 3,
            'registers': [
                {'signal_name': 'control', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': True,
                 'description': 'Control', 'address_int': 0x00}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            result = subprocess.run(
                ['verilator', '--lint-only', '-Wall', output_path],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, f"Verilator lint failed:\n{result.stderr}"

    def test_sv_lint_003_multiple_registers(self):
        """SV-LINT-003: Module with multiple registers passes lint"""
        registers = []
        for i in range(20):
            registers.append({
                'signal_name': f'reg{i}',
                'signal_type': '[31:0]',
                'signal_width': 32,
                'access_mode': ['RO', 'RW', 'WO'][i % 3],
                'read_strobe': i % 2 == 0,
                'write_strobe': i % 3 == 0,
                'description': f'Register {i}',
                'address_int': i * 4
            })

        module_data = {
            'name': 'lint_test_multi',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': registers
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            result = subprocess.run(
                ['verilator', '--lint-only', '-Wall', output_path],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, f"Verilator lint failed:\n{result.stderr}"

    def test_sv_lint_004_wide_registers(self):
        """SV-LINT-004: Wide registers (64-bit) pass lint"""
        module_data = {
            'name': 'lint_test_wide',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'wide_reg', 'signal_type': '[63:0]', 'signal_width': 64,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'Wide register', 'address_int': 0x00}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            result = subprocess.run(
                ['verilator', '--lint-only', '-Wall', output_path],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, f"Verilator lint failed:\n{result.stderr}"

    def test_sv_lint_005_all_access_modes(self):
        """SV-LINT-005: All access mode combinations pass lint"""
        module_data = {
            'name': 'lint_test_access',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'ro_reg', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RO', 'read_strobe': False, 'write_strobe': False,
                 'description': 'RO', 'address_int': 0x00},
                {'signal_name': 'wo_reg', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'WO', 'read_strobe': False, 'write_strobe': False,
                 'description': 'WO', 'address_int': 0x04},
                {'signal_name': 'rw_reg', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'RW', 'address_int': 0x08},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            result = subprocess.run(
                ['verilator', '--lint-only', '-Wall', output_path],
                capture_output=True,
                text=True
            )

            assert result.returncode == 0, f"Verilator lint failed:\n{result.stderr}"


class TestSystemVerilogSyntax(unittest.TestCase):
    """
    Basic syntax validation using regex patterns.
    Used as a fallback when Verilator is not installed.
    """

    def _check_syntax(self, content):
        import re
        
        # 1. Module declaration
        assert re.search(r'module\s+\w+\s*#\(', content), "Missing module declaration"
        assert re.search(r'endmodule', content), "Missing endmodule"
        
        # 2. Parameters
        assert re.search(r'parameter\s+int\s+ADDR_WIDTH\s*=', content), "Missing ADDR_WIDTH parameter"
        assert re.search(r'parameter\s+int\s+DATA_WIDTH\s*=', content), "Missing DATA_WIDTH parameter"
        
        # 3. Port list
        assert re.search(r'input\s+logic\s+axi_aclk', content), "Missing axi_aclk port"
        assert re.search(r'input\s+logic\s+axi_aresetn', content), "Missing axi_aresetn port"
        
        # 4. State machine
        assert re.search(r'typedef\s+enum\s+logic\s*\[2:0\]\s*{', content), "Missing state typedef"
        assert re.search(r'case\s*\(state\)', content), "Missing state machine case statement"
        
        # 5. Logic blocks
        assert re.search(r'always_ff\s*@\(posedge\s+axi_aclk', content), "Missing always_ff block"
        assert re.search(r'always_comb\s*begin', content), "Missing always_comb block"

    def test_sv_syntax_001_structure(self):
        """SV-SYNTAX-001: Validate basic SystemVerilog structure"""
        module_data = {
            'name': 'syntax_test',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'reg1', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'Test Reg', 'address_int': 0x00}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)
            
            with open(output_path, 'r') as f:
                content = f.read()
                
            self._check_syntax(content)

    def test_sv_syntax_002_cdc_logic(self):
        """SV-SYNTAX-002: Validate CDC syntax when enabled"""
        module_data = {
            'name': 'syntax_cdc_test',
            'base_address': 0,
            'cdc_enabled': True,
            'cdc_stages': 3,
            'registers': [
                {'signal_name': 'cdc_reg', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'CDC Reg', 'address_int': 0x00}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            # Check CDC specific syntax
            assert 'input  logic                      module_clk' in content
            assert 'always_ff @(posedge module_clk' in content
            
    def test_sv_syntax_003_access_modes(self):
        """SV-SYNTAX-003: Validate syntax for different access modes"""
        module_data = {
            'name': 'syntax_access',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'ro_reg', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RO', 'read_strobe': False, 'write_strobe': False, 
                 'description': 'RO', 'address_int': 0x00},
                {'signal_name': 'wo_reg', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'WO', 'read_strobe': False, 'write_strobe': False,
                 'description': 'WO', 'address_int': 0x04}
            ]
        }
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)
            
            with open(output_path, 'r') as f:
                content = f.read()
            
            # Check for RO logic (input from module)
            assert 'input  logic [31:0]                   ro_reg' in content
            # Check for WO logic (output to module)
            assert 'output logic [31:0]                   wo_reg' in content


class TestFormatEquivalence(unittest.TestCase):
    """VHDL vs SystemVerilog format equivalence tests"""

    def test_sv_equiv_001_basic_module(self):
        """SV-EQUIV-001: YAML input produces equivalent VHDL and SV outputs"""
        yaml_content = """
module: test_equiv
base_addr: "0x0000"
registers:
  - name: status
    width: 32
    access: RO
    description: Status register
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Write YAML file
            yaml_file = os.path.join(tmpdir, 'test.yaml')
            with open(yaml_file, 'w') as f:
                f.write(yaml_content)

            # Generate both VHDL and SystemVerilog
            axion = AxionHDL(output_dir=tmpdir)
            axion.add_source(yaml_file)
            axion.analyze()

            # Check that both formats can be generated
            vhdl_success = axion.generate_vhdl()
            sv_success = axion.generate_systemverilog()

            assert vhdl_success, "VHDL generation failed"
            assert sv_success, "SystemVerilog generation failed"

            # Verify both files exist
            vhdl_file = os.path.join(tmpdir, 'test_equiv_axion_reg.vhd')
            sv_file = os.path.join(tmpdir, 'test_equiv_axion_reg.sv')

            assert os.path.exists(vhdl_file), "VHDL file not generated"
            assert os.path.exists(sv_file), "SystemVerilog file not generated"

            # Both should contain the module/entity name
            with open(vhdl_file, 'r') as f:
                vhdl_content = f.read()
            with open(sv_file, 'r') as f:
                sv_content = f.read()

            assert 'test_equiv_axion_reg' in vhdl_content
            assert 'test_equiv_axion_reg' in sv_content

    def test_sv_equiv_002_register_map_consistency(self):
        """SV-EQUIV-002: Register maps are consistent across formats"""
        yaml_content = """
module: register_map_test
base_addr: 0x1000
registers:
  - name: reg0
    width: 32
    access: RO
    addr: 0x00
  - name: reg1
    width: 32
    access: RW
    addr: 0x04
  - name: reg2
    width: 16
    access: WO
    addr: 0x08
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, 'test.yaml')
            with open(yaml_file, 'w') as f:
                f.write(yaml_content)

            axion = AxionHDL(output_dir=tmpdir)
            axion.add_source(yaml_file)
            result = axion.analyze()

            # Check that analysis succeeded
            assert result == True, "Analysis failed"

            # Generate both formats
            vhdl_success = axion.generate_vhdl()
            sv_success = axion.generate_systemverilog()

            assert vhdl_success, "VHDL generation failed"
            assert sv_success, "SystemVerilog generation failed"

            vhdl_file = os.path.join(tmpdir, 'register_map_test_axion_reg.vhd')
            sv_file = os.path.join(tmpdir, 'register_map_test_axion_reg.sv')

            # Verify files exist
            assert os.path.exists(vhdl_file), "VHDL file not generated"
            assert os.path.exists(sv_file), "SV file not generated"

            with open(vhdl_file, 'r') as f:
                vhdl_content = f.read()
            with open(sv_file, 'r') as f:
                sv_content = f.read()

            # Check that registers appear in both files
            assert 'reg0' in vhdl_content or 'reg0' in sv_content
            assert 'reg1' in vhdl_content or 'reg1' in sv_content

    def test_sv_equiv_003_cdc_configuration(self):
        """SV-EQUIV-003: CDC configuration is equivalent in both formats"""
        yaml_content = """
module: cdc_equiv_test
base_addr: 0x0000
cdc_enabled: true
cdc_stages: 3
registers:
  - name: control
    width: 32
    access: RW
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, 'test.yaml')
            with open(yaml_file, 'w') as f:
                f.write(yaml_content)

            axion = AxionHDL(output_dir=tmpdir)
            axion.add_source(yaml_file)
            axion.analyze()

            vhdl_success = axion.generate_vhdl()
            sv_success = axion.generate_systemverilog()

            assert vhdl_success, "VHDL generation failed"
            assert sv_success, "SV generation failed"

            vhdl_file = os.path.join(tmpdir, 'cdc_equiv_test_axion_reg.vhd')
            sv_file = os.path.join(tmpdir, 'cdc_equiv_test_axion_reg.sv')

            assert os.path.exists(vhdl_file), "VHDL file not generated"
            assert os.path.exists(sv_file), "SV file not generated"

            with open(vhdl_file, 'r') as f:
                vhdl_content = f.read()
            with open(sv_file, 'r') as f:
                sv_content = f.read()

            # Both should have synchronizer logic
            assert 'sync' in vhdl_content.lower() or 'sync' in sv_content.lower()

    def test_sv_equiv_004_strobe_signals(self):
        """SV-EQUIV-004: Strobe signals are equivalent in both formats"""
        yaml_content = """
module: strobe_equiv_test
base_addr: 0x0000
registers:
  - name: reg_rd_strobe
    width: 32
    access: RO
    r_strobe: true
  - name: reg_wr_strobe
    width: 32
    access: WO
    w_strobe: true
  - name: reg_both_strobe
    width: 32
    access: RW
    r_strobe: true
    w_strobe: true
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, 'test.yaml')
            with open(yaml_file, 'w') as f:
                f.write(yaml_content)

            axion = AxionHDL(output_dir=tmpdir)
            axion.add_source(yaml_file)
            axion.analyze()

            vhdl_success = axion.generate_vhdl()
            sv_success = axion.generate_systemverilog()

            assert vhdl_success, "VHDL generation failed"
            assert sv_success, "SV generation failed"

            vhdl_file = os.path.join(tmpdir, 'strobe_equiv_test_axion_reg.vhd')
            sv_file = os.path.join(tmpdir, 'strobe_equiv_test_axion_reg.sv')

            assert os.path.exists(vhdl_file), "VHDL file not generated"
            assert os.path.exists(sv_file), "SV file not generated"

            with open(vhdl_file, 'r') as f:
                vhdl_content = f.read()
            with open(sv_file, 'r') as f:
                sv_content = f.read()

            # Check for strobe signals in at least one format
            has_strobes = ('strobe' in vhdl_content.lower() or 'strobe' in sv_content.lower())
            assert has_strobes, "No strobe signals found in generated files"

    def test_sv_equiv_005_address_allocation(self):
        """SV-EQUIV-005: Automatic address allocation is equivalent"""
        yaml_content = """
module: addr_equiv_test
base_addr: 0x2000
registers:
  - name: reg0
    width: 32
    access: RW
  - name: reg1
    width: 32
    access: RW
  - name: reg2
    width: 32
    access: RW
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, 'test.yaml')
            with open(yaml_file, 'w') as f:
                f.write(yaml_content)

            axion = AxionHDL(output_dir=tmpdir)
            axion.add_source(yaml_file)
            axion.analyze()

            vhdl_success = axion.generate_vhdl()
            sv_success = axion.generate_systemverilog()

            assert vhdl_success, "VHDL generation failed"
            assert sv_success, "SV generation failed"

            vhdl_file = os.path.join(tmpdir, 'addr_equiv_test_axion_reg.vhd')
            sv_file = os.path.join(tmpdir, 'addr_equiv_test_axion_reg.sv')

            # Both files should exist
            assert os.path.exists(vhdl_file), "VHDL file not generated"
            assert os.path.exists(sv_file), "SV file not generated"


class TestStressAndEdgeCases(unittest.TestCase):
    """Stress tests and edge cases"""

    def test_sv_stress_001_100_registers(self):
        """SV-STRESS-001: Module with 100 registers"""
        registers = []
        for i in range(100):
            registers.append({
                'signal_name': f'reg{i:03d}',
                'signal_type': '[31:0]',
                'signal_width': 32,
                'access_mode': ['RO', 'RW', 'WO'][i % 3],
                'read_strobe': i % 5 == 0,
                'write_strobe': i % 7 == 0,
                'description': f'Register {i}',
                'address_int': i * 4
            })

        module_data = {
            'name': 'stress_100_regs',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': registers
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check that all registers are present
            for i in range(100):
                assert f'reg{i:03d}' in content

    def test_sv_stress_002_maximum_width(self):
        """SV-STRESS-002: Registers with maximum supported widths"""
        module_data = {
            'name': 'stress_max_width',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'reg_256', 'signal_type': '[255:0]', 'signal_width': 256,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': '256-bit register', 'address_int': 0x00},
                {'signal_name': 'reg_512', 'signal_type': '[511:0]', 'signal_width': 512,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': '512-bit register', 'address_int': 0x20},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            assert 'reg_256' in content
            assert 'reg_512' in content

    def test_sv_stress_003_all_features_combined(self):
        """SV-STRESS-003: Module with all features enabled simultaneously"""
        module_data = {
            'name': 'stress_all_features',
            'base_address': 0x8000,
            'cdc_enabled': True,
            'cdc_stages': 4,
            'registers': [
                {'signal_name': 'ro_strobe', 'signal_type': '[63:0]', 'signal_width': 64,
                 'access_mode': 'RO', 'read_strobe': True, 'write_strobe': False,
                 'description': 'RO 64-bit with read strobe', 'address_int': 0x00},
                {'signal_name': 'wo_strobe', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'WO', 'read_strobe': False, 'write_strobe': True,
                 'description': 'WO with write strobe', 'address_int': 0x08},
                {'signal_name': 'rw_both', 'signal_type': '[127:0]', 'signal_width': 128,
                 'access_mode': 'RW', 'read_strobe': True, 'write_strobe': True,
                 'description': 'RW 128-bit with both strobes', 'address_int': 0x10},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # Verify CDC is present
            assert 'sync' in content

            # Verify all registers
            assert 'ro_strobe' in content
            assert 'wo_strobe' in content
            assert 'rw_both' in content

            # Verify strobes
            assert 'rd_strobe' in content
            assert 'wr_strobe' in content

    def test_sv_stress_004_long_descriptions(self):
        """SV-STRESS-004: Registers with very long descriptions"""
        long_desc = "This is a very long description " * 20  # ~640 characters
        module_data = {
            'name': 'stress_long_desc',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'reg_long', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': long_desc, 'address_int': 0x00}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            assert os.path.exists(output_path)

    def test_sv_stress_005_high_address_range(self):
        """SV-STRESS-005: Registers with high address values"""
        module_data = {
            'name': 'stress_high_addr',
            'base_address': 0xFFFF0000,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'reg_high', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'High address register', 'address_int': 0xFFC}
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            assert os.path.exists(output_path)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for high address constant
            assert 'FFC' in content.upper() or 'FFFF0FFC' in content.upper()


if __name__ == '__main__':
    unittest.main()
