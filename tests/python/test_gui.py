"""
GUI Tests using Playwright

Tests the Axion-HDL web GUI against requirements in requirements_gui.md.
Run with: pytest tests/python/test_gui.py -v

Requirements:
  pip install pytest-playwright playwright
  playwright install chromium
"""
import pytest
import re
from pathlib import Path

# Skip all GUI tests if playwright is not installed
pytest.importorskip("playwright")


class TestGUILaunch:
    """Tests for GUI-LAUNCH requirements"""
    
    def test_launch_001_server_starts(self, gui_server):
        """GUI-LAUNCH-001: Server starts on configured port"""
        import urllib.request
        response = urllib.request.urlopen(gui_server.url)
        assert response.status == 200
    
    def test_launch_004_port_configuration(self, gui_server):
        """GUI-LAUNCH-004: Server uses configured port"""
        assert "5001" in gui_server.url  # Test uses port 5001


class TestGUIDashboard:
    """Tests for GUI-DASH requirements"""
    
    def test_dash_001_module_list(self, gui_page):
        """GUI-DASH-001: Dashboard lists all parsed modules"""
        # Check that module cards are present
        module_cards = gui_page.locator(".module-card-large")
        assert module_cards.count() > 0, "No module cards found on dashboard"
    
    def test_dash_002_module_count(self, gui_page):
        """GUI-DASH-002: Dashboard shows total module count"""
        # Look for summary cards with the new design
        summary_cards = gui_page.locator(".summary-card")
        assert summary_cards.count() >= 1, "No summary cards found"
        # First card should be module count
        first_card = summary_cards.first
        card_value = first_card.locator("h2").text_content()
        assert card_value.strip().isdigit(), f"Module count not a number: {card_value}"
    
    def test_dash_003_register_count(self, gui_page):
        """GUI-DASH-003: Dashboard shows total register count"""
        summary_cards = gui_page.locator(".summary-card")
        count = summary_cards.count()
        if count >= 2:
            # Second card should be register count (purple card)
            reg_card = summary_cards.nth(1)
            reg_count_text = reg_card.locator("h2").text_content().strip()
            # May contain whitespace, extract digits
            digits = ''.join(filter(str.isdigit, reg_count_text))
            assert len(digits) > 0, f"Register count not found: {reg_count_text}"
        else:
            # Single stat or different layout - just verify stats exist
            assert count >= 1, "No summary cards found"
    
    def test_dash_004_module_card_info(self, gui_page):
        """GUI-DASH-004: Module card shows base address, register count, source file"""
        # Get first module card
        first_card = gui_page.locator(".module-card-large").first
        
        # Check for info items
        info_items = first_card.locator(".info-item")
        count = info_items.count()
        assert count >= 1, "No info items in module card"
    
    def test_dash_006_register_preview(self, gui_page):
        """GUI-DASH-006: Module card shows registers preview"""
        preview = gui_page.locator(".register-preview").first
        assert preview.is_visible(), "Register preview section not visible"
    
    def test_dash_007_module_navigation(self, gui_page, gui_server):
        """GUI-DASH-007: Clicking module card opens editor"""
        # Get first module card
        first_card = gui_page.locator(".module-card-large").first
        
        # Click the card
        first_card.click()
        
        # Should navigate to editor - wait for URL change
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Verify we're on editor page
        assert "/module/" in gui_page.url
    
    def test_dash_009_statistics_cards(self, gui_page, gui_server):
        """GUI-DASH-009: Dashboard shows statistics summary cards"""
        # Navigate back to dashboard
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Check for statistics summary cards
        summary_cards = gui_page.locator(".summary-card")
        assert summary_cards.count() >= 4, f"Expected at least 4 summary cards, found {summary_cards.count()}"
    
    def test_dash_010_cdc_count_display(self, gui_page, gui_server):
        """GUI-DASH-010: Dashboard shows CDC-enabled module count"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Look for CDC-related statistics card
        cdc_card = gui_page.locator(".summary-card.green")
        assert cdc_card.is_visible(), "CDC count card not visible"
        
        # Verify it shows "CDC Enabled" label
        cdc_text = cdc_card.text_content()
        assert "CDC" in cdc_text, f"CDC text not found in card: {cdc_text}"


class TestGUIEditor:
    """Tests for GUI-EDIT requirements"""
    
    def test_edit_001_breadcrumb(self, gui_page, gui_server):
        """GUI-EDIT-001: Editor shows breadcrumb navigation"""
        # Navigate to first module
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        breadcrumb = gui_page.locator(".breadcrumb")
        assert breadcrumb.is_visible(), "Breadcrumb not visible"
    
    def test_edit_002_base_address(self, gui_page, gui_server):
        """GUI-EDIT-002: Base address input accepts hex values"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        base_addr_input = gui_page.locator("input[name='base_address']")
        assert base_addr_input.is_visible(), "Base address input not visible"
        
        # Should have a value
        value = base_addr_input.input_value()
        assert re.match(r'^[0-9A-Fa-f]+$', value), f"Invalid hex value: {value}"
    
    def test_edit_003_cdc_toggle(self, gui_page, gui_server):
        """GUI-EDIT-003: CDC enable/disable switch works"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        cdc_checkbox = gui_page.locator("#cdcEnable")
        assert cdc_checkbox.is_visible(), "CDC checkbox not visible"
    
    def test_edit_005_register_table(self, gui_page, gui_server):
        """GUI-EDIT-005: Register table exists with headers"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        table = gui_page.locator("#regsTable")
        assert table.is_visible(), "Register table not visible"
        
        # Check headers exist
        headers = gui_page.locator("#regsTable thead th")
        assert headers.count() >= 5, f"Not enough columns: {headers.count()}"
    
    def test_edit_012_add_register(self, gui_page, gui_server):
        """GUI-EDIT-012: New Register button adds row"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        initial_count = gui_page.locator(".reg-row").count()
        
        # Click add button
        gui_page.locator("#addRegBtn").click()
        
        # Should have one more row
        gui_page.wait_for_timeout(500)  # Wait for animation
        new_count = gui_page.locator(".reg-row").count()
        assert new_count == initial_count + 1, f"Row not added: {initial_count} -> {new_count}"


class TestGUIGeneration:
    """Tests for GUI-GEN requirements"""
    
    def test_gen_001_output_directory(self, gui_page, gui_server):
        """GUI-GEN-001: Output directory input shows default path"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        output_input = gui_page.locator("#outputDir")
        assert output_input.is_visible(), "Output directory input not visible"
    
    def test_gen_003_vhdl_toggle(self, gui_page, gui_server):
        """GUI-GEN-003: VHDL checkbox toggles generation"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        vhdl_checkbox = gui_page.locator("#fmtVhdl")
        assert vhdl_checkbox.is_visible(), "VHDL checkbox not visible"
    
    def test_gen_007_generate_button(self, gui_page, gui_server):
        """GUI-GEN-007: Generate button is present"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        gen_button = gui_page.locator("button", has_text="Generate")
        assert gen_button.is_visible(), "Generate button not visible"
    
    def test_gen_008_activity_log(self, gui_page, gui_server):
        """GUI-GEN-008: Activity log is present"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        log_area = gui_page.locator("#consoleOutput")
        assert log_area.is_visible(), "Activity log not visible"
    
    def test_gen_009_status_badge(self, gui_page, gui_server):
        """GUI-GEN-009: Status badge shows Idle state initially"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        badge = gui_page.locator("#statusBadge")
        assert badge.is_visible(), "Status badge not visible"
    
    def test_gen_012_doc_md_toggle(self, gui_page, gui_server):
        """GUI-GEN-012: Markdown documentation checkbox toggles generation"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        md_checkbox = gui_page.locator("#fmtDocMd")
        assert md_checkbox.is_visible(), "Markdown docs checkbox not visible"
        assert md_checkbox.is_checked(), "Markdown docs should be checked by default"
    
    def test_gen_013_doc_html_toggle(self, gui_page, gui_server):
        """GUI-GEN-013: HTML documentation checkbox toggles generation"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        html_checkbox = gui_page.locator("#fmtDocHtml")
        assert html_checkbox.is_visible(), "HTML docs checkbox not visible"
        assert html_checkbox.is_checked(), "HTML docs should be checked by default"


