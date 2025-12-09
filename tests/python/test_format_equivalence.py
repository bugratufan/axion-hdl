#!/usr/bin/env python3
"""
test_format_equivalence.py - Cross-Format Equivalence Tests

Tests for EQUIV-001 through EQUIV-006 requirements.
Verifies that XML, YAML, and JSON inputs produce equivalent outputs.
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from axion_hdl.xml_input_parser import XMLInputParser
from axion_hdl.yaml_input_parser import YAMLInputParser
from axion_hdl.json_input_parser import JSONInputParser
from axion_hdl import AxionHDL


class TestFormatEquivalence(unittest.TestCase):
    """Test cases for cross-format equivalence (EQUIV-xxx requirements)"""
    
    @classmethod
    def setUpClass(cls):
        """Load test files from all formats"""
        cls.project_root = Path(__file__).parent.parent.parent
        cls.xml_file = cls.project_root / "tests" / "xml" / "sensor_controller.xml"
        cls.yaml_file = cls.project_root / "tests" / "yaml" / "sensor_controller.yaml"
        cls.json_file = cls.project_root / "tests" / "json" / "sensor_controller.json"
        cls.temp_dir = tempfile.mkdtemp()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up temp files"""
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def _compare_modules(self, mod1, mod2, desc=""):
        """Compare two module dictionaries for equivalence"""
        # Compare basic properties
        self.assertEqual(mod1['name'], mod2['name'], f"Module names differ {desc}")
        self.assertEqual(mod1['base_address'], mod2['base_address'], f"Base addresses differ {desc}")
        self.assertEqual(mod1['cdc_enabled'], mod2['cdc_enabled'], f"CDC enabled differs {desc}")
        self.assertEqual(mod1['cdc_stages'], mod2['cdc_stages'], f"CDC stages differ {desc}")
        
        # Compare register count
        self.assertEqual(len(mod1['registers']), len(mod2['registers']), 
                        f"Register counts differ {desc}")
        
        # Compare each register
        for i, (r1, r2) in enumerate(zip(mod1['registers'], mod2['registers'])):
            self.assertEqual(r1['signal_name'], r2['signal_name'], 
                           f"Register {i} name differs {desc}")
            self.assertEqual(r1['access_mode'], r2['access_mode'],
                           f"Register {i} access differs {desc}")
            self.assertEqual(r1['relative_address_int'], r2['relative_address_int'],
                           f"Register {i} address differs {desc}")
            self.assertEqual(r1.get('r_strobe', False), r2.get('r_strobe', False),
                           f"Register {i} r_strobe differs {desc}")
            self.assertEqual(r1.get('w_strobe', False), r2.get('w_strobe', False),
                           f"Register {i} w_strobe differs {desc}")
    
    # EQUIV-001: XML→YAML equivalence
    def test_equiv_001_xml_yaml_equivalence(self):
        """EQUIV-001: XML and YAML with same content produce identical modules"""
        xml_parser = XMLInputParser()
        yaml_parser = YAMLInputParser()
        
        xml_module = xml_parser.parse_file(str(self.xml_file))
        yaml_module = yaml_parser.parse_file(str(self.yaml_file))
        
        self.assertIsNotNone(xml_module)
        self.assertIsNotNone(yaml_module)
        self._compare_modules(xml_module, yaml_module, "(XML vs YAML)")
    
    # EQUIV-002: XML→JSON equivalence
    def test_equiv_002_xml_json_equivalence(self):
        """EQUIV-002: XML and JSON with same content produce identical modules"""
        xml_parser = XMLInputParser()
        json_parser = JSONInputParser()
        
        xml_module = xml_parser.parse_file(str(self.xml_file))
        json_module = json_parser.parse_file(str(self.json_file))
        
        self.assertIsNotNone(xml_module)
        self.assertIsNotNone(json_module)
        self._compare_modules(xml_module, json_module, "(XML vs JSON)")
    
    # EQUIV-003: YAML→JSON equivalence
    def test_equiv_003_yaml_json_equivalence(self):
        """EQUIV-003: YAML and JSON with same content produce identical modules"""
        yaml_parser = YAMLInputParser()
        json_parser = JSONInputParser()
        
        yaml_module = yaml_parser.parse_file(str(self.yaml_file))
        json_module = json_parser.parse_file(str(self.json_file))
        
        self.assertIsNotNone(yaml_module)
        self.assertIsNotNone(json_module)
        self._compare_modules(yaml_module, json_module, "(YAML vs JSON)")
    
    # EQUIV-004: YAML roundtrip
    def test_equiv_004_yaml_roundtrip(self):
        """EQUIV-004: Parse YAML → generate YAML → parse again produces identical modules"""
        from axion_hdl.doc_generators import YAMLGenerator
        
        yaml_parser = YAMLInputParser()
        original = yaml_parser.parse_file(str(self.yaml_file))
        self.assertIsNotNone(original)
        
        # Generate YAML output
        yaml_gen = YAMLGenerator(self.temp_dir)
        output_path = yaml_gen.generate_yaml(original)
        
        # Parse the generated YAML
        roundtrip = yaml_parser.parse_file(output_path)
        self.assertIsNotNone(roundtrip)
        
        self._compare_modules(original, roundtrip, "(YAML roundtrip)")
    
    # EQUIV-005: JSON roundtrip
    def test_equiv_005_json_roundtrip(self):
        """EQUIV-005: Parse JSON → generate JSON → parse again produces identical modules"""
        from axion_hdl.doc_generators import JSONGenerator
        
        json_parser = JSONInputParser()
        original = json_parser.parse_file(str(self.json_file))
        self.assertIsNotNone(original)
        
        # Generate JSON output
        json_gen = JSONGenerator(self.temp_dir)
        output_path = json_gen.generate_json(original)
        
        # Parse the generated JSON
        roundtrip = json_parser.parse_file(output_path)
        self.assertIsNotNone(roundtrip)
        
        self._compare_modules(original, roundtrip, "(JSON roundtrip)")
    
    # EQUIV-006: Cross-format VHDL output
    def test_equiv_006_cross_format_vhdl_output(self):
        """EQUIV-006: XML/YAML/JSON inputs produce identical VHDL outputs"""
        import re
        from axion_hdl.generator import VHDLGenerator
        
        xml_parser = XMLInputParser()
        yaml_parser = YAMLInputParser()
        json_parser = JSONInputParser()
        
        xml_module = xml_parser.parse_file(str(self.xml_file))
        yaml_module = yaml_parser.parse_file(str(self.yaml_file))
        json_module = json_parser.parse_file(str(self.json_file))
        
        # Generate VHDL for each
        xml_dir = os.path.join(self.temp_dir, "xml_out")
        yaml_dir = os.path.join(self.temp_dir, "yaml_out")
        json_dir = os.path.join(self.temp_dir, "json_out")
        os.makedirs(xml_dir, exist_ok=True)
        os.makedirs(yaml_dir, exist_ok=True)
        os.makedirs(json_dir, exist_ok=True)
        
        xml_gen = VHDLGenerator(xml_dir)
        yaml_gen = VHDLGenerator(yaml_dir)
        json_gen = VHDLGenerator(json_dir)
        
        xml_vhdl = xml_gen.generate_module(xml_module)
        yaml_vhdl = yaml_gen.generate_module(yaml_module)
        json_vhdl = json_gen.generate_module(json_module)
        
        # Compare VHDL outputs (filter out source file path comments which differ)
        def normalize_vhdl(content):
            # Remove source file path comment lines  
            content = re.sub(r'--\s*Source:.*\n', '', content)
            content = re.sub(r'sensor_controller\.(xml|yaml|json)', 'sensor_controller.src', content)
            return content
        
        with open(xml_vhdl, 'r') as f:
            xml_content = normalize_vhdl(f.read())
        with open(yaml_vhdl, 'r') as f:
            yaml_content = normalize_vhdl(f.read())
        with open(json_vhdl, 'r') as f:
            json_content = normalize_vhdl(f.read())
        
        self.assertEqual(xml_content, yaml_content, "XML and YAML VHDL outputs differ")
        self.assertEqual(xml_content, json_content, "XML and JSON VHDL outputs differ")


def run_equivalence_tests():
    """Run all equivalence tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestFormatEquivalence)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_equivalence_tests()
    sys.exit(0 if success else 1)
