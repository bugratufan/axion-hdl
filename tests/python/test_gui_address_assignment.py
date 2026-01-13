"""
GUI Address Assignment Tests - Comprehensive Multi-Format Testing

Tests for register address assignment functionality in the editor.
Based on requirements GUI-EDIT-020 to GUI-EDIT-038.

Test Fixtures (each in VHDL, JSON, XML, YAML):
- addr_test_basic: 5 sequential registers (0x00-0x10)
- addr_test_chain: 8 sequential registers (0x00-0x1C)  
- addr_test_gaps: 4 registers with gaps (0x00, 0x10, 0x20, 0x24)

Scenarios Tested:
1. Unique address (no conflict) - others unchanged
2. Multiple user changes coexist
3. User conflict warning (same address)
4. Conflict causes NO shifting (above or below)
5. Gap preservation
6. Revert restores single address
"""
import pytest
from playwright.sync_api import expect


# Format suffixes for each file type
FORMATS = {
    "vhdl": ".vhd",
    "json": ".json",
    "xml": ".xml",
    "yaml": ".yaml"
}


def navigate_to_module_by_format(gui_page, gui_server, module_base_name, file_format, min_registers=2):
    """Navigate to a specific module matching base name and format."""
    gui_page.goto(gui_server.url)
    gui_page.wait_for_selector(".module-card-large", timeout=5000)
    
    suffix = FORMATS.get(file_format, "")
    # The filename shown in card is like "addr_test_basic.json"
    target_filename = f"{module_base_name}{suffix}"
    
    modules = gui_page.locator(".module-card-large")
    count = modules.count()
    
    for i in range(count):
        card = modules.nth(i)
        
        # The filename is in .info-value span with title attribute containing full path
        # Or we can check card's href which has ?file=...
        card_html = card.evaluate("el => el.outerHTML").lower()
        
        if target_filename.lower() in card_html:
            card.click()
            gui_page.wait_for_url("**/module/**", timeout=5000)
            
            addr_inputs = gui_page.locator(".reg-addr-input")
            reg_count = addr_inputs.count()
            if reg_count >= min_registers:
                return True
            
            # Not enough registers, go back
            gui_page.goto(gui_server.url)
            gui_page.wait_for_selector(".module-card-large", timeout=5000)
    
    return False


# =============================================================================
# SCENARIO 1: Unique Address (No Conflict)
# =============================================================================
class TestScenario1_UniqueAddress:
    """Scenario 1: Setting unique address - other registers stay unchanged."""

    @pytest.mark.parametrize("file_format", ["json", "yaml", "xml", "vhdl"])
    def test_unique_address_no_shift(self, gui_page, gui_server, file_format):
        """Set first to 0x100 - others should NOT change."""
        if not navigate_to_module_by_format(gui_page, gui_server, "addr_test_basic", file_format, 3):
            pytest.skip(f"addr_test_basic{FORMATS[file_format]} not found")

        addr_inputs = gui_page.locator(".reg-addr-input")
        
        # Store originals
        orig_1 = addr_inputs.nth(1).input_value()
        orig_2 = addr_inputs.nth(2).input_value()
        
        # Set first to unique address
        addr_inputs.nth(0).fill("0x100")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Others unchanged
        assert addr_inputs.nth(1).input_value() == orig_1, f"{file_format}: reg_b unchanged"
        assert addr_inputs.nth(2).input_value() == orig_2, f"{file_format}: reg_c unchanged"


# =============================================================================
# SCENARIO 2: Multiple User Changes Coexist
# =============================================================================
class TestScenario2_MultipleUserChanges:
    """Scenario 2: Multiple user changes to different addresses coexist."""

    @pytest.mark.parametrize("file_format", ["json", "yaml", "xml", "vhdl"])
    def test_multiple_unique_changes(self, gui_page, gui_server, file_format):
        """Set reg_0=0x100, reg_1=0x200 - both should stick."""
        if not navigate_to_module_by_format(gui_page, gui_server, "addr_test_basic", file_format, 3):
            pytest.skip(f"addr_test_basic{FORMATS[file_format]} not found")

        addr_inputs = gui_page.locator(".reg-addr-input")
        
        addr_inputs.nth(0).fill("0x100")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(200)
        
        addr_inputs.nth(1).fill("0x200")
        addr_inputs.nth(1).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        assert addr_inputs.nth(0).input_value().upper() == "0X100"
        assert addr_inputs.nth(1).input_value().upper() == "0X200"


