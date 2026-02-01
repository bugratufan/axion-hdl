"""
Unit tests for SystemVerilog parser
Tests SV-AXION-001 through SV-AXION-029 requirements
"""

import unittest
import os
import tempfile
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from axion_hdl.systemverilog_parser import SystemVerilogParser


class TestSystemVerilogParser(unittest.TestCase):
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


    def test_sv_axion_023_wide_signal_64bit(self):
        """SV-AXION-023: Parse 64-bit wide signal"""
        content = """
module test_module (
    input logic clk
);
    logic [63:0] wide_data; // @axion RO DESC="64-bit data"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert len(result['registers']) >= 1  # Should split into 2 registers

            # First register should be lower 32 bits
            reg0 = result['registers'][0]
            assert reg0['signal_name'] == 'wide_data'
            assert reg0['signal_width'] == 64

            os.unlink(f.name)

    def test_sv_axion_024_wide_signal_128bit(self):
        """SV-AXION-024: Parse 128-bit wide signal"""
        content = """
module test_module (
    input logic clk
);
    logic [127:0] huge_data; // @axion RO DESC="128-bit data"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            reg = result['registers'][0]
            assert reg['signal_width'] == 128

            os.unlink(f.name)

    def test_sv_axion_025_error_missing_module(self):
        """SV-AXION-025: Handle file without module declaration"""
        content = """
// Just a comment
logic [31:0] orphan_signal; // @axion RO
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            # Should return None when no module found
            assert result is None

            os.unlink(f.name)

    def test_sv_axion_026_error_invalid_access_mode(self):
        """SV-AXION-026: Handle invalid access mode"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] bad_reg; // @axion INVALID DESC="Bad access mode"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            # Should default to RW
            assert result is not None
            reg = result['registers'][0]
            assert reg['access_mode'] == 'RW'  # Default fallback

            os.unlink(f.name)

    def test_sv_axion_027_error_duplicate_address(self):
        """SV-AXION-027: Detect duplicate manual addresses"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] reg1; // @axion RO ADDR=0x100
    logic [31:0] reg2; // @axion RO ADDR=0x100
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            # Should only have 1 register (second should be rejected)
            assert result is not None
            assert len(result['registers']) == 1

            # Should have an error
            errors = parser.get_errors()
            assert len(errors) > 0

            os.unlink(f.name)

    def test_sv_axion_028_empty_file(self):
        """SV-AXION-028: Handle empty file"""
        content = ""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is None

            os.unlink(f.name)

    def test_sv_axion_029_comments_only(self):
        """SV-AXION-029: Handle file with only comments"""
        content = """
// This is a comment
/* This is a
   multi-line comment */
// More comments
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is None

            os.unlink(f.name)

    def test_sv_axion_030_multiple_registers_stress(self):
        """SV-AXION-030: Stress test with 50 registers"""
        lines = ["module test_module (", "    input logic clk", ");"]
        for i in range(50):
            lines.append(f"    logic [31:0] reg{i}; // @axion RW DESC=\"Register {i}\"")
        lines.append("endmodule")
        content = "\n".join(lines)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert len(result['registers']) == 50

            # Check sequential addresses
            for i, reg in enumerate(result['registers']):
                assert reg['signal_name'] == f'reg{i}'
                assert reg['address_int'] == i * 4

            os.unlink(f.name)

    def test_sv_axion_031_mixed_signal_widths(self):
        """SV-AXION-031: Mix of different signal widths"""
        content = """
module test_module (
    input logic clk
);
    logic       bit1;   // @axion RO DESC="1-bit"
    logic [7:0] byte1;  // @axion RO DESC="8-bit"
    logic [15:0] word1; // @axion RO DESC="16-bit"
    logic [31:0] dword; // @axion RO DESC="32-bit"
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert len(result['registers']) == 4

            assert result['registers'][0]['signal_width'] == 1
            assert result['registers'][1]['signal_width'] == 8
            assert result['registers'][2]['signal_width'] == 16
            assert result['registers'][3]['signal_width'] == 32

            os.unlink(f.name)

    def test_sv_axion_032_all_access_modes(self):
        """SV-AXION-032: All access mode combinations in one module"""
        content = """
module test_module (
    input logic clk
);
    logic [31:0] ro_reg;     // @axion RO
    logic [31:0] wo_reg;     // @axion WO
    logic [31:0] rw_reg;     // @axion RW
    logic [31:0] ro_strobe;  // @axion RO R_STROBE
    logic [31:0] wo_strobe;  // @axion WO W_STROBE
    logic [31:0] rw_both;    // @axion RW R_STROBE W_STROBE
endmodule
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sv', delete=False) as f:
            f.write(content)
            f.flush()

            parser = SystemVerilogParser()
            result = parser.parse_file(f.name)

            assert result is not None
            assert len(result['registers']) == 6

            assert result['registers'][0]['access_mode'] == 'RO'
            assert result['registers'][1]['access_mode'] == 'WO'
            assert result['registers'][2]['access_mode'] == 'RW'
            assert result['registers'][3]['read_strobe'] == True
            assert result['registers'][4]['write_strobe'] == True
            assert result['registers'][5]['read_strobe'] == True
            assert result['registers'][5]['write_strobe'] == True

            os.unlink(f.name)


if __name__ == '__main__':
    unittest.main()
