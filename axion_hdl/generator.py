"""
VHDL Generator Module for Axion HDL

This module generates VHDL register interface modules from parsed data.
Uses axion_hdl for reusable utilities.

Features:
- Proper access control with SLVERR responses
- Correct continuous assignment syntax for RO registers
- Address decoding with hex values
- Byte-level write strobe support (wstrb)
"""

import os
import sys
from typing import Dict, List

# Import from axion_hdl (unified package)
from axion_hdl.code_formatter import CodeFormatter


class VHDLGenerator:
    """Generator for creating AXI register interface VHDL modules."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.formatter = CodeFormatter()
    
    @staticmethod
    def _signal_type_to_vhdl(signal_type: str) -> str:
        """
        Convert internal signal type format to VHDL type.
        
        Args:
            signal_type: Internal format like "[31:0]", "[5:0]", "[0:0]"
            
        Returns:
            VHDL type string like "std_logic_vector(31 downto 0)" or "std_logic"
            
        Examples:
            "[31:0]" -> "std_logic_vector(31 downto 0)"
            "[5:0]"  -> "std_logic_vector(5 downto 0)"
            "[0:0]"  -> "std_logic"
        """
        import re
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            if high == 0 and low == 0:
                return "std_logic"
            else:
                return f"std_logic_vector({high} downto {low})"
        # Default fallback
        return "std_logic_vector(31 downto 0)"
    
    @staticmethod
    def _get_signal_width(signal_type: str) -> int:
        """
        Get the width of a signal from its type.
        
        Args:
            signal_type: Internal format like "[31:0]", "[5:0]", "[0:0]"
            
        Returns:
            Width in bits
        """
        import re
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            return high - low + 1
        return 32
    
    @staticmethod
    def _expand_to_32bit(signal_name: str, signal_type: str) -> str:
        """
        Generate VHDL expression to expand a signal to 32-bit for internal register.
        
        Args:
            signal_name: Name of the source signal
            signal_type: Internal format like "[31:0]", "[5:0]", "[0:0]"
            
        Returns:
            VHDL expression for 32-bit value
            
        Examples:
            For std_logic:       '(31 downto 1 => '0') & signal_name'
            For 6-bit vector:    '(31 downto 6 => '0') & signal_name'
            For 32-bit:          'signal_name'
            For >32-bit:         'signal_name(31 downto 0)' (first 32 bits only)
        """
        import re
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            width = high - low + 1
            
            if width > 32:
                # For signals wider than 32 bits, take only the first 32 bits
                return f"{signal_name}(31 downto 0)"
            elif width == 32:
                return signal_name
            elif width == 1:  # std_logic
                return f"(31 downto 1 => '0') & {signal_name}"
            else:
                return f"(31 downto {width} => '0') & {signal_name}"
        return signal_name
    
    @staticmethod
    def _slice_from_32bit(signal_name: str, signal_type: str) -> str:
        """
        Generate VHDL expression to slice from 32-bit register to actual width.
        
        Args:
            signal_name: Name of the 32-bit source register
            signal_type: Internal format like "[31:0]", "[5:0]", "[0:0]"
            
        Returns:
            VHDL expression with proper slicing
            
        Examples:
            For std_logic:       'signal_name(0)'
            For 6-bit vector:    'signal_name(5 downto 0)'
            For 32-bit:          'signal_name'
            For >32-bit:         'signal_name' (only 32 bits available)
        """
        import re
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            width = high - low + 1
            
            if width > 32:
                # For signals wider than 32 bits, only first 32 bits are in the register
                # Return full 32-bit register value
                return signal_name
            elif width == 32:
                return signal_name
            elif width == 1:  # std_logic
                return f"{signal_name}(0)"
            else:
                return f"{signal_name}({high} downto {low})"
        return signal_name
    
    @staticmethod
    def _get_num_regs(signal_type: str) -> int:
        """
        Get number of 32-bit registers needed for a signal.
        
        Args:
            signal_type: Internal format like "[31:0]", "[63:0]", "[99:0]"
            
        Returns:
            Number of 32-bit registers needed
        """
        import re
        match = re.match(r'\[(\d+):(\d+)\]', signal_type)
        if match:
            high = int(match.group(1))
            low = int(match.group(2))
            width = high - low + 1
            return (width + 31) // 32
        return 1
        
    def generate_module(self, module_data: Dict) -> str:
        """
        Generate VHDL register module for a parsed module.
        
        Args:
            module_data: Parsed module dictionary
            
        Returns:
            Path to generated file
        """
        module_name = module_data['name']
        output_filename = f"{module_name}_axion_reg.vhd"
        output_path = os.path.join(self.output_dir, output_filename)
        
        vhdl_code = self._generate_vhdl_code(module_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vhdl_code)
            
        return output_path
    
    def _generate_vhdl_code(self, module_data: Dict) -> str:
        """Generate complete VHDL code for register module."""
        lines = []
        
        # Header
        lines.extend(self._generate_header(module_data))
        
        # Entity
        lines.extend(self._generate_entity(module_data))
        
        # Architecture
        lines.extend(self._generate_architecture(module_data))
        
        return '\n'.join(lines)
    
    def _generate_header(self, module_data: Dict) -> List[str]:
        """Generate file header using common formatter."""
        return self.formatter.format_vhdl_header(
            filename=f"{module_data['name']}_axion_reg.vhd",
            description="AXI Register Interface Module",
            additional_info=[
                f"Module: {module_data['name']}",
                f"Source: {os.path.basename(module_data['file'])}"
            ]
        ) + [
            "",
            "library ieee;",
            "use ieee.std_logic_1164.all;",
            "use ieee.numeric_std.all;",
            ""
        ]
    
    def _generate_entity(self, module_data: Dict) -> List[str]:
        """Generate entity declaration."""
        base_addr = module_data.get('base_address', 0)
        lines = [
            f"entity {module_data['name']}_axion_reg is",
            "    generic (",
            f"        BASE_ADDR : std_logic_vector(31 downto 0) := x\"{base_addr:08X}\"",
            "    );",
            "    port (",
            "        -- AXI4-Lite Interface",
            "        axi_aclk    : in  std_logic;",
            "        axi_aresetn : in  std_logic;",
            "        ",
            "        -- AXI Write Address Channel",
            "        axi_awaddr  : in  std_logic_vector(31 downto 0);",
            "        axi_awvalid : in  std_logic;",
            "        axi_awready : out std_logic;",
            "        ",
            "        -- AXI Write Data Channel",
            "        axi_wdata   : in  std_logic_vector(31 downto 0);",
            "        axi_wstrb   : in  std_logic_vector(3 downto 0);",
            "        axi_wvalid  : in  std_logic;",
            "        axi_wready  : out std_logic;",
            "        ",
            "        -- AXI Write Response Channel",
            "        axi_bresp   : out std_logic_vector(1 downto 0);",
            "        axi_bvalid  : out std_logic;",
            "        axi_bready  : in  std_logic;",
            "        ",
            "        -- AXI Read Address Channel",
            "        axi_araddr  : in  std_logic_vector(31 downto 0);",
            "        axi_arvalid : in  std_logic;",
            "        axi_arready : out std_logic;",
            "        ",
            "        -- AXI Read Data Channel",
            "        axi_rdata   : out std_logic_vector(31 downto 0);",
            "        axi_rresp   : out std_logic_vector(1 downto 0);",
            "        axi_rvalid  : out std_logic;",
        ]
        
        # Determine if we need comma after rready
        has_more = module_data['cdc_enabled'] or module_data['registers'] or module_data.get('packed_registers', [])
        if has_more:
            lines.append("        axi_rready  : in  std_logic;")
        else:
            lines.append("        axi_rready  : in  std_logic")
        
        # Add module clock if CDC enabled
        if module_data['cdc_enabled']:
            lines.extend([
                "        ",
                "        -- Module Clock (for CDC)",
            ])
            # Check if registers follow
            if module_data['registers']:
                lines.append("        module_clk  : in  std_logic;")
            else:
                lines.append("        module_clk  : in  std_logic")
        
        # Add register signals
        if module_data['registers']:
            lines.extend([
                "        ",
                "        -- Register Signals",
            ])
            
            # Build list of all port lines first
            port_lines = []
            for i, reg in enumerate(module_data['registers']):
                # Skip packed registers (handled separately)
                if reg.get('is_packed'):
                    continue
                    
                # Use actual signal type from parsed data
                signal_type = self._signal_type_to_vhdl(reg['signal_type'])
                
                # Port direction based on access mode:
                # RO: in (module provides value, AXI reads)
                # WO: out (AXI writes, module reads)
                # RW: out (AXI writes/reads, module reads)
                if reg['access_mode'] == 'RO':
                    port_dir = "in "
                else:  # WO or RW
                    port_dir = "out"
                
                # Get description if available
                description = reg.get('description', '')
                desc_comment = f"  -- {description}" if description else ""
                
                port_lines.append(f"        {reg['signal_name']} : {port_dir} {signal_type}{desc_comment}")
                
                # Read strobe (always out)
                if reg['read_strobe']:
                    port_lines.append(f"        {reg['signal_name']}_rd_strobe : out std_logic")
                
                # Write strobe (always out)
                if reg['write_strobe']:
                    port_lines.append(f"        {reg['signal_name']}_wr_strobe : out std_logic")
            
            # Add proper separators
            for i, line in enumerate(port_lines):
                # Check if line has a description comment
                if '  -- ' in line:
                    # Split into signal part and comment part
                    signal_part, comment_part = line.split('  -- ', 1)
                    has_packed = len(module_data.get('packed_registers', [])) > 0
                    if i < len(port_lines) - 1 or has_packed:
                        lines.append(f"{signal_part};  -- {comment_part}")
                    else:
                        lines.append(f"{signal_part}  -- {comment_part}")  # Last line, no semicolon
                else:
                    has_packed = len(module_data.get('packed_registers', [])) > 0
                    if i < len(port_lines) - 1 or has_packed:
                        lines.append(line + ";")
                    else:
                        lines.append(line)  # Last line, no semicolon
        
        # Add packed register (subregister) field signals  
        packed_registers = module_data.get('packed_registers', [])
        if packed_registers:
            lines.extend([
                "        ",
                "        -- Packed Register Fields (Subregisters)",
            ])
            
            packed_port_lines = []
            for packed_reg in packed_registers:
                for field in packed_reg.get('fields', []):
                    # Convert field signal type to VHDL
                    signal_type = self._signal_type_to_vhdl(field['signal_type'])
                    
                    # Port direction based on access mode
                    if field['access_mode'] == 'RO':
                        port_dir = "in "
                    else:
                        port_dir = "out"
                    
                    desc = field.get('description', '')
                    desc_comment = f"  -- {desc}" if desc else ""
                    packed_port_lines.append(f"        {field['name']} : {port_dir} {signal_type}{desc_comment}")
            
            for i, line in enumerate(packed_port_lines):
                if '  -- ' in line:
                    signal_part, comment_part = line.split('  -- ', 1)
                    if i < len(packed_port_lines) - 1:
                        lines.append(f"{signal_part};  -- {comment_part}")
                    else:
                        lines.append(f"{signal_part}  -- {comment_part}")
                else:
                    if i < len(packed_port_lines) - 1:
                        lines.append(line + ";")
                    else:
                        lines.append(line)
                    
        lines.extend([
            "    );",
            f"end entity {module_data['name']}_axion_reg;",
            ""
        ])
        
        return lines
    
    def _generate_architecture(self, module_data: Dict) -> List[str]:
        """Generate architecture body with full AXI4-Lite protocol compliance."""
        lines = [
            f"architecture rtl of {module_data['name']}_axion_reg is",
            "    ",
            "    -- AXI4-Lite Compliant State Machine",
            "    -- Supports independent address and data channels per AXI-LITE-005",
            "    type axi_state_type is (IDLE, WR_WAIT_ADDR, WR_WAIT_DATA, WR_DO_WRITE, WR_RESP, RD_ADDR, RD_DATA);",
            "    signal axi_state : axi_state_type;",
            "    ",
            "    -- Internal signals for write transaction",
            "    signal wr_addr_reg : std_logic_vector(31 downto 0);",
            "    signal wr_data_reg : std_logic_vector(31 downto 0);",
            "    signal wr_strb_reg : std_logic_vector(3 downto 0);",
            "    ",
            "    -- Internal signals for read transaction",
            "    signal rd_addr_reg : std_logic_vector(31 downto 0);",
            "    signal rd_data_reg : std_logic_vector(31 downto 0);",
            "    ",
            "    -- Access control",
            "    signal wr_access_error : std_logic;",
            "    signal rd_access_error : std_logic;",
            "    signal wr_addr_valid_n : std_logic;  -- Combinational write address invalid flag",
            "    signal rd_addr_valid_n : std_logic;  -- Combinational read address invalid flag",
            "    ",
            "    -- Write trigger signal",
            "    signal do_reg_write : std_logic;",
            "    ",
            "    -- Register storage",
        ]
        
        # Add register storage signals (32-bit chunks for wide signals)
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            num_regs = self._get_num_regs(reg['signal_type'])
            if num_regs == 1:
                lines.append(f"    signal {reg['signal_name']}_reg : std_logic_vector(31 downto 0);")
            else:
                for i in range(num_regs):
                    lines.append(f"    signal {reg['signal_name']}_reg{i} : std_logic_vector(31 downto 0);")
        
        # Add packed register (subregister) storage signals
        packed_registers = module_data.get('packed_registers', [])
        if packed_registers:
            lines.append("    ")
            lines.append("    -- Packed register storage (32-bit)")
            for packed_reg in packed_registers:
                lines.append(f"    signal {packed_reg['reg_name']}_reg : std_logic_vector(31 downto 0);")
        
        if module_data['cdc_enabled']:
            lines.append("    ")
            lines.append(f"    -- CDC synchronizer ({module_data['cdc_stages']} stages)")
            for reg in module_data['registers']:
                if reg.get('is_packed'):
                    continue
                num_regs = self._get_num_regs(reg['signal_type'])
                if num_regs == 1:
                    for stage in range(module_data['cdc_stages']):
                        lines.append(f"    signal {reg['signal_name']}_sync{stage} : std_logic_vector(31 downto 0);")
                else:
                    for i in range(num_regs):
                        for stage in range(module_data['cdc_stages']):
                            lines.append(f"    signal {reg['signal_name']}{i}_sync{stage} : std_logic_vector(31 downto 0);")
        lines.extend([
            "    ",
            "begin",
            "    ",
            "    ---------------------------------------------------------------------------",
            "    -- Packed Register Mapping (Subregister connections)",
            "    ---------------------------------------------------------------------------",
        ])
        
        # Packed register mapping
        packed_registers = module_data.get('packed_registers', [])
        
        # Output mapping (RW/WO) - Concurrent assignments
        for packed_reg in packed_registers:
            if packed_reg['access_mode'] in ['RW', 'WO']:
                for field in packed_reg.get('fields', []):
                    high = field['bit_high']
                    low = field['bit_low']
                    if high == low:
                        lines.append(f"    {field['name']} <= {packed_reg['reg_name']}_reg({high});")
                    else:
                        lines.append(f"    {field['name']} <= {packed_reg['reg_name']}_reg({high} downto {low});")
        
        if packed_registers:
             lines.append("")

        # Input mapping (RO) - Process
        has_ro_packed = any(pr['access_mode'] == 'RO' for pr in packed_registers)
        if has_ro_packed:
            # Build sensitivity list
            sens_list = []
            for pr in packed_registers:
                if pr['access_mode'] == 'RO':
                    for f in pr.get('fields', []):
                        sens_list.append(f['name'])
            
            sens_str = ", ".join(sens_list)
            lines.append(f"    process({sens_str})")
            lines.append("    begin")
            for pr in packed_registers:
                if pr['access_mode'] == 'RO':
                    lines.append(f"        {pr['reg_name']}_reg <= (others => '0');")
                    for f in pr.get('fields', []):
                        high = f['bit_high']
                        low = f['bit_low']
                        if high == low:
                            lines.append(f"        {pr['reg_name']}_reg({high}) <= {f['name']};")
                        else:
                            lines.append(f"        {pr['reg_name']}_reg({high} downto {low}) <= {f['name']};")
            lines.append("    end process;")
            
        lines.extend([
            "    ",
            "    ---------------------------------------------------------------------------",
            "    -- AXI4-Lite Interface State Machine",
            "    -- Full protocol compliance per ARM AMBA AXI4-Lite specification:",
            "    --   - AXI-LITE-001: Safe reset state for all outputs",
            "    --   - AXI-LITE-004: VALID stability until READY",
            "    --   - AXI-LITE-005: Independent write address and data channels",
            "    --   - AXI-LITE-007/008: Correct response timing",
            "    --   - AXI-LITE-016/017: Delayed and early READY handling",
            "    ---------------------------------------------------------------------------",
            "    process(axi_aclk)",
            "    begin",
            "        if rising_edge(axi_aclk) then",
            "            if axi_aresetn = '0' then",
            "                -- AXI-LITE-001: Reset State Requirements",
            "                axi_state <= IDLE;",
            "                axi_awready <= '0';",
            "                axi_wready <= '0';",
            "                axi_bvalid <= '0';",
            "                axi_bresp <= \"00\";",
            "                axi_arready <= '0';",
            "                axi_rvalid <= '0';",
            "                axi_rresp <= \"00\";",
            "                wr_access_error <= '0';",
            "                rd_access_error <= '0';",
            "                do_reg_write <= '0';",
            "            else",
            "                -- Default: clear one-shot signals",
            "                do_reg_write <= '0';",
            "                ",
            "                case axi_state is",
            "                    ------------------------------------",
            "                    -- IDLE: Wait for transaction start",
            "                    ------------------------------------",
            "                    when IDLE =>",
            "                        -- Check for write transaction (address or data can come first)",
            "                        -- AXI-LITE-005: Write Address and Data Independence",
            "                        if axi_awvalid = '1' and axi_wvalid = '1' then",
            "                            -- Both address and data arrived simultaneously",
            "                            axi_awready <= '1';",
            "                            axi_wready <= '1';",
            "                            wr_addr_reg <= axi_awaddr;",
            "                            wr_data_reg <= axi_wdata;",
            "                            wr_strb_reg <= axi_wstrb;",
            "                            wr_access_error <= wr_addr_valid_n;",
            "                            axi_state <= WR_DO_WRITE;",
            "                        elsif axi_awvalid = '1' then",
            "                            -- Address first - wait for data",
            "                            axi_awready <= '1';",
            "                            wr_addr_reg <= axi_awaddr;",
            "                            wr_access_error <= wr_addr_valid_n;",
            "                            axi_state <= WR_WAIT_DATA;",
            "                        elsif axi_wvalid = '1' then",
            "                            -- Data first - wait for address",
            "                            axi_wready <= '1';",
            "                            wr_data_reg <= axi_wdata;",
            "                            wr_strb_reg <= axi_wstrb;",
            "                            axi_state <= WR_WAIT_ADDR;",
            "                        elsif axi_arvalid = '1' then",
            "                            -- Read transaction",
            "                            axi_arready <= '1';",
            "                            rd_addr_reg <= axi_araddr;",
            "                            rd_access_error <= rd_addr_valid_n;",
            "                            axi_state <= RD_ADDR;",
            "                        end if;",
            "                    ",
            "                    ------------------------------------",
            "                    -- WR_WAIT_ADDR: Data received, waiting for address",
            "                    -- AXI-LITE-005: Data-first ordering support",
            "                    ------------------------------------",
            "                    when WR_WAIT_ADDR =>",
            "                        axi_wready <= '0';",
            "                        if axi_awvalid = '1' then",
            "                            axi_awready <= '1';",
            "                            wr_addr_reg <= axi_awaddr;",
            "                            wr_access_error <= wr_addr_valid_n;",
            "                            axi_state <= WR_DO_WRITE;",
            "                        end if;",
            "                    ",
            "                    ------------------------------------",
            "                    -- WR_WAIT_DATA: Address received, waiting for data",
            "                    -- AXI-LITE-005: Address-first ordering support",
            "                    ------------------------------------",
            "                    when WR_WAIT_DATA =>",
            "                        axi_awready <= '0';",
            "                        if axi_wvalid = '1' then",
            "                            axi_wready <= '1';",
            "                            wr_data_reg <= axi_wdata;",
            "                            wr_strb_reg <= axi_wstrb;",
            "                            axi_state <= WR_DO_WRITE;",
            "                        end if;",
            "                    ",
            "                    ------------------------------------",
            "                    -- WR_DO_WRITE: Perform register write",
            "                    ------------------------------------",
            "                    when WR_DO_WRITE =>",
            "                        axi_awready <= '0';",
            "                        axi_wready <= '0';",
            "                        do_reg_write <= '1';  -- Trigger register write",
            "                        axi_state <= WR_RESP;",
            "                        axi_bvalid <= '1';",
            "                        -- AXI-LITE-014: Response Code Compliance",
            "                        if wr_access_error = '1' then",
            "                            axi_bresp <= \"10\"; -- SLVERR",
            "                        else",
            "                            axi_bresp <= \"00\"; -- OKAY",
            "                        end if;",
            "                    ",
            "                    ------------------------------------",
            "                    -- WR_RESP: Wait for response acknowledgment",
            "                    -- AXI-LITE-007: Write Response Timing",
            "                    ------------------------------------",
            "                    when WR_RESP =>",
            "                        -- AXI-LITE-016/017: READY handling (immediate or delayed)",
            "                        if axi_bready = '1' then",
            "                            axi_bvalid <= '0';",
            "                            axi_bresp <= \"00\";",
            "                            axi_state <= IDLE;",
            "                        end if;",
            "                    ",
            "                    ------------------------------------",
            "                    -- RD_ADDR: Read address received",
            "                    ------------------------------------",
            "                    when RD_ADDR =>",
            "                        axi_arready <= '0';",
            "                        axi_state <= RD_DATA;",
            "                        axi_rvalid <= '1';",
            "                        -- AXI-LITE-014: Response Code Compliance",
            "                        if rd_access_error = '1' then",
            "                            axi_rresp <= \"10\"; -- SLVERR",
            "                        else",
            "                            axi_rresp <= \"00\"; -- OKAY",
            "                        end if;",
            "                    ",
            "                    ------------------------------------",
            "                    -- RD_DATA: Output read data",
            "                    -- AXI-LITE-008: Read Response Timing",
            "                    -- AXI-LITE-016/017: READY handling",
            "                    ------------------------------------",
            "                    when RD_DATA =>",
            "                        if axi_rready = '1' then",
            "                            axi_rvalid <= '0';",
            "                            axi_rresp <= \"00\";",
            "                            axi_state <= IDLE;",
            "                        end if;",
            "                end case;",
            "            end if;",
            "        end if;",
            "    end process;",
            "    ",
        ])
        
        # Generate CDC synchronizer process if CDC is enabled
        if module_data['cdc_enabled']:
            lines.extend(self._generate_cdc_process(module_data))
        
        # Generate write address valid detection (combinational, uses axi_awaddr)
        lines.extend([
            "    -- Write Address Valid Detection (combinational)",
            "    process(axi_awaddr)",
            "    begin",
            "        wr_addr_valid_n <= '1';  -- Default: invalid",
        ])
        
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['WO', 'RW']:
                num_regs = self._get_num_regs(reg['signal_type'])
                if num_regs == 1:
                    offset = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                    lines.append(f"        if unsigned(axi_awaddr) = unsigned(BASE_ADDR) + {offset} then")
                    lines.append("            wr_addr_valid_n <= '0';  -- Valid write address")
                    lines.append("        end if;")
                else:
                    # Multi-register signal - add all chunk addresses
                    base_relative = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                    for i in range(num_regs):
                        offset = base_relative + (i * 4)
                        lines.append(f"        if unsigned(axi_awaddr) = unsigned(BASE_ADDR) + {offset} then")
                        lines.append(f"            wr_addr_valid_n <= '0';  -- Valid write address ({reg['signal_name']} reg{i})")
                        lines.append("        end if;")
        
        # Add packed register write address validation
        for packed_reg in module_data.get('packed_registers', []):
            if packed_reg['access_mode'] in ['WO', 'RW']:
                offset = packed_reg.get("relative_address_int", packed_reg["address_int"] - module_data.get('base_address', 0))
                lines.append(f"        if unsigned(axi_awaddr) = unsigned(BASE_ADDR) + {offset} then")
                lines.append(f"            wr_addr_valid_n <= '0';  -- Valid write address ({packed_reg['reg_name']} packed)")
                lines.append("        end if;")
        
        lines.extend([
            "    end process;",
            "    ",
        ])
        
        # Generate read address valid detection (combinational, uses axi_araddr)
        lines.extend([
            "    -- Read Address Valid Detection (combinational)",
            "    process(axi_araddr)",
            "    begin",
            "        rd_addr_valid_n <= '1';  -- Default: invalid",
        ])
        
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['RO', 'RW']:
                num_regs = self._get_num_regs(reg['signal_type'])
                if num_regs == 1:
                    offset = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                    lines.append(f"        if unsigned(axi_araddr) = unsigned(BASE_ADDR) + {offset} then")
                    lines.append("            rd_addr_valid_n <= '0';  -- Valid read address")
                    lines.append("        end if;")
                else:
                    # Multi-register signal - add all chunk addresses
                    base_relative = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                    for i in range(num_regs):
                        offset = base_relative + (i * 4)
                        lines.append(f"        if unsigned(axi_araddr) = unsigned(BASE_ADDR) + {offset} then")
                        lines.append(f"            rd_addr_valid_n <= '0';  -- Valid read address ({reg['signal_name']} reg{i})")
                        lines.append("        end if;")
        
        # Add packed register read address validation
        for packed_reg in module_data.get('packed_registers', []):
            if packed_reg['access_mode'] in ['RO', 'RW']:
                offset = packed_reg.get("relative_address_int", packed_reg["address_int"] - module_data.get('base_address', 0))
                lines.append(f"        if unsigned(axi_araddr) = unsigned(BASE_ADDR) + {offset} then")
                lines.append(f"            rd_addr_valid_n <= '0';  -- Valid read address ({packed_reg['reg_name']} packed)")
                lines.append("        end if;")
        
        lines.extend([
            "    end process;",
            "    ",
        ])
        
        # Register Write Logic - triggered by do_reg_write signal
        lines.extend([
            "    -- Register Write Logic",
            "    -- Write occurs when do_reg_write is asserted (WR_DO_WRITE state)",
            "    process(axi_aclk)",
            "    begin",
            "        if rising_edge(axi_aclk) then",
            "            if axi_aresetn = '0' then",
        ])
        
        # Reset logic for registers - use default_value if specified
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['WO', 'RW']:
                num_regs = self._get_num_regs(reg['signal_type'])
                default_val = reg.get('default_value', 0)
                if num_regs == 1:
                    if default_val != 0:
                        lines.append(f"                {reg['signal_name']}_reg <= x\"{default_val:08X}\";")
                    else:
                        lines.append(f"                {reg['signal_name']}_reg <= (others => '0');")
                else:
                    for i in range(num_regs):
                        # For wide signals, split default across chunks
                        chunk_default = (default_val >> (i * 32)) & 0xFFFFFFFF
                        if chunk_default != 0:
                            lines.append(f"                {reg['signal_name']}_reg{i} <= x\"{chunk_default:08X}\";")
                        else:
                            lines.append(f"                {reg['signal_name']}_reg{i} <= (others => '0');")
        
        # Reset logic for packed registers (subregisters)
        for packed_reg in module_data.get('packed_registers', []):
            # Skip RO packed registers in reset logic (they are driven by inputs)
            if packed_reg['access_mode'] == 'RO':
                continue
                
            default_val = packed_reg.get('default_value', 0)
            if default_val != 0:
                lines.append(f"                {packed_reg['reg_name']}_reg <= x\"{default_val:08X}\";  -- Combined default from subregisters")
            else:
                lines.append(f"                {packed_reg['reg_name']}_reg <= (others => '0');")
        
        lines.extend([
            "            else",
            "                if do_reg_write = '1' and wr_access_error = '0' then",
        ])
        
        # Write address decoder with byte-level strobe support
        # Write address decoder with byte-level strobe support
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['WO', 'RW']:
                num_regs = self._get_num_regs(reg['signal_type'])
                base_relative = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                
                for chunk in range(num_regs):
                    offset = base_relative + (chunk * 4)
                    reg_suffix = f"_reg{chunk}" if num_regs > 1 else "_reg"
                    
                    lines.append(f"                    if unsigned(wr_addr_reg) = unsigned(BASE_ADDR) + {offset} then")
                    lines.append("                        -- Byte-level write strobe")
                    lines.append("                        if wr_strb_reg(0) = '1' then")
                    lines.append(f"                            {reg['signal_name']}{reg_suffix}(7 downto 0) <= wr_data_reg(7 downto 0);")
                    lines.append("                        end if;")
                    lines.append("                        if wr_strb_reg(1) = '1' then")
                    lines.append(f"                            {reg['signal_name']}{reg_suffix}(15 downto 8) <= wr_data_reg(15 downto 8);")
                    lines.append("                        end if;")
                    lines.append("                        if wr_strb_reg(2) = '1' then")
                    lines.append(f"                            {reg['signal_name']}{reg_suffix}(23 downto 16) <= wr_data_reg(23 downto 16);")
                    lines.append("                        end if;")
                    lines.append("                        if wr_strb_reg(3) = '1' then")
                    lines.append(f"                            {reg['signal_name']}{reg_suffix}(31 downto 24) <= wr_data_reg(31 downto 24);")
                    lines.append("                        end if;")
                    lines.append("                    end if;")
        
        # Packed register write logic (subregisters)
        for packed_reg in module_data.get('packed_registers', []):
            if packed_reg['access_mode'] in ['WO', 'RW']:
                offset = packed_reg.get("relative_address_int", packed_reg["address_int"] - module_data.get('base_address', 0))
                
                lines.append(f"                    if unsigned(wr_addr_reg) = unsigned(BASE_ADDR) + {offset} then")
                lines.append("                        -- Byte-level write strobe")
                lines.append("                        if wr_strb_reg(0) = '1' then")
                lines.append(f"                            {packed_reg['reg_name']}_reg(7 downto 0) <= wr_data_reg(7 downto 0);")
                lines.append("                        end if;")
                lines.append("                        if wr_strb_reg(1) = '1' then")
                lines.append(f"                            {packed_reg['reg_name']}_reg(15 downto 8) <= wr_data_reg(15 downto 8);")
                lines.append("                        end if;")
                lines.append("                        if wr_strb_reg(2) = '1' then")
                lines.append(f"                            {packed_reg['reg_name']}_reg(23 downto 16) <= wr_data_reg(23 downto 16);")
                lines.append("                        end if;")
                lines.append("                        if wr_strb_reg(3) = '1' then")
                lines.append(f"                            {packed_reg['reg_name']}_reg(31 downto 24) <= wr_data_reg(31 downto 24);")
                lines.append("                        end if;")
                lines.append("                    end if;")
        
        lines.extend([
            "                end if;",
            "            end if;",
            "        end if;",
            "    end process;",
            "    ",
        ])
        
        # Register Read Logic
        lines.extend([
            "    -- Register Read Logic",
            "    process(rd_addr_reg, rd_access_error",
        ])
        
        # Add read sensitivity list
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['RO', 'RW']:
                num_regs = self._get_num_regs(reg['signal_type'])
                if num_regs == 1:
                    lines.append(f"        , {reg['signal_name']}_reg")
                else:
                    for i in range(num_regs):
                        lines.append(f"        , {reg['signal_name']}_reg{i}")
        
        # Add packed register to sensitivity list
        for packed_reg in module_data.get('packed_registers', []):
            if packed_reg['access_mode'] in ['RO', 'RW']:
                lines.append(f"        , {packed_reg['reg_name']}_reg")
        
        lines.extend([
            "    )",
            "    begin",
            "        rd_data_reg <= (others => '0');",
            "        if rd_access_error = '0' then",
        ])
        
        # Read address decoder
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            if reg['access_mode'] in ['RO', 'RW']:
                num_regs = self._get_num_regs(reg['signal_type'])
                base_relative = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                
                for chunk in range(num_regs):
                    offset = base_relative + (chunk * 4)
                    reg_suffix = f"_reg{chunk}" if num_regs > 1 else "_reg"
                    
                    lines.append(f"            if unsigned(rd_addr_reg) = unsigned(BASE_ADDR) + {offset} then")
                    lines.append(f"                rd_data_reg <= {reg['signal_name']}{reg_suffix};")
                    lines.append("            end if;")
        
        # Packed register read address decoder
        for packed_reg in module_data.get('packed_registers', []):
            if packed_reg['access_mode'] in ['RO', 'RW']:
                offset = packed_reg.get("relative_address_int", packed_reg["address_int"] - module_data.get('base_address', 0))
                lines.append(f"            if unsigned(rd_addr_reg) = unsigned(BASE_ADDR) + {offset} then")
                lines.append(f"                rd_data_reg <= {packed_reg['reg_name']}_reg;")
                lines.append("            end if;")
        
        lines.extend([
            "        end if;",
            "    end process;",
            "    ",
            "    axi_rdata <= rd_data_reg;",
            "    ",
        ])
        
        cdc_enabled = module_data['cdc_enabled']
        cdc_last_stage = module_data['cdc_stages'] - 1 if cdc_enabled else 0
        
        # Generate signal assignments based on port direction
        for reg in module_data['registers']:
            if reg.get('is_packed'):
                continue
            addr_hex = self._addr_to_vhdl_hex(reg["address_int"], module_data)
            signal_type = reg['signal_type']
            num_regs = self._get_num_regs(signal_type)
            signal_width = self._get_signal_width(signal_type)
            
            if reg['access_mode'] == 'RO':
                lines.append(f"    -- Read-Only (in port - module provides value, AXI reads): {reg['signal_name']}")
                if reg['read_strobe']:
                    offset = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                    lines.append(f"    {reg['signal_name']}_rd_strobe <= '1' when (axi_state = RD_DATA and axi_rready = '1' and unsigned(rd_addr_reg) = unsigned(BASE_ADDR) + {offset}) else '0';")
                
                # RO is 'in' port - assign chunks from input to internal registers
                if num_regs == 1:
                    if cdc_enabled:
                        lines.append(f"    {reg['signal_name']}_reg <= {reg['signal_name']}_sync{cdc_last_stage};")
                    else:
                        expanded_input = self._expand_to_32bit(reg['signal_name'], signal_type)
                        lines.append(f"    {reg['signal_name']}_reg <= {expanded_input};")
                else:
                    # Wide signal - assign each 32-bit chunk
                    for i in range(num_regs):
                        start_bit = i * 32
                        end_bit = min((i + 1) * 32 - 1, signal_width - 1)
                        if cdc_enabled:
                            lines.append(f"    {reg['signal_name']}_reg{i} <= {reg['signal_name']}{i}_sync{cdc_last_stage};")
                        else:
                            if end_bit - start_bit + 1 == 32:
                                lines.append(f"    {reg['signal_name']}_reg{i} <= {reg['signal_name']}({end_bit} downto {start_bit});")
                            else:
                                # Last chunk may be smaller than 32 bits
                                remaining_bits = end_bit - start_bit + 1
                                lines.append(f"    {reg['signal_name']}_reg{i} <= (31 downto {remaining_bits} => '0') & {reg['signal_name']}({end_bit} downto {start_bit});")
                                
            elif reg['access_mode'] == 'WO':
                lines.append(f"    -- Write-Only (out port - AXI writes, module reads): {reg['signal_name']}")
                if reg['write_strobe']:
                    offset = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                    lines.append(f"    {reg['signal_name']}_wr_strobe <= '1' when (axi_state = WR_DO_WRITE and unsigned(wr_addr_reg) = unsigned(BASE_ADDR) + {offset}) else '0';")
                
                # WO is 'out' port - concatenate chunks to output
                if num_regs == 1:
                    sliced_reg = self._slice_from_32bit(f"{reg['signal_name']}_reg", signal_type)
                    if cdc_enabled:
                        sliced_sync = self._slice_from_32bit(f"{reg['signal_name']}_sync{cdc_last_stage}", signal_type)
                        lines.append(f"    {reg['signal_name']} <= {sliced_sync};")
                    else:
                        lines.append(f"    {reg['signal_name']} <= {sliced_reg};")
                else:
                    # Wide signal - concatenate all chunks
                    if cdc_enabled:
                        chunks = [f"{reg['signal_name']}{i}_sync{cdc_last_stage}" for i in range(num_regs-1, -1, -1)]
                    else:
                        chunks = [f"{reg['signal_name']}_reg{i}" for i in range(num_regs-1, -1, -1)]
                    
                    # Handle last chunk if it's smaller than 32 bits
                    last_chunk_bits = signal_width - (num_regs - 1) * 32
                    if last_chunk_bits < 32:
                        chunks[0] = f"{chunks[0]}({last_chunk_bits - 1} downto 0)"
                    
                    lines.append(f"    {reg['signal_name']} <= {' & '.join(chunks)};")
                    
            else:  # RW
                lines.append(f"    -- Read-Write (out port - AXI reads/writes, module reads): {reg['signal_name']}")
                offset = reg.get("relative_address_int", reg["address_int"] - module_data.get('base_address', 0))
                if reg['read_strobe']:
                    lines.append(f"    {reg['signal_name']}_rd_strobe <= '1' when (axi_state = RD_DATA and axi_rready = '1' and unsigned(rd_addr_reg) = unsigned(BASE_ADDR) + {offset}) else '0';")
                if reg['write_strobe']:
                    lines.append(f"    {reg['signal_name']}_wr_strobe <= '1' when (axi_state = WR_DO_WRITE and unsigned(wr_addr_reg) = unsigned(BASE_ADDR) + {offset}) else '0';")
                
                # RW is 'out' port - concatenate chunks to output
                if num_regs == 1:
                    sliced_reg = self._slice_from_32bit(f"{reg['signal_name']}_reg", signal_type)
                    if cdc_enabled:
                        sliced_sync = self._slice_from_32bit(f"{reg['signal_name']}_sync{cdc_last_stage}", signal_type)
                        lines.append(f"    {reg['signal_name']} <= {sliced_sync};")
                    else:
                        lines.append(f"    {reg['signal_name']} <= {sliced_reg};")
                else:
                    # Wide signal - concatenate all chunks
                    if cdc_enabled:
                        chunks = [f"{reg['signal_name']}{i}_sync{cdc_last_stage}" for i in range(num_regs-1, -1, -1)]
                    else:
                        chunks = [f"{reg['signal_name']}_reg{i}" for i in range(num_regs-1, -1, -1)]
                    
                    # Handle last chunk if it's smaller than 32 bits
                    last_chunk_bits = signal_width - (num_regs - 1) * 32
                    if last_chunk_bits < 32:
                        chunks[0] = f"{chunks[0]}({last_chunk_bits - 1} downto 0)"
                    
                    lines.append(f"    {reg['signal_name']} <= {' & '.join(chunks)};")
            lines.append("    ")
        
        # Packed register (subregister) output assignments
        # Extract bit fields from the 32-bit packed register and assign to output ports
        packed_registers = module_data.get('packed_registers', [])
        if packed_registers:
            lines.append("    -- Packed register (subregister) output assignments")
            for packed_reg in packed_registers:
                for field in packed_reg.get('fields', []):
                    if field['access_mode'] in ['WO', 'RW']:
                        # Extract bit slice from packed register
                        if field['width'] == 1:
                            lines.append(f"    {field['name']} <= {packed_reg['reg_name']}_reg({field['bit_low']});")
                        else:
                            lines.append(f"    {field['name']} <= {packed_reg['reg_name']}_reg({field['bit_high']} downto {field['bit_low']});")
                    elif field['access_mode'] == 'RO':
                        pass # handled in process below
            
            # Generate combinatorial process for RO packed registers
            lines.append("    -- Packed register (subregister) input assignments (RO)")
            lines.append("    process(all) -- VHDL-2008 sensitivity")
            lines.append("    begin")
            
            for packed_reg in packed_registers:
                has_ro_fields = False
                for field in packed_reg.get('fields', []):
                    if field['access_mode'] == 'RO':
                        has_ro_fields = True
                        break
                
                if has_ro_fields:
                    lines.append(f"        {packed_reg['reg_name']}_reg <= (others => '0');")
                    for field in packed_reg.get('fields', []):
                        if field['access_mode'] == 'RO':
                            if field['width'] == 1:
                                lines.append(f"        {packed_reg['reg_name']}_reg({field['bit_low']}) <= {field['name']};")
                            else:
                                lines.append(f"        {packed_reg['reg_name']}_reg({field['bit_high']} downto {field['bit_low']}) <= {field['name']};")
            
            lines.append("    end process;")
            lines.append("    ")
        
        lines.extend([
            f"end architecture rtl;",
            ""
        ])
        
        return lines
    
    def _get_addr_bits(self, module_data: Dict) -> str:
        """Determine address bit range needed."""
        if not module_data.get('registers'):
            return "7 downto 0"  # Default to 8 bits if no registers

        max_addr = max(reg['address_int'] for reg in module_data['registers'])
        if max_addr < 256:
            return "7 downto 0"   # 8 bits, 2 hex digits
        elif max_addr < 4096:
            return "11 downto 0"  # 12 bits, 3 hex digits
        else:
            return "15 downto 0"  # 16 bits, 4 hex digits
    
    def _addr_to_vhdl_hex(self, addr_int: int, module_data: Dict = None) -> str:
        """Convert address integer to VHDL hex string literal with proper width."""
        # Determine required bit width based on max address in module
        if module_data and module_data.get('registers'):
            max_addr = max(reg['address_int'] for reg in module_data['registers'])
            if max_addr < 256:
                hex_digits = 2  # 8 bits
            elif max_addr < 4096:
                hex_digits = 3  # 12 bits
            else:
                hex_digits = 4  # 16 bits
        else:
            # Default: use minimum digits needed
            if addr_int < 256:
                hex_digits = 2
            elif addr_int < 4096:
                hex_digits = 3
            else:
                hex_digits = 4
        
        # Convert to hex with proper width
        hex_str = f"{addr_int:0{hex_digits}X}"
        return f'x"{hex_str}"'

    def _generate_cdc_process(self, module_data: Dict) -> List[str]:
        """Generate CDC synchronization process for cross-domain signals."""
        lines = []
        cdc_stages = module_data['cdc_stages']
        
        lines.extend([
            "    ---------------------------------------------------------------------------",
            f"    -- CDC Synchronizer Process ({cdc_stages}-stage synchronization)",
            "    -- Synchronizes signals between module_clk and axi_aclk domains",
            "    -- RO registers: module_clk -> axi_aclk (input to AXI)",
            "    -- WO/RW registers: axi_aclk -> module_clk (output from AXI)",
            "    ---------------------------------------------------------------------------",
        ])
        
        # Process for RO registers (module_clk -> axi_aclk)
        # These are inputs from module that AXI needs to read
        ro_regs = [reg for reg in module_data['registers'] if reg['access_mode'] == 'RO' and not reg.get('is_packed')]
        if ro_regs:
            lines.extend([
                "    -- CDC: Module clock domain to AXI clock domain (for RO registers)",
                "    process(axi_aclk)",
                "    begin",
                "        if rising_edge(axi_aclk) then",
                "            if axi_aresetn = '0' then",
            ])
            # Reset all sync stages
            for reg in ro_regs:
                num_regs = self._get_num_regs(reg['signal_type'])
                if num_regs == 1:
                    for stage in range(cdc_stages):
                        lines.append(f"                {reg['signal_name']}_sync{stage} <= (others => '0');")
                else:
                    for i in range(num_regs):
                        for stage in range(cdc_stages):
                            lines.append(f"                {reg['signal_name']}{i}_sync{stage} <= (others => '0');")
            lines.extend([
                "            else",
            ])
            # Synchronization chain
            for reg in ro_regs:
                num_regs = self._get_num_regs(reg['signal_type'])
                signal_width = self._get_signal_width(reg['signal_type'])
                
                if num_regs == 1:
                    lines.append(f"                -- {reg['signal_name']} synchronization chain")
                    expanded_input = self._expand_to_32bit(reg['signal_name'], reg['signal_type'])
                    lines.append(f"                {reg['signal_name']}_sync0 <= {expanded_input};")
                    for stage in range(1, cdc_stages):
                        lines.append(f"                {reg['signal_name']}_sync{stage} <= {reg['signal_name']}_sync{stage-1};")
                else:
                    lines.append(f"                -- {reg['signal_name']} synchronization chain ({num_regs} chunks)")
                    for i in range(num_regs):
                        start_bit = i * 32
                        end_bit = min((i + 1) * 32 - 1, signal_width - 1)
                        chunk_width = end_bit - start_bit + 1
                        
                        if chunk_width == 32:
                            lines.append(f"                {reg['signal_name']}{i}_sync0 <= {reg['signal_name']}({end_bit} downto {start_bit});")
                        else:
                            lines.append(f"                {reg['signal_name']}{i}_sync0 <= (31 downto {chunk_width} => '0') & {reg['signal_name']}({end_bit} downto {start_bit});")
                        
                        for stage in range(1, cdc_stages):
                            lines.append(f"                {reg['signal_name']}{i}_sync{stage} <= {reg['signal_name']}{i}_sync{stage-1};")
            lines.extend([
                "            end if;",
                "        end if;",
                "    end process;",
                "    ",
            ])
        
        # Process for WO/RW registers (axi_aclk -> module_clk)
        # These are outputs from AXI that module needs to read
        wo_rw_regs = [reg for reg in module_data['registers'] if reg['access_mode'] in ['WO', 'RW'] and not reg.get('is_packed')]
        if wo_rw_regs:
            lines.extend([
                "    -- CDC: AXI clock domain to Module clock domain (for WO/RW registers)",
                "    process(module_clk)",
                "    begin",
                "        if rising_edge(module_clk) then",
            ])
            # Synchronization chain (no reset needed for output sync - follows AXI register values)
            for reg in wo_rw_regs:
                num_regs = self._get_num_regs(reg['signal_type'])
                
                if num_regs == 1:
                    lines.append(f"            -- {reg['signal_name']} synchronization chain")
                    lines.append(f"            {reg['signal_name']}_sync0 <= {reg['signal_name']}_reg;")
                    for stage in range(1, cdc_stages):
                        lines.append(f"            {reg['signal_name']}_sync{stage} <= {reg['signal_name']}_sync{stage-1};")
                else:
                    lines.append(f"            -- {reg['signal_name']} synchronization chain ({num_regs} chunks)")
                    for i in range(num_regs):
                        lines.append(f"            {reg['signal_name']}{i}_sync0 <= {reg['signal_name']}_reg{i};")
                        for stage in range(1, cdc_stages):
                            lines.append(f"            {reg['signal_name']}{i}_sync{stage} <= {reg['signal_name']}{i}_sync{stage-1};")
            lines.extend([
                "        end if;",
                "    end process;",
                "    ",
            ])
        
        return lines