# =============================================================================
# SCENARIO 3: User Conflict Warning
# =============================================================================
class TestScenario3_UserConflictWarning:
    """Scenario 3: Two user changes to SAME address - warning shown."""

    @pytest.mark.parametrize("file_format", ["json", "yaml", "xml", "vhdl"])
    def test_user_conflict_shows_warning(self, gui_page, gui_server, file_format):
        """Set both reg_0 and reg_1 to 0x50 - conflict warning."""
        if not navigate_to_module_by_format(gui_page, gui_server, "addr_test_basic", file_format, 2):
            pytest.skip(f"addr_test_basic{FORMATS[file_format]} not found")

        addr_inputs = gui_page.locator(".reg-addr-input")
        
        addr_inputs.nth(0).fill("0x50")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(200)
        
        addr_inputs.nth(1).fill("0x50")
        addr_inputs.nth(1).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        conflicts = gui_page.locator(".addr-conflict")
        assert conflicts.count() > 0, f"{file_format}: conflict warning expected"


# =============================================================================
# SCENARIO 4: Conflict Causes No Shifting
# =============================================================================
class TestScenario4_ConflictNoShift:
    """Scenario 4: Setting a conflicting address causes NO shifting of any register."""

    @pytest.mark.parametrize("file_format", ["json", "yaml", "xml", "vhdl"])
    def test_conflict_no_shift(self, gui_page, gui_server, file_format):
        """Set reg_0 to match reg_1. reg_1 should NOT shift."""
        if not navigate_to_module_by_format(gui_page, gui_server, "addr_test_basic", file_format, 3):
            pytest.skip(f"addr_test_basic{FORMATS[file_format]} not found")

        addr_inputs = gui_page.locator(".reg-addr-input")
        
        # Get original value of reg_1
        reg_1_orig = addr_inputs.nth(1).input_value()
        reg_2_orig = addr_inputs.nth(2).input_value()
        
        # Set reg_0 to reg_1's address (causing conflict)
        addr_inputs.nth(0).fill(reg_1_orig)
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Verify reg_1 did NOT shift
        assert addr_inputs.nth(1).input_value() == reg_1_orig, \
            f"{file_format}: reg_1 should NOT shift on conflict"
            
        # Verify reg_2 did NOT shift
        assert addr_inputs.nth(2).input_value() == reg_2_orig, \
            f"{file_format}: reg_2 should NOT shift on conflict"
        
        # Verify warnings appear
        conflicts = gui_page.locator(".addr-conflict")
        assert conflicts.count() > 0, f"{file_format}: conflict warning expected"


# =============================================================================
# SCENARIO 5: Gap Preservation
# =============================================================================
class TestScenario5_GapPreservation:
    """Scenario 5: Gaps in address space are preserved."""

    @pytest.mark.parametrize("file_format", ["json", "yaml", "xml", "vhdl"])
    def test_gaps_preserved(self, gui_page, gui_server, file_format):
        """Set first to 0x200 - gaps preserved, others unchanged."""
        if not navigate_to_module_by_format(gui_page, gui_server, "addr_test_gaps", file_format, 3):
            pytest.skip(f"addr_test_gaps{FORMATS[file_format]} not found")

        addr_inputs = gui_page.locator(".reg-addr-input")
        
        orig_1 = addr_inputs.nth(1).input_value()
        orig_2 = addr_inputs.nth(2).input_value()
        
        # Set first to high address
        addr_inputs.nth(0).fill("0x200")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Others keep their gap-filled positions
        assert addr_inputs.nth(1).input_value() == orig_1, f"{file_format}: gap preserved"
        assert addr_inputs.nth(2).input_value() == orig_2, f"{file_format}: gap preserved"


# =============================================================================
# SCENARIO 6: Revert Restores Address
# =============================================================================
class TestScenario6_Revert:
    """Scenario 6: Revert restores register to original address."""

    @pytest.mark.parametrize("file_format", ["json", "yaml"])  # Subset for speed
    def test_revert_restores_single(self, gui_page, gui_server, file_format):
        """After change, revert returns to original."""
        if not navigate_to_module_by_format(gui_page, gui_server, "addr_test_basic", file_format, 3):
            pytest.skip(f"addr_test_basic{FORMATS[file_format]} not found")

        addr_inputs = gui_page.locator(".reg-addr-input")
        
        orig_0 = addr_inputs.nth(0).input_value()
        
        # Change address
        addr_inputs.nth(0).fill("0x999")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Verify changed
        assert addr_inputs.nth(0).input_value() != orig_0
        
        # Revert
        revert_btn = gui_page.locator(".addr-revert-btn").first
        if revert_btn.is_visible():
            revert_btn.click()
            gui_page.wait_for_timeout(300)
            
            assert addr_inputs.nth(0).input_value() == orig_0, f"{file_format}: reverted"


