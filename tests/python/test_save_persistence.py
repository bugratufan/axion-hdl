import pytest
from flask import json
import os
import tempfile
import shutil
from unittest.mock import MagicMock

from axion_hdl.gui import AxionGUI
from axion_hdl.axion import AxionHDL

# Fixture to setup GUI app for testing
@pytest.fixture
def test_client():
    # Setup - use temp dir
    temp_dir = tempfile.mkdtemp()
    
    # Mock AxionHDL
    axion = MagicMock(spec=AxionHDL)
    axion.src_dirs = [temp_dir]
    axion.analyzed_modules = []
    
    # Init GUI
    gui_app = AxionGUI(axion)
    gui_app.setup_app()
    gui_app.app.config['TESTING'] = True
    
    client = gui_app.app.test_client()
    
    yield client, temp_dir
    
    # Teardown
    shutil.rmtree(temp_dir)

def test_save_new_module_persists_auto_address(test_client):
    """Test that saving a new module includes addresses even if not manual."""
    client, temp_dir = test_client
    
    file_path = os.path.join(temp_dir, "test_module.json")
    
    payload = {
        'module_name': 'test_module',
        'file_path': file_path,
        'format': 'json',
        'properties': {
            'base_address': '0x1000'
        },
        'registers': [
            {
                'name': 'reg_0',
                'width': 32,
                'access': 'RW',
                'description': 'Test Reg 0',
                # Address is auto-assigned/calculated in frontend and passed here
                # Even if manual_address is NOT set (implied false), addr should be saved
                'address': '0x00',
                'manual_address': False 
            },
            {
                'name': 'reg_1',
                'width': 32,
                'access': 'RO',
                'description': 'Test Reg 1',
                'address': '0x04',
                'manual_address': True # This one manually set
            }
        ]
    }
    
    response = client.post('/api/save_new_module', 
                          data=json.dumps(payload),
                          content_type='application/json')
    
    assert response.status_code == 200
    assert response.json['success'] == True
    
    # Verify file content
    with open(file_path, 'r') as f:
        saved_data = json.load(f)
    
    regs = saved_data['registers']
    assert len(regs) == 2
    
    # Check reg_0 (auto-assigned)
    r0 = next(r for r in regs if r['name'] == 'reg_0')
    assert 'addr' in r0
    assert r0['addr'] == '0x0' or r0['addr'] == '0x00'
    
    # Check reg_1 (manual)
    r1 = next(r for r in regs if r['name'] == 'reg_1')
    assert 'addr' in r1
    assert r1['addr'] == '0x4' or r1['addr'] == '0x04'



