"""
Axion HDL - Automated AXI4-Lite Register Interface Generator

This package provides automated generation of AXI4-Lite register interfaces
for VHDL modules, including address management, code generation, and documentation.

Main Features:
- Parse VHDL files with @axion annotations
- Generate AXI4-Lite register interface modules (*_axion_reg.vhd)
- Generate C header files with register definitions
- Generate XML register maps (IP-XACT compatible)
- Generate Markdown documentation

Usage:
    CLI:
        $ axion-hdl -s ./src -o ./output --all
    
    Python API:
        from axion_hdl import AxionHDL
        
        axion = AxionHDL(output_dir="./output")
        axion.add_src("./src")
        axion.analyze()
        axion.generate_all()

Author: Bugra Tufan
License: MIT
Repository: https://github.com/bugratufan/axion-hdl
"""

# Import core classes for convenient access
from .address_manager import AddressManager, AddressConflictError
from .vhdl_utils import VHDLUtils
from .annotation_parser import AnnotationParser
from .code_formatter import CodeFormatter
from .parser import VHDLParser
from .generator import VHDLGenerator
from .doc_generators import DocGenerator, CHeaderGenerator, XMLGenerator
from .axion import AxionHDL

# Package metadata
__version__ = "0.3.0"
__author__ = "Bugra Tufan"
__email__ = "bugratufan97@gmail.com"
__license__ = "MIT"

# Public API - classes exposed when using 'from axion_hdl import *'
__all__ = [
    'AxionHDL',              # Main interface class
    'AddressManager',        # Address allocation and management
    'AddressConflictError',  # Exception for address conflicts
    'VHDLUtils',             # VHDL parsing utilities
    'AnnotationParser',      # @axion annotation parser
    'CodeFormatter',         # Code formatting utilities
    'VHDLParser',            # VHDL file parser
    'VHDLGenerator',         # VHDL code generator
    'DocGenerator',          # Documentation generator
    'CHeaderGenerator',      # C header file generator
    'XMLGenerator',          # XML register map generator
    '__version__',
    '__author__',
    '__email__',
    '__license__',
]
