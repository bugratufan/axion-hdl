import pytest
import os
import shutil
import tempfile
import json
import yaml
from axion_hdl import AxionHDL
from axion_hdl.rule_checker import RuleChecker

@pytest.fixture
def env():
    tmp_dir = tempfile.mkdtemp()
    output_dir = os.path.join(tmp_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    yield tmp_dir, output_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)

def run_checks(modules):
    checker = RuleChecker()
    return checker.run_all_checks(modules)

def test_yaml_duplicate_address(env):
    """YAML: Detect two registers at same address."""
    tmp_dir, output_dir = env
    yaml_content = """
module: spi_master
base_addr: "0x1000"
registers:
  - name: control
    addr: "0x04"
    access: RW
  - name: status
    addr: "0x04"
    access: RO
"""
    with open(os.path.join(tmp_dir, "spi.yaml"), 'w') as f:
        f.write(yaml_content)
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_source(tmp_dir)
    axion.analyze()
    
    results = run_checks(axion.analyzed_modules)
    assert len(results['errors']) > 0
    error_msgs = [e['msg'] for e in results['errors']]
    assert any('0x1004' in msg or 'control' in msg or 'status' in msg for msg in error_msgs)

def test_json_duplicate_address(env):
    """JSON: Detect two registers at same address."""
    tmp_dir, output_dir = env
    json_content = {
        "module": "uart",
        "base_addr": "0x2000",
        "registers": [
            {"name": "tx", "addr": "0x00", "access": "WO"},
            {"name": "rx", "addr": "0x00", "access": "RO"}
        ]
    }
    with open(os.path.join(tmp_dir, "uart.json"), 'w') as f:
        json.dump(json_content, f)
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_source(tmp_dir)
    axion.analyze()
    
    results = run_checks(axion.analyzed_modules)
    assert len(results['errors']) > 0
    assert any('tx' in e['msg'] or 'rx' in e['msg'] for e in results['errors'])

def test_vhdl_duplicate_address(env):
    """VHDL: Detect two registers at same address."""
    tmp_dir, output_dir = env
    vhdl_content = """
-- @axion_def BASE_ADDR=0x4000
entity timer is
    port (clk : in std_logic);
end entity;
architecture rtl of timer is
    signal count : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00
    signal reload : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00
begin
end architecture;
"""
    with open(os.path.join(tmp_dir, "timer.vhd"), 'w') as f:
        f.write(vhdl_content)
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_source(tmp_dir)
    axion.analyze()
    
    # Check parsing errors or rule checker
    parsing_errors = [err for m in axion.analyzed_modules for err in m.get('parsing_errors', [])]
    results = run_checks(axion.analyzed_modules)
    assert (len(results['errors']) + len(parsing_errors)) > 0

def test_yaml_wide_register_overlap(env):
    """YAML: Detect overlap when wide register spans multiple addresses."""
    tmp_dir, output_dir = env
    yaml_content = """
module: dma
base_addr: "0x5000"
registers:
  - name: buf_addr
    addr: "0x00"
    width: 64
    access: RW
  - name: ctrl
    addr: "0x04"
    width: 32
    access: RW
"""
    with open(os.path.join(tmp_dir, "dma.yaml"), 'w') as f:
        f.write(yaml_content)
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_source(tmp_dir)
    axion.analyze()
    
    results = run_checks(axion.analyzed_modules)
    assert len(results['errors']) > 0
    assert any('overlap' in e['msg'].lower() or 'conflict' in e['msg'].lower() for e in results['errors'])

def test_no_conflict_valid_addresses(env):
    """Should not report errors for valid non-overlapping addresses."""
    tmp_dir, output_dir = env
    yaml_content = """
module: ok
registers:
  - {name: a, addr: "0x00", width: 32, access: RW}
  - {name: b, addr: "0x04", width: 32, access: RW}
"""
    with open(os.path.join(tmp_dir, "ok.yaml"), 'w') as f:
        f.write(yaml_content)
    
    axion = AxionHDL(output_dir=output_dir)
    axion.add_source(tmp_dir)
    axion.analyze()
    
    results = run_checks(axion.analyzed_modules)
    addr_errors = [e for e in results['errors'] if 'Address' in e['category'] or 'Duplicate' in e['category']]
    assert len(addr_errors) == 0
