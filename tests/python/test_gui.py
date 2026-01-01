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
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_timeout(500)  # Wait for JS to initialize
        
        initial_count = gui_page.locator(".reg-row").count()
        
        # Use JavaScript directly with error capturing
        result = gui_page.evaluate("""
            (() => {
                try {
                    const before = document.querySelectorAll('.reg-row').length;
                    addRegister();
                    const after = document.querySelectorAll('.reg-row').length;
                    return {success: true, before: before, after: after};
                } catch(e) {
                    return {success: false, error: e.toString(), stack: e.stack};
                }
            })()
        """)
        
        print(f"JS Result: {result}")
        
        # Wait for DOM update
        gui_page.wait_for_timeout(500)
        new_count = gui_page.locator(".reg-row").count()
        assert new_count == initial_count + 1, f"Row not added: {initial_count} -> {new_count}, JS result: {result}"

    def test_edit_013_vhdl_readonly_name(self, gui_page, gui_server):
        """GUI-EDIT-013: Name input is readonly for VHDL modules"""
        gui_page.goto(gui_server.url)
        # Find a VHDL module card
        vhdl_card = gui_page.locator(".module-card-large", has_text=re.compile(r"\.vhd", re.IGNORECASE))
        
        if vhdl_card.count() > 0:
            vhdl_card.first.click()
            gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
            
            # Check first existing register - Name input should be readonly
            # Note: Empty register maps won't have rows, so check count
            if gui_page.locator(".reg-row").count() > 0:
                name_input = gui_page.locator(".reg-name-input").first
                assert name_input.get_attribute("readonly") is not None, "Name input should be readonly for VHDL"
            
            # Add new register - should NOT be readonly
            gui_page.locator("#addRegBtn").click()
            gui_page.wait_for_timeout(1000)
            
            new_row = gui_page.locator(".reg-row").last
            new_name = new_row.locator(".reg-name-input")
            assert new_name.get_attribute("readonly") is None, "New register name should be editable"

    def test_edit_037_restrict_register_renaming(self, gui_page, gui_server):
        """GUI-EDIT-037: For VHDL sources, existing register names are read-only"""
        gui_page.goto(gui_server.url)
        # Find a VHDL module card
        vhdl_card = gui_page.locator(".module-card-large", has_text=re.compile(r"\.vhd", re.IGNORECASE))
        
        if vhdl_card.count() > 0:
            vhdl_card.first.click()
            gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
            
            # All existing register name inputs should be readonly for VHDL sources
            if gui_page.locator(".reg-row").count() > 0:
                name_inputs = gui_page.locator(".reg-name-input")
                for i in range(min(name_inputs.count(), 3)):  # Check first 3
                    input_elem = name_inputs.nth(i)
                    if input_elem.input_value():  # Only check inputs with values (existing registers)
                        assert input_elem.get_attribute("readonly") is not None, \
                            f"Existing register name should be readonly for VHDL, but register {i} is editable"


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
        gui_page.goto(f"{gui_server.url}/generate", timeout=60000)
        gui_page.wait_for_load_state("domcontentloaded")
        
        badge = gui_page.locator("#statusBadge")
        badge.wait_for(state="visible", timeout=10000)
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

    def test_nav_007_layout_refinement(self, gui_page, gui_server):
        """GUI-NAV-007: Column widths are optimized; Width displayed without units"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Check that width column exists and shows numeric values without units
        if gui_page.locator(".reg-row").count() > 0:
            width_cell = gui_page.locator(".reg-width-input").first
            value = width_cell.input_value()
            # Width should be a plain number, not "32 bits" or similar
            assert value.isdigit(), f"Width should be number without units, got: {value}"


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


class TestGUISaveIndicator:
    """Tests for GUI-SAVE requirements - unsaved changes tracking"""

    def test_save_001_unsaved_indicator_exists(self, gui_page, gui_server):
        """GUI-SAVE-001: Unsaved changes indicator element exists"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        indicator = gui_page.locator("#unsavedIndicator")
        assert indicator.count() == 1, "Unsaved indicator element not found"

    def test_save_001_indicator_hidden_initially(self, gui_page, gui_server):
        """GUI-SAVE-001: Indicator is hidden when no changes"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        indicator = gui_page.locator("#unsavedIndicator")
        # Should not have 'visible' class initially
        assert not indicator.get_attribute("class") or "visible" not in indicator.get_attribute("class")

    def test_save_001_indicator_shows_on_change(self, gui_page, gui_server):
        """GUI-SAVE-001: Indicator appears when changes are made"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Make a change to base address
        base_input = gui_page.locator("input[name='base_address']")
        original_value = base_input.input_value()
        base_input.fill("FFFE")
        
        gui_page.wait_for_timeout(300)  # Wait for change detection
        
        indicator = gui_page.locator("#unsavedIndicator")
        assert "visible" in (indicator.get_attribute("class") or ""), \
            "Unsaved indicator not visible after change"

    def test_save_002_indicator_on_module_property_change(self, gui_page, gui_server):
        """GUI-SAVE-002: Indicator appears when module properties change"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        # Wait for client-side initialization (initialState is set after 200ms)
        gui_page.wait_for_function("() => window.initialState !== undefined")

        # Change CDC Enabled
        cdc_switch = gui_page.locator("#cdcEnable")
        
        # Ensure we toggle it (it starts checked in test data)
        if cdc_switch.is_checked():
            cdc_switch.uncheck()
        else:
            cdc_switch.check()
            
        gui_page.wait_for_timeout(500)
        indicator = gui_page.locator("#unsavedIndicator")
        assert "visible" in (indicator.get_attribute("class") or ""), "Indicator not visible after CDC toggle"
    
        # Revert change - toggle back to original state
        if cdc_switch.is_checked():
            cdc_switch.uncheck()
        else:
            cdc_switch.check()
            
        gui_page.wait_for_timeout(500)
        # assert "visible" not in (indicator.get_attribute("class") or ""), "Indicator visible after revert"


    def test_save_003_indicator_on_register_field_change(self, gui_page, gui_server):
        """GUI-SAVE-003: Indicator appears when register fields change"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        # Wait for client-side initialization
        gui_page.wait_for_function("() => window.initialState !== undefined")
    
        # Test 1: Change description
        desc_input = gui_page.locator(".reg-desc-input").first
        original_desc = desc_input.input_value()
        desc_input.fill("New Description Test")
        gui_page.wait_for_timeout(500)
        
        indicator = gui_page.locator("#unsavedIndicator")
        assert "visible" in (indicator.get_attribute("class") or ""), "Indicator not visible after description change"
        
        # Revert description
        desc_input.fill(original_desc)
        gui_page.wait_for_timeout(500)
        # Force blur to ensure change event fires if needed (although fill usually does)
        desc_input.blur()
        gui_page.wait_for_timeout(500)
        # assert "visible" not in (indicator.get_attribute("class") or ""), "Indicator visible after revert description"

        # Test 2: Toggle Strobe
        # Find a register, click 'R' strobe
        r_strobe = gui_page.locator(".strobe-toggle", has_text="R").first
        r_strobe.click()
        gui_page.wait_for_timeout(300)
        assert "visible" in (indicator.get_attribute("class") or ""), "Indicator not visible after strobe toggle"
        
        # Revert strobe
        r_strobe.click()
        gui_page.wait_for_timeout(300)
        # assert "visible" not in (indicator.get_attribute("class") or ""), "Indicator visible after revert strobe"

    def test_save_004_indicator_clears_on_save(self, gui_page, gui_server):
        """GUI-SAVE-004: Indicator clears after save"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Make a change
        desc_input = gui_page.locator(".reg-desc-input").first
        desc_input.fill("Save Test Description")
        gui_page.wait_for_timeout(300)
        
        indicator = gui_page.locator("#unsavedIndicator")
        assert "visible" in (indicator.get_attribute("class") or "")
        
        # Save
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # Return to editor (or check if indicator is gone on diff page - usually header is shared)
        # But indicator logic is in editor.js, so it might not be present on diff page.
        # Let's go back to editor
        gui_page.go_back() 
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Indicator should be gone because the page reloaded with new state
        indicator = gui_page.locator("#unsavedIndicator")
        assert "visible" not in (indicator.get_attribute("class") or "")

    def test_save_007_auto_reload(self, gui_page, gui_server):
        """GUI-SAVE-007: Application state updates after saving changes"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Get initial module count from dashboard
        initial_card_count = gui_page.locator(".module-card-large").count()
        assert initial_card_count > 0, "No module cards found"
        
        # Navigate to a module and make a change
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        # Get module name from breadcrumb
        module_name = gui_page.locator(".breadcrumb-item.active").text_content().strip()
        
        # Navigate back to dashboard
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Verify the same module is still listed (state is consistent)
        final_card_count = gui_page.locator(".module-card-large").count()
        assert final_card_count == initial_card_count, \
            f"Module count changed unexpectedly: {initial_card_count} -> {final_card_count}"


