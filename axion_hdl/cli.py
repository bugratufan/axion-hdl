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
import json

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
        metavar='PATH',
        default=[],
        help='Source file (.vhd, .vhdl, .xml, .yaml, .yml, .json) or directory. '
             'File type is auto-detected by extension. '
             'Can be specified multiple times.'
    )
    
    parser.add_argument(
        '-x', '--xml-source',
        action='append',
        dest='xml_sources',
        metavar='PATH',
        default=[],
        help='(Deprecated: use -s instead) XML source file or directory. '
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

    parser.add_argument(
        '-c', '--config',
        dest='config_file',
        metavar='FILE',
        help='Load configuration (sources, excludes) from JSON file'
    )
    
    # Generation options
    gen_group = parser.add_argument_group('Generation Options')
    
    gen_group.add_argument(
        '--all',
        action='store_true',
        help='Generate all outputs: VHDL, documentation, XML, YAML, JSON, and C headers'
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
    
    gen_group.add_argument(
        '--yaml',
        action='store_true',
        help='Generate YAML register map description'
    )
    
    gen_group.add_argument(
        '--json',
        action='store_true',
        help='Generate JSON register map description'
    )

    gen_group.add_argument(
        '--gui',
        action='store_true',
        help='Launch interactive GUI editor for visualizing and modifying registers'
    )

    gen_group.add_argument(
        '--rule-check',
        nargs='?',
        const='rule_check_report.json',
        default=None,
        metavar='REPORT_FILE',
        help='Run validation rules. Optional: specify output report file (default: rule_check_report.json)'
    )
    
    gen_group.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port number for GUI server (default: 5000)'
    )
    
    # Parse arguments
    args = parser.parse_args()

    # Check for default config file if not specified
    if not args.config_file and os.path.exists(".axion_conf"):
        print("Using configuration from .axion_conf")
        args.config_file = ".axion_conf"

    # Load configuration from file if specified
    if args.config_file:
        try:
            with open(args.config_file, 'r') as f:
                config = json.load(f)
                
                # Merge sources
                config_sources = []
                config_sources.extend(config.get('src_dirs', []))
                config_sources.extend(config.get('src_files', []))
                config_sources.extend(config.get('xml_src_dirs', []))
                config_sources.extend(config.get('xml_src_files', []))
                config_sources.extend(config.get('yaml_src_dirs', []))
                config_sources.extend(config.get('yaml_src_files', []))
                config_sources.extend(config.get('json_src_dirs', []))
                config_sources.extend(config.get('json_src_files', []))
                
                # Append to args.sources (CLI flags take precedence? No, we merge)
                # Actually, adding them to list effectively merges them.
                if args.sources is None: args.sources = []
                args.sources.extend(config_sources)
                
                # Merge excludes
                if args.excludes is None: args.excludes = []
                args.excludes.extend(config.get('exclude_patterns', []))
                
                # Output dir (CLI flag takes precedence if not default)
                if 'output_dir' in config and args.output_dir == './axion_output':
                    args.output_dir = config['output_dir']
                    
        except Exception as e:
            print(f"Error loading config file: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Validate at least one source is provided
    if not args.sources and not args.xml_sources:
        print("Error: At least one source file or directory required. Use -s to specify.", 
              file=sys.stderr)
        sys.exit(1)
    
    # Validate all sources exist (files or directories)
    for src in args.sources:
        if not os.path.exists(src):
            print(f"Error: Source path does not exist: {src}", file=sys.stderr)
            sys.exit(1)
    
    # Validate XML sources exist (deprecated, but still supported)
    for src in args.xml_sources:
        if not os.path.exists(src):
            print(f"Error: XML source path does not exist: {src}", file=sys.stderr)
            sys.exit(1)
    
    # If no specific generation option is provided, default to --all (unless --gui or --rule-check is present)
    if not any([args.all, args.vhdl, args.doc, args.xml, args.yaml, args.json, args.c_header, args.gui, args.rule_check]):
        args.all = True
    
    # Initialize Axion-HDL
    axion = AxionHDL(output_dir=args.output_dir)
    
    # Add sources using unified add_source() method
    for src in args.sources:
        axion.add_source(src)
    
    # Add XML sources (deprecated path, still supported)
    for src in args.xml_sources:
        axion.add_xml_src(src)
    
    # Add exclusion patterns
    if args.excludes:
        axion.exclude(*args.excludes)
    
    # Analyze files
    # For GUI mode, tolerate analysis errors - GUI will display them gracefully
    analysis_error = None
    try:
        if not axion.analyze():
            if not args.gui:
                print("Error: Analysis failed. No modules found.", 
                      file=sys.stderr)
                sys.exit(1)
    except Exception as e:
        if args.gui:
            # Store error for GUI to display, but don't exit
            analysis_error = str(e)
            print(f"Warning: Analysis error (will be shown in GUI): {e}")
        else:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Check if any modules were found (skip for GUI mode with errors)
    if not axion.analyzed_modules and not args.gui:
        print("Warning: No modules with @axion annotations found in source directories.",
              file=sys.stderr)
        sys.exit(0)
    
    # Launch GUI if requested
    if args.gui:
        try:
            from axion_hdl import gui
            gui.start_gui(axion)
            sys.exit(0)
        except ImportError as e:
            print(f"Error launching GUI: {e}", file=sys.stderr)
            sys.exit(1)

    # Run rule checking if requested
    if args.rule_check is not None:
        print("Running Rule Checks...")
        passed = axion.run_rules(report_file=args.rule_check)
        if not passed:
            print("Rule Check failed with errors.", file=sys.stderr)
            sys.exit(1)
        # If not generating anything else, exit success
        if not any([args.all, args.vhdl, args.doc, args.xml, args.yaml, args.json, args.c_header]):
             sys.exit(0)
            
    # Generate outputs based on user selection
    success = True
    
    if args.all:
        # Generate all output types: VHDL, docs, XML, YAML, JSON, and C headers
        success = axion.generate_all(doc_format=args.doc_format)
    else:
        # Generate only selected output types
        if args.vhdl:
            success &= axion.generate_vhdl()
        if args.doc:
            success &= axion.generate_documentation(format=args.doc_format)
        if args.xml:
            success &= axion.generate_xml()
        if args.yaml:
            success &= axion.generate_yaml()
        if args.json:
            success &= axion.generate_json()
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
