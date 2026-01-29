import pytest
import os
import sys
import tempfile
import subprocess
import shutil
from pathlib import Path

# Add project root to path for imports if needed
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture
def cli_env():
    """Set up temporary directory and sample VHDL for CLI testing."""
    tmp_dir = tempfile.mkdtemp()
    
    vhdl_content = """
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
"""
    vhdl_file = os.path.join(tmp_dir, "cli_test.vhd")
    with open(vhdl_file, 'w') as f:
        f.write(vhdl_content)
    
    cli_cmd = [sys.executable, '-m', 'axion_hdl.cli']
    
    yield tmp_dir, vhdl_file, cli_cmd
    
    shutil.rmtree(tmp_dir, ignore_errors=True)

def run_cli(cmd, args, cwd=None):
    """Run CLI with arguments and return result."""
    full_cmd = cmd + args
    return subprocess.run(full_cmd, capture_output=True, text=True, cwd=cwd or str(project_root))

def test_cli_001_help(cli_env):
    """CLI-001: --help displays usage information."""
    tmp_dir, vhdl_file, cli_cmd = cli_env
    result = run_cli(cli_cmd, ['--help'])
    assert result.returncode == 0
    assert 'usage' in result.stdout.lower()

def test_cli_002_version(cli_env):
    """CLI-002: --version displays version."""
    tmp_dir, vhdl_file, cli_cmd = cli_env
    result = run_cli(cli_cmd, ['--version'])
    assert result.returncode == 0
    output = result.stdout + result.stderr
    assert any(c.isdigit() for c in output)

def test_cli_003_source_and_output(cli_env):
    """CLI-003, CLI-005: Source and output options."""
    tmp_dir, vhdl_file, cli_cmd = cli_env
    output_dir = os.path.join(tmp_dir, "out")
    result = run_cli(cli_cmd, ['-s', vhdl_file, '-o', output_dir])
    assert result.returncode == 0
    assert os.path.exists(output_dir)
    assert os.path.exists(os.path.join(output_dir, "cli_test_axion_reg.vhd"))

def test_cli_003_xml_input(cli_env):
    """CLI-003: -s accepts single XML file."""
    tmp_dir, vhdl_file, cli_cmd = cli_env
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<register_map module="xml_test" base_addr="0x0000">
  <register name="status" addr="0x00" access="RO" width="32" />
</register_map>
"""
    xml_file = os.path.join(tmp_dir, "test.xml")
    with open(xml_file, 'w') as f:
        f.write(xml_content)
    
    output_dir = os.path.join(tmp_dir, "out_xml")
    result = run_cli(cli_cmd, ['-s', xml_file, '-o', output_dir])
    assert result.returncode == 0
    assert os.path.exists(output_dir)

def test_cli_006_exclude(cli_env):
    """CLI-006: -e option excludes patterns."""
    tmp_dir, vhdl_file, cli_cmd = cli_env
    # Create sub-directory to exclude
    sub = os.path.join(tmp_dir, "ignore_me")
    os.makedirs(sub)
    with open(os.path.join(sub, "bad.vhd"), 'w') as f: f.write("bad")
    
    output_dir = os.path.join(tmp_dir, "out_ex")
    result = run_cli(cli_cmd, ['-s', tmp_dir, '-o', output_dir, '-e', 'ignore_me'])
    assert result.returncode == 0

def test_cli_009_invalid_source(cli_env):
    """CLI-009: Non-existent source reports error."""
    tmp_dir, vhdl_file, cli_cmd = cli_env
    result = run_cli(cli_cmd, ['-s', '/tmp/nonexistent_path_xxx', '-o', tmp_dir])
    assert result.returncode != 0

def test_cli_011_yaml_json_flags(cli_env):
    """CLI-011, CLI-012: YAML and JSON output flags."""
    tmp_dir, vhdl_file, cli_cmd = cli_env
    output_dir = os.path.join(tmp_dir, "out_flags")
    result = run_cli(cli_cmd, ['-s', vhdl_file, '-o', output_dir, '--yaml', '--json'])
    assert result.returncode == 0
    assert len(list(Path(output_dir).glob('*_regs.yaml'))) > 0
    assert len(list(Path(output_dir).glob('*_regs.json'))) > 0

def test_cli_013_config_file(cli_env):
    """CLI-013: --config loads settings from JSON file."""
    import json
    tmp_dir, vhdl_file, cli_cmd = cli_env
    output_dir = os.path.join(tmp_dir, "out_config")
    config = {
        "src_files": [vhdl_file],
        "output_dir": output_dir
    }
    config_path = os.path.join(tmp_dir, "conf.json")
    with open(config_path, 'w') as f:
        json.dump(config, f)
        
    result = run_cli(cli_cmd, ['--config', config_path])
    assert result.returncode == 0
    assert os.path.exists(output_dir)

def test_cli_015_auto_load_config(cli_env):
    """CLI-015: Auto-load .axion_conf."""
    import json
    tmp_dir, vhdl_file, cli_cmd = cli_env
    
    project_dir = os.path.join(tmp_dir, "proj")
    os.makedirs(project_dir)
    
    with open(os.path.join(project_dir, "mod.json"), "w") as f:
        f.write('{ "module": "m", "registers": [] }')
        
    config = { "src_files": ["mod.json"], "output_dir": "gen" }
    with open(os.path.join(project_dir, ".axion_conf"), "w") as f:
        json.dump(config, f)
        
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    
    result = subprocess.run(cli_cmd, cwd=project_dir, capture_output=True, text=True, env=env)
    assert result.returncode == 0
    assert os.path.exists(os.path.join(project_dir, "gen"))