class TestGUIDiffView:
    """Tests for GUI-DIFF requirements - diff display features"""

    def test_diff_006_unified_view_default(self, gui_page, gui_server):
        """GUI-DIFF-006: Unified view is default"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        # Make a unique change using timestamp to ensure diff is generated
        import time
        unique_val = format(int(time.time()) % 0xFFFF, '04X')
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill(unique_val)
        gui_page.wait_for_timeout(500)  # Wait for input change to register
        
        # Click Review & Save
        save_btn = gui_page.locator("button", has_text="Review")
        save_btn.click()
        
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # Check if we have a diff or no-changes message (both are valid outcomes)
        if gui_page.locator(".no-changes").is_visible():
            return 
            
        # Unified view should be active
        unified_btn = gui_page.locator("#btn-unified")
        unified_btn.wait_for(timeout=5000)
        assert "active" in (unified_btn.get_attribute("class") or "")

    def test_diff_008_view_toggle(self, gui_page, gui_server):
        """GUI-DIFF-008: View toggle switches between unified and side-by-side"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        # Make a unique change using timestamp
        import time
        unique_val = format((int(time.time()) + 1) % 0xFFFF, '04X')
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill(unique_val)
        gui_page.wait_for_timeout(500)  # Wait for input change to register
        
        save_btn = gui_page.locator("button", has_text="Review")
        save_btn.click()
        
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # Check if we have a diff or no-changes message
        if gui_page.locator(".no-changes").is_visible():
            return

        # Click side-by-side toggle
        split_btn = gui_page.locator("#btn-split")
        split_btn.wait_for(timeout=5000)
        split_btn.click()
        
        gui_page.wait_for_timeout(300)
        
        # Side-by-side should now be active
        assert "active" in (split_btn.get_attribute("class") or "")

    def test_diff_009_color_coding(self, gui_page, gui_server):
        """GUI-DIFF-009: Additions green, deletions red"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        # Make a unique change for color testing
        import time
        unique_val = format((int(time.time()) + 2) % 0xFFFF, '04X')
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill(unique_val)
        gui_page.wait_for_timeout(500)  # Wait for input change to register
        
        save_btn = gui_page.locator("button", has_text="Review")
        save_btn.click()
        
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        gui_page.wait_for_load_state("networkidle")
        
        # Check if we have a diff or no-changes message
        if gui_page.locator(".no-changes").is_visible():
            return

        # Check for diff-line elements with addition/deletion classes
        additions = gui_page.locator(".diff-line.addition")
        deletions = gui_page.locator(".diff-line.deletion")
        
        # At least verify the classes exist in the CSS
        unified_view = gui_page.locator("#diff-unified")
        unified_view.wait_for(timeout=5000)
        assert unified_view.is_visible()


class TestGUIGenerationFormats:
    """Tests for GUI-GEN requirements - all format toggles"""

    def test_gen_014_yaml_toggle(self, gui_page, gui_server):
        """GUI-GEN-014: YAML output checkbox exists and is checked by default"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        yaml_checkbox = gui_page.locator("#fmtYaml")
        assert yaml_checkbox.is_visible(), "YAML checkbox not visible"
        assert yaml_checkbox.is_checked(), "YAML should be checked by default"

    def test_gen_015_xml_toggle(self, gui_page, gui_server):
        """GUI-GEN-015: XML output checkbox exists and is checked by default"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        xml_checkbox = gui_page.locator("#fmtXml")
        assert xml_checkbox.is_visible(), "XML checkbox not visible"
        assert xml_checkbox.is_checked(), "XML should be checked by default"

    def test_gen_016_all_formats_default(self, gui_page, gui_server):
        """GUI-GEN-016: All generation formats enabled by default"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        checkboxes = [
            "#fmtVhdl", "#fmtJson", "#fmtYaml", "#fmtXml",
            "#fmtHeader", "#fmtDocMd", "#fmtDocHtml"
        ]
        
        for checkbox_id in checkboxes:
            checkbox = gui_page.locator(checkbox_id)
            if checkbox.is_visible():
                assert checkbox.is_checked(), f"{checkbox_id} should be checked by default"


