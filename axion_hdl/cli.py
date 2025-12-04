#!/usr/bin/env python3
"""
Axion-HDL Command Line Interface

This module provides the command-line interface for the Axion HDL tool.
It allows users to generate AXI4-Lite register interfaces from VHDL files
with @axion annotations.

Usage Examples:
    # Generate all outputs from a single source directory
    $ axion-hdl -s ./src -o ./output --all
    
    # Generate only VHDL and C headers from multiple source directories
    $ axion-hdl -s ./rtl -s ./ip -o ./generated --vhdl --c-header
    
    # Generate documentation in HTML format
    $ axion-hdl -s ./hdl -o ./out --doc --doc-format html

Exit Codes:
    0 - Success
    1 - Error (invalid arguments, analysis failure, or generation failure)

For more information, visit: https://github.com/bugratufan/axion-hdl
"""

import argparse
import sys
import os

from axion_hdl import AxionHDL, __version__


def main():
    """
    Main entry point for the Axion-HDL CLI.
    
    Parses command-line arguments, initializes the AxionHDL instance,
    performs analysis on VHDL source files, and generates requested outputs.
    
    Returns:
        None (exits with appropriate exit code)
    """
    parser = argparse.ArgumentParser(
        prog='axion-hdl',
        description='Axion-HDL: Automated AXI4-Lite Register Interface Generator for VHDL',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  axion-hdl -s ./src -o ./output
  axion-hdl -s ./rtl -s ./ip -o ./generated --all
  axion-hdl -s ./hdl -o ./out --vhdl --c-header
  axion-hdl -s ./design --doc-format html

For more information, visit: https://github.com/bugratufan/axion-hdl
        """
    )
    
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    parser.add_argument(
        '-s', '--source',
        action='append',
        dest='sources',
        metavar='DIR',
        required=True,
        help='Source directory containing VHDL files with @axion annotations. '
             'Can be specified multiple times.'
    )
    
    parser.add_argument(
        '-o', '--output',
        dest='output_dir',
        metavar='DIR',
        default='./axion_output',
        help='Output directory for generated files (default: ./axion_output)'
    )
    
    parser.add_argument(
        '-e', '--exclude',
        action='append',
        dest='excludes',
        metavar='PATTERN',
        default=[],
        help='Exclude files or directories matching pattern. '
             'Can be file names, directory names, or glob patterns. '
             'Can be specified multiple times. '
             'Examples: -e "error_cases" -e "*_tb.vhd"'
    )
    
    # Generation options
    gen_group = parser.add_argument_group('Generation Options')
    
    gen_group.add_argument(
        '--all',
        action='store_true',
        help='Generate all outputs: VHDL, documentation, XML, and C headers'
    )
    
    gen_group.add_argument(
        '--vhdl',
        action='store_true',
        help='Generate VHDL register interface modules (*_axion_reg.vhd)'
    )
    
    gen_group.add_argument(
        '--doc',
        action='store_true',
        help='Generate register map documentation'
    )
    
    gen_group.add_argument(
        '--doc-format',
        choices=['md', 'html', 'pdf'],
        default='md',
        metavar='FORMAT',
        help='Documentation format: md (default), html, or pdf'
    )
    
    gen_group.add_argument(
        '--xml',
        action='store_true',
        help='Generate XML register map description (IP-XACT compatible)'
    )
    
    gen_group.add_argument(
        '--c-header',
        action='store_true',
        help='Generate C header files with register definitions'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Validate source directories
    for src in args.sources:
        if not os.path.isdir(src):
            print(f"Error: Source directory does not exist: {src}", file=sys.stderr)
            sys.exit(1)
    
    # If no specific generation option is provided, default to --all
    if not any([args.all, args.vhdl, args.doc, args.xml, args.c_header]):
        args.all = True
    
    # Initialize Axion-HDL
    axion = AxionHDL(output_dir=args.output_dir)
    
    # Add source directories
    for src in args.sources:
        axion.add_src(src)
    
    # Add exclusion patterns
    if args.excludes:
        axion.exclude(*args.excludes)
    
    # Analyze VHDL files
    if not axion.analyze():
        print("Error: Analysis failed. No modules with @axion annotations found.", 
              file=sys.stderr)
        sys.exit(1)
    
    # Check if any modules were found
    if not axion.analyzed_modules:
        print("Warning: No modules with @axion annotations found in source directories.",
              file=sys.stderr)
        sys.exit(0)
    
    # Generate outputs based on user selection
    success = True
    
    if args.all:
        # Generate all output types: VHDL, docs, XML, and C headers
        success = axion.generate_all(doc_format=args.doc_format)
    else:
        # Generate only selected output types
        if args.vhdl:
            success &= axion.generate_vhdl()
        if args.doc:
            success &= axion.generate_documentation(format=args.doc_format)
        if args.xml:
            success &= axion.generate_xml()
        if args.c_header:
            success &= axion.generate_c_header()
    
    # Report final status
    if success:
        print(f"\nGeneration completed successfully!")
        print(f"Output directory: {os.path.abspath(args.output_dir)}")
        sys.exit(0)
    else:
        print("Error: Generation failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
