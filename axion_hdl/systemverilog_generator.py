"""
SystemVerilog Generator Module for Axion HDL

This module generates SystemVerilog register interface modules from parsed data.
Equivalent to generator.py but generates SystemVerilog instead of VHDL.

Features:
- AXI4-Lite protocol implementation using SystemVerilog constructs
- Proper access control with SLVERR responses
- CDC synchronizer generation (when enabled)
- Byte-level write strobe support
- SystemVerilog enums, always_ff, always_comb
"""

import os
import re
import sys
from datetime import datetime
from typing import Dict, List, Optional

# Import from axion_hdl (unified package)
from axion_hdl.code_formatter import CodeFormatter
from axion_hdl.systemverilog_utils import SystemVerilogUtils


class SystemVerilogGenerator:
    """Generator for creating AXI register interface SystemVerilog modules."""

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.formatter = CodeFormatter()
        self.sv_utils = SystemVerilogUtils()

    def generate_module(self, module_data: Dict) -> str:
        """
        Generate SystemVerilog register interface module.

        Args:
            module_data: Parsed module data dictionary containing:
                - name: Module name
                - registers: List of register dictionaries
                - base_address: Base address
                - cdc_enabled: CDC flag
                - cdc_stages: CDC synchronizer stages

        Returns:
            Path to generated file
        """
        effective_name = module_data.get('_effective_name')
        if effective_name:
            module_data = dict(module_data)
            module_data['name'] = effective_name

        module_name = module_data.get('name', 'unnamed_module')
        # Sanitize: strip any path components and extensions that don't belong
        module_name = os.path.basename(module_name)
        module_name = os.path.splitext(module_name)[0] if '.' in module_name else module_name
        # Skip modules with invalid SystemVerilog identifiers (e.g. names with hyphens from JS files)
        import re as _re
        if not _re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', module_name):
            return None
        # Write sanitized name back so the module declaration matches the filename
        module_data = dict(module_data)
        module_data['name'] = module_name
        output_filename = f"{module_name}_axion_reg.sv"
        output_path = os.path.join(self.output_dir, output_filename)

        # Generate module content
        content = self._generate_module_content(module_data) + "\n"

        # Write to file
        os.makedirs(self.output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def _generate_module_content(self, module_data: Dict) -> str:
        """Generate complete SystemVerilog module content."""
        sections = []

        # Header
        sections.append(self._generate_header(module_data))

        # Module declaration
        sections.append(self._generate_module_declaration(module_data))

        # Internal signals and parameters
        sections.append(self._generate_internals(module_data))

        # CDC synchronizers (if enabled)
        if module_data.get('cdc_enabled', False):
            sections.append(self._generate_cdc_logic(module_data))

        # AXI4-Lite state machine
        sections.append(self._generate_axi_state_machine(module_data))

        # Register logic
        sections.append(self._generate_register_logic(module_data))

        # Output assignments
        sections.append(self._generate_output_assignments(module_data))

        # Module end
        sections.append("endmodule")

        return '\n\n'.join(sections)

    def generate_sv_pkg(self, module_data: Dict) -> Optional[str]:
        """
        Generate a SystemVerilog typedef enum package for enumerated field values.

        Generates <module>_regs_pkg.sv if any packed register field has enum_values.

        Args:
            module_data: Parsed module dictionary

        Returns:
            Path to generated package file, or None if no enum_values present
        """
        module_name = module_data.get('_effective_name', module_data.get('name', 'unnamed_module'))

        # Collect all registers/fields with enum_values
        enum_fields = []
        for reg in module_data.get('registers', []):
            reg_name = reg.get('reg_name', reg.get('signal_name', ''))
            if reg.get('is_packed'):
                for field in reg.get('fields', []):
                    if field.get('enum_values'):
                        enum_fields.append((reg_name, field))
            elif reg.get('enum_values'):
                synthetic = {
                    'name': reg_name,
                    'width': reg.get('signal_width', reg.get('width', 32)),
                    'enum_values': reg['enum_values'],
                }
                enum_fields.append((reg_name, synthetic))

        if not enum_fields:
            return None

        output_filename = f"{module_name}_regs_pkg.sv"
        output_path = os.path.join(self.output_dir, output_filename)

        lines = [
            f"// Package: {module_name}_regs_pkg",
            f"// Enumerated typedefs for {module_name} register fields",
            "",
            f"package {module_name}_regs_pkg;",
            "",
        ]

        for reg_name, field in enum_fields:
            width = int(field.get('width', 1))
            field_name = field['name']
            enum_dict = field.get('enum_values', {})
            safe_reg = SystemVerilogUtils.sanitize_identifier(reg_name)
            safe_field = SystemVerilogUtils.sanitize_identifier(field_name)
            typedef_name = f"t_{safe_reg}_{safe_field}_e"

            # Prefix enum member names with REG_FIELD_ to ensure uniqueness in package scope
            prefix = f"{reg_name}_{field_name}".upper()
            enum_entries = []
            for val, name in sorted(enum_dict.items()):
                safe_name = SystemVerilogUtils.sanitize_identifier(name)
                bin_literal = format(int(val), f'0{width}b')
                member_name = f"{prefix}_{safe_name}"
                if width == 1:
                    entry = f"    {member_name} = 1'b{bin_literal}"
                else:
                    entry = f"    {member_name} = {width}'b{bin_literal}"
                enum_entries.append(entry)

            if width == 1:
                lines.append(f"    typedef enum logic {{")
            else:
                lines.append(f"    typedef enum logic [{width - 1}:0] {{")

            lines.append(',\n'.join(enum_entries))
            lines.append(f"    }} {typedef_name};")
            lines.append("")

        lines.extend([
            f"endpackage // {module_name}_regs_pkg",
            "",
        ])

        os.makedirs(self.output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return output_path

    def _generate_header(self, module_data: Dict) -> str:
        """Generate file header with metadata."""
        module_name = module_data.get('name', 'unnamed_module')
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        use_axion_types = module_data.get('use_axion_types', False)

        header = (
            f"//-----------------------------------------------------------------------------\n"
            f"// File: {module_name}_axion_reg.sv\n"
            f"// Module: {module_name}_axion_reg\n"
            f"// Description: AXI4-Lite Register Interface for {module_name}\n"
            f"// Generated by: Axion-HDL\n"
            f"// Date: {timestamp}\n"
            f"//\n"
            f"// This file was automatically generated. Manual modifications may be lost.\n"
            f"//-----------------------------------------------------------------------------"
        )
        if use_axion_types:
            header += "\n\nimport axion_common_pkg::*;"
        return header

    def _generate_module_declaration(self, module_data: Dict) -> str:
        """Generate module declaration with parameters and ports."""
        module_name = module_data.get('name', 'unnamed_module')
        registers = module_data.get('registers', [])
        cdc_enabled = module_data.get('cdc_enabled', False)
        use_axion_types = module_data.get('use_axion_types', False)

        # Module header
        lines = [
            f"module {module_name}_axion_reg #(",
            "    parameter int ADDR_WIDTH = 32,",
            "    parameter int DATA_WIDTH = 32",
            ") ("
        ]

        # AXI4-Lite interface
        if use_axion_types:
            lines.extend([
                "    // AXI4-Lite Interface (typed record ports from axion_common_pkg)",
                "    input  logic          axi_aclk,",
                "    input  logic          axi_aresetn,",
                "    input  t_axi_lite_m2s axi_m2s,",
                "    output t_axi_lite_s2m axi_s2m,",
                ""
            ])
        else:
            lines.extend([
                "    // AXI4-Lite Interface",
                "    input  logic                      axi_aclk,",
                "    input  logic                      axi_aresetn,",
                "    input  logic [ADDR_WIDTH-1:0]     axi_awaddr,",
                "    input  logic [2:0]                axi_awprot,",
                "    input  logic                      axi_awvalid,",
                "    output logic                      axi_awready,",
                "    input  logic [DATA_WIDTH-1:0]     axi_wdata,",
                "    input  logic [(DATA_WIDTH/8)-1:0] axi_wstrb,",
                "    input  logic                      axi_wvalid,",
                "    output logic                      axi_wready,",
                "    output logic [1:0]                axi_bresp,",
                "    output logic                      axi_bvalid,",
                "    input  logic                      axi_bready,",
                "    input  logic [ADDR_WIDTH-1:0]     axi_araddr,",
                "    input  logic [2:0]                axi_arprot,",
                "    input  logic                      axi_arvalid,",
                "    output logic                      axi_arready,",
                "    output logic [DATA_WIDTH-1:0]     axi_rdata,",
                "    output logic [1:0]                axi_rresp,",
                "    output logic                      axi_rvalid,",
                "    input  logic                      axi_rready,",
                ""
            ])

        # Module clock (if CDC enabled)
        if cdc_enabled:
            lines.extend([
                "    // Module Clock (CDC enabled)",
                "    input  logic                      module_clk,",
                ""
            ])

        # Register interface ports
        lines.append("    // Register Interface")

        for i, reg in enumerate(registers):
            signal_name = reg['signal_name']
            signal_type = reg['signal_type']
            access_mode = reg['access_mode']
            read_strobe = reg.get('read_strobe', False)
            write_strobe = reg.get('write_strobe', False)

            # Convert type to SystemVerilog
            sv_type = self._signal_type_to_sv(signal_type)

            # Determine port direction
            if access_mode == 'RO':
                direction = 'input '
            elif access_mode == 'WO':
                direction = 'output'
            else:  # RW
                # RW registers are both input and output
                # Input for reading current value, output for writing
                direction = 'output'

            # Add signal port (with enum comment if applicable)
            enum_dict = reg.get('enum_values')
            comma = ',' if i < len(registers) - 1 or read_strobe or write_strobe else ''
            if enum_dict:
                enum_comment = ' // ' + ', '.join(f"{n}={v}" for v, n in sorted(enum_dict.items()))
                lines.append(f"    {direction} {sv_type:30} {signal_name}{comma}{enum_comment}")
            else:
                lines.append(f"    {direction} {sv_type:30} {signal_name}{comma}")

            # Add strobe signals
            if read_strobe:
                comma = ',' if write_strobe or i < len(registers) - 1 else ''
                lines.append(f"    output logic                      {signal_name}_rd_strobe{comma}")

            if write_strobe:
                comma = ',' if i < len(registers) - 1 else ''
                lines.append(f"    output logic                      {signal_name}_wr_strobe{comma}")

        lines.append(");")

        return '\n'.join(lines)

    def _generate_struct_definitions(self, registers: List[Dict]) -> str:
        """Generate struct types for packed registers."""
        lines = []
        lines.append("    //-------------------------------------------------------------------------")
        lines.append("    // Struct Definitions")
        lines.append("    //-------------------------------------------------------------------------")
        lines.append("")

        for reg in registers:
            fields = reg.get('fields', [])
            if fields:
                signal_name = reg['signal_name']
                lines.append(f"    typedef struct packed {{")
                
                # Sort fields by bit_offset descending (MSB first for packed struct)
                sorted_fields = sorted(fields, key=lambda x: x.get('bit_offset', 0), reverse=True)
                
                for field in sorted_fields:
                    f_name = field['name']
                    f_width = int(field['width'])
                    
                    if f_width == 1:
                        lines.append(f"        logic        {f_name};")
                    else:
                        lines.append(f"        logic [{f_width-1}:0] {f_name};")
                
                lines.append(f"    }} {signal_name}_t;")
                lines.append("")
        
        return '\n'.join(lines)

    def _generate_internals(self, module_data: Dict) -> str:
        """Generate internal signals and parameters."""
        registers = module_data.get('registers', [])

        lines = [
            "    // AXI4-Lite response codes",
            "    localparam [1:0] OKAY   = 2'b00;",
            "    localparam [1:0] SLVERR = 2'b10;",
            ""
        ]

        # Register addresses
        lines.append("    // Register addresses")
        for reg in registers:
            signal_name = reg['signal_name'].upper()
            address = reg['address_int']
            lines.append(f"    localparam [ADDR_WIDTH-1:0] ADDR_{signal_name} = 32'h{address:08X};")

        lines.append("")
        
        # Generate struct definitions
        has_structs = any(reg.get('fields') for reg in registers)
        if has_structs:
            lines.append(self._generate_struct_definitions(registers))
            lines.append("")

        # State machine enum
        lines.extend([
            "    // AXI4-Lite state machine",
            "    typedef enum logic [2:0] {",
            "        IDLE,",
            "        WRITE_ADDR,",
            "        WRITE_DATA,",
            "        WRITE_RESP,",
            "        READ_ADDR,",
            "        READ_DATA",
            "    } axi_state_t;",
            "",
            "    axi_state_t state, next_state;",
            ""
        ])

        # Internal registers
        lines.append("    // Internal registers")
        for reg in registers:
            if reg['access_mode'] in ['RW', 'WO']:
                signal_name = reg['signal_name']
                if reg.get('fields'):
                     lines.append(f"    {signal_name}_t{' '*20} {signal_name}_reg;")
                else:
                    signal_type = reg['signal_type']
                    sv_type = self._signal_type_to_sv(signal_type)
                    lines.append(f"    {sv_type:30} {signal_name}_reg;")

        lines.append("")

        use_axion_types = module_data.get('use_axion_types', False)

        # Other internal signals
        lines.extend([
            "    // Internal signals",
            "    logic [DATA_WIDTH-1:0] rdata_reg;",
            "    logic [1:0]            rresp_reg;",
            "    logic [1:0]            bresp_reg;",
            "    logic [ADDR_WIDTH-1:0] write_addr;",
            "    logic [ADDR_WIDTH-1:0] read_addr;",
            ""
        ])

        if use_axion_types:
            lines.extend([
                "    // Intermediate signals unpacked from axi_m2s / axi_s2m record ports",
                "    logic [ADDR_WIDTH-1:0]     axi_awaddr;",
                "    logic [2:0]                axi_awprot;",
                "    logic                      axi_awvalid;",
                "    logic                      axi_awready;",
                "    logic [DATA_WIDTH-1:0]     axi_wdata;",
                "    logic [(DATA_WIDTH/8)-1:0] axi_wstrb;",
                "    logic                      axi_wvalid;",
                "    logic                      axi_wready;",
                "    logic [1:0]                axi_bresp;",
                "    logic                      axi_bvalid;",
                "    logic                      axi_bready;",
                "    logic [ADDR_WIDTH-1:0]     axi_araddr;",
                "    logic [2:0]                axi_arprot;",
                "    logic                      axi_arvalid;",
                "    logic                      axi_arready;",
                "    logic [DATA_WIDTH-1:0]     axi_rdata;",
                "    logic [1:0]                axi_rresp;",
                "    logic                      axi_rvalid;",
                "    logic                      axi_rready;",
                "",
                "    // Sink for unused intermediate signals to silence lint warnings",
                "    logic _unused_ok;",
                "    assign _unused_ok = &{1'b0, axi_awprot, axi_arprot, axi_wstrb, axi_wdata, 1'b0};",
                ""
            ])
        else:
            lines.extend([
                "    // Sink for unused signals to silence lint warnings",
                "    logic _unused_ok;",
                "    assign _unused_ok = &{1'b0, axi_awprot, axi_arprot, axi_wstrb, axi_wdata, 1'b0};",
                ""
            ])

        # Strobe signals
        has_strobes = any(reg.get('read_strobe') or reg.get('write_strobe') for reg in registers)
        if has_strobes:
            lines.append("    // Strobe signals")
            for reg in registers:
                if reg.get('write_strobe'):
                    lines.append(f"    logic {reg['signal_name']}_wr_strobe_int;")
            lines.append("")

        return '\n'.join(lines)

    def _generate_cdc_logic(self, module_data: Dict) -> str:
        """Generate CDC synchronizer logic."""
        cdc_stages = module_data.get('cdc_stages', 2)
        registers = module_data.get('registers', [])

        lines = [
            "    //-------------------------------------------------------------------------",
            "    // Clock Domain Crossing (CDC) Synchronizers",
            "    //-------------------------------------------------------------------------",
            ""
        ]

        # 1. Input Synchronizers (RO): Module -> AXI (axi_aclk domain)
        # ---------------------------------------------------------------------
        lines.append("    // Input Synchronizers (Module -> AXI)")
        lines.append("    // -----------------------------------")
        
        has_ro = False
        for reg in registers:
            if reg['access_mode'] == 'RO':
                has_ro = True
                signal_name = reg['signal_name']
                signal_type = reg['signal_type']
                sv_type = self._signal_type_to_sv(signal_type)

                lines.append(f"    // CDC for {signal_name} (RO)")
                lines.append(f"    {sv_type:30} {signal_name}_sync [{cdc_stages}];")
        
        if has_ro:
            lines.append("")
            lines.append(f"    always_ff @(posedge axi_aclk or negedge axi_aresetn) begin")
            lines.append(f"        if (!axi_aresetn) begin")
            for reg in registers:
                if reg['access_mode'] == 'RO':
                     lines.append(f"            {reg['signal_name']}_sync <= '{{default: '0}};")
            lines.append(f"        end else begin")
            for reg in registers:
                if reg['access_mode'] == 'RO':
                    lines.append(f"            {reg['signal_name']}_sync[0] <= {reg['signal_name']};")
                    for i in range(1, cdc_stages):
                        lines.append(f"            {reg['signal_name']}_sync[{i}] <= {reg['signal_name']}_sync[{i-1}];")
            lines.append(f"        end")
            lines.append(f"    end")
        else:
             lines.append("    // No RO registers found")
        
        lines.append("")

        # 2. Output Synchronizers (RW/WO): AXI -> Module (module_clk domain)
        # ----------------------------------------------------------------------
        lines.append("    // Output Synchronizers (AXI -> Module)")
        lines.append("    // ------------------------------------")
        
        has_out = False
        for reg in registers:
            if reg['access_mode'] in ['RW', 'WO']:
                has_out = True
                signal_name = reg['signal_name']
                signal_type = reg['signal_type']
                sv_type = self._signal_type_to_sv(signal_type)

                lines.append(f"    // CDC for {signal_name} ({reg['access_mode']})")
                lines.append(f"    {sv_type:30} {signal_name}_sync [{cdc_stages}];")

        if has_out:
            lines.append("")
            lines.append(f"    always_ff @(posedge module_clk or negedge axi_aresetn) begin")
            lines.append(f"        if (!axi_aresetn) begin")
            for reg in registers:
                if reg['access_mode'] in ['RW', 'WO']:
                    # Use '0 because SystemVerilog unpacked arrays rely on default: '0 or strict loop
                    # Using {default: '0} is safer for unpacked
                    lines.append(f"            {reg['signal_name']}_sync <= '{{default: '0}};")
            lines.append(f"        end else begin")
            for reg in registers:
                if reg['access_mode'] in ['RW', 'WO']:
                    lines.append(f"            {reg['signal_name']}_sync[0] <= {reg['signal_name']}_reg;")
                    for i in range(1, cdc_stages):
                        lines.append(f"            {reg['signal_name']}_sync[{i}] <= {reg['signal_name']}_sync[{i-1}];")
            lines.append(f"        end")
            lines.append(f"    end")
        else:
             lines.append("    // No RW/WO registers found")

        return '\n'.join(lines)

    def _generate_axi_state_machine(self, module_data: Dict) -> str:
        """Generate AXI4-Lite protocol state machine."""
        lines = [
            "    //-------------------------------------------------------------------------",
            "    // AXI4-Lite State Machine",
            "    //-------------------------------------------------------------------------",
            "",
            "    // State register",
            "    always_ff @(posedge axi_aclk or negedge axi_aresetn) begin",
            "        if (!axi_aresetn) begin",
            "            state <= IDLE;",
            "        end else begin",
            "            state <= next_state;",
            "        end",
            "    end",
            "",
            "    // Next state logic",
            "    always_comb begin",
            "        next_state = state;",
            "",
            "        case (state)",
            "            IDLE: begin",
            "                if (axi_awvalid) begin",
            "                    next_state = WRITE_ADDR;",
            "                end else if (axi_arvalid) begin",
            "                    next_state = READ_ADDR;",
            "                end",
            "            end",
            "",
            "            WRITE_ADDR: begin",
            "                if (axi_wvalid) begin",
            "                    next_state = WRITE_DATA;",
            "                end",
            "            end",
            "",
            "            WRITE_DATA: begin",
            "                next_state = WRITE_RESP;",
            "            end",
            "",
            "            WRITE_RESP: begin",
            "                if (axi_bready) begin",
            "                    next_state = IDLE;",
            "                end",
            "            end",
            "",
            "            READ_ADDR: begin",
            "                next_state = READ_DATA;",
            "            end",
            "",
            "            READ_DATA: begin",
            "                if (axi_rready) begin",
            "                    next_state = IDLE;",
            "                end",
            "            end",
            "",
            "            default: begin",
            "                next_state = IDLE;",
            "            end",
            "        endcase",
            "    end",
            "",
            "    // Output logic",
            "    assign axi_awready = (state == WRITE_ADDR);",
            "    assign axi_wready  = (state == WRITE_DATA);",
            "    assign axi_bvalid  = (state == WRITE_RESP);",
            "    assign axi_bresp   = bresp_reg;",
            "    assign axi_arready = (state == READ_ADDR);",
            "    assign axi_rvalid  = (state == READ_DATA);",
            "    assign axi_rdata   = rdata_reg;",
            "    assign axi_rresp   = rresp_reg;",
            ""
        ]

        return '\n'.join(lines)

    def _generate_register_logic(self, module_data: Dict) -> str:
        """Generate register read/write logic."""
        registers = module_data.get('registers', [])
        cdc_enabled = module_data.get('cdc_enabled', False)
        cdc_stages = module_data.get('cdc_stages', 2)

        lines = [
            "    //-------------------------------------------------------------------------",
            "    // Register Logic",
            "    //-------------------------------------------------------------------------",
            "",
            "    // Address capture",
            "    always_ff @(posedge axi_aclk or negedge axi_aresetn) begin",
            "        if (!axi_aresetn) begin",
            "            write_addr <= '0;",
            "            read_addr <= '0;",
            "        end else begin",
            "            if (state == WRITE_ADDR && axi_awvalid) begin",
            "                write_addr <= axi_awaddr;",
            "            end",
            "            if (state == READ_ADDR && axi_arvalid) begin",
            "                read_addr <= axi_araddr;",
            "            end",
            "        end",
            "    end",
            ""
        ]

        # Write logic
        lines.extend([
            "    // Register write logic",
            "    always_ff @(posedge axi_aclk or negedge axi_aresetn) begin",
            "        if (!axi_aresetn) begin"
        ])

        # Reset all writable registers
        for reg in registers:
            if reg['access_mode'] in ['RW', 'WO']:
                default_val = reg.get('default_value')
                if default_val is None:
                    default_val = reg.get('default')
                width = reg.get('signal_width', 32)

                if default_val is not None:
                    if isinstance(default_val, str) and (default_val.startswith('0x') or default_val.startswith('0X')):
                        # Hex string
                        hex_val = default_val[2:]
                        lines.append(f"            {reg['signal_name']}_reg <= {width}'h{hex_val};")
                    else:
                        # Decimal/Integer
                        lines.append(f"            {reg['signal_name']}_reg <= {width}'d{default_val};")
                else:
                    lines.append(f"            {reg['signal_name']}_reg <= '0;")

        # Reset write strobes
        for reg in registers:
            if reg.get('write_strobe'):
                lines.append(f"            {reg['signal_name']}_wr_strobe_int <= 1'b0;")

        lines.append("            bresp_reg <= OKAY;")
        lines.append("        end else begin")

        # Clear strobes
        for reg in registers:
            if reg.get('write_strobe'):
                lines.append(f"            {reg['signal_name']}_wr_strobe_int <= 1'b0;")

        lines.extend([
            "",
            "            if (state == WRITE_DATA && axi_wvalid) begin",
            "                case (write_addr)"
        ])

        # Write cases for each register
        for reg in registers:
            signal_name = reg['signal_name']
            signal_name_upper = signal_name.upper()
            access_mode = reg['access_mode']
            width = reg.get('signal_width', 32)
            num_words = (width + 31) // 32

            for i in range(num_words):
                # Calculate address offset for this word
                addr_suffix = f" + 32'h{i*4:X}" if i > 0 else ""
                lines.append(f"                    ADDR_{signal_name_upper}{addr_suffix}: begin")

                if access_mode == 'RO':
                    # Read-only: return error
                    lines.append("                        bresp_reg <= SLVERR;")
                elif access_mode in ['RW', 'WO']:
                    # Writable: update register
                    low = i * 32
                    high = min((i + 1) * 32 - 1, width - 1)
                    slice_width = high - low + 1

                    if width <= 32:
                        if width == 32:
                            lines.append(f"                        {signal_name}_reg <= axi_wdata;")
                        else:
                            lines.append(f"                        {signal_name}_reg <= axi_wdata[{width-1}:0];")
                    else:
                        # Wide register logic
                        if slice_width == 32:
                            lines.append(f"                        {signal_name}_reg[{high}:{low}] <= axi_wdata;")
                        else:
                            lines.append(f"                        {signal_name}_reg[{high}:{low}] <= axi_wdata[{slice_width-1}:0];")

                    if reg.get('write_strobe'):
                        lines.append(f"                        {signal_name}_wr_strobe_int <= 1'b1;")

                    lines.append("                        bresp_reg <= OKAY;")

                lines.append("                    end")

        lines.extend([
            "                    default: begin",
            "                        bresp_reg <= SLVERR;",
            "                    end",
            "                endcase",
            "            end",
            "        end",
            "    end",
            ""
        ])

        # Read logic
        lines.extend([
            "    // Register read logic",
            "    always_comb begin",
            "        rdata_reg = '0;",
            "        rresp_reg = OKAY;",
            "",
            "        case (read_addr)"
        ])

        # Read cases for each register
        for reg in registers:
            signal_name = reg['signal_name']
            signal_name_upper = signal_name.upper()
            access_mode = reg['access_mode']
            width = reg.get('signal_width', 32)
            num_words = (width + 31) // 32

            for i in range(num_words):
                addr_suffix = f" + 32'h{i*4:X}" if i > 0 else ""
                lines.append(f"            ADDR_{signal_name_upper}{addr_suffix}: begin")

                if access_mode == 'WO':
                    # Write-only: return error
                    lines.append("                rresp_reg = SLVERR;")
                else:
                    # Determine source signal
                    if cdc_enabled and access_mode == 'RO':
                        source = f"{signal_name}_sync[{cdc_stages-1}]"
                    elif access_mode == 'RO':
                        source = signal_name
                    else:
                        source = f"{signal_name}_reg"

                    low = i * 32
                    high = min((i + 1) * 32 - 1, width - 1)
                    slice_width = high - low + 1

                    if width <= 32:
                        if width == 32:
                            lines.append(f"                rdata_reg = {source};")
                        else:
                            lines.append(f"                rdata_reg = {{{{{32 - width}'{{1'b0}}}}, {source}}};")
                    else:
                        # Wide register logic
                        if slice_width == 32:
                             lines.append(f"                rdata_reg = {source}[{high}:{low}];")
                        else:
                             padding = 32 - slice_width
                             lines.append(f"                rdata_reg = {{{{{padding}'{{1'b0}}}}, {source}[{high}:{low}]}};")

                lines.append("            end")

        lines.extend([
            "            default: begin",
            "                rresp_reg = SLVERR;",
            "            end",
            "        endcase",
            "    end",
            ""
        ])

        return '\n'.join(lines)

    def _generate_output_assignments(self, module_data: Dict) -> str:
        """Generate output port assignments."""
        registers = module_data.get('registers', [])
        cdc_enabled = module_data.get('cdc_enabled', False)
        cdc_stages = module_data.get('cdc_stages', 2)
        use_axion_types = module_data.get('use_axion_types', False)

        lines = [
            "    //-------------------------------------------------------------------------",
            "    // Output Assignments",
            "    //-------------------------------------------------------------------------",
            ""
        ]

        if use_axion_types:
            lines.extend([
                "    // Unpack AXI M2S record into intermediate signals",
                "    assign axi_awaddr  = axi_m2s.awaddr;",
                "    assign axi_awprot  = axi_m2s.awprot;",
                "    assign axi_awvalid = axi_m2s.awvalid;",
                "    assign axi_wdata   = axi_m2s.wdata;",
                "    assign axi_wstrb   = axi_m2s.wstrb;",
                "    assign axi_wvalid  = axi_m2s.wvalid;",
                "    assign axi_bready  = axi_m2s.bready;",
                "    assign axi_araddr  = axi_m2s.araddr;",
                "    assign axi_arprot  = axi_m2s.arprot;",
                "    assign axi_arvalid = axi_m2s.arvalid;",
                "    assign axi_rready  = axi_m2s.rready;",
                "",
                "    // Pack intermediate signals into AXI S2M record",
                "    assign axi_s2m.awready = axi_awready;",
                "    assign axi_s2m.wready  = axi_wready;",
                "    assign axi_s2m.bresp   = axi_bresp;",
                "    assign axi_s2m.bvalid  = axi_bvalid;",
                "    assign axi_s2m.arready = axi_arready;",
                "    assign axi_s2m.rdata   = axi_rdata;",
                "    assign axi_s2m.rresp   = axi_rresp;",
                "    assign axi_s2m.rvalid  = axi_rvalid;",
                ""
            ])

        for reg in registers:
            signal_name = reg['signal_name']
            access_mode = reg['access_mode']

            if access_mode in ['RW', 'WO']:
                if cdc_enabled:
                     # Use the last stage of the synchronizer
                     lines.append(f"    assign {signal_name} = {signal_name}_sync[{cdc_stages-1}];")
                else:
                     lines.append(f"    assign {signal_name} = {signal_name}_reg;")

            # Strobe assignments
            if reg.get('write_strobe'):
                lines.append(f"    assign {signal_name}_wr_strobe = {signal_name}_wr_strobe_int;")

            if reg.get('read_strobe'):
                # Read strobe is asserted when reading this register
                signal_name_upper = signal_name.upper()
                lines.append(f"    assign {signal_name}_rd_strobe = (state == READ_DATA && read_addr == ADDR_{signal_name_upper});")

        return '\n'.join(lines)

    def _signal_type_to_sv(self, signal_type: str) -> str:
        """
        Convert internal signal type format to SystemVerilog type.

        Args:
            signal_type: Internal format like "[31:0]", "[5:0]", "[0:0]"

        Returns:
            SystemVerilog type string like "logic [31:0]" or "logic"

        Examples:
            "[31:0]" -> "logic [31:0]"
            "[5:0]"  -> "logic [5:0]"
            "[0:0]"  -> "logic"
        """
        import re
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            if high == 0 and low == 0:
                return "logic"
            else:
                return f"logic [{high}:{low}]"
        # Default fallback
        return "logic [31:0]"
