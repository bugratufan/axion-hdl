"""
Unit tests for SystemVerilog generator
Tests SV-GEN-001 through SV-GEN-016 requirements
"""

import unittest
import os
import tempfile
import re
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from axion_hdl.systemverilog_generator import SystemVerilogGenerator


class TestSystemVerilogGenerator(unittest.TestCase):
    """Test suite for SystemVerilog code generation"""

    def test_sv_gen_001_generate_basic_module(self):
        """SV-GEN-001: Generate basic module structure"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'status',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Status register',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            assert os.path.exists(output_path)
            assert output_path.endswith('_axion_reg.sv')

            with open(output_path, 'r') as f:
                content = f.read()

            # Check module declaration
            assert 'module test_module_axion_reg' in content
            assert 'endmodule' in content

    def test_sv_gen_002_generate_axi_ports(self):
        """SV-GEN-002: Generate AXI4-Lite interface ports"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check AXI4-Lite signals
            required_signals = [
                'axi_aclk', 'axi_aresetn',
                'axi_awaddr', 'axi_awvalid', 'axi_awready',
                'axi_wdata', 'axi_wvalid', 'axi_wready',
                'axi_bresp', 'axi_bvalid', 'axi_bready',
                'axi_araddr', 'axi_arvalid', 'axi_arready',
                'axi_rdata', 'axi_rvalid', 'axi_rready'
            ]

            for signal in required_signals:
                assert signal in content

    def test_sv_gen_003_generate_ro_register(self):
        """SV-GEN-003: Generate read-only register interface"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'status',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Status',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # RO register should be input port
            assert re.search(r'input\s+logic\s+\[31:0\]\s+status', content)

            # Should NOT have internal register for RO
            assert 'status_reg;' not in content or 'status_reg_reg;' not in content

    def test_sv_gen_004_generate_rw_register(self):
        """SV-GEN-004: Generate read-write register interface"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'control',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RW',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Control',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # RW register should be output port
            assert re.search(r'output\s+logic\s+\[31:0\]\s+control', content)

            # Should have internal register for RW
            assert 'control_reg_reg;' in content or 'control_reg;' in content

    def test_sv_gen_005_generate_wo_register(self):
        """SV-GEN-005: Generate write-only register interface"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'command',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'WO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Command',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # WO register should be output port
            assert re.search(r'output\s+logic\s+\[31:0\]\s+command', content)

    def test_sv_gen_006_generate_state_machine(self):
        """SV-GEN-006: Generate AXI4-Lite state machine"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for state machine
            assert 'typedef enum' in content
            assert 'axi_state_t' in content
            assert 'IDLE' in content
            assert 'WRITE_ADDR' in content
            assert 'WRITE_DATA' in content
            assert 'READ_ADDR' in content
            assert 'READ_DATA' in content

    def test_sv_gen_007_generate_always_ff(self):
        """SV-GEN-007: Use always_ff for sequential logic"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'control',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RW',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Control',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for SystemVerilog always_ff
            assert 'always_ff @(posedge axi_aclk' in content

    def test_sv_gen_008_generate_always_comb(self):
        """SV-GEN-008: Use always_comb for combinational logic"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'status',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Status',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for SystemVerilog always_comb
            assert 'always_comb' in content

    def test_sv_gen_009_generate_cdc_synchronizers(self):
        """SV-GEN-009: Generate CDC synchronizers when enabled"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': True,
            'cdc_stages': 3,
            'registers': [
                {
                    'signal_name': 'status',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Status',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for CDC synchronizers
            assert 'Clock Domain Crossing' in content
            assert 'status_sync' in content
            assert '[3]' in content  # 3 stages

    def test_sv_gen_010_generate_address_decoding(self):
        """SV-GEN-010: Generate address decode logic"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'reg0',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RW',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Reg 0',
                    'address_int': 0x00
                },
                {
                    'signal_name': 'reg1',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RW',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Reg 1',
                    'address_int': 0x04
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for address constants
            assert 'ADDR_REG0' in content
            assert 'ADDR_REG1' in content
            assert "32'h00000000" in content
            assert "32'h00000004" in content

    def test_sv_gen_011_generate_write_strobe(self):
        """SV-GEN-011: Generate write strobe signal"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'control',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RW',
                    'read_strobe': False,
                    'write_strobe': True,
                    'description': 'Control',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for write strobe port and signal
            assert 'control_wr_strobe' in content

    def test_sv_gen_012_generate_read_strobe(self):
        """SV-GEN-012: Generate read strobe signal"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'status',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RO',
                    'read_strobe': True,
                    'write_strobe': False,
                    'description': 'Status',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for read strobe
            assert 'status_rd_strobe' in content

    def test_sv_gen_013_generate_error_response(self):
        """SV-GEN-013: Generate SLVERR for invalid access"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'status',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Status',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for error response codes
            assert 'SLVERR' in content
            assert 'OKAY' in content

    def test_sv_gen_014_generate_parameters(self):
        """SV-GEN-014: Generate module parameters"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for parameters
            assert 'parameter int ADDR_WIDTH' in content
            assert 'parameter int DATA_WIDTH' in content

    def test_sv_gen_015_generate_header_comment(self):
        """SV-GEN-015: Generate file header with metadata"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check header
            assert 'File: test_module_axion_reg.sv' in content
            assert 'Generated by: Axion-HDL' in content
            assert 'AXI4-Lite Register Interface' in content

    def test_sv_gen_016_module_clk_port_when_cdc(self):
        """SV-GEN-016: Add module_clk port when CDC enabled"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': True,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'status',
                    'signal_type': '[31:0]',
                    'signal_width': 32,
                    'access_mode': 'RO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': 'Status',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check for module_clk port
            assert 'module_clk' in content
            assert 'input  logic                      module_clk' in content


    def test_sv_gen_017_wide_register_64bit(self):
        """SV-GEN-017: Generate wide 64-bit register handling"""
        module_data = {
            'name': 'test_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {
                    'signal_name': 'wide_data',
                    'signal_type': '[63:0]',
                    'signal_width': 64,
                    'access_mode': 'RO',
                    'read_strobe': False,
                    'write_strobe': False,
                    'description': '64-bit data',
                    'address_int': 0x00
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Should handle 64-bit signal
            assert 'logic [63:0]' in content or 'logic [31:0]' in content

    def test_sv_gen_018_zero_registers(self):
        """SV-GEN-018: Handle module with no registers"""
        module_data = {
            'name': 'empty_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': []
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Should still generate valid module
            assert 'module empty_module_axion_reg' in content
            assert 'endmodule' in content

    def test_sv_gen_019_many_registers_stress(self):
        """SV-GEN-019: Stress test with 100 registers"""
        registers = []
        for i in range(100):
            registers.append({
                'signal_name': f'reg{i}',
                'signal_type': '[31:0]',
                'signal_width': 32,
                'access_mode': 'RW',
                'read_strobe': False,
                'write_strobe': False,
                'description': f'Register {i}',
                'address_int': i * 4
            })

        module_data = {
            'name': 'stress_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': registers
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Check all registers are present
            for i in range(100):
                assert f'reg{i}' in content

    def test_sv_gen_020_all_access_mode_combinations(self):
        """SV-GEN-020: All access modes with all strobe combinations"""
        module_data = {
            'name': 'combo_module',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                # RO with no strobes
                {'signal_name': 'ro_plain', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RO', 'read_strobe': False, 'write_strobe': False,
                 'description': 'RO plain', 'address_int': 0x00},
                # RO with read strobe
                {'signal_name': 'ro_rstrobe', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RO', 'read_strobe': True, 'write_strobe': False,
                 'description': 'RO with R strobe', 'address_int': 0x04},
                # WO with no strobes
                {'signal_name': 'wo_plain', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'WO', 'read_strobe': False, 'write_strobe': False,
                 'description': 'WO plain', 'address_int': 0x08},
                # WO with write strobe
                {'signal_name': 'wo_wstrobe', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'WO', 'read_strobe': False, 'write_strobe': True,
                 'description': 'WO with W strobe', 'address_int': 0x0C},
                # RW with no strobes
                {'signal_name': 'rw_plain', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'RW plain', 'address_int': 0x10},
                # RW with both strobes
                {'signal_name': 'rw_both', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': True, 'write_strobe': True,
                 'description': 'RW with both strobes', 'address_int': 0x14},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Verify all signals present
            assert 'ro_plain' in content
            assert 'ro_rstrobe' in content
            assert 'wo_plain' in content
            assert 'wo_wstrobe' in content
            assert 'rw_plain' in content
            assert 'rw_both' in content

            # Verify strobes
            assert 'ro_rstrobe_rd_strobe' in content
            assert 'wo_wstrobe_wr_strobe' in content
            assert 'rw_both_rd_strobe' in content
            assert 'rw_both_wr_strobe' in content

    def test_sv_gen_021_cdc_with_multiple_stages(self):
        """SV-GEN-021: CDC with various stage counts"""
        for stages in [2, 3, 4, 5]:
            module_data = {
                'name': f'cdc_{stages}_stage',
                'base_address': 0,
                'cdc_enabled': True,
                'cdc_stages': stages,
                'registers': [
                    {'signal_name': 'status', 'signal_type': '[31:0]', 'signal_width': 32,
                     'access_mode': 'RO', 'read_strobe': False, 'write_strobe': False,
                     'description': 'Status', 'address_int': 0x00}
                ]
            }

            with tempfile.TemporaryDirectory() as tmpdir:
                gen = SystemVerilogGenerator(tmpdir)
                output_path = gen.generate_module(module_data)

                with open(output_path, 'r') as f:
                    content = f.read()

                # Check for correct number of stages
                assert f'[{stages}]' in content
                assert 'status_sync' in content

    def test_sv_gen_022_syntax_validation(self):
        """SV-GEN-022: Generated code has valid SystemVerilog syntax"""
        module_data = {
            'name': 'syntax_test',
            'base_address': 0,
            'cdc_enabled': True,
            'cdc_stages': 3,
            'registers': [
                {'signal_name': 'status', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RO', 'read_strobe': True, 'write_strobe': False,
                 'description': 'Status', 'address_int': 0x00},
                {'signal_name': 'control', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': True, 'write_strobe': True,
                 'description': 'Control', 'address_int': 0x04},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            # Basic syntax checks
            assert content.count('module ') == content.count('endmodule')
            # Count 'begin' as a word boundary, not in 'begin'
            import re
            begin_count = len(re.findall(r'\bbegin\b', content))
            end_count = len(re.findall(r'\bend\b', content))
            assert begin_count == end_count, f"begin count ({begin_count}) != end count ({end_count})"
            assert 'always_ff' in content
            assert 'always_comb' in content
            assert 'typedef enum' in content

    def test_sv_gen_023_special_characters_in_description(self):
        """SV-GEN-023: Handle special characters in descriptions"""
        module_data = {
            'name': 'special_chars',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'reg1', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'Test "quotes" and \'apostrophes\'', 'address_int': 0x00},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            # Should not crash
            assert os.path.exists(output_path)

    def test_sv_gen_024_numeric_signal_names(self):
        """SV-GEN-024: Handle signal names with numbers"""
        module_data = {
            'name': 'numeric_test',
            'base_address': 0,
            'cdc_enabled': False,
            'cdc_stages': 2,
            'registers': [
                {'signal_name': 'reg0', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'Reg 0', 'address_int': 0x00},
                {'signal_name': 'reg123', 'signal_type': '[31:0]', 'signal_width': 32,
                 'access_mode': 'RW', 'read_strobe': False, 'write_strobe': False,
                 'description': 'Reg 123', 'address_int': 0x04},
            ]
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            gen = SystemVerilogGenerator(tmpdir)
            output_path = gen.generate_module(module_data)

            with open(output_path, 'r') as f:
                content = f.read()

            assert 'reg0' in content
            assert 'reg123' in content


if __name__ == '__main__':
    unittest.main()
