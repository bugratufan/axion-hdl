"""
Axion HDL Main Interface Module

This module provides the main AxionHDL class which serves as the primary
interface for the Axion HDL tool. It orchestrates the parsing of VHDL files,
analysis of @axion annotations, and generation of various output files.

The typical workflow is:
    1. Create an AxionHDL instance with output directory
    2. Add source directories containing VHDL files
    3. Call analyze() to parse all VHDL files
    4. Generate outputs (VHDL, C headers, XML, documentation)

Example:
    from axion_hdl import AxionHDL
    
    axion = AxionHDL(output_dir="./output")
    axion.add_src("./rtl")
    axion.analyze()
    axion.generate_all()
"""

import os
from .parser import VHDLParser
from .generator import VHDLGenerator
from .doc_generators import DocGenerator, CHeaderGenerator, XMLGenerator


class AxionHDL:
    """
    Main interface class for Axion HDL tool.
    
    This class provides methods to:
    - Add and manage VHDL source directories
    - Analyze VHDL files for @axion annotations
    - Generate AXI4-Lite register interface modules
    - Generate documentation and header files
    
    Attributes:
        src_dirs (list): List of source directories to search for VHDL files
        output_dir (str): Output directory for generated files
        analyzed_modules (list): List of parsed module data after analysis
        is_analyzed (bool): Flag indicating if analysis has been performed
    """
    
    def __init__(self, output_dir="./axion_output"):
        """
        Initialize Axion HDL generator.
        
        Args:
            output_dir: Output directory for generated files (default: ./axion_output)
        """
        self.src_dirs = []
        self.output_dir = os.path.abspath(output_dir)
        self.analyzed_modules = []
        self.is_analyzed = False
        self._exclude_patterns = set()
        
    def set_output_dir(self, dir_path):
        """
        Set the output directory for generated files.
        
        Args:
            dir_path: Path to output directory
        """
        self.output_dir = os.path.abspath(dir_path)
        print(f"Output directory set to: {self.output_dir}")
    
    def exclude(self, *patterns):
        """
        Exclude files or directories from parsing.
        
        Patterns can be:
        - File names: "address_conflict_test.vhd"
        - Directory names: "error_cases", "testbenches"
        - Glob patterns: "test_*.vhd", "*_tb.vhd"
        - Multiple patterns at once
        
        Args:
            *patterns: One or more patterns to exclude
            
        Example:
            axion.exclude("error_cases")
            axion.exclude("*_tb.vhd", "test_*.vhd")
            axion.exclude("debug_module.vhd", "deprecated")
        """
        for pattern in patterns:
            self._exclude_patterns.add(pattern)
            print(f"Exclusion added: {pattern}")
            
    def include(self, *patterns):
        """
        Remove exclusion patterns (re-include previously excluded items).
        
        Args:
            *patterns: One or more patterns to remove from exclusions
        """
        for pattern in patterns:
            if pattern in self._exclude_patterns:
                self._exclude_patterns.discard(pattern)
                print(f"Exclusion removed: {pattern}")
            else:
                print(f"Pattern not in exclusions: {pattern}")
                
    def clear_excludes(self):
        """Clear all exclusion patterns."""
        self._exclude_patterns.clear()
        print("All exclusions cleared.")
        
    def list_excludes(self):
        """List all current exclusion patterns."""
        if self._exclude_patterns:
            print("Exclusion patterns:")
            for pattern in sorted(self._exclude_patterns):
                print(f"  - {pattern}")
        else:
            print("No exclusion patterns defined.")
        
    def add_src(self, dir_path):
        """
        Add a source directory containing VHDL files.
        
        Args:
            dir_path: Path to the source directory
        """
        normalized_path = os.path.abspath(dir_path)
        if os.path.isdir(normalized_path):
            if normalized_path not in self.src_dirs:
                self.src_dirs.append(normalized_path)
                print(f"Source directory added: {normalized_path}")
            else:
                print(f"Source directory already exists: {normalized_path}")
        else:
            print(f"Error: '{normalized_path}' is not a valid directory.")

    def list_src(self):
        """List all added source directories."""
        if self.src_dirs:
            print("Source directories:")
            for directory in self.src_dirs:
                print(f"  - {directory}")
        else:
            print("No source directories added yet.")
            
    def analyze(self):
        """
        Analyze all VHDL files in source directories and parse @axion annotations.
        This must be called before any generation functions.
        
        Files and directories matching exclusion patterns will be skipped.
        Use exclude() to add patterns before calling analyze().
        """
        if not self.src_dirs:
            print("Error: No source directories added. Use add_src() first.")
            return False
            
        print(f"\n{'='*60}")
        print("Starting analysis of VHDL files...")
        print(f"{'='*60}")
        
        # Show exclusions if any
        if self._exclude_patterns:
            print(f"Excluding: {', '.join(sorted(self._exclude_patterns))}")
        
        # Parse VHDL files
        parser = VHDLParser()
        
        # Apply exclusion patterns
        for pattern in self._exclude_patterns:
            parser.add_exclude(pattern)
            
        self.analyzed_modules = parser.parse_vhdl_files(self.src_dirs)
        self.is_analyzed = True
        
        print(f"\nAnalysis complete. Found {len(self.analyzed_modules)} modules with @axion annotations.")
        
        # Display register summary for each module
        if self.analyzed_modules:
            self._print_analysis_summary()
        
        return True
    
    def _print_analysis_summary(self):
        """
        Print a formatted table summary of all detected registers for each module.
        """
        for module in self.analyzed_modules:
            base_addr = module.get('base_address', 0x00)
            base_addr_str = f"0x{base_addr:04X}"
            
            print(f"\n{'='*110}")
            print(f"Module: {module['name']}")
            if module.get('cdc_enabled'):
                cdc_info = f"CDC: Enabled (Stages: {module.get('cdc_stages', 2)})"
            else:
                cdc_info = "CDC: Disabled"
            print(f"File: {module['file']}")
            print(f"{cdc_info}")
            print(f"Base Address: {base_addr_str}")
            print(f"{'='*110}")
            
            if not module.get('registers'):
                print("No registers found in this module.")
                continue
            
            # Print table header
            print(f"\n{'Signal Name':<25} {'Type':<8} {'Abs.Addr':<10} {'Offset':<10} {'Access':<8} {'Strobes':<15} {'Ports Generated'}")
            print(f"{'-'*25} {'-'*8} {'-'*10} {'-'*10} {'-'*8} {'-'*15} {'-'*40}")
            
            # Print each register
            for reg in module['registers']:
                signal_name = reg['signal_name']
                signal_type = reg['signal_type']
                address = reg.get('address', 'Auto')
                offset = reg.get('relative_address', address)
                access_mode = reg['access_mode']
                
                # Determine strobes
                strobes = []
                if reg.get('read_strobe'):
                    strobes.append('RD')
                if reg.get('write_strobe'):
                    strobes.append('WR')
                strobe_str = ', '.join(strobes) if strobes else 'None'
                
                # Determine generated ports
                ports = [signal_name]
                if reg.get('read_strobe'):
                    ports.append(f"{signal_name}_rd_strobe")
                if reg.get('write_strobe'):
                    ports.append(f"{signal_name}_wr_strobe")
                
                ports_str = ', '.join(ports)
                
                print(f"{signal_name:<25} {signal_type:<8} {address:<10} {offset:<10} {access_mode:<8} {strobe_str:<15} {ports_str}")
            
            print(f"\nTotal Registers: {len(module['registers'])}")
            
        print(f"\n{'='*110}")
        print(f"Summary: {len(self.analyzed_modules)} module(s) analyzed")
        total_regs = sum(len(m.get('registers', [])) for m in self.analyzed_modules)
        print(f"Total Registers: {total_regs}")
        print(f"{'='*110}\n")
        
    def generate_vhdl(self):
        """
        Generate VHDL register interface modules (*_axion_reg.vhd) for all analyzed modules.
        """
        if not self.is_analyzed:
            print("Error: Analysis not performed. Call analyze() first.")
            return False
            
        print(f"\n{'='*60}")
        print("Generating VHDL register modules...")
        print(f"{'='*60}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate VHDL modules
        generator = VHDLGenerator(self.output_dir)
        for module in self.analyzed_modules:
            output_path = generator.generate_module(module)
            print(f"  Generated: {os.path.basename(output_path)}")
        
        print(f"\nVHDL files generated in: {self.output_dir}")
        return True
        
    def generate_documentation(self, format="md"):
        """
        Generate register map documentation.
        
        Args:
            format: Documentation format - "md" (Markdown), "html", or "pdf"
        """
        if not self.is_analyzed:
            print("Error: Analysis not performed. Call analyze() first.")
            return False
            
        print(f"\n{'='*60}")
        print(f"Generating documentation ({format.upper()})...")
        print(f"{'='*60}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate documentation
        doc_gen = DocGenerator(self.output_dir)
        if format == "md":
            output_path = doc_gen.generate_markdown(self.analyzed_modules)
            print(f"  Generated: {os.path.basename(output_path)}")
        
        print(f"\nDocumentation generated in: {self.output_dir}")
        return True
        
    def generate_xml(self):
        """
        Generate XML register map description.
        Useful for integration with IP-XACT or other tools.
        """
        if not self.is_analyzed:
            print("Error: Analysis not performed. Call analyze() first.")
            return False
            
        print(f"\n{'='*60}")
        print("Generating XML register map...")
        print(f"{'='*60}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate XML files
        xml_gen = XMLGenerator(self.output_dir)
        for module in self.analyzed_modules:
            output_path = xml_gen.generate_xml(module)
            print(f"  Generated: {os.path.basename(output_path)}")
        
        print(f"\nXML files generated in: {self.output_dir}")
        return True
        
    def generate_c_header(self):
        """
        Generate C header files with register definitions.
        Useful for software development targeting the AXI registers.
        """
        if not self.is_analyzed:
            print("Error: Analysis not performed. Call analyze() first.")
            return False
            
        print(f"\n{'='*60}")
        print("Generating C header files...")
        print(f"{'='*60}")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Generate C headers
        c_gen = CHeaderGenerator(self.output_dir)
        for module in self.analyzed_modules:
            output_path = c_gen.generate_header(module)
            print(f"  Generated: {os.path.basename(output_path)}")
        
        print(f"\nC header files generated in: {self.output_dir}")
        return True
        
    def generate_all(self, doc_format="md"):
        """
        Generate all outputs: VHDL, documentation, XML, and C headers.
        
        Args:
            doc_format: Documentation format - "md", "html", or "pdf"
        """
        if not self.is_analyzed:
            print("Error: Analysis not performed. Call analyze() first.")
            return False
            
        success = True
        success &= self.generate_vhdl()
        success &= self.generate_documentation(doc_format)
        success &= self.generate_xml()
        success &= self.generate_c_header()
        
        if success:
            print(f"\n{'='*60}")
            print("All files generated successfully!")
            print(f"Output directory: {self.output_dir}")
            print(f"{'='*60}")
        
        return success