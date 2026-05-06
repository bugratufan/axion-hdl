"""
Hierarchy Parser for Axion HDL

Parses hierarchy/address-map files that centralize base address assignment
for multiple module instances. Supports YAML, JSON, TOML, and XML formats.
All formats are normalized to a common Python dict structure before processing,
following the same pattern as the existing input parsers.

Hierarchy file format (YAML example):

    instances:
      - module: spi_master
        instance: spi_master_0
        base_addr: 0x20000
      - module: spi_master
        instance: spi_master_1
        base_addr: 0x21000
      - module: uart_ctrl
        base_addr: 0x30000

Rules:
- If a module name appears more than once, 'instance' is required for every entry.
- 'instance' is optional when a module appears exactly once.
- base_addr may be an integer or a hex string ("0x10000").
"""

import os
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional

_USE_TOML_PACKAGE = False

try:
    import tomllib
except ImportError:
    try:
        import toml as tomllib
        _USE_TOML_PACKAGE = True
    except ImportError:
        tomllib = None


class HierarchyParser:
    """
    Parser for hierarchy/address-map files.

    Converts YAML, JSON, TOML, and XML formats to a normalized list of instance
    dicts before validating them. All format-specific loaders produce the same
    Python dict structure: {'instances': [{'module': str, 'instance': str|None,
    'base_addr': int}, ...]}.
    """

    def parse(self, file_path: str) -> List[Dict]:
        """
        Parse a hierarchy file and return a list of instance dicts.

        Args:
            file_path: Path to the hierarchy file (.yaml, .yml, .json, .toml, .xml).

        Returns:
            List of dicts: [{'module': str, 'instance': str|None, 'base_addr': int}, ...]

        Raises:
            ValueError: If the format is unsupported, a required field is missing,
                        or 'instance' is absent when the same module appears more than once.
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Hierarchy file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext in ('.yaml', '.yml'):
            data = self._load_yaml(file_path)
        elif ext == '.json':
            data = self._load_json(file_path)
        elif ext == '.toml':
            data = self._load_toml(file_path)
        elif ext == '.xml':
            data = self._load_xml(file_path)
        else:
            raise ValueError(
                f"Unsupported hierarchy file format: '{ext}'. "
                "Supported formats: .yaml, .yml, .json, .toml, .xml"
            )

        return self._parse_dict(data, file_path)

    # ------------------------------------------------------------------
    # Format loaders — each returns {'instances': [...]} as Python dict
    # ------------------------------------------------------------------

    def _load_yaml(self, path: str) -> dict:
        try:
            import yaml
        except ImportError:
            raise ImportError(
                "PyYAML is required for YAML hierarchy files. Install with: pip install PyYAML"
            )
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Hierarchy YAML must be a mapping, got {type(data).__name__}")
        return data

    def _load_json(self, path: str) -> dict:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Hierarchy JSON must be an object, got {type(data).__name__}")
        return data

    def _load_toml(self, path: str) -> dict:
        if tomllib is None:
            raise ImportError(
                "TOML support requires Python 3.11+ (tomllib) or the 'toml' package. "
                "Install with: pip install toml"
            )
        if _USE_TOML_PACKAGE:
            with open(path, 'r', encoding='utf-8') as f:
                data = tomllib.load(f)
        else:
            with open(path, 'rb') as f:
                data = tomllib.load(f)
        if not isinstance(data, dict):
            raise ValueError(f"Hierarchy TOML must be a table, got {type(data).__name__}")
        return data

    def _load_xml(self, path: str) -> dict:
        """Parse XML hierarchy file into the standard dict structure.

        Expected XML format:
            <hierarchy>
              <instance module="spi_master" name="spi_master_0" base_addr="0x20000"/>
              <instance module="uart_ctrl" base_addr="0x30000"/>
            </hierarchy>
        """
        tree = ET.parse(path)
        root = tree.getroot()

        instances = []
        for elem in root.findall('instance'):
            entry = {
                'module': elem.get('module'),
                'instance': elem.get('name') or elem.get('instance'),
                'base_addr': elem.get('base_addr'),
            }
            instances.append(entry)

        return {'instances': instances}

    # ------------------------------------------------------------------
    # Common processor
    # ------------------------------------------------------------------

    def _parse_dict(self, data: dict, source: str = '') -> List[Dict]:
        """
        Validate and normalize the common dict structure.

        Args:
            data: {'instances': [...]} dict produced by a format loader.
            source: Source file path (used in error messages).

        Returns:
            List of normalized instance dicts.

        Raises:
            ValueError: On missing required fields or validation failures.
        """
        if 'instances' not in data:
            raise ValueError(
                f"Hierarchy file {source!r} must contain an 'instances' key at the top level."
            )

        raw_instances = data['instances']
        if not isinstance(raw_instances, list):
            raise ValueError(
                f"'instances' in hierarchy file {source!r} must be a list."
            )

        # First pass: normalize each entry
        normalized: List[Dict] = []
        for i, entry in enumerate(raw_instances):
            if not isinstance(entry, dict):
                raise ValueError(
                    f"Entry #{i} in hierarchy file {source!r} must be a mapping."
                )

            module = entry.get('module')
            if not module:
                raise ValueError(
                    f"Entry #{i} in hierarchy file {source!r} is missing the 'module' field."
                )

            raw_addr = entry.get('base_addr')
            if raw_addr is None:
                raise ValueError(
                    f"Entry #{i} (module='{module}') in hierarchy file {source!r} "
                    "is missing the 'base_addr' field."
                )

            base_addr = self._parse_addr(raw_addr, module, source)
            instance_name: Optional[str] = entry.get('instance') or None

            normalized.append({
                'module': str(module),
                'instance': instance_name,
                'base_addr': base_addr,
            })

        # Second pass: validate instance requirements
        from collections import Counter, defaultdict
        module_counts = Counter(e['module'] for e in normalized)
        no_instance_counts: dict = defaultdict(int)
        for e in normalized:
            if e['instance'] is None:
                no_instance_counts[e['module']] += 1

        for mod, count in module_counts.items():
            if count > 1 and no_instance_counts[mod] > 1:
                raise ValueError(
                    f"Module '{mod}' appears {count} times in hierarchy file "
                    f"{source!r} but {no_instance_counts[mod]} entries are missing the "
                    "'instance' field. At most one canonical entry (without instance name) "
                    "is allowed per module when it appears more than once."
                )

        return normalized

    @staticmethod
    def _parse_addr(raw: object, module: str, source: str) -> int:
        """Normalize base_addr to int, accepting int or hex/decimal string."""
        if isinstance(raw, int):
            return raw
        if isinstance(raw, str):
            raw_stripped = raw.strip()
            try:
                return int(raw_stripped, 0)
            except ValueError:
                pass
        raise ValueError(
            f"Invalid base_addr value {raw!r} for module '{module}' in hierarchy "
            f"file {source!r}. Expected an integer or a hex string (e.g. '0x10000')."
        )
