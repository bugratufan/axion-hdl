import pytest
import os
import tempfile
import shutil
from pathlib import Path
from axion_hdl.generator import VHDLGenerator

@pytest.fixture
def out_dir():
    tmp = tempfile.mkdtemp()
    out = Path(tmp) / "output"
    out.mkdir()
    yield out
    shutil.rmtree(tmp, ignore_errors=True)

def test_overwrite_existing_file(out_dir):
    """Verify that generation overwrites an existing file (AXION-027)."""
    module_name = "test_module"
    filename = f"{module_name}_axion_reg.vhd"
    file_path = out_dir / filename
    
    # 1. Create pre-existing file
    original = "-- Original content"
    file_path.write_text(original)
    assert file_path.read_text() == original
    
    # 2. Generate
    gen = VHDLGenerator(str(out_dir))
    data = {
        "name": module_name,
        "file": "s.vhd",
        "base_address": 0x0,
        "registers": [],
        "cdc_enabled": False,
        "packed_registers": []
    }
    path = gen.generate_module(data)
    
    # 3. Verify
    assert os.path.exists(path)
    new = file_path.read_text()
    assert new != original
    assert "entity test_module_axion_reg" in new.lower()