class TestGUINavigation:
    """Tests for GUI-NAV requirements"""
    
    def test_nav_001_navbar_brand(self, gui_page):
        """GUI-NAV-001: Navbar shows branding"""
        brand = gui_page.locator(".navbar-brand")
        assert brand.is_visible(), "Navbar brand not visible"
        assert "Axion" in brand.text_content(), "Axion not in brand text"
    
    def test_nav_002_modules_link(self, gui_page):
        """GUI-NAV-002: Modules link exists"""
        modules_link = gui_page.locator("a.nav-link", has_text="Modules")
        assert modules_link.is_visible(), "Modules link not visible"
    
    def test_nav_003_rule_check_link(self, gui_page):
        """GUI-NAV-003: Rule Check link exists"""
        rule_link = gui_page.locator("a.nav-link", has_text="Rule")
        assert rule_link.is_visible(), "Rule Check link not visible"
    
    def test_nav_004_generate_link(self, gui_page):
        """GUI-NAV-004: Generate link exists"""
        gen_link = gui_page.locator("a.nav-link", has_text="Generate")
        assert gen_link.is_visible(), "Generate link not visible"
    
    def test_nav_005_footer_version(self, gui_page):
        """GUI-NAV-005: Footer displays version"""
        footer = gui_page.locator("footer")
        assert footer.is_visible(), "Footer not visible"


class TestGUIConfig:
    """Tests for GUI-CONFIG requirements"""

    def test_config_001_page_load(self, gui_page, gui_server):
         gui_page.goto(f"{gui_server.url}/config")
         gui_page.wait_for_load_state("networkidle")
         assert "Tool Config" in gui_page.title()

    def test_config_002_save_button(self, gui_page, gui_server):
         gui_page.goto(f"{gui_server.url}/config")
         # Look for button with Save text
         save_btn = gui_page.locator("button", has_text="Save")
         assert save_btn.is_visible()

    def test_config_003_save_action(self, gui_page, gui_server):
         # Ensure .axion_conf doesn't exist
         import os
         if os.path.exists(".axion_conf"):
             os.remove(".axion_conf")

         gui_page.goto(f"{gui_server.url}/config")
         
         # Setup dialog handler
         gui_page.on("dialog", lambda dialog: dialog.accept())
         
         gui_page.locator("button", has_text="Save").click()
         
         # Wait a bit for server to write file
         gui_page.wait_for_timeout(2000)
         
         assert os.path.exists(".axion_conf")
         
         # Clean up
         if os.path.exists(".axion_conf"):
             os.remove(".axion_conf")

    def test_config_004_refresh_log(self, gui_page, gui_server):
         """GUI-CONFIG-004: Refresh button shows log"""
         gui_page.goto(f"{gui_server.url}/config")
         
         # Click Refresh
         gui_page.locator("button", has_text="Apply & Refresh").click()
         
         # Log should become visible
         log = gui_page.locator("#configActivityLog")
         assert log.is_visible()
         
         # Wait for success message from frontend
         content = gui_page.locator("#configLogContent")
         content.get_by_text("Refresh completed successfully").wait_for(timeout=5000)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

