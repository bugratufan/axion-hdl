"""
Unit tests for SystemVerilog generator
Tests SV-GEN-001 through SV-GEN-016 requirements
"""

import pytest
import os
import tempfile
import re
from axion_hdl.systemverilog_generator import SystemVerilogGenerator


class TestSystemVerilogGenerator:
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