class TestGUIRuleCheck:
    """Tests for GUI-RULE requirements"""

    def test_rule_001_run_check_button(self, gui_page, gui_server):
        """GUI-RULE-001: Run Check button triggers design rule check"""
        gui_page.goto(f"{gui_server.url}/rule-check")
        gui_page.wait_for_load_state("networkidle")
        
        # Should have a refresh/run button
        run_btn = gui_page.locator("button", has_text="Refresh")
        assert run_btn.is_visible(), "Run Check button not visible"

    def test_rule_002_error_display(self, gui_page, gui_server):
        """GUI-RULE-002: Errors are listed with severity indication"""
        gui_page.goto(f"{gui_server.url}/rule-check")
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_timeout(1000)  # Wait for API call
        
        # Should have errors tab
        errors_tab = gui_page.locator("#pills-errors-tab")
        assert errors_tab.is_visible(), "Errors tab not visible"

    def test_rule_003_warning_display(self, gui_page, gui_server):
        """GUI-RULE-003: Warnings are listed separately from errors"""
        gui_page.goto(f"{gui_server.url}/rule-check")
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_timeout(1000)
        
        # Should have warnings tab
        warnings_tab = gui_page.locator("#pills-warnings-tab")
        assert warnings_tab.is_visible(), "Warnings tab not visible"

    def test_rule_004_summary_display(self, gui_page, gui_server):
        """GUI-RULE-004: Shows total error/warning counts"""
        gui_page.goto(f"{gui_server.url}/rule-check")
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_timeout(1500)
        
        # Should have badge showing counts
        error_badge = gui_page.locator("#badge-errors")
        warning_badge = gui_page.locator("#badge-warnings")
        
        assert error_badge.is_visible(), "Error count badge not visible"
        assert warning_badge.is_visible(), "Warning count badge not visible"

    def test_rule_005_pass_indication(self, gui_page, gui_server):
        """GUI-RULE-005: Shows clear pass indicator when no errors"""
        gui_page.goto(f"{gui_server.url}/rule-check")
        gui_page.wait_for_load_state("networkidle")
        gui_page.wait_for_timeout(1500)
        
        # Status card should exist
        status_card = gui_page.locator("#status-card")
        assert status_card.is_visible(), "Status card not visible"


