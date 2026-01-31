"""
TOML Input Parser for Axion HDL

This module provides parsing functionality for TOML (Tom's Obvious, Minimal Language)
format register definition files. TOML files are converted to YAML-compatible dictionary
structures and processed by the YAMLInputParser for consistency.

The TOML format follows the same structure as YAML/JSON:
    [module]
    name = "sensor_controller"
    base_addr = "0x0000"

    [config]
    cdc_en = true
    cdc_stage = 2

    [[registers]]
    name = "control"
    addr = "0x00"
    access = "RW"
    width = 32
"""

import os
import sys

try:
    # Python 3.11+ has tomllib in standard library
    import tomllib
except ImportError:
    try:
        # Fallback to toml package for older Python versions
        import toml as tomllib
        # toml package uses load() with file object, tomllib uses load() with binary file
        _USE_TOML_PACKAGE = True
    except ImportError:
        tomllib = None
        _USE_TOML_PACKAGE = False

from axion_hdl.yaml_input_parser import YAMLInputParser


class TOMLInputParser:
    """
    Parser for TOML format register definition files.

    This parser converts TOML data to YAML-compatible dictionary structures
    and delegates to YAMLInputParser for actual parsing. This ensures format
    equivalence across TOML, YAML, JSON, and XML inputs.

    Attributes:
        yaml_parser (YAMLInputParser): Internal YAML parser for processing converted data
        errors (list): Collection of parsing errors encountered
        _exclude_patterns (set): File patterns to exclude from parsing
    """

    def __init__(self):
        """Initialize the TOML parser with a YAML parser delegate."""
        self.yaml_parser = YAMLInputParser()
        self._exclude_patterns = set()
        self.errors = []

    def parse_file(self, filepath):
        """
        Parse a single TOML file and convert to module dictionary.

        Args:
            filepath (str): Path to the TOML file

        Returns:
            dict: Module dictionary with register definitions, or None on error

        The TOML data is loaded and converted to a YAML-compatible dictionary,
        then passed to YAMLInputParser for standard processing.
        """
        if tomllib is None:
            error_msg = (
                "TOML support requires Python 3.11+ (tomllib) or 'toml' package. "
                "Install with: pip install toml"
            )
            self.errors.append({'file': filepath, 'msg': error_msg})
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            return None

        if not os.path.isfile(filepath):
            error_msg = f"TOML file not found: {filepath}"
            self.errors.append({'file': filepath, 'msg': error_msg})
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            return None

        try:
            # Load TOML data
            if hasattr(tomllib, 'load'):
                # Python 3.11+ tomllib expects binary mode
                if _USE_TOML_PACKAGE:
                    # toml package uses text mode
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = tomllib.load(f)
                else:
                    # tomllib (Python 3.11+) uses binary mode
                    with open(filepath, 'rb') as f:
                        data = tomllib.load(f)
            else:
                error_msg = "Invalid TOML library configuration"
                self.errors.append({'file': filepath, 'msg': error_msg})
                return None

            # Convert TOML to YAML-compatible dict structure
            yaml_dict = self._toml_to_yaml(data, filepath)

            if yaml_dict is None:
                return None

            # Delegate to YAML parser for standard processing
            result = self.yaml_parser.parse_data(yaml_dict, filepath)

            # Collect errors from YAML parser
            if self.yaml_parser.errors:
                self.errors.extend(self.yaml_parser.errors)

            return result

        except Exception as e:
            error_msg = f"Failed to parse TOML file: {str(e)}"
            self.errors.append({'file': filepath, 'msg': error_msg})
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            return None

    def _toml_to_yaml(self, data, filepath):
        """
        Convert TOML data structure to YAML-compatible dictionary.

        Args:
            data (dict): Parsed TOML data
            filepath (str): Source file path (for error reporting)

        Returns:
            dict: YAML-compatible dictionary structure

        The TOML format closely mirrors the YAML structure, so minimal
        conversion is needed. This method primarily validates structure
        and ensures consistency with YAML expectations.
        """
        try:
            # TOML structure already closely matches YAML
            # Main conversion is ensuring all expected fields exist
            yaml_dict = {}

            # Extract module name (required)
            if 'module' in data:
                if isinstance(data['module'], dict):
                    # [module] table format
                    module_name = data['module'].get('name')
                    base_addr = data['module'].get('base_addr', '0x0000')
                else:
                    # module = "name" format
                    module_name = data['module']
                    base_addr = data.get('base_addr', '0x0000')
            else:
                # Try top-level name field
                module_name = data.get('name')
                base_addr = data.get('base_addr', '0x0000')

            if not module_name:
                error_msg = "TOML file must specify 'module' or 'name' field"
                self.errors.append({'file': filepath, 'msg': error_msg})
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                return None

            yaml_dict['module'] = module_name
            yaml_dict['base_addr'] = base_addr

            # Extract config (optional)
            if 'config' in data:
                config = data['config']
                yaml_dict['config'] = {
                    'cdc_en': config.get('cdc_en', False),
                    'cdc_stage': config.get('cdc_stage', 2)
                }

            # Extract registers (required)
            if 'registers' in data:
                registers = []
                for reg in data['registers']:
                    reg_dict = {
                        'name': reg.get('name'),
                        'addr': reg.get('addr'),
                        'access': reg.get('access', 'RW'),
                    }

                    # Optional fields
                    if 'width' in reg:
                        reg_dict['width'] = reg['width']
                    if 'description' in reg:
                        reg_dict['description'] = reg['description']
                    if 'default' in reg:
                        reg_dict['default'] = reg['default']
                    if 'r_strobe' in reg:
                        reg_dict['r_strobe'] = reg['r_strobe']
                    if 'w_strobe' in reg:
                        reg_dict['w_strobe'] = reg['w_strobe']
                    if 'reg_name' in reg:
                        reg_dict['reg_name'] = reg['reg_name']
                    if 'bit_offset' in reg:
                        reg_dict['bit_offset'] = reg['bit_offset']

                    registers.append(reg_dict)

                yaml_dict['registers'] = registers
            else:
                error_msg = "TOML file must contain 'registers' array"
                self.errors.append({'file': filepath, 'msg': error_msg})
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                return None

            return yaml_dict

        except Exception as e:
            error_msg = f"Error converting TOML to YAML format: {str(e)}"
            self.errors.append({'file': filepath, 'msg': error_msg})
            print(f"[ERROR] {error_msg}", file=sys.stderr)
            return None

    def parse_toml_files(self, source_dirs):
        """
        Parse all TOML files in specified directories.

        Args:
            source_dirs (list): List of directory paths to scan

        Returns:
            list: List of module dictionaries from all parsed files

        Scans directories recursively for .toml files and parses each one.
        Respects exclude patterns configured via add_exclude().
        """
        import fnmatch

        modules = []

        for src_dir in source_dirs:
            if not os.path.isdir(src_dir):
                error_msg = f"Directory not found: {src_dir}"
                self.errors.append({'file': src_dir, 'msg': error_msg})
                print(f"[ERROR] {error_msg}", file=sys.stderr)
                continue

            for root, dirs, files in os.walk(src_dir):
                for filename in files:
                    if filename.endswith('.toml'):
                        filepath = os.path.join(root, filename)

                        # Check exclusion patterns
                        excluded = False
                        for pattern in self._exclude_patterns:
                            if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(filename, pattern):
                                excluded = True
                                break

                        if excluded:
                            continue

                        module = self.parse_file(filepath)
                        if module:
                            modules.append(module)

        return modules

    def add_exclude(self, pattern):
        """
        Add a file pattern to exclude from parsing.

        Args:
            pattern (str): Glob pattern (e.g., '*_test.toml', 'temp_*')
        """
        self._exclude_patterns.add(pattern)

    def remove_exclude(self, pattern):
        """
        Remove a file pattern from exclusion list.

        Args:
            pattern (str): Pattern to remove
        """
        self._exclude_patterns.discard(pattern)

    def clear_excludes(self):
        """Clear all exclusion patterns."""
        self._exclude_patterns.clear()

    def list_excludes(self):
        """
        Get list of all exclusion patterns.

        Returns:
            list: Sorted list of exclusion patterns
        """
        return sorted(self._exclude_patterns)
