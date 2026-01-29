import pytest
import os
import tempfile
from axion_hdl.axion import AxionHDL

@pytest.fixture
def axion_ready():
    axion = AxionHDL()
    axion.analyzed_modules = [{'name': 'mod1', 'registers': []}]
    axion.is_analyzed = True
    return axion

def test_run_rules_writes_file(axion_ready):
    """Verify that run_rules writes a text report to file."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        report_path = tmp.name
        
    try:
        axion_ready.run_rules(report_file=report_path)
        assert os.path.exists(report_path)
        with open(report_path, 'r') as f:
            content = f.read()
            assert "AXION HDL RULE CHECK REPORT" in content
    finally:
        if os.path.exists(report_path):
            os.remove(report_path)

def test_run_rules_json_output(axion_ready):
    """Verify that run_rules writes a JSON report when extension is .json."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp:
        report_path = tmp.name
    
    try:
        axion_ready.run_rules(report_file=report_path)
        assert os.path.exists(report_path)
        with open(report_path, 'r') as f:
            content = f.read()
            assert content.strip().startswith('{')
            assert '"summary":' in content
            assert '"total_errors":' in content
    finally:
         if os.path.exists(report_path):
            os.remove(report_path)