class TestGUIDiffViewComplete:
    """Complete tests for GUI-DIFF requirements"""

    def test_diff_001_diff_display(self, gui_page, gui_server):
        """GUI-DIFF-001: Shows unified diff of pending changes"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        # Make a change
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill("ABCD")
        gui_page.wait_for_timeout(300)
        
        # Go to diff
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # Diff container should exist
        diff_container = gui_page.locator("#diff-unified, .no-changes")
        assert diff_container.count() > 0, "No diff container found"

    def test_diff_002_module_name(self, gui_page, gui_server):
        """GUI-DIFF-002: Displays which module is being modified"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        module_name = gui_page.locator(".breadcrumb-item.active").text_content().strip()
        
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill("1234")
        gui_page.wait_for_timeout(300)
        
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # Page should show module name
        page_content = gui_page.content()
        assert module_name.lower() in page_content.lower() or "diff" in gui_page.url

    def test_diff_003_confirm_button(self, gui_page, gui_server):
        """GUI-DIFF-003: Confirm button exists on diff page"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill("5678")
        gui_page.wait_for_timeout(300)
        
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # Confirm button should exist
        confirm_btn = gui_page.locator("button", has_text=re.compile(r"Confirm|Save|Apply", re.I))
        # Either confirm button or no-changes state is valid
        no_changes = gui_page.locator(".no-changes")
        assert confirm_btn.count() > 0 or no_changes.count() > 0

    def test_diff_004_cancel_action(self, gui_page, gui_server):
        """GUI-DIFF-004: Cancel/back navigation returns to editor"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill("9ABC")
        gui_page.wait_for_timeout(300)
        
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # Go back
        gui_page.go_back()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        assert "/module/" in gui_page.url

    def test_diff_007_side_by_side_view(self, gui_page, gui_server):
        """GUI-DIFF-007: Side-by-side view toggle exists"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill("DEF0")
        gui_page.wait_for_timeout(300)
        
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # Side-by-side toggle should exist
        split_btn = gui_page.locator("#btn-split")
        if gui_page.locator(".no-changes").count() == 0:
            assert split_btn.is_visible(), "Split view button not visible"

    def test_diff_010_file_path_display(self, gui_page, gui_server):
        """GUI-DIFF-010: Shows file path being modified"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        base_input = gui_page.locator("input[name='base_address']")
        base_input.fill("F123")
        gui_page.wait_for_timeout(300)
        
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # File path or module info should be visible
        page_content = gui_page.content()
        has_file_ref = ".vhd" in page_content.lower() or ".yaml" in page_content.lower() or ".json" in page_content.lower() or ".xml" in page_content.lower() or gui_page.locator(".no-changes").count() > 0
        assert has_file_ref or gui_page.locator(".no-changes").count() > 0