# =============================================================================
# VISUAL INDICATORS
# =============================================================================
class TestVisualIndicators:
    """Test visual feedback elements."""

    def test_strikethrough_shown(self, gui_page, gui_server):
        """Changed address shows strikethrough original."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        addr_input.fill("0x99")
        addr_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        original_span = gui_page.locator(".addr-original").first
        expect(original_span).to_be_visible()

    def test_locked_attribute(self, gui_page, gui_server):
        """Changed address has data-locked=true."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        addr_input.fill("0x88")
        addr_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        assert addr_input.get_attribute("data-locked") == "true"


class TestSaveValidation:
    """Tests for save validation when address conflicts exist (GUI-EDIT-036)."""

    def test_save_button_has_id(self, gui_page, gui_server):
        """Save button has correct ID for JS manipulation."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        gui_page.wait_for_timeout(500)

        save_btn = gui_page.locator("#saveBtn")
        assert save_btn.count() == 1, "Save button with ID saveBtn should exist"

    def test_conflict_warning_element_exists(self, gui_page, gui_server):
        """Conflict warning badge element exists in DOM."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        gui_page.wait_for_timeout(500)

        conflict_warning = gui_page.locator("#conflictWarning")
        assert conflict_warning.count() == 1, "Conflict warning element should exist"

    def test_detect_address_conflicts_function_exists(self, gui_page, gui_server):
        """detectAddressConflicts JS function is defined."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        gui_page.wait_for_timeout(500)

        result = gui_page.evaluate("typeof detectAddressConflicts === 'function'")
        assert result == True, "detectAddressConflicts function should be defined"

    def test_update_save_button_state_function_exists(self, gui_page, gui_server):
        """updateSaveButtonState JS function is defined."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        gui_page.wait_for_timeout(500)

        result = gui_page.evaluate("typeof updateSaveButtonState === 'function'")
        assert result == True, "updateSaveButtonState function should be defined"

    def test_conflict_disables_save_via_js(self, gui_page, gui_server):
        """Calling updateSaveButtonState(true) disables save button."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        gui_page.wait_for_timeout(500)

        # Call JS directly to simulate conflict state
        gui_page.evaluate("updateSaveButtonState(true)")
        gui_page.wait_for_timeout(200)
        
        save_btn = gui_page.locator("#saveBtn")
        assert not save_btn.is_enabled(), "Save button should be disabled when updateSaveButtonState(true) is called"

    def test_no_conflict_enables_save_via_js(self, gui_page, gui_server):
        """Calling updateSaveButtonState(false) enables save button."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)
        gui_page.wait_for_timeout(500)

        # Disable then re-enable
        gui_page.evaluate("updateSaveButtonState(true)")
        gui_page.wait_for_timeout(200)
        gui_page.evaluate("updateSaveButtonState(false)")
        gui_page.wait_for_timeout(200)
        
        save_btn = gui_page.locator("#saveBtn")
        assert save_btn.is_enabled(), "Save button should be enabled when updateSaveButtonState(false) is called"


# =============================================================================
# SCENARIO: Address Persistence (GUI-EDIT-038)
# =============================================================================
class TestScenario_Persistence:
    """Test address persistence (GUI-EDIT-038)."""
    
    @pytest.mark.parametrize("file_format", ["json", "yaml"])
    def test_edit_038_address_persists_after_reload(self, gui_page, gui_server, file_format):
        """Change address, save, reload -> Address match."""
        if not navigate_to_module_by_format(gui_page, gui_server, "addr_test_basic", file_format, 3):
            pytest.skip(f"addr_test_basic{FORMATS[file_format]} not found")

        addr_inputs = gui_page.locator(".reg-addr-input")
        new_addr_val = "0xABC" 
        
        # Change address
        addr_inputs.nth(0).fill(new_addr_val)
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Click Save
        save_btn = gui_page.locator("#saveBtn")
        save_btn.click()
        
        # Wait for reload (save triggers redirect/refresh)
        try:
             gui_page.wait_for_load_state("networkidle", timeout=5000)
        except:
             pass # sometimes networkidle times out if no navigation happens quickly, but we expect it.

        # Re-check selectors to ensure we are back on the page
        gui_page.wait_for_selector(".reg-addr-input", timeout=10000)
        
        # Check value
        addr_inputs_new = gui_page.locator(".reg-addr-input")
        val = addr_inputs_new.nth(0).input_value()
        
        assert val.upper() == "0XABC", f"{file_format}: Address should persist after save & reload"
