import os
import shutil
import tempfile
import contextlib
from axion_hdl import AxionHDL
from axion_hdl.gui import AxionGUI

class TestGUIParsingErrors:
    
    @contextlib.contextmanager
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
        
        # Check for error badge presence
        assert "stat-value" in html  # Module count class
        
        # Look for Error count in summary
        # Based on index.html: <span class="stat-value stat-value-error">{{ total_errors }}</span>
        
        assert "stat-value-error" in html
        assert "1</span>" in html or "1 </span>" in html # The count value 

    def test_gui_rule_check_integration(self, test_env):
        """GUI-RULE-006: Parsing errors are included in Rule Check report"""
        src_dir = os.path.join(test_env, "src")
        axion = AxionHDL()
        axion.add_src(src_dir)
        axion.analyze()
        
        gui = AxionGUI(axion)
        gui.setup_app()
        client = gui.app.test_client()
        
        # Run rule check via API
        response = client.get('/api/run_check')
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify parsing errors are in the results
        # Parsing Errors from AddressManager raise AddressConflictError which VHDLParser catches
        errors = data.get('errors', [])
        assert any(e.get('type') == 'Parsing Error' or e.get('type') == 'Format Error' for e in errors)
        assert any("Address Conflict" in e.get('msg', '') for e in errors)

    def test_gui_blocks_generation_on_error(self, test_env):
        """GUI-GEN-017: Generation is blocked if module has parsing errors"""
        src_dir = os.path.join(test_env, "src")
        out_dir = os.path.join(test_env, "out")
        os.makedirs(out_dir, exist_ok=True)
        
        axion = AxionHDL(output_dir=out_dir)
        axion.add_src(src_dir)
        axion.analyze()
        
        gui = AxionGUI(axion)
        gui.setup_app()
        client = gui.app.test_client()
        
        # Request generation via API
        payload = {
            'output_dir': out_dir,
            'formats': {'vhdl': True, 'xml': True},
            'modules': ['conflict_guitest']
        }
        response = client.post('/api/generate', json=payload)
        assert response.status_code == 200
        data = response.get_json()
        
        # Should report failure
        assert data.get('success') is False
        assert any("Cannot proceed due to parsing errors" in log for log in data.get('logs', []))
        
        # Verify no files generated
        assert len(os.listdir(out_dir)) == 0

    def test_gui_dashboard_parsing_error_indicator(self, test_env):
        """GUI-DASH-011: Modules with parsing errors show error indicator"""
        src_dir = os.path.join(test_env, "src")
        axion = AxionHDL()
        axion.add_src(src_dir)
        axion.analyze()
        
        gui = AxionGUI(axion)
        gui.setup_app()
        client = gui.app.test_client()
        
        response = client.get('/')
        html = response.data.decode('utf-8')
        
        # Should have a badge or indicator for the module with error
        assert "badge-error" in html
        assert "Error" in html

