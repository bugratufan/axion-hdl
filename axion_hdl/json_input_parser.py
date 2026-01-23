"""
JSON Input Parser Module for Axion HDL

This module parses JSON register definition files by first converting them to YAML format,
then using YAMLInputParser for processing. This provides a unified parsing pipeline.
"""

import os
import json
import fnmatch
from typing import Dict, List, Optional, Set

# Import from axion_hdl
from axion_hdl.address_manager import AddressManager
from axion_hdl.yaml_input_parser import YAMLInputParser

try:
    import yaml
except ImportError:
    yaml = None


class JSONInputParser:
    """Parser for JSON register definition files.
    
    Supports JSON format matching the XML/YAML simple format structure:
    
    Example format:
        {
          "module": "my_module",
          "base_addr": "0x0000",
          "config": {
            "cdc_en": true,
            "cdc_stage": 2
          },
          "registers": [
            {
              "name": "status",
              "addr": "0x00",
              "access": "RO",
              "width": 32,
              "description": "Status register"
            }
          ]
        }
    """
    
    def __init__(self):
        self.address_manager = AddressManager()
        self._exclude_patterns: Set[str] = set()
        self.errors = []
        self.yaml_parser = YAMLInputParser()
        
        if yaml is None:
            raise ImportError("PyYAML is required for JSON input support. Install with: pip install PyYAML")
    
    def add_exclude(self, pattern: str):
        """Add an exclusion pattern for files/directories."""
        self._exclude_patterns.add(pattern)
    
    def remove_exclude(self, pattern: str):
        """Remove an exclusion pattern."""
        self._exclude_patterns.discard(pattern)
    
    def clear_excludes(self):
        """Clear all exclusion patterns."""
        self._exclude_patterns.clear()
    
    def list_excludes(self) -> List[str]:
        """Return list of exclusion patterns."""
        return list(self._exclude_patterns)
    
    def _is_excluded(self, filepath: str) -> bool:
        """Check if a file path matches any exclusion pattern."""
        filename = os.path.basename(filepath)
        
        for pattern in self._exclude_patterns:
            if fnmatch.fnmatch(filename, pattern):
                return True
            if fnmatch.fnmatch(filepath, f"*/{pattern}/*"):
                return True
            if fnmatch.fnmatch(filepath, f"*/{pattern}"):
                return True
        return False
    
    def parse_file(self, filepath: str) -> Optional[Dict]:
        """
        Parse a single JSON file by converting to YAML then using YAMLInputParser.
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Dictionary with module data or None if parsing fails
        """
        print(f"Parsing JSON file: {filepath}")
        if not os.path.exists(filepath):
            msg = f"JSON file not found: {filepath}"
            print(f"  Warning: {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                print(f"  Warning: Empty JSON file: {filepath}")
                return None
            
            # JSON data is already a dict, directly compatible with YAML structure
            # Use YAML parser for processing
            result = self.yaml_parser._parse_yaml_data(data, filepath)
            
            # Merge errors from YAML parser
            if self.yaml_parser.errors:
                self.errors.extend(self.yaml_parser.errors)
                self.yaml_parser.errors = []
            
            return result
            
        except json.JSONDecodeError as e:
            msg = f"Error parsing JSON file {filepath}: {e}"
            print(f"  {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
        except Exception as e:
            msg = f"Error processing JSON file {filepath}: {e}"
            print(f"  {msg}")
            self.errors.append({'file': filepath, 'msg': msg})
            return None
    
    def parse_json_files(self, source_dirs: List[str]) -> List[Dict]:
        """
        Parse all JSON files in source directories.
        
        Args:
            source_dirs: List of source directory paths
            
        Returns:
            List of parsed module dictionaries
        """
        modules = []
        
        for src_dir in source_dirs:
            if not os.path.isdir(src_dir):
                print(f"  Warning: JSON source directory not found: {src_dir}")
                continue
            
            json_files = self._find_json_files(src_dir)
            
            for json_file in json_files:
                if self._is_excluded(json_file):
                    print(f"  Skipping excluded: {json_file}")
                    continue
                
                module = self.parse_file(json_file)
                if module:
                    modules.append(module)
        
        return modules
    
    def _find_json_files(self, directory: str) -> List[str]:
        """Find all JSON files in directory (recursive)."""
        json_files = []
        
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith('.json'):
                    json_files.append(os.path.join(root, filename))
        
        return sorted(json_files)
