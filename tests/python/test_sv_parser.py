"""
Unit tests for SystemVerilog parser
Tests SV-AXION-001 through SV-AXION-029 requirements
"""

import pytest
import os
import tempfile
from axion_hdl.systemverilog_parser import SystemVerilogParser


class TestSystemVerilogParser:
    """Test suite for SystemVerilog annotation parsing"""

    def test_sv_axion_001_parse_ro_register(self):
        """SV-AXION-001: Parse read-only register"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] status; // @axion RO DESC="Status register"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert result['name'] == 'test_module'
            assert len(result['registers']) == 1

            reg = result['registers'][0]
            assert reg['signal_name'] == 'status'
            assert reg['access_mode'] == 'RO'
            assert reg['description'] == 'Status register'

            os.unlink(f.name)

    def test_sv_axion_002_parse_rw_register(self):
        """SV-AXION-002: Parse read-write register"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] control; // @axion RW DESC="Control register"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_name'] == 'control'
            assert reg['access_mode'] == 'RW'

            os.unlink(f.name)

    def test_sv_axion_003_parse_wo_register(self):
        """SV-AXION-003: Parse write-only register"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] config; // @axion WO DESC="Config register"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_name'] == 'config'
            assert reg['access_mode'] == 'WO'

            os.unlink(f.name)

    def test_sv_axion_004_parse_read_strobe(self):
        """SV-AXION-004: Parse read strobe annotation"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] data; // @axion RO R_STROBE DESC="Data with read strobe"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['read_strobe'] == True
            assert reg['write_strobe'] == False

            os.unlink(f.name)

    def test_sv_axion_005_parse_write_strobe(self):
        """SV-AXION-005: Parse write strobe annotation"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] cmd; // @axion WO W_STROBE DESC="Command with write strobe"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['write_strobe'] == True
            assert reg['read_strobe'] == False

            os.unlink(f.name)

    def test_sv_axion_006_parse_both_strobes(self):
        """SV-AXION-006: Parse both read and write strobes"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] intr; // @axion RW R_STROBE W_STROBE DESC="Interrupt with both strobes"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['read_strobe'] == True
            assert reg['write_strobe'] == True

            os.unlink(f.name)

    def test_sv_axion_007_parse_cdc_enable(self):
        """SV-AXION-007: Parse CDC enable configuration"""
        content = """
// @axion_def CDC_EN

module test_module (
    input logic clk
);
    logic [31:0] data; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert result['cdc_enabled'] == True
            assert result['cdc_stages'] == 2  # Default

            os.unlink(f.name)

    def test_sv_axion_008_parse_cdc_stages(self):
        """SV-AXION-008: Parse CDC stage configuration"""
        content = """
// @axion_def CDC_EN CDC_STAGE=3

module test_module (
    input logic clk
);
    logic [31:0] data; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert result['cdc_enabled'] == True
            assert result['cdc_stages'] == 3

            os.unlink(f.name)

    def test_sv_axion_009_parse_base_address(self):
        """SV-AXION-009: Parse base address configuration"""
        content = """
// @axion_def BASE_ADDR=0x1000

module test_module (
    input logic clk
);
    logic [31:0] data; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert result['base_address'] == 0x1000

            os.unlink(f.name)

    def test_sv_axion_010_auto_address_allocation(self):
        """SV-AXION-010: Test automatic address allocation"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] reg0; // @axion RO
    logic [31:0] reg1; // @axion RO
    logic [31:0] reg2; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert len(result['registers']) == 3

            # Check sequential allocation
            assert result['registers'][0]['address_int'] == 0x00
            assert result['registers'][1]['address_int'] == 0x04
            assert result['registers'][2]['address_int'] == 0x08

            os.unlink(f.name)

    def test_sv_axion_011_manual_address(self):
        """SV-AXION-011: Test manual address assignment"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] special; // @axion RO ADDR=0x100
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['address_int'] == 0x100

            os.unlink(f.name)

    def test_sv_axion_012_signal_width_32bit(self):
        """SV-AXION-012: Parse 32-bit signal"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] data32; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_width'] == 32
            assert reg['signal_type'] == '[31:0]'

            os.unlink(f.name)

    def test_sv_axion_013_signal_width_8bit(self):
        """SV-AXION-013: Parse 8-bit signal"""
        content = """
module test_module (
    input logic clk
);
    logic [7:0] data8; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_width'] == 8
            assert reg['signal_type'] == '[7:0]'

            os.unlink(f.name)

    def test_sv_axion_014_signal_width_1bit(self):
        """SV-AXION-014: Parse single-bit signal"""
        content = """
module test_module (
    input logic clk
);
    logic flag; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_width'] == 1
            assert reg['signal_type'] == '[0:0]'

            os.unlink(f.name)

    def test_sv_axion_015_module_name_extraction(self):
        """SV-AXION-015: Extract module name correctly"""
        content = """
module my_sensor_controller (
    input logic clk
);
    logic [31:0] data; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert result['name'] == 'my_sensor_controller'

            os.unlink(f.name)

    def test_sv_axion_016_multiple_registers(self):
        """SV-AXION-016: Parse multiple registers correctly"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] status;  // @axion RO DESC="Status"
    logic [31:0] control; // @axion RW DESC="Control"
    logic [31:0] data;    // @axion WO DESC="Data"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert len(result['registers']) == 3

            assert result['registers'][0]['signal_name'] == 'status'
            assert result['registers'][1]['signal_name'] == 'control'
            assert result['registers'][2]['signal_name'] == 'data'

            os.unlink(f.name)

    def test_sv_axion_017_reg_type_support(self):
        """SV-AXION-017: Support reg type (not just logic)"""
        content = """
module test_module (
    input logic clk
);
    reg [31:0] old_style; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_name'] == 'old_style'

            os.unlink(f.name)

    def test_sv_axion_018_wire_type_support(self):
        """SV-AXION-018: Support wire type"""
        content = """
module test_module (
    input logic clk
);
    wire [31:0] status_wire; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_name'] == 'status_wire'

            os.unlink(f.name)

    def test_sv_axion_019_no_registers(self):
        """SV-AXION-019: Handle module with no annotated registers"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] internal_signal;
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            # Should return None when no registers found
            assert result is None

            os.unlink(f.name)

    def test_sv_axion_020_annotation_with_colon(self):
        """SV-AXION-020: Support both @axion and @axion: syntax"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] reg1; // @axion RO
    logic [31:0] reg2; // @axion: RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert len(result['registers']) == 2

            os.unlink(f.name)

    def test_sv_axion_021_description_with_spaces(self):
        """SV-AXION-021: Handle descriptions with spaces"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] status; // @axion RO DESC="System status flags and indicators"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['description'] == 'System status flags and indicators'

            os.unlink(f.name)

    def test_sv_axion_022_mixed_configuration(self):
        """SV-AXION-022: Mix CDC and BASE_ADDR configuration"""
        content = """
// @axion_def BASE_ADDR=0x2000 CDC_EN CDC_STAGE=4

module test_module (
    input logic clk
);
    logic [31:0] data; // @axion RO
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert result['base_address'] == 0x2000
            assert result['cdc_enabled'] == True
            assert result['cdc_stages'] == 4

            os.unlink(f.name)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
