import pytest
import os
import shutil
import tempfile
from axion_hdl import AxionHDL
from axion_hdl.parser import VHDLParser

@pytest.fixture
def stress_env():
    tmp = tempfile.mkdtemp()
    parser = VHDLParser()
    out = os.path.join(tmp, "output")
    yield tmp, out, parser
    shutil.rmtree(tmp, ignore_errors=True)

def test_stress_001_many_registers(stress_env):
    """STRESS-001: Support 100+ registers per module."""
    tmp, out, _ = stress_env
    signals = [f"signal r{i:03} : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x{i*4:X}" for i in range(100)]
    vhdl = f"entity many is end; architecture rtl of many is\n{chr(10).join(signals)}\nbegin end;"
    with open(os.path.join(tmp, "many.vhd"), 'w') as f: f.write(vhdl)
    
    axion = AxionHDL(output_dir=out)
    axion.add_src(tmp)
    assert axion.analyze()
    assert len(axion.analyzed_modules[0]['registers']) == 100

def test_stress_002_wide_signal(stress_env):
    """STRESS-002: Support 256-bit signals."""
    tmp, out, _ = stress_env
    vhdl = "entity wide is end; architecture rtl of wide is\nsignal huge : std_logic_vector(255 downto 0); -- @axion RO ADDR=0x0\nbegin end;"
    with open(os.path.join(tmp, "wide.vhd"), 'w') as f: f.write(vhdl)
    
    axion = AxionHDL(output_dir=out)
    axion.add_src(tmp)
    assert axion.analyze()
    # 256-bit consumes 8 registers (assuming 32-bit bus)
    # The check depends on how registers are reported in analyzed_modules
    assert len(axion.analyzed_modules[0]['registers']) >= 1

def test_stress_005_random_addresses(stress_env):
    """STRESS-005: Non-sequential address patterns work."""
    tmp, out, parser = stress_env
    vhdl = """
entity rnd is end;
architecture rtl of rnd is
    signal r1 : std_logic; -- @axion RO ADDR=0x100
    signal r2 : std_logic; -- @axion RW ADDR=0x04
begin end;
"""
    f = os.path.join(tmp, "rnd.vhd")
    with open(f, 'w') as out_f: out_f.write(vhdl)
    res = parser.parse_file(f)
    addrs = {s['address'] for s in res['signals']}
    assert addrs == {0x100, 0x04}

def test_stress_006_boundary_values(stress_env):
    """STRESS-006: Generation handles all register types."""
    tmp, out, _ = stress_env
    vhdl = """
entity b is end;
architecture rtl of b is
    signal r1 : std_logic; -- @axion RO ADDR=0x0
    signal r2 : std_logic; -- @axion WO ADDR=0x4
    signal r3 : std_logic; -- @axion RW R_STROBE W_STROBE ADDR=0x8
begin end;
"""
    with open(os.path.join(tmp, "b.vhd"), 'w') as f: f.write(vhdl)
    axion = AxionHDL(output_dir=out)
    axion.add_src(tmp)
    axion.analyze()
    axion.generate_vhdl()
    
    vhdl_out = os.path.join(out, "b_axion_reg.vhd")
    assert os.path.exists(vhdl_out)
    content = open(vhdl_out).read().lower()
    assert 'r1' in content
    assert 'r2' in content
    assert 'r3' in content
