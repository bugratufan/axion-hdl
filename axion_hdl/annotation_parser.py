"""
Annotation Parser Module

Parses @axion annotations and other comment-based metadata from source files.
Provides a flexible annotation parsing framework for HDL tools.
"""

import re
from typing import Dict, List, Optional, Tuple, Any


class AnnotationParser:
    """
    Generic annotation parser for extracting metadata from comments.
    
    Features:
    - Parse key-value pairs from annotations
    - Support for multiple annotation formats
    - Attribute validation and type conversion
    - Extensible annotation schema
    """
    
    def __init__(self, annotation_prefix: str = '@axion'):
        """
        Initialize AnnotationParser.
        
        Args:
            annotation_prefix: Prefix for annotations (default: '@axion')
        """
        self.annotation_prefix = annotation_prefix
        self.annotation_pattern = re.compile(
            rf'--\s*{re.escape(annotation_prefix)}\s+(.+)',
            re.IGNORECASE
        )
        self.def_pattern = re.compile(
            rf'--\s*{re.escape(annotation_prefix)}_def\s+(.+)',
            re.IGNORECASE
        )
        
    def parse_annotation(self, comment: str) -> Optional[Dict[str, Any]]:
        """
        Parse a single annotation comment.
        
        Args:
            comment: Comment line containing annotation
            
        Returns:
            Dictionary of parsed attributes or None
            
        Example:
            "-- @axion RW ADDR=0x10 W_STROBE" -> 
            {'access_mode': 'RW', 'address': '0x10', 'write_strobe': True}
        """
        match = self.annotation_pattern.search(comment)
        if not match:
            return None
            
        attrs_str = match.group(1).strip()
        return self.parse_attributes(attrs_str)
    
    def parse_def_annotation(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse module-level definition annotation.
        
        Args:
            content: Source file content
            
        Returns:
            Dictionary of parsed module attributes or None
            
        Example:
            "-- @axion_def CDC_EN CDC_STAGE=3" ->
            {'cdc_enabled': True, 'cdc_stages': 3}
        """
        match = self.def_pattern.search(content)
        if not match:
            return None
            
        attrs_str = match.group(1).strip()
        return self.parse_attributes(attrs_str)
    
    def parse_attributes(self, attrs_str: str) -> Dict[str, Any]:
        """
        Parse attribute string into dictionary.
        
        Args:
            attrs_str: Space-separated attributes
            
        Returns:
            Dictionary of parsed attributes
            
        Supports:
            - Boolean flags: "CDC_EN" -> {'cdc_enabled': True}
            - Key-value pairs: "ADDR=0x10" -> {'address': '0x10'}
            - Quoted strings: DESC="My description" -> {'description': 'My description'}
            - Access modes: "RW", "RO", "WO"
            - Strobes: "R_STROBE", "W_STROBE"
        """
        attrs = {}
        
        # First, extract quoted strings (DESC="..." or similar)
        # This handles spaces within quoted values
        quoted_pattern = re.compile(r'(\w+)=["\']([^"\']*)["\']')
        for match in quoted_pattern.finditer(attrs_str):
            key = match.group(1)
            value = match.group(2)
            attrs[self._normalize_key(key)] = value
        
        # Remove quoted strings from attrs_str for further processing
        remaining = quoted_pattern.sub('', attrs_str)
        
        # Now process remaining tokens (non-quoted)
        tokens = remaining.split()
        
        for token in tokens:
            if '=' in token:
                # Key-value pair (non-quoted)
                key, value = token.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Skip if already processed as quoted string
                if self._normalize_key(key) in attrs:
                    continue
                
                # Convert to appropriate type
                attrs[self._normalize_key(key)] = self._convert_value(value)
            else:
                # Boolean flag or mode
                token = token.strip()
                if not token:
                    continue
                
                # Check for access modes
                if token in ['RO', 'RW', 'WO']:
                    attrs['access_mode'] = token
                # Check for strobe flags
                elif token == 'R_STROBE':
                    attrs['read_strobe'] = True
                elif token == 'W_STROBE':
                    attrs['write_strobe'] = True
                # Check for CDC enable
                elif token == 'CDC_EN':
                    attrs['cdc_enabled'] = True
                # Generic boolean flag
                else:
                    attrs[self._normalize_key(token)] = True
        
        return attrs
    
    def _normalize_key(self, key: str) -> str:
        """
        Normalize attribute key to Python naming convention.
        
        Args:
            key: Attribute key (e.g., "CDC_STAGE")
            
        Returns:
            Normalized key (e.g., "cdc_stages")
        """
        key = key.lower()
        
        # Handle common transformations
        replacements = {
            'addr': 'address',
            'base_addr': 'base_address',
            'cdc_stage': 'cdc_stages',
            'r_strobe': 'read_strobe',
            'w_strobe': 'write_strobe',
            'desc': 'description',
            'reg_name': 'reg_name',
            'bit_offset': 'bit_offset',
            'default': 'default_value',
            'cdc_en': 'cdc_enabled'
        }
        
        return replacements.get(key, key)
    
    def _convert_value(self, value: str) -> Any:
        """
        Convert string value to appropriate Python type.
        Supports hex (0x prefix) and decimal formats.
        
        Args:
            value: String value
            
        Returns:
            Converted value (int, bool, str)
        """
        value = value.strip()
        
        # Try hexadecimal integer (with 0x or 0X prefix)
        if value.startswith('0x') or value.startswith('0X'):
            try:
                return int(value, 16)
            except ValueError:
                pass
        
        # Try decimal integer (including negative)
        try:
            return int(value, 10)
        except ValueError:
            pass
        
        # Try boolean
        if value.lower() in ['true', 'yes', '1']:
            return True
        if value.lower() in ['false', 'no', '0']:
            return False
        
        # Return as string
        return value
    
    def validate_access_mode(self, mode: str) -> bool:
        """
        Validate access mode value.
        
        Args:
            mode: Access mode string
            
        Returns:
            True if valid, False otherwise
        """
        return mode in ['RO', 'WO', 'RW']
    
    def get_required_attributes(self, annotation_type: str = 'register') -> List[str]:
        """
        Get list of required attributes for annotation type.
        
        Args:
            annotation_type: Type of annotation ('register', 'module', etc.)
            
        Returns:
            List of required attribute names
        """
        required = {
            'register': ['access_mode'],
            'module': [],
            'field': ['access_mode', 'bit_range']
        }
        return required.get(annotation_type, [])
    
    def validate_annotation(
        self, 
        attrs: Dict[str, Any], 
        annotation_type: str = 'register'
    ) -> Tuple[bool, List[str]]:
        """
        Validate parsed annotation attributes.
        
        Args:
            attrs: Parsed attributes dictionary
            annotation_type: Type of annotation to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        required = self.get_required_attributes(annotation_type)
        
        # Check required attributes
        for req_attr in required:
            if req_attr not in attrs:
                errors.append(f"Missing required attribute: {req_attr}")
        
        # Validate access mode if present
        if 'access_mode' in attrs:
            if not self.validate_access_mode(attrs['access_mode']):
                errors.append(f"Invalid access mode: {attrs['access_mode']}")
        
        # Validate address if present
        if 'address' in attrs:
            addr = attrs['address']
            if isinstance(addr, str):
                try:
                    if addr.startswith('0x'):
                        int(addr, 16)
                    else:
                        int(addr)
                except ValueError:
                    errors.append(f"Invalid address format: {addr}")
        
        return (len(errors) == 0, errors)
    
    def extract_all_annotations(
        self, 
        content: str, 
        annotation_type: Optional[str] = None
    ) -> List[Tuple[int, Dict[str, Any]]]:
        """
        Extract all annotations from source content.
        
        Args:
            content: Source file content
            annotation_type: Filter by annotation type (optional)
            
        Returns:
            List of (line_number, attributes) tuples
        """
        annotations = []
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            parsed = self.parse_annotation(line)
            if parsed:
                annotations.append((line_num, parsed))
        
        return annotations
    
    def set_annotation_prefix(self, prefix: str):
        """
        Change the annotation prefix.
        
        Args:
            prefix: New annotation prefix
        """
        self.annotation_prefix = prefix
        # Recompile patterns
        self.annotation_pattern = re.compile(
            rf'--\s*{re.escape(prefix)}\s+(.+)',
            re.IGNORECASE
        )
        self.def_pattern = re.compile(
            rf'--\s*{re.escape(prefix)}_def\s+(.+)',
            re.IGNORECASE
        )
