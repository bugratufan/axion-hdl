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
            sections.append(self._generate_strobe_cdc_logic(module_data))

        # Packed register field mapping (combined read values)
        if module_data.get('packed_registers', []):
            sections.append(self._generate_packed_mapping(module_data))

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

            enum_entries = []
            for val, name in sorted(enum_dict.items()):
                safe_name = SystemVerilogUtils.sanitize_identifier(name)
                bin_literal = format(int(val), f'0{width}b')
                if width == 1:
                    entry = f"    {safe_name} = 1'b{bin_literal}"
                else:
                    entry = f"    {safe_name} = {width}'b{bin_literal}"
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

    @staticmethod
    def _packed_ro_fields(packed_reg: Dict) -> List[Dict]:
        """Return the RO fields of a packed register (inputs from module domain)."""
        return [f for f in packed_reg.get('fields', []) if f['access_mode'] == 'RO']

    @staticmethod
    def _packed_writable_fields(packed_reg: Dict) -> List[Dict]:
        """Return the RW/WO fields of a packed register (outputs to module domain)."""
        return [f for f in packed_reg.get('fields', []) if f['access_mode'] in ('RW', 'WO')]

    @staticmethod
    def _packed_has_writable_fields(packed_reg: Dict) -> bool:
        """True if the packed register has RW/WO fields (outputs to module domain)."""
        return any(f['access_mode'] in ('RW', 'WO') for f in packed_reg.get('fields', []))

    @staticmethod
    def _get_strobe_cdc_names(module_data: Dict):
        """
        Collect the base names of every read/write strobe that needs CDC.

        Unlike VHDL, SystemVerilog's `registers` list already includes the
        packed-register container entries (is_packed=True) alongside plain
        registers, and both carry read_strobe/write_strobe directly - so a
        single pass over `registers` (no is_packed filtering, no separate
        walk of packed_registers) covers both cases without double-counting.
        """
        rd_names = []
        wr_names = []
        for reg in module_data.get('registers', []):
            if reg.get('read_strobe'):
                rd_names.append(reg['signal_name'])
            if reg.get('write_strobe'):
                wr_names.append(reg['signal_name'])
        return rd_names, wr_names

    @staticmethod
    def _field_width(field: Dict) -> int:
        """Width in bits of a packed register field."""
        if 'bit_high' in field and 'bit_low' in field:
            return field['bit_high'] - field['bit_low'] + 1
        return int(field.get('width', 1))

    @staticmethod
    def _field_sv_type(field: Dict) -> str:
        """SystemVerilog type of a packed register field."""
        width = SystemVerilogGenerator._field_width(field)
        return "logic" if width == 1 else f"logic [{width - 1}:0]"

    @staticmethod
    def _field_slice(field: Dict) -> str:
        """Bit-select into the 32-bit parent register for a packed field."""
        high = field['bit_high']
        low = field['bit_low']
        return f"[{low}]" if high == low else f"[{high}:{low}]"

    @staticmethod
    def _reg_is_writable(reg: Dict) -> bool:
        """True if the register has AXI-writable storage (RW/WO, or packed with RW/WO fields)."""
        if reg.get('is_packed'):
            return SystemVerilogGenerator._packed_has_writable_fields(reg)
        return reg['access_mode'] in ('RW', 'WO')

    @staticmethod
    def _get_reg_width(reg: Dict) -> int:
        """
        Width in bits of a register, regardless of input format.

        Annotation-parsed registers carry 'signal_width'; structured inputs
        (YAML/JSON/TOML/XML) carry 'width' and a VHDL-style 'signal_type'.
        """
        width = reg.get('signal_width')
        if width:
            return int(width)
        signal_type = reg.get('signal_type', '')
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            return int(match.group(1)) - int(match.group(2)) + 1
        match = re.match(r'std_logic_vector\((\d+)\s+downto\s+(\d+)\)', signal_type)
        if match:
            return int(match.group(1)) - int(match.group(2)) + 1
        if signal_type.strip() == 'std_logic':
            return 1
        return int(reg.get('width', 32))

    def _generate_module_declaration(self, module_data: Dict) -> str:
        """Generate module declaration with parameters and ports."""
        module_name = module_data.get('name', 'unnamed_module')
        registers = module_data.get('registers', [])
        packed_registers = module_data.get('packed_registers', [])
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

        # Register interface ports.
        # Collect (declaration, comment) pairs first so comma placement stays
        # correct regardless of how many regular/packed/strobe ports follow.
        port_entries = []

        for reg in registers:
            # Packed registers expose per-field ports instead of one word port
            if reg.get('is_packed'):
                continue

            signal_name = reg['signal_name']
            signal_type = reg['signal_type']
            access_mode = reg['access_mode']

            # Convert type to SystemVerilog
            sv_type = self._signal_type_to_sv(signal_type)

            # Determine port direction
            if access_mode == 'RO':
                direction = 'input '
            else:  # WO or RW: AXI writes, module reads
                direction = 'output'

            enum_dict = reg.get('enum_values')
            comment = ''
            if enum_dict:
                comment = ' // ' + ', '.join(f"{n}={v}" for v, n in sorted(enum_dict.items()))
            port_entries.append((f"    {direction} {sv_type:30} {signal_name}", comment))

            if reg.get('read_strobe', False):
                port_entries.append((f"    output logic                      {signal_name}_rd_strobe", ''))
            if reg.get('write_strobe', False):
                port_entries.append((f"    output logic                      {signal_name}_wr_strobe", ''))

        # Packed register (subregister) field ports: <reg_name>_<field_name>
        packed_entries = []
        for packed_reg in packed_registers:
            # Aggregated parent-register strobes
            if packed_reg.get('read_strobe'):
                packed_entries.append((f"    output logic                      {packed_reg['reg_name']}_rd_strobe", ''))
            if packed_reg.get('write_strobe'):
                packed_entries.append((f"    output logic                      {packed_reg['reg_name']}_wr_strobe", ''))

            for field in packed_reg.get('fields', []):
                sv_type = self._field_sv_type(field)
                direction = 'input ' if field['access_mode'] == 'RO' else 'output'

                desc = field.get('description', '')
                enum_dict = field.get('enum_values')
                if enum_dict:
                    enum_str = ', '.join(f"{n}={v}" for v, n in sorted(enum_dict.items()))
                    desc = f"{desc} ({enum_str})" if desc else enum_str
                comment = f" // {desc}" if desc else ''

                sig_name = f"{packed_reg['reg_name']}_{field['name']}"
                packed_entries.append((f"    {direction} {sv_type:30} {sig_name}", comment))

        lines.append("    // Register Interface")
        all_entries = port_entries + packed_entries
        for i, (decl, comment) in enumerate(all_entries):
            if packed_entries and i == len(port_entries):
                lines.append("")
                lines.append("    // Packed Register Fields (Subregisters)")
            comma = ',' if i < len(all_entries) - 1 else ''
            lines.append(f"{decl}{comma}{comment}")

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
            # is_packed registers are decomposed into per-field ports and a
            # 32-bit storage word instead of a struct-typed register.
            if fields and not reg.get('is_packed'):
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
        packed_registers = module_data.get('packed_registers', [])

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
        has_structs = any(reg.get('fields') and not reg.get('is_packed') for reg in registers)
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
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['RW', 'WO']:
                signal_name = reg['signal_name']
                if reg.get('fields'):
                     lines.append(f"    {signal_name}_t{' '*20} {signal_name}_reg;")
                else:
                    signal_type = reg['signal_type']
                    sv_type = self._signal_type_to_sv(signal_type)
                    lines.append(f"    {sv_type:30} {signal_name}_reg;")

        # Packed register internals: AXI-domain storage word for RW/WO bits
        # and the combined value returned on AXI reads.
        if packed_registers:
            lines.append("")
            lines.append("    // Packed register internals (storage for RW/WO bits, combined read value)")
            for pr in packed_registers:
                if self._packed_has_writable_fields(pr):
                    lines.append(f"    logic [31:0]                   {pr['reg_name']}_reg;")
                lines.append(f"    logic [31:0]                   {pr['reg_name']}_val;")

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

        # Packed storage words are only partially consumed when some bit
        # positions belong to RO fields or gaps; sink them to keep lint clean.
        packed_sink = ''.join(
            f", {pr['reg_name']}_reg" for pr in packed_registers
            if self._packed_has_writable_fields(pr)
        )

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
                f"    assign _unused_ok = &{{1'b0, axi_awprot, axi_arprot, axi_wstrb, axi_wdata{packed_sink}, 1'b0}};",
                ""
            ])
        else:
            lines.extend([
                "    // Sink for unused signals to silence lint warnings",
                "    logic _unused_ok;",
                f"    assign _unused_ok = &{{1'b0, axi_awprot, axi_arprot, axi_wstrb, axi_wdata{packed_sink}, 1'b0}};",
                ""
            ])

        # Strobe signals
        cdc_enabled = module_data.get('cdc_enabled', False)
        cdc_stages = module_data.get('cdc_stages', 2)
        has_strobes = any(reg.get('read_strobe') or reg.get('write_strobe') for reg in registers)
        if has_strobes:
            lines.append("    // Strobe signals")
            for reg in registers:
                if reg.get('write_strobe'):
                    lines.append(f"    logic {reg['signal_name']}_wr_strobe_int;")
                if reg.get('read_strobe') and cdc_enabled:
                    lines.append(f"    logic {reg['signal_name']}_rd_strobe_int;")
            lines.append("")

        # Strobe pulse CDC: toggle synchronizer (clock-ratio independent).
        # Strobes are single-cycle pulses, so the level-signal N-stage sync
        # used for register data is not safe for them (a fast pulse can be
        # missed entirely by a slower destination clock). Each strobe gets
        # its own toggle flip-flop in axi_aclk, an ASYNC_REG-tagged sync
        # chain into module_clk, and an edge detector that regenerates a
        # clean single-cycle pulse regardless of the module_clk/axi_aclk
        # ratio.
        if cdc_enabled:
            rd_names, wr_names = self._get_strobe_cdc_names(module_data)
            if rd_names or wr_names:
                lines.append("    // Strobe pulse CDC (toggle synchronizer)")
                for name in rd_names:
                    lines.append(f"    logic {name}_rd_toggle;")
                    lines.append(f"    (* ASYNC_REG = \"TRUE\" *) logic {name}_rd_toggle_sync [{cdc_stages}];")
                    lines.append(f"    logic {name}_rd_toggle_prev;")
                for name in wr_names:
                    lines.append(f"    logic {name}_wr_toggle;")
                    lines.append(f"    (* ASYNC_REG = \"TRUE\" *) logic {name}_wr_toggle_sync [{cdc_stages}];")
                    lines.append(f"    logic {name}_wr_toggle_prev;")
                lines.append("")

        return '\n'.join(lines)

    def _generate_cdc_logic(self, module_data: Dict) -> str:
        """Generate CDC synchronizer logic."""
        cdc_stages = module_data.get('cdc_stages', 2)
        registers = module_data.get('registers', [])
        packed_registers = module_data.get('packed_registers', [])

        lines = [
            "    //-------------------------------------------------------------------------",
            "    // Clock Domain Crossing (CDC) Synchronizers",
            "    //-------------------------------------------------------------------------",
            ""
        ]

        # 1. Input Synchronizers (RO): Module -> AXI (axi_aclk domain)
        #    Full RO registers and RO fields of packed registers.
        #    Chains as (base_name, sv_type, source_expr, comment) tuples.
        # ---------------------------------------------------------------------
        ro_chains = []
        for reg in registers:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] == 'RO':
                sv_type = self._signal_type_to_sv(reg['signal_type'])
                ro_chains.append((reg['signal_name'], sv_type, reg['signal_name'], 'RO'))
        for pr in packed_registers:
            for field in self._packed_ro_fields(pr):
                sig_name = f"{pr['reg_name']}_{field['name']}"
                ro_chains.append((sig_name, self._field_sv_type(field), sig_name, 'packed RO field'))

        lines.append("    // Input Synchronizers (Module -> AXI)")
        lines.append("    // -----------------------------------")

        for name, sv_type, _, kind in ro_chains:
            lines.append(f"    // CDC for {name} ({kind})")
            lines.append(f"    (* ASYNC_REG = \"TRUE\" *) {sv_type:30} {name}_sync [{cdc_stages}];")

        if ro_chains:
            lines.append("")
            lines.append(f"    always_ff @(posedge axi_aclk or negedge axi_aresetn) begin")
            lines.append(f"        if (!axi_aresetn) begin")
            for name, _, _, _ in ro_chains:
                for i in range(cdc_stages):
                    lines.append(f"            {name}_sync[{i}] <= '0;")
            lines.append(f"        end else begin")
            for name, _, source, _ in ro_chains:
                lines.append(f"            {name}_sync[0] <= {source};")
                for i in range(1, cdc_stages):
                    lines.append(f"            {name}_sync[{i}] <= {name}_sync[{i-1}];")
            lines.append(f"        end")
            lines.append(f"    end")
        else:
             lines.append("    // No RO registers found")

        lines.append("")

        # 2. Output Synchronizers (RW/WO): AXI -> Module (module_clk domain)
        #    Full RW/WO registers and, for packed registers with writable
        #    fields, one chain of the whole 32-bit storage word; field outputs
        #    are then sliced from the last stage.
        # ----------------------------------------------------------------------
        out_chains = []
        for reg in registers:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['RW', 'WO']:
                sv_type = self._signal_type_to_sv(reg['signal_type'])
                out_chains.append((reg['signal_name'], sv_type,
                                   f"{reg['signal_name']}_reg", reg['access_mode']))
        for pr in packed_registers:
            if self._packed_has_writable_fields(pr):
                out_chains.append((f"{pr['reg_name']}_reg", "logic [31:0]",
                                   f"{pr['reg_name']}_reg", 'packed RW/WO storage'))

        lines.append("    // Output Synchronizers (AXI -> Module)")
        lines.append("    // ------------------------------------")

        for name, sv_type, _, kind in out_chains:
            lines.append(f"    // CDC for {name} ({kind})")
            lines.append(f"    (* ASYNC_REG = \"TRUE\" *) {sv_type:30} {name}_sync [{cdc_stages}];")

        if out_chains:
            lines.append("")
            lines.append(f"    always_ff @(posedge module_clk or negedge axi_aresetn) begin")
            lines.append(f"        if (!axi_aresetn) begin")
            for name, _, _, _ in out_chains:
                for i in range(cdc_stages):
                    lines.append(f"            {name}_sync[{i}] <= '0;")
            lines.append(f"        end else begin")
            for name, _, source, _ in out_chains:
                lines.append(f"            {name}_sync[0] <= {source};")
                for i in range(1, cdc_stages):
                    lines.append(f"            {name}_sync[{i}] <= {name}_sync[{i-1}];")
            lines.append(f"        end")
            lines.append(f"    end")
        else:
             lines.append("    // No RW/WO registers found")

        return '\n'.join(lines)

    def _generate_strobe_cdc_logic(self, module_data: Dict) -> str:
        """
        Generate toggle-synchronizer CDC for read/write strobe pulses.

        Strobes are single-cycle pulses decoded in the axi_aclk domain. The
        plain N-stage level synchronizer used for register data is not safe
        for them: if module_clk is slower than axi_aclk, a fast pulse can be
        sampled as high for zero destination cycles and missed entirely.
        Each strobe is instead converted to a toggle in axi_aclk,
        resynchronized into module_clk through an ASYNC_REG-tagged chain,
        and turned back into a clean single-cycle pulse via edge detection.
        This works correctly regardless of the module_clk/axi_aclk frequency
        ratio in either direction.
        """
        cdc_stages = module_data.get('cdc_stages', 2)
        rd_names, wr_names = self._get_strobe_cdc_names(module_data)

        if not rd_names and not wr_names:
            return ""

        lines = [
            "    //-------------------------------------------------------------------------",
            "    // Strobe Pulse CDC (toggle synchronizer, clock-ratio independent)",
            "    // axi_aclk: strobe pulse -> toggle flip-flop",
            "    // module_clk: toggle sync chain -> edge detect -> regenerated pulse",
            "    //-------------------------------------------------------------------------",
            "",
            "    // CDC: strobe toggle generation (axi_aclk domain)",
            "    always_ff @(posedge axi_aclk or negedge axi_aresetn) begin",
            "        if (!axi_aresetn) begin",
        ]
        for name in rd_names:
            lines.append(f"            {name}_rd_toggle <= 1'b0;")
        for name in wr_names:
            lines.append(f"            {name}_wr_toggle <= 1'b0;")
        lines.append("        end else begin")
        for name in rd_names:
            lines.append(f"            if ({name}_rd_strobe_int) {name}_rd_toggle <= ~{name}_rd_toggle;")
        for name in wr_names:
            lines.append(f"            if ({name}_wr_strobe_int) {name}_wr_toggle <= ~{name}_wr_toggle;")
        lines.extend([
            "        end",
            "    end",
            "",
            "    // CDC: strobe toggle resync and pulse regeneration (module_clk domain)",
            "    always_ff @(posedge module_clk or negedge axi_aresetn) begin",
            "        if (!axi_aresetn) begin",
        ])
        for name in rd_names:
            for stage in range(cdc_stages):
                lines.append(f"            {name}_rd_toggle_sync[{stage}] <= 1'b0;")
            lines.append(f"            {name}_rd_toggle_prev <= 1'b0;")
            lines.append(f"            {name}_rd_strobe <= 1'b0;")
        for name in wr_names:
            for stage in range(cdc_stages):
                lines.append(f"            {name}_wr_toggle_sync[{stage}] <= 1'b0;")
            lines.append(f"            {name}_wr_toggle_prev <= 1'b0;")
            lines.append(f"            {name}_wr_strobe <= 1'b0;")
        lines.append("        end else begin")
        for name in rd_names:
            lines.append(f"            {name}_rd_toggle_sync[0] <= {name}_rd_toggle;")
            for stage in range(1, cdc_stages):
                lines.append(f"            {name}_rd_toggle_sync[{stage}] <= {name}_rd_toggle_sync[{stage-1}];")
            lines.append(f"            {name}_rd_toggle_prev <= {name}_rd_toggle_sync[{cdc_stages-1}];")
            lines.append(f"            {name}_rd_strobe <= {name}_rd_toggle_sync[{cdc_stages-1}] ^ {name}_rd_toggle_prev;")
        for name in wr_names:
            lines.append(f"            {name}_wr_toggle_sync[0] <= {name}_wr_toggle;")
            for stage in range(1, cdc_stages):
                lines.append(f"            {name}_wr_toggle_sync[{stage}] <= {name}_wr_toggle_sync[{stage-1}];")
            lines.append(f"            {name}_wr_toggle_prev <= {name}_wr_toggle_sync[{cdc_stages-1}];")
            lines.append(f"            {name}_wr_strobe <= {name}_wr_toggle_sync[{cdc_stages-1}] ^ {name}_wr_toggle_prev;")
        lines.extend([
            "        end",
            "    end",
        ])

        return '\n'.join(lines)

    def _generate_packed_mapping(self, module_data: Dict) -> str:
        """
        Generate the packed register field mapping.

        Builds the combined AXI read value for each packed register:
        RW/WO bit positions read back from the axi_aclk-domain storage word,
        RO bit positions come from the field input ports (via their
        axi_aclk-domain synchronizer chains when CDC is enabled).
        """
        packed_registers = module_data.get('packed_registers', [])
        cdc_enabled = module_data.get('cdc_enabled', False)
        cdc_stages = module_data.get('cdc_stages', 2)
        last = cdc_stages - 1

        lines = [
            "    //-------------------------------------------------------------------------",
            "    // Packed Register Field Mapping",
            "    //-------------------------------------------------------------------------",
            ""
        ]

        for pr in packed_registers:
            reg_name = pr['reg_name']
            lines.append(f"    // Combined read value for {reg_name}")
            lines.append("    always_comb begin")
            lines.append(f"        {reg_name}_val = '0;")
            for field in pr.get('fields', []):
                dest = f"{reg_name}_val{self._field_slice(field)}"
                sig_name = f"{reg_name}_{field['name']}"
                if field['access_mode'] == 'RO':
                    # RO bits come from the module inputs (synced when CDC on)
                    source = f"{sig_name}_sync[{last}]" if cdc_enabled else sig_name
                else:
                    # RW/WO bits read back from the axi_aclk-domain storage
                    source = f"{reg_name}_reg{self._field_slice(field)}"
                lines.append(f"        {dest} = {source};")
            lines.append("    end")
            lines.append("")

        return '\n'.join(lines).rstrip()

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
            if self._reg_is_writable(reg):
                default_val = reg.get('default_value')
                if default_val is None:
                    default_val = reg.get('default')
                width = self._get_reg_width(reg)

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
            width = self._get_reg_width(reg)
            num_words = (width + 31) // 32

            for i in range(num_words):
                # Calculate address offset for this word
                addr_suffix = f" + 32'h{i*4:X}" if i > 0 else ""
                lines.append(f"                    ADDR_{signal_name_upper}{addr_suffix}: begin")

                if not self._reg_is_writable(reg):
                    # Read-only: return error
                    lines.append("                        bresp_reg <= SLVERR;")
                else:
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
            width = self._get_reg_width(reg)
            num_words = (width + 31) // 32

            for i in range(num_words):
                addr_suffix = f" + 32'h{i*4:X}" if i > 0 else ""
                lines.append(f"            ADDR_{signal_name_upper}{addr_suffix}: begin")

                if access_mode == 'WO':
                    # Write-only: return error
                    lines.append("                rresp_reg = SLVERR;")
                else:
                    # Determine source signal
                    if reg.get('is_packed'):
                        # Combined value: RO bits from field inputs (synced
                        # when CDC on), RW/WO bits from axi_aclk-domain storage
                        source = f"{signal_name}_val"
                    elif cdc_enabled and access_mode == 'RO':
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
                            lines.append(f"                rdata_reg = {{{{{32 - width}{{1'b0}}}}, {source}}};")
                    else:
                        # Wide register logic
                        if slice_width == 32:
                             lines.append(f"                rdata_reg = {source}[{high}:{low}];")
                        else:
                             padding = 32 - slice_width
                             lines.append(f"                rdata_reg = {{{{{padding}{{1'b0}}}}, {source}[{high}:{low}]}};")

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

            # Packed registers drive per-field output ports below instead
            if access_mode in ['RW', 'WO'] and not reg.get('is_packed'):
                if cdc_enabled:
                     # Use the last stage of the synchronizer
                     lines.append(f"    assign {signal_name} = {signal_name}_sync[{cdc_stages-1}];")
                else:
                     lines.append(f"    assign {signal_name} = {signal_name}_reg;")

            # Strobe assignments. When CDC is enabled, the port itself is
            # driven by the toggle-synchronizer's edge detector (see
            # _generate_strobe_cdc_logic) instead of directly - route the
            # axi_aclk-domain pulse condition into the "_int" signal that
            # feeds the toggle instead.
            if reg.get('write_strobe'):
                if cdc_enabled:
                    lines.append(f"    // {signal_name}_wr_strobe driven by strobe CDC toggle synchronizer below")
                else:
                    lines.append(f"    assign {signal_name}_wr_strobe = {signal_name}_wr_strobe_int;")

            if reg.get('read_strobe'):
                # Read strobe is asserted when reading this register
                signal_name_upper = signal_name.upper()
                rd_target = f"{signal_name}_rd_strobe_int" if cdc_enabled else f"{signal_name}_rd_strobe"
                lines.append(f"    assign {rd_target} = (state == READ_DATA && read_addr == ADDR_{signal_name_upper});")

        # Packed register RW/WO field outputs, sliced from the storage word
        # (from the last module_clk-domain sync stage when CDC is enabled)
        packed_registers = module_data.get('packed_registers', [])
        for pr in packed_registers:
            writable_fields = self._packed_writable_fields(pr)
            if not writable_fields:
                continue
            reg_name = pr['reg_name']
            src_base = f"{reg_name}_reg_sync[{cdc_stages-1}]" if cdc_enabled else f"{reg_name}_reg"
            lines.append(f"    // Field outputs for packed register {reg_name}")
            for field in writable_fields:
                sig_name = f"{reg_name}_{field['name']}"
                lines.append(f"    assign {sig_name} = {src_base}{self._field_slice(field)};")

        return '\n'.join(lines)

    def _signal_type_to_sv(self, signal_type: str) -> str:
        """
        Convert internal signal type format to SystemVerilog type.

        Args:
            signal_type: Internal format like "[31:0]", "[5:0]", "[0:0]",
                         or VHDL format like "std_logic_vector(15 downto 0)", "std_logic"

        Returns:
            SystemVerilog type string like "logic [31:0]" or "logic"
        """
        import re
        # Internal bracket format: [high:low]
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            if high == 0 and low == 0:
                return "logic"
            else:
                return f"logic [{high}:{low}]"
        # VHDL format from YAML/XML input: std_logic_vector(high downto low)
        match = re.match(r'std_logic_vector\((\d+)\s+downto\s+(\d+)\)', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            return f"logic [{high}:{low}]"
        if signal_type.strip() == 'std_logic':
            return "logic"
        # Default fallback
        return "logic [31:0]"
