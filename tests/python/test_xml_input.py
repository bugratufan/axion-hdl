import unittest
import os
import shutil
import tempfile
import sys

# Ensure axion_hdl is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from axion_hdl import AxionHDL
from axion_hdl.xml_parser import XMLParser, XMLParseError, XMLValidationError
from axion_hdl.address_manager import AddressConflictError

class TestXMLInput(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(self.output_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_custom_xml_parsing(self):
        """Test parsing of custom Axion XML format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="sensor_controller" base_address="0x1000">
    <config>
        <cdc enabled="true" stages="3"/>
    </config>

    <registers>
        <register name="status_reg" address="0x00" access="RO" width="32"
                  description="System status flags"/>
        <register name="control_reg" address="0x04" access="WO" width="32"
                  write_strobe="true" description="Main control register"/>
        <register name="config_reg" address="0x08" access="RW" width="32"
                  read_strobe="true" write_strobe="true" description="Configuration settings"/>
    </registers>
</axion_registers>
"""
        xml_file = os.path.join(self.temp_dir, "custom_regs.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        result = parser.parse_xml_file(xml_file)

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'sensor_controller')
        self.assertEqual(result['base_address'], 0x1000)
        self.assertTrue(result['cdc_enabled'])
        self.assertEqual(result['cdc_stages'], 3)
        self.assertEqual(len(result['registers']), 3)

        # Check registers
        status_reg = next(r for r in result['registers'] if r['signal_name'] == 'status_reg')
        self.assertEqual(status_reg['access_mode'], 'RO')

        control_reg = next(r for r in result['registers'] if r['signal_name'] == 'control_reg')
        self.assertTrue(control_reg['write_strobe'])

    def test_ipxact_xml_parsing(self):
        """Test parsing of basic IP-XACT format."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<spirit:component xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009">
    <spirit:name>spi_controller</spirit:name>
    <spirit:memoryMaps>
        <spirit:memoryMap>
            <spirit:addressBlock>
                <spirit:baseAddress>0x2000</spirit:baseAddress>
                <spirit:register>
                    <spirit:name>data_reg</spirit:name>
                    <spirit:description>Data register</spirit:description>
                    <spirit:addressOffset>0x0</spirit:addressOffset>
                    <spirit:size>32</spirit:size>
                    <spirit:access>read-write</spirit:access>
                </spirit:register>
                <spirit:register>
                    <spirit:name>status_reg</spirit:name>
                    <spirit:addressOffset>0x4</spirit:addressOffset>
                    <spirit:size>32</spirit:size>
                    <spirit:access>read-only</spirit:access>
                </spirit:register>
            </spirit:addressBlock>
        </spirit:memoryMap>
    </spirit:memoryMaps>
</spirit:component>
"""
        xml_file = os.path.join(self.temp_dir, "ipxact_regs.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        result = parser.parse_xml_file(xml_file)

        self.assertIsNotNone(result)
        self.assertEqual(result['name'], 'spi_controller')
        self.assertEqual(result['base_address'], 0x2000)
        self.assertEqual(len(result['registers']), 2)

        data_reg = next(r for r in result['registers'] if r['signal_name'] == 'data_reg')
        self.assertEqual(data_reg['access_mode'], 'RW')

        status_reg = next(r for r in result['registers'] if r['signal_name'] == 'status_reg')
        self.assertEqual(status_reg['access_mode'], 'RO')

    def test_axion_integration(self):
        """Test full integration with AxionHDL class."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="integration_test" base_address="0x0000">
    <registers>
        <register name="test_reg" access="RW"/>
    </registers>
</axion_registers>
"""
        xml_file = os.path.join(self.temp_dir, "integration.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        axion = AxionHDL(output_dir=self.output_dir)
        axion.add_xml(xml_file)

        self.assertTrue(axion.analyze())
        modules = axion.get_modules()
        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0]['name'], 'integration_test')

        # Test generation
        self.assertTrue(axion.generate_all())

        # Check generated files
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "integration_test_axion_reg.vhd")))
        self.assertTrue(os.path.exists(os.path.join(self.output_dir, "integration_test_regs.h")))

    def test_stress_xml_input(self):
        """Test with a large number of registers defined in XML."""
        header = """<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="stress_test" base_address="0x0000">
    <registers>
"""
        footer = """    </registers>
</axion_registers>
"""
        body = ""
        for i in range(200):
            body += f'        <register name="reg_{i}" width="32" access="RW" description="Register {i}"/>\n'

        xml_content = header + body + footer
        xml_file = os.path.join(self.temp_dir, "stress.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        result = parser.parse_xml_file(xml_file)

        self.assertEqual(len(result['registers']), 200)
        self.assertEqual(result['registers'][199]['signal_name'], 'reg_199')

    def test_malformed_xml(self):
        """Test with invalid XML syntax."""
        xml_content = "<axion_registers><unclosed_tag></axion_registers>"
        xml_file = os.path.join(self.temp_dir, "malformed.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        with self.assertRaises(XMLParseError):
            parser.parse_xml_file(xml_file)

    def test_invalid_schema_missing_name(self):
        """Test with missing required attribute 'name'."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="bad_schema">
    <registers>
        <register access="RW" width="32"/>
    </registers>
</axion_registers>
"""
        xml_file = os.path.join(self.temp_dir, "missing_name.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        with self.assertRaises(XMLValidationError):
            parser.parse_xml_file(xml_file)

    def test_invalid_access_mode(self):
        """Test with invalid access mode."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="bad_access">
    <registers>
        <register name="bad_reg" access="XYZ" width="32"/>
    </registers>
</axion_registers>
"""
        xml_file = os.path.join(self.temp_dir, "bad_access.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        with self.assertRaises(XMLValidationError):
            parser.parse_xml_file(xml_file)

    def test_invalid_integer_value(self):
        """Test with invalid integer for width/address."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="bad_int">
    <registers>
        <register name="bad_width" access="RW" width="not_an_int"/>
    </registers>
</axion_registers>
"""
        xml_file = os.path.join(self.temp_dir, "bad_int.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        with self.assertRaises(XMLValidationError):
            parser.parse_xml_file(xml_file)

    def test_address_conflict_in_xml(self):
        """Test that address conflict detection works for XML input."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="conflict_test">
    <registers>
        <register name="reg_a" address="0x00" access="RW"/>
        <register name="reg_b" address="0x00" access="RW"/>
    </registers>
</axion_registers>
"""
        xml_file = os.path.join(self.temp_dir, "conflict.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        # AddressManager raises AddressConflictError
        with self.assertRaises(AddressConflictError):
            parser.parse_xml_file(xml_file)

    def test_unknown_xml_format(self):
        """Test with unknown XML root tag."""
        xml_content = "<unknown_root></unknown_root>"
        xml_file = os.path.join(self.temp_dir, "unknown.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)

        parser = XMLParser()
        with self.assertRaises(XMLValidationError):
            parser.parse_xml_file(xml_file)

if __name__ == "__main__":
    unittest.main()