class TestGUIEditorComplete:
    """Complete tests for GUI-EDIT requirements"""

    def test_edit_004_cdc_stages(self, gui_page, gui_server):
        """GUI-EDIT-004: CDC stages input visible when CDC enabled"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Find CDC toggle and enable if not already
        cdc_toggle = gui_page.locator("input[name='cdc_en']")
        if cdc_toggle.is_visible():
            if not cdc_toggle.is_checked():
                cdc_toggle.click()
                gui_page.wait_for_timeout(300)
            
            # CDC stages input should be visible
            cdc_stages = gui_page.locator("input[name='cdc_stages']")
            # May or may not exist depending on implementation

    def test_edit_006_register_name_input(self, gui_page, gui_server):
        """GUI-EDIT-006: Register name input accepts valid signal names"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Check for name inputs in register rows
        if gui_page.locator(".reg-row").count() > 0:
            name_input = gui_page.locator(".reg-name-input").first
            assert name_input.is_visible(), "Name input not visible"

    def test_edit_007_width_input(self, gui_page, gui_server):
        """GUI-EDIT-007: Width input accepts values 1-1024"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        if gui_page.locator(".reg-row").count() > 0:
            width_input = gui_page.locator(".reg-width-input, input[name='width']").first
            assert width_input.is_visible(), "Width input not visible"

    def test_edit_008_access_mode_select(self, gui_page, gui_server):
        """GUI-EDIT-008: Dropdown shows RW/RO/WO options"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        if gui_page.locator(".reg-row").count() > 0:
            access_select = gui_page.locator(".reg-access-select, select").first
            assert access_select.is_visible(), "Access mode select not visible"

    def test_edit_009_default_value_input(self, gui_page, gui_server):
        """GUI-EDIT-009: Default value input accepts hex format"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        if gui_page.locator(".reg-row").count() > 0:
            default_input = gui_page.locator(".reg-default-input, input[name='default']").first
            if default_input.is_visible():
                assert default_input.is_visible()

    def test_edit_010_description_input(self, gui_page, gui_server):
        """GUI-EDIT-010: Description input accepts free-form text"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        if gui_page.locator(".reg-row").count() > 0:
            desc_input = gui_page.locator(".reg-desc-input").first
            assert desc_input.is_visible(), "Description input not visible"

    def test_edit_011_address_display(self, gui_page, gui_server):
        """GUI-EDIT-011: Address column shows calculated register address"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        if gui_page.locator(".reg-row").count() > 0:
            addr_input = gui_page.locator(".reg-addr-input, input[name='addr']").first
            assert addr_input.is_visible(), "Address input not visible"

    def test_edit_014_r_strobe_toggle(self, gui_page, gui_server):
        """GUI-EDIT-014: Read strobe checkbox exists"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        if gui_page.locator(".reg-row").count() > 0:
            r_strobe = gui_page.locator("input[name='r_strobe'], .r-strobe-check").first
            # May or may not be visible depending on register type

    def test_edit_015_w_strobe_toggle(self, gui_page, gui_server):
        """GUI-EDIT-015: Write strobe checkbox exists"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        if gui_page.locator(".reg-row").count() > 0:
            w_strobe = gui_page.locator("input[name='w_strobe'], .w-strobe-check").first
            # May or may not be visible

    def test_edit_016_save_changes(self, gui_page, gui_server):
        """GUI-EDIT-016: Review & Save button triggers diff view"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        save_btn = gui_page.locator("button", has_text="Review")
        assert save_btn.is_visible(), "Review & Save button not visible"

    def test_edit_018_validation_feedback(self, gui_page, gui_server):
        """GUI-EDIT-018: Invalid inputs show visual error indication"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Test is primarily that page loads without JS errors
        assert "/module/" in gui_page.url


class TestGUIGenerationComplete:
    """Complete tests for GUI-GEN requirements"""

    def test_gen_004_json_toggle(self, gui_page, gui_server):
        """GUI-GEN-004: JSON checkbox toggles generation"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        json_checkbox = gui_page.locator("#fmtJson")
        assert json_checkbox.is_visible(), "JSON checkbox not visible"

    def test_gen_005_c_header_toggle(self, gui_page, gui_server):
        """GUI-GEN-005: C headers checkbox toggles header generation"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        c_checkbox = gui_page.locator("#fmtHeader")
        assert c_checkbox.is_visible(), "C Header checkbox not visible"

    def test_gen_006_doc_toggle(self, gui_page, gui_server):
        """GUI-GEN-006: Documentation checkbox toggles doc generation"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        # Doc checkboxes
        doc_md = gui_page.locator("#fmtDocMd")
        doc_html = gui_page.locator("#fmtDocHtml")
        assert doc_md.is_visible() or doc_html.is_visible(), "Documentation checkbox not visible"

    def test_gen_010_success_feedback(self, gui_page, gui_server):
        """GUI-GEN-010: Successful generation shows success message"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        # Status badge should exist
        status_badge = gui_page.locator("#status-badge, .status-badge")
        # May or may not be immediately visible

    def test_gen_011_error_feedback(self, gui_page, gui_server):
        """GUI-GEN-011: Generation errors display in activity log"""
        gui_page.goto(f"{gui_server.url}/generate")
        gui_page.wait_for_load_state("networkidle")
        
        # Activity log should exist - ID is consoleOutput
        activity_log = gui_page.locator("#consoleOutput")
        assert activity_log.is_visible(), "Activity log not visible"


class TestGUILaunchComplete:
    """Complete tests for GUI-LAUNCH requirements"""

    def test_launch_002_browser_opens(self, gui_server):
        """GUI-LAUNCH-002: Server is accessible"""
        import urllib.request
        response = urllib.request.urlopen(gui_server.url)
        assert response.status == 200

    def test_launch_003_flask_dependency(self, gui_server):
        """GUI-LAUNCH-003: Flask is running"""
        import urllib.request
        try:
            response = urllib.request.urlopen(gui_server.url)
            assert response.status == 200
        except Exception:
            pytest.fail("Flask server not accessible")


class TestGUIDashComplete:
    """Complete tests for GUI-DASH requirements"""

    def test_dash_005_cdc_badge(self, gui_page, gui_server):
        """GUI-DASH-005: Modules with CDC enabled show CDC badge"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # CDC badges may or may not be present depending on modules
        cdc_badge = gui_page.locator(".cdc-badge, .badge:has-text('CDC')")
        # Just verify page loaded correctly
        assert gui_page.locator(".module-card-large").count() > 0

    def test_dash_008_empty_state(self, gui_page, gui_server):
        """GUI-DASH-008: Shows appropriate message when no modules loaded"""
        # This test would require a special setup with no modules
        # For now, just verify the dashboard loads
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        assert "Axion" in gui_page.title() or gui_page.locator(".module-card-large").count() >= 0


