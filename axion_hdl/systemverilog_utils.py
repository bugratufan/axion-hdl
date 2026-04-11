"""
SystemVerilog Utilities Module
==============================

Provides utility functions for parsing and formatting SystemVerilog code.
This module is the SystemVerilog equivalent of vhdl_utils.py.

Author: Axion-HDL
License: MIT
"""

import re
from typing import Optional, Tuple


class SystemVerilogUtils:
    """Utility class for SystemVerilog parsing and formatting operations"""

    # Regex patterns for SystemVerilog constructs
    MODULE_PATTERN = re.compile(
        r'module\s+(\w+)\s*[#(]',
        re.IGNORECASE
    )

    SIGNAL_TYPE_PATTERN = re.compile(
        r'(logic|reg|wire)\s*(\[[^\]]+\])?',
        re.IGNORECASE
    )

    RANGE_PATTERN = re.compile(
        r'\[(\d+):(\d+)\]'
    )

    PARAMETER_PATTERN = re.compile(
        r'parameter\s+(?:(int|logic|reg|wire)\s+)?(\w+)\s*=\s*(.+?)(?:;|,)',
        re.IGNORECASE
    )

    @staticmethod
    def parse_signal_type(type_str: str) -> Tuple[str, int, int]:
        """
        Parse SystemVerilog signal type declaration.

        Args:
            type_str: Signal type string (e.g., "logic [31:0]", "logic", "reg [7:0]")

        Returns:
            Tuple of (base_type, high_index, low_index)
            - For "logic [31:0]" -> ("logic", 31, 0)
            - For "logic" -> ("logic", 0, 0)
            - For "reg [7:0]" -> ("reg", 7, 0)

        Examples:
            >>> SystemVerilogUtils.parse_signal_type("logic [31:0]")
            ("logic", 31, 0)
            >>> SystemVerilogUtils.parse_signal_type("logic")
            ("logic", 0, 0)
            >>> SystemVerilogUtils.parse_signal_type("wire [15:0]")
            ("wire", 15, 0)
        """
        type_str = type_str.strip()

        # Match signal type pattern
        match = SystemVerilogUtils.SIGNAL_TYPE_PATTERN.match(type_str)
        if not match:
            # Default to logic if no match
            return ("logic", 0, 0)

        base_type = match.group(1).lower()  # logic, reg, or wire
        range_str = match.group(2)  # [31:0] or None

        if range_str:
            # Parse range
            range_match = SystemVerilogUtils.RANGE_PATTERN.search(range_str)
            if range_match:
                high = int(range_match.group(1))
                low = int(range_match.group(2))
                return (base_type, high, low)

        # No range found, single-bit signal
        return (base_type, 0, 0)

    @staticmethod
    def format_signal_type(high: int, low: int = 0, base_type: str = "logic") -> str:
        """
        Format signal type as SystemVerilog type string.

        Args:
            high: High index of range
            low: Low index of range (default: 0)
            base_type: Base type (default: "logic")

        Returns:
            Formatted type string
            - (31, 0) -> "logic [31:0]"
            - (0, 0) -> "logic"
            - (7, 0, "reg") -> "reg [7:0]"

        Examples:
            >>> SystemVerilogUtils.format_signal_type(31, 0)
            "logic [31:0]"
            >>> SystemVerilogUtils.format_signal_type(0, 0)
            "logic"
            >>> SystemVerilogUtils.format_signal_type(15, 0, "wire")
            "wire [15:0]"
        """
        if high == 0 and low == 0:
            # Single-bit signal
            return base_type
        else:
            # Multi-bit signal with range
            return f"{base_type} [{high}:{low}]"

    @staticmethod
    def format_range(high: int, low: int = 0) -> str:
        """
        Format range as SystemVerilog range string.

        Args:
            high: High index
            low: Low index (default: 0)

        Returns:
            Range string
            - (31, 0) -> "[31:0]"
            - (0, 0) -> "" (empty string for single bit)

        Examples:
            >>> SystemVerilogUtils.format_range(31, 0)
            "[31:0]"
            >>> SystemVerilogUtils.format_range(7, 0)
            "[7:0]"
            >>> SystemVerilogUtils.format_range(0, 0)
            ""
        """
        if high == 0 and low == 0:
            return ""
        return f"[{high}:{low}]"

    @staticmethod
    def extract_module_name(content: str) -> Optional[str]:
        """
        Extract module name from SystemVerilog file content.

        Args:
            content: SystemVerilog file content

        Returns:
            Module name if found, None otherwise

        Examples:
            >>> content = "module sensor_controller (..."
            >>> SystemVerilogUtils.extract_module_name(content)
            "sensor_controller"

            >>> content = "module my_module #(parameter..."
            >>> SystemVerilogUtils.extract_module_name(content)
            "my_module"
        """
        match = SystemVerilogUtils.MODULE_PATTERN.search(content)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def parse_parameter(param_str: str) -> Tuple[Optional[str], str, str]:
        """
        Parse SystemVerilog parameter declaration.

        Args:
            param_str: Parameter string (e.g., "parameter int ADDR_WIDTH = 32")

        Returns:
            Tuple of (type, name, value)
            - "parameter int ADDR_WIDTH = 32" -> ("int", "ADDR_WIDTH", "32")
            - "parameter DATA_WIDTH = 32" -> (None, "DATA_WIDTH", "32")

        Examples:
            >>> SystemVerilogUtils.parse_parameter("parameter int ADDR_WIDTH = 32")
            ("int", "ADDR_WIDTH", "32")
            >>> SystemVerilogUtils.parse_parameter("parameter DATA_WIDTH = 32")
            (None, "DATA_WIDTH", "32")
        """
        match = SystemVerilogUtils.PARAMETER_PATTERN.search(param_str)
        if match:
            param_type = match.group(1)  # Can be None
            param_name = match.group(2)
            param_value = match.group(3).strip()
            return (param_type, param_name, param_value)
        return (None, "", "")

    @staticmethod
    def calculate_width(high: int, low: int = 0) -> int:
        """
        Calculate signal width from high and low indices.

        Args:
            high: High index
            low: Low index (default: 0)

        Returns:
            Signal width in bits

        Examples:
            >>> SystemVerilogUtils.calculate_width(31, 0)
            32
            >>> SystemVerilogUtils.calculate_width(7, 0)
            8
            >>> SystemVerilogUtils.calculate_width(0, 0)
            1
        """
        return abs(high - low) + 1

    @staticmethod
    def is_single_bit(high: int, low: int = 0) -> bool:
        """
        Check if signal is single-bit.

        Args:
            high: High index
            low: Low index (default: 0)

        Returns:
            True if single-bit, False otherwise

        Examples:
            >>> SystemVerilogUtils.is_single_bit(0, 0)
            True
            >>> SystemVerilogUtils.is_single_bit(7, 0)
            False
        """
        return high == 0 and low == 0

    @staticmethod
    def sanitize_identifier(name: str) -> str:
        """
        Sanitize identifier to be valid SystemVerilog.

        Args:
            name: Identifier name

        Returns:
            Sanitized identifier

        Examples:
            >>> SystemVerilogUtils.sanitize_identifier("my-signal")
            "my_signal"
            >>> SystemVerilogUtils.sanitize_identifier("123signal")
            "_123signal"
        """
        # Replace invalid characters with underscore
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', name)

        # Ensure doesn't start with digit
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized

        return sanitized

    @staticmethod
    def format_hex_value(value: int, width: int = 32) -> str:
        """
        Format integer value as SystemVerilog hex literal.

        Args:
            value: Integer value
            width: Bit width (default: 32)

        Returns:
            SystemVerilog hex literal

        Examples:
            >>> SystemVerilogUtils.format_hex_value(255, 8)
            "8'hFF"
            >>> SystemVerilogUtils.format_hex_value(4096, 32)
            "32'h00001000"
        """
        hex_digits = (width + 3) // 4  # Round up to nearest hex digit
        hex_str = f"{value:0{hex_digits}X}"
        return f"{width}'h{hex_str}"

    @staticmethod
    def format_binary_value(value: int, width: int) -> str:
        """
        Format integer value as SystemVerilog binary literal.

        Args:
            value: Integer value
            width: Bit width

        Returns:
            SystemVerilog binary literal

        Examples:
            >>> SystemVerilogUtils.format_binary_value(15, 4)
            "4'b1111"
            >>> SystemVerilogUtils.format_binary_value(5, 8)
            "8'b00000101"
        """
        bin_str = f"{value:0{width}b}"
        return f"{width}'b{bin_str}"
