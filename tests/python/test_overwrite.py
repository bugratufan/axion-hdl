import unittest
import os
import tempfile
import shutil
from pathlib import Path
from axion_hdl.generator import VHDLGenerator

class TestGenerationOverwrite(unittest.TestCase):
    """Test verification for AXION-027: Existing File Overwrite."""
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.test_dir.name) / "output"
        if not self.output_dir.exists():
            self.output_dir.mkdir()
    
    def tearDown(self):
        self.test_dir.cleanup()
    
    def test_overwrite_existing_file(self):
        """
        Verify that generation overwrites an existing file with the same name.
        Target: AXION-027
        """
        module_name = "test_module"
        filename = f"{module_name}_axion_reg.vhd"
        file_path = self.output_dir / filename
        
        # 1. Create a pre-existing file with specific content
        original_content = "-- This is the original content that should be overwritten"
        with open(file_path, "w") as f:
            f.write(original_content)
            
        self.assertEqual(file_path.read_text(), original_content)
        
        # 2. Setup generator and module data
        generator = VHDLGenerator(str(self.output_dir))
        module_data = {
            "name": module_name,
            "file": "source.vhd",
            "base_address": 0x0,
            "registers": [],
            "cdc_enabled": False,
            "packed_registers": []
        }
        
        # 4. Run generation
        generated_path = generator.generate_module(module_data)
        
        # 5. Verify file was overwritten
        self.assertTrue(os.path.exists(generated_path))
        new_content = file_path.read_text()
        
        self.assertNotEqual(new_content, original_content)
        self.assertIn("entity test_module_axion_reg is", new_content)
        self.assertIn("architecture rtl of test_module_axion_reg is", new_content)