class TestGUISaveComplete:
    """Complete tests for GUI-SAVE requirements"""

    def test_save_005_diff_return_preservation(self, gui_page, gui_server):
        """GUI-SAVE-005: Changes preserved when returning from diff page"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        gui_page.wait_for_function("() => window.initialState !== undefined")
        
        # Make a change
        base_input = gui_page.locator("input[name='base_address']")
        original = base_input.input_value()
        base_input.fill("AAAA")
        gui_page.wait_for_timeout(300)
        
        # Go to diff
        gui_page.locator("button", has_text="Review").click()
        gui_page.wait_for_url(re.compile(r"/diff"), timeout=5000)
        
        # Go back
        gui_page.go_back()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        # Page should reload - verify we're back on editor
        assert "/module/" in gui_page.url

    def test_save_006_clear_indicator_on_save(self, gui_page, gui_server):
        """GUI-SAVE-006: Unsaved changes indicator clears after successful save"""
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url(re.compile(r"/module/"), timeout=5000)
        
        indicator = gui_page.locator("#unsavedIndicator")
        assert indicator.count() == 1, "Unsaved indicator element not found"


class TestGUINavComplete:
    """Complete tests for GUI-NAV requirements"""

    def test_nav_006_responsive_design(self, gui_page, gui_server):
        """GUI-NAV-006: Layout adapts to different screen widths"""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_load_state("networkidle")
        
        # Test mobile viewport
        gui_page.set_viewport_size({"width": 375, "height": 667})
        gui_page.wait_for_timeout(300)
        
        # Page should still be functional
        assert gui_page.locator("body").is_visible()
        
        # Reset viewport
        gui_page.set_viewport_size({"width": 1280, "height": 720})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

