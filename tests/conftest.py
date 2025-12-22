"""
Pytest configuration and fixtures for GUI testing

Uses Flask test client instead of subprocess for more reliable testing.
"""
import pytest
import sys
import os
import subprocess
from pathlib import Path
import threading
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def reset_vhdl_files():
    """Reset VHDL test files to their git state"""
    vhdl_dir = PROJECT_ROOT / "tests" / "vhdl"
    subprocess.run(["git", "checkout", str(vhdl_dir)], cwd=PROJECT_ROOT, capture_output=True)


def reset_all_test_files():
    """Reset all test source files (VHDL, XML, YAML, JSON) to their git state"""
    for subdir in ["vhdl", "xml", "yaml", "json"]:
        test_dir = PROJECT_ROOT / "tests" / subdir
        if test_dir.exists():
            subprocess.run(["git", "checkout", str(test_dir)], cwd=PROJECT_ROOT, capture_output=True)


@pytest.fixture(scope="session", autouse=True)
def reset_test_files():
    """Reset test files before and after test session"""
    reset_vhdl_files()
    yield
    reset_vhdl_files()


class FlaskTestServer:
    """Manages Flask app for testing using werkzeug server in a thread"""
    
    def __init__(self, port: int = 5001):
        self.port = port
        self.url = f"http://127.0.0.1:{port}"
        self.server = None
        self.thread = None
        self.app = None
    
    def start(self):
        """Start the Flask server in a background thread"""
        from axion_hdl import AxionHDL
        from axion_hdl.gui import AxionGUI
        from werkzeug.serving import make_server
        
        # Create Axion instance and analyze
        axion = AxionHDL(output_dir=str(PROJECT_ROOT / "output"))
        axion.add_src(str(PROJECT_ROOT / "tests" / "vhdl"))
        axion.add_source(str(PROJECT_ROOT / "tests" / "xml"))
        axion.add_source(str(PROJECT_ROOT / "tests" / "yaml"))
        axion.add_source(str(PROJECT_ROOT / "tests" / "json"))
        axion.exclude("error_cases")
        axion.analyze()
        
        # Create GUI and setup Flask app
        gui = AxionGUI(axion)
        gui.setup_app()
        self.app = gui.app
        
        # Create werkzeug server
        self.server = make_server('127.0.0.1', self.port, self.app, threaded=True)
        
        # Run in background thread
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()
        
        # Wait for server to be ready
        self._wait_for_ready()
    
    def _wait_for_ready(self, timeout=10):
        """Wait for server to accept connections"""
        import urllib.request
        start = time.time()
        while time.time() - start < timeout:
            try:
                urllib.request.urlopen(self.url, timeout=1)
                return
            except Exception:
                time.sleep(0.2)
        raise RuntimeError(f"Server failed to start within {timeout}s")
    
    def stop(self):
        """Stop the Flask server"""
        if self.server:
            self.server.shutdown()
        if self.thread:
            self.thread.join(timeout=5)


# Global server instances - one per worker
_server_instances = {}


def get_worker_port(worker_id):
    """Get unique port for each parallel worker"""
    if worker_id == "master" or worker_id is None:
        return 5001
    # worker_id is like "gw0", "gw1", etc.
    try:
        worker_num = int(worker_id.replace("gw", ""))
        return 5001 + worker_num
    except:
        return 5001


@pytest.fixture(scope="session")
def gui_server(request):
    """Fixture that provides a running GUI server for the test session"""
    global _server_instances
    
    # Get worker id for parallel testing
    worker_id = getattr(request.config, "workerinput", {}).get("workerid", "master")
    port = get_worker_port(worker_id)
    
    if worker_id not in _server_instances:
        _server_instances[worker_id] = FlaskTestServer(port=port)
        _server_instances[worker_id].start()
    
    yield _server_instances[worker_id]
    
    # Cleanup at end of session
    if worker_id in _server_instances:
        _server_instances[worker_id].stop()
        del _server_instances[worker_id]


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for Playwright tests"""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 720},
        "ignore_https_errors": True,
    }


@pytest.fixture
def gui_page(page, gui_server):
    """Fixture that provides a page connected to the GUI server"""
    page.goto(gui_server.url)
    page.wait_for_load_state("networkidle")
    return page
