import pytest
import os
import shutil
import tempfile
from axion_hdl import AxionHDL
from axion_hdl.gui import AxionGUI

class TestGUIParsingErrors:
    
    @pytest.fixture
    def test_env(self):
        """Setup temporary test environment with conflicting VHDL"""
        tmp_dir = tempfile.mkdtemp()
        
        # Create a conflicting VHDL file
        vhdl_content = """
        library ieee;
        use ieee.std_logic_1164.all;
        entity conflict_guitest is
        end entity;
        
        architecture rtl of conflict_guitest is
            -- @axion_def base_address=0x1000
            signal reg1 : std_logic_vector(31 downto 0); -- @axion address=0x0
            signal reg2 : std_logic_vector(31 downto 0); -- @axion address=0x0 -- CONFLICT!
        begin
        end architecture;
        """
        
        src_dir = os.path.join(tmp_dir, "src")
        os.makedirs(src_dir)
        with open(os.path.join(src_dir, "conflict.vhd"), "w") as f:
            f.write(vhdl_content)
            
        yield tmp_dir
        
        shutil.rmtree(tmp_dir)

    def test_dashboard_shows_parsing_errors(self, test_env):
        """Verify dashboard includes parsing errors in stats"""
        src_dir = os.path.join(test_env, "src")
        
        # Initialize Axion
        axion = AxionHDL(output_dir=os.path.join(test_env, "out"))
        axion.add_src(src_dir)
        axion.analyze()
        
        # Ensure parser definitely found the error
        module = next((m for m in axion.analyzed_modules if m["name"] == "conflict_guitest"), None)
        assert module is not None
        assert "parsing_errors" in module
        assert len(module["parsing_errors"]) > 0
        
        # Initialize GUI
        gui = AxionGUI(axion)
        gui.setup_app()
        client = gui.app.test_client()
        
        # Get dashboard
        response = client.get('/')
        assert response.status_code == 200
        html = response.data.decode('utf-8')
        
        # Check for error card presence
        # Look for "1 Modules"
        assert "1</h2>" in html or "1 </h2>" in html  # Module count
        
        # Look for Error count in summary card
        # The Red card should be visible with "1 Errors" or similar
        # Based on index.html: <div class="summary-card red"> ... <h2>{{ total_errors + total_warnings }}</h2> ... <p>{{ total_errors }} Errors
        
        assert "summary-card red" in html
        assert "1 Errors" in html
