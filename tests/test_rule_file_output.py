import os
import unittest
import tempfile
from unittest.mock import MagicMock
from axion_hdl.axion import AxionHDL
from axion_hdl.rule_checker import RuleChecker

class TestRuleFileOutput(unittest.TestCase):
    def test_run_rules_writes_file(self):
        # Setup Axion with mocked modules
        axion = AxionHDL()
        axion.analyzed_modules = [{'name': 'mod1', 'registers': []}] # Minimal valid module
        axion.is_analyzed = True
        
        # Temp file
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            report_path = tmp.name
            
        try:
            # Run rules with file path
            axion.run_rules(report_file=report_path)
            
            # Check if file exists and has content
            self.assertTrue(os.path.exists(report_path))
            with open(report_path, 'r') as f:
                content = f.read()
                self.assertIn("AXION HDL RULE CHECK REPORT", content)
                
        finally:
            if os.path.exists(report_path):
                os.remove(report_path)

    def test_run_rules_json_output(self):
        axion = AxionHDL()
        axion.analyzed_modules = [{'name': 'mod1', 'registers': []}] 
        axion.is_analyzed = True
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
            report_path = tmp.name
        
        try:
            axion.run_rules(report_file=report_path)
            
            with open(report_path, 'r') as f:
                content = f.read()
                # Verify it looks like JSON
                self.assertTrue(content.strip().startswith('{'))
                self.assertIn('"summary":', content)
                self.assertIn('"total_errors":', content)
        finally:
             if os.path.exists(report_path):
                os.remove(report_path)

if __name__ == '__main__':
    unittest.main()
