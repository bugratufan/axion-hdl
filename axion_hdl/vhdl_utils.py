"""
VHDL Utilities Module

Common utilities for VHDL parsing and code generation.
Provides functions for type parsing, entity extraction, and code formatting.
"""

import re
from typing import Optional, Tuple, Dict, List


class VHDLUtils:
    """
    Collection of utility functions for VHDL processing.
    
    Features:
    - Signal type parsing and width extraction
    - Entity and architecture extraction
    - Port and signal parsing
    - Comment and annotation handling
    """
    
    # Common regex patterns
    ENTITY_PATTERN = re.compile(r'entity\s+(\w+)\s+is', re.IGNORECASE)
    ARCHITECTURE_PATTERN = re.compile(r'architecture\s+(\w+)\s+of\s+(\w+)\s+is', re.IGNORECASE)
    SIGNAL_PATTERN = re.compile(
        r'signal\s+(\w+)\s*:\s*([^;]+);',
        re.IGNORECASE
    )
    PORT_PATTERN = re.compile(
        r'(\w+)\s*:\s*(in|out|inout)\s+([^;:]+)',
        re.IGNORECASE
    )
    
    @staticmethod
    def parse_signal_type(type_str: str) -> Tuple[str, int, int]:
        """
        Parse VHDL signal type and extract width information.
        
        Args:
            type_str: Type string (e.g., "std_logic_vector(31 downto 0)")
            
        Returns:
            Tuple of (type_name, high_bit, low_bit)
            
        Examples:
            "std_logic_vector(31 downto 0)" -> ("std_logic_vector", 31, 0)
            "std_logic" -> ("std_logic", 0, 0)
            "unsigned(15 downto 0)" -> ("unsigned", 15, 0)
        """
        type_str = type_str.strip()
        
        # Remove initialization if present
        if ':=' in type_str:
            type_str = type_str.split(':=')[0].strip()
        
        # Check for vector types with range
        vector_match = re.search(
            r'(\w+)\s*\(\s*(\d+)\s+(downto|to)\s+(\d+)\s*\)',
            type_str,
            re.IGNORECASE
        )
        
        if vector_match:
            type_name = vector_match.group(1)
            first = int(vector_match.group(2))
            second = int(vector_match.group(4))
            direction = vector_match.group(3).lower()
            
            if direction == 'downto':
                return (type_name, first, second)
            else:  # 'to'
                return (type_name, second, first)
        
        # Check for single-bit types
        if re.match(r'std_logic\s*$', type_str, re.IGNORECASE):
            return ("std_logic", 0, 0)
        
        # Default to 32-bit
        return ("std_logic_vector", 31, 0)
    
    @staticmethod
    def format_signal_type(high: int, low: int = 0) -> str:
        """
        Format signal type as VHDL range string.
        
        Args:
            high: High bit index
            low: Low bit index (default: 0)
            
        Returns:
            Formatted type string
            
        Examples:
            format_signal_type(31, 0) -> "[31:0]"
            format_signal_type(0, 0) -> "[0:0]"
        """
        return f"[{high}:{low}]"
    
    @staticmethod
    def get_signal_width(high: int, low: int = 0) -> int:
        """
        Calculate signal width from bit range.
        
        Args:
            high: High bit index
            low: Low bit index
            
        Returns:
            Width in bits
        """
        return abs(high - low) + 1
    
    @staticmethod
    def extract_entity_name(vhdl_content: str) -> Optional[str]:
        """
        Extract entity name from VHDL content.
        
        Args:
            vhdl_content: VHDL source code
            
        Returns:
            Entity name or None if not found
        """
        match = VHDLUtils.ENTITY_PATTERN.search(vhdl_content)
        return match.group(1) if match else None
    
    @staticmethod
    def extract_architecture_info(vhdl_content: str) -> Optional[Tuple[str, str]]:
        """
        Extract architecture name and entity name.
        
        Args:
            vhdl_content: VHDL source code
            
        Returns:
            Tuple of (architecture_name, entity_name) or None
        """
        match = VHDLUtils.ARCHITECTURE_PATTERN.search(vhdl_content)
        if match:
            return (match.group(1), match.group(2))
        return None
    
    @staticmethod
    def parse_ports(port_declaration: str) -> List[Dict]:
        """
        Parse port declarations from entity.
        
        Args:
            port_declaration: Port declaration text
            
        Returns:
            List of port dictionaries with name, direction, and type
        """
        ports = []
        for match in VHDLUtils.PORT_PATTERN.finditer(port_declaration):
            port_name = match.group(1)
            direction = match.group(2)
            port_type = match.group(3).strip()
            
            type_info = VHDLUtils.parse_signal_type(port_type)
            
            ports.append({
                'name': port_name,
                'direction': direction,
                'type': port_type,
                'type_parsed': type_info
            })
        
        return ports
    
    @staticmethod
    def extract_comments(vhdl_content: str, comment_marker: str = '--') -> List[str]:
        """
        Extract all comments from VHDL content.
        
        Args:
            vhdl_content: VHDL source code
            comment_marker: Comment marker (default: '--')
            
        Returns:
            List of comment strings (without marker)
        """
        pattern = re.compile(rf'{re.escape(comment_marker)}\s*(.*)$', re.MULTILINE)
        matches = pattern.findall(vhdl_content)
        return [m.strip() for m in matches]
    
    @staticmethod
    def remove_comments(vhdl_content: str, comment_marker: str = '--') -> str:
        """
        Remove all comments from VHDL content.
        
        Args:
            vhdl_content: VHDL source code
            comment_marker: Comment marker (default: '--')
            
        Returns:
            VHDL content without comments
        """
        pattern = re.compile(rf'{re.escape(comment_marker)}.*$', re.MULTILINE)
        return pattern.sub('', vhdl_content)
    
    @staticmethod
    def format_vhdl_identifier(name: str) -> str:
        """
        Format identifier according to VHDL naming conventions.
        
        Args:
            name: Identifier name
            
        Returns:
            Formatted identifier (lowercase, valid characters)
        """
        # Convert to lowercase
        name = name.lower()
        # Replace invalid characters with underscores
        name = re.sub(r'[^a-z0-9_]', '_', name)
        # Ensure it doesn't start with a digit
        if name and name[0].isdigit():
            name = 'reg_' + name
        return name
    
    @staticmethod
    def generate_bit_mask(high: int, low: int = 0) -> int:
        """
        Generate bit mask for signal range.
        
        Args:
            high: High bit index
            low: Low bit index
            
        Returns:
            Integer bit mask
            
        Example:
            generate_bit_mask(7, 4) -> 0xF0
        """
        width = abs(high - low) + 1
        mask = (1 << width) - 1
        return mask << low
    
    @staticmethod
    def indent_vhdl_code(code: str, indent: int = 4) -> str:
        """
        Indent VHDL code.
        
        Args:
            code: VHDL code to indent
            indent: Number of spaces for indentation
            
        Returns:
            Indented code
        """
        lines = code.split('\n')
        indented = [' ' * indent + line if line.strip() else line for line in lines]
        return '\n'.join(indented)
