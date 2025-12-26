#!/usr/bin/env python3
"""
test_cli.py - Command Line Interface Requirements Tests

Tests for CLI-001 through CLI-010 requirements
Verifies CLI options and behavior.
"""

import os
import sys
import tempfile
import unittest
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestCLIRequirements(unittest.TestCase):
    """Test cases for CLI-xxx requirements"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures"""
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create test VHDL file
        cls.vhdl_content = '''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x0000
entity cli_test is
    port (clk : in std_logic);
end entity;
architecture rtl of cli_test is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin
end architecture;
'''
        cls.vhdl_file = os.path.join(cls.temp_dir, "cli_test.vhd")
        with open(cls.vhdl_file, 'w') as f:
            f.write(cls.vhdl_content)
        
        # CLI command
        cls.cli_cmd = [sys.executable, '-m', 'axion_hdl.cli']
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temp files"""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)
    
    def _run_cli(self, args):
        """Run CLI with arguments and return result"""
        cmd = self.cli_cmd + args
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(project_root))
        return result
    
    # =========================================================================
    # CLI-001: Help Option Display
    # =========================================================================
    def test_cli_001_help_option(self):
        """CLI-001: --help displays usage information"""
        result = self._run_cli(['--help'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    def test_cli_001_help_short_option(self):
        """CLI-001: -h displays usage information"""
        result = self._run_cli(['-h'])
        self.assertEqual(result.returncode, 0)
        self.assertIn('usage', result.stdout.lower())
    
    # =========================================================================
    # CLI-002: Version Option Display
    # =========================================================================
    def test_cli_002_version_option(self):
        """CLI-002: --version displays version"""
        result = self._run_cli(['--version'])
        # Should exit 0 and print version
        self.assertEqual(result.returncode, 0)
        # Version should be in output (stdout or stderr depending on argparse)
        output = result.stdout + result.stderr
        # Should contain a version number pattern (X.Y.Z or similar)
        self.assertTrue(any(c.isdigit() for c in output))
    
    # =========================================================================
    # CLI-003: Source Directory Option
    # =========================================================================
    def test_cli_003_source_option_long(self):
        """CLI-003: --source option specifies source directory"""
        output_dir = os.path.join(self.temp_dir, "output1")
        result = self._run_cli([
            '--source', self.temp_dir,
            '--output', output_dir
        ])
        # Should process without error
        self.assertEqual(result.returncode, 0)
    
    def test_cli_003_source_option_short(self):
        """CLI-003: -s option specifies source directory"""
        output_dir = os.path.join(self.temp_dir, "output2")
        result = self._run_cli([
            '-s', self.temp_dir,
            '-o', output_dir
        ])
        self.assertEqual(result.returncode, 0)
    
    def test_cli_003_source_file_vhdl(self):
        """CLI-003: -s accepts single VHDL file"""
        output_dir = os.path.join(self.temp_dir, "output_file")
        result = self._run_cli([
            '-s', self.vhdl_file,
            '-o', output_dir
        ])
        self.assertEqual(result.returncode, 0)
        # Verify output was generated
        self.assertTrue(os.path.exists(output_dir))
    
    def test_cli_003_source_file_xml(self):
        """CLI-003: -s accepts single XML file"""
        # Create test XML file with correct attribute names
        xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
<register_map module="xml_cli_test" base_addr="0x0000">
  <register name="status" addr="0x00" access="RO" width="32" />
</register_map>
'''
        xml_file = os.path.join(self.temp_dir, "test_cli.xml")
        with open(xml_file, 'w') as f:
            f.write(xml_content)
        
        output_dir = os.path.join(self.temp_dir, "output_xml_file")
        result = self._run_cli([
            '-s', xml_file,
            '-o', output_dir
        ])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_dir))
    
    # =========================================================================
    # CLI-004: Multiple Source Path Support
    # =========================================================================
    def test_cli_004_multiple_sources(self):
        """CLI-004: Multiple -s options accepted"""
        # Create second temp directory with VHDL
        temp_dir2 = tempfile.mkdtemp()
        vhdl2 = os.path.join(temp_dir2, "module2.vhd")
        with open(vhdl2, 'w') as f:
            f.write('''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x1000
entity module2 is port (clk : in std_logic); end entity;
architecture rtl of module2 is
    signal reg : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin end architecture;
''')
        
        output_dir = os.path.join(self.temp_dir, "output_multi")
        result = self._run_cli([
            '-s', self.temp_dir,
            '-s', temp_dir2,
            '-o', output_dir
        ])
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir2, ignore_errors=True)
        
        self.assertEqual(result.returncode, 0)
    
    def test_cli_004_mixed_files_and_dirs(self):
        """CLI-004: -s accepts mix of files and directories"""
        # Create a separate VHDL file
        vhdl_file2 = os.path.join(self.temp_dir, "standalone.vhd")
        with open(vhdl_file2, 'w') as f:
            f.write('''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x2000
entity standalone is port (clk : in std_logic); end entity;
architecture rtl of standalone is
    signal data : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin end architecture;
''')
        
        # Create a temp directory with another VHDL file
        temp_dir2 = tempfile.mkdtemp()
        vhdl3 = os.path.join(temp_dir2, "module3.vhd")
        with open(vhdl3, 'w') as f:
            f.write('''
library ieee;
use ieee.std_logic_1164.all;
-- @axion_def BASE_ADDR=0x3000
entity module3 is port (clk : in std_logic); end entity;
architecture rtl of module3 is
    signal ctrl : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
begin end architecture;
''')
        
        output_dir = os.path.join(self.temp_dir, "output_mixed")
        result = self._run_cli([
            '-s', vhdl_file2,  # Single file
            '-s', temp_dir2,  # Directory
            '-o', output_dir
        ])
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir2, ignore_errors=True)
        
        self.assertEqual(result.returncode, 0)
    
    # =========================================================================
    # CLI-005: Output Directory Option
    # =========================================================================
    def test_cli_005_output_option_long(self):
        """CLI-005: --output option specifies output directory"""
        output_dir = os.path.join(self.temp_dir, "custom_output")
        result = self._run_cli([
            '-s', self.temp_dir,
            '--output', output_dir
        ])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_dir))
    
    def test_cli_005_output_option_short(self):
        """CLI-005: -o option specifies output directory"""
        output_dir = os.path.join(self.temp_dir, "custom_output2")
        result = self._run_cli([
            '-s', self.temp_dir,
            '-o', output_dir
        ])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_dir))
    
    # =========================================================================
    # CLI-006: Exclude Pattern Option
    # =========================================================================
    def test_cli_006_exclude_option(self):
        """CLI-006: -e option excludes files/directories"""
        # Create directory to exclude
        exclude_dir = os.path.join(self.temp_dir, "error_cases")
        os.makedirs(exclude_dir, exist_ok=True)
        exclude_vhdl = os.path.join(exclude_dir, "bad.vhd")
        with open(exclude_vhdl, 'w') as f:
            f.write('-- bad file\n')
        
        output_dir = os.path.join(self.temp_dir, "output_exclude")
        result = self._run_cli([
            '-s', self.temp_dir,
            '-o', output_dir,
            '-e', 'error_cases'
        ])
        self.assertEqual(result.returncode, 0)
    
    # =========================================================================
    # CLI-009: Invalid Source Directory Error
    # =========================================================================
    def test_cli_009_invalid_source_error(self):
        """CLI-009: Non-existent source reports error"""
        result = self._run_cli([
            '-s', '/nonexistent/path/that/does/not/exist',
            '-o', self.temp_dir
        ])
        # Should return non-zero exit code
        self.assertNotEqual(result.returncode, 0)
    
    # =========================================================================
    # CLI-010: Output Directory Creation
    # =========================================================================
    def test_cli_010_output_dir_creation(self):
        """CLI-010: Non-existent output directory is created"""
        output_dir = os.path.join(self.temp_dir, "nested", "deep", "output")
        # Ensure it doesn't exist
        if os.path.exists(output_dir):
            import shutil
            shutil.rmtree(output_dir)
        
        result = self._run_cli([
            '-s', self.temp_dir,
            '-o', output_dir
        ])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_dir))

    # =========================================================================
    # CLI-011: YAML Output Flag
    # =========================================================================
    def test_cli_011_yaml_output_flag(self):
        """CLI-011: --yaml flag generates YAML register map"""
        output_dir = os.path.join(self.temp_dir, "output_yaml_flag")
        result = self._run_cli([
            '-s', self.temp_dir,
            '-o', output_dir,
            '--yaml'
        ])
        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        
        # Check YAML file was generated
        yaml_files = list(Path(output_dir).glob('*_regs.yaml'))
        self.assertGreater(len(yaml_files), 0, 
            "YAML register map should be generated with --yaml flag")

    # =========================================================================
    # CLI-012: JSON Output Flag
    # =========================================================================
    def test_cli_012_json_output_flag(self):
        """CLI-012: --json flag generates JSON register map"""
        output_dir = os.path.join(self.temp_dir, "output_json_flag")
        result = self._run_cli([
            '-s', self.temp_dir,
            '-o', output_dir,
            '--json'
        ])
        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        
        # Check JSON file was generated
        json_files = list(Path(output_dir).glob('*_regs.json'))
        self.assertGreater(len(json_files), 0, 
            "JSON register map should be generated with --json flag")

    # =========================================================================
    # CLI-013: Configuration File Support
    # =========================================================================
    def test_cli_013_config_file_support(self):
        """CLI-013: --config loads settings from JSON file"""
        import json
        output_dir = os.path.join(self.temp_dir, "config_output")
        config = {
            "src_dirs": [self.temp_dir],
            "output_dir": output_dir,
            "exclude_patterns": ["*.txt"]
        }
        config_path = os.path.join(self.temp_dir, "test_config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f)
            
        # Run without -s or -o, should pick up from config
        result = self._run_cli(['--config', config_path])
        self.assertEqual(result.returncode, 0)
        self.assertTrue(os.path.exists(output_dir))



    def test_cli_015_auto_load_config(self):
        """CLI-015: Auto-load .axion_conf if no --config specified"""
        import json
        import shutil
        import subprocess
        import sys
        
        # Create a subdirectory to act as project root
        project_dir = os.path.join(self.temp_dir, "project_root_auto")
        if os.path.exists(project_dir):
            shutil.rmtree(project_dir)
        os.makedirs(project_dir)
        
        # Create a dummy source file
        src_file = os.path.join(project_dir, "my_reg.json")
        with open(src_file, "w") as f:
            f.write('{ "module": "my_reg", "base_addr": "0x00", "registers": [] }')
            
        # Create .axion_conf in project root
        output_dir = "default_output"
        config = {
            "src_files": ["my_reg.json"],
            "output_dir": output_dir
        }
        with open(os.path.join(project_dir, ".axion_conf"), "w") as f:
            json.dump(config, f)
            
        # Run CLI in that directory WITHOUT --config
        import sys
        import subprocess
        
        # Need to ensure python can find axion_hdl package
        # The project root is available in global 'project_root'
        env = os.environ.copy()
        env["PYTHONPATH"] = str(project_root)
        
        cmd = [sys.executable, "-m", "axion_hdl.cli"]
        result = subprocess.run(
            cmd,
            cwd=project_dir,
            capture_output=True,
            text=True,
            env=env
        )
        
        self.assertEqual(result.returncode, 0, f"CLI failed: {result.stderr}")
        self.assertTrue(os.path.exists(os.path.join(project_dir, output_dir)), "Output directory was not created from default config")


def run_cli_tests():
    """Run all CLI tests and return results"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestCLIRequirements)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_cli_tests()
    sys.exit(0 if success else 1)
