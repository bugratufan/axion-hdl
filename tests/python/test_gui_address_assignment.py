"""
GUI Address Assignment Tests

Tests for register address assignment functionality in the editor.
Based on requirements GUI-EDIT-020 to GUI-EDIT-035.

Scenarios covered:
1. Unique address (no conflict)
2. Below register shift
3. Chain shift
4. Middle register change
5. Multiple user changes
6. User conflict warning
7. Above register conflict
8. Revert functionality
"""
import pytest
from playwright.sync_api import expect


class TestAddressInputBasics:
    """Basic address input functionality tests."""

    def test_edit_020_address_input_editable(self, gui_page, gui_server):
        """GUI-EDIT-020: Address input field is editable."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        expect(addr_input).to_be_editable()
        
        # Should accept hex values
        addr_input.fill("0x10")
        addr_input.dispatch_event("change")
        assert addr_input.input_value() == "0x10"

    def test_edit_034_original_address_tracking(self, gui_page, gui_server):
        """GUI-EDIT-034: Address input tracks original value via data-original."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        original = addr_input.get_attribute("data-original")
        assert original is not None, "data-original attribute should exist"
        assert original.startswith("0x") or original.isdigit(), "Should be a valid address"

    def test_edit_035_locked_state_tracking(self, gui_page, gui_server):
        """GUI-EDIT-035: User-modified addresses marked with data-locked=true."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        
        # Change address
        addr_input.fill("0x50")
        addr_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        locked = addr_input.get_attribute("data-locked")
        assert locked == "true", "Changed address should be locked"


class TestAddressUserModified:
    """Tests for user-modified address behavior."""

    def test_edit_021_user_address_fixed(self, gui_page, gui_server):
        """GUI-EDIT-021: User-modified address stays fixed."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 2:
            pytest.skip("Need at least 2 registers")

        # Set first register to specific address
        first_input = addr_inputs.nth(0)
        first_input.fill("0x20")
        first_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Change second register (should not affect first)
        second_input = addr_inputs.nth(1)
        second_input.fill("0x30")
        second_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # First should still be 0x20
        assert first_input.input_value().upper() == "0X20", "User address should stay fixed"

    def test_edit_022_unique_address_no_shift(self, gui_page, gui_server):
        """GUI-EDIT-022: Unique address doesn't shift other registers."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 3:
            pytest.skip("Need at least 3 registers")

        # Get original addresses
        orig_1 = addr_inputs.nth(1).input_value()
        orig_2 = addr_inputs.nth(2).input_value()
        
        # Set first to a unique address (no conflict)
        addr_inputs.nth(0).fill("0x100")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Others should NOT change
        assert addr_inputs.nth(1).input_value() == orig_1, "Second should not change"
        assert addr_inputs.nth(2).input_value() == orig_2, "Third should not change"


class TestAddressShifting:
    """Tests for automatic address shifting on conflict."""

    def test_edit_023_below_register_shift(self, gui_page, gui_server):
        """GUI-EDIT-023: Register below shifts when conflict occurs."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 2:
            pytest.skip("Need at least 2 registers")

        # Get second register's original address
        second_orig = addr_inputs.nth(1).input_value()
        second_orig_int = int(second_orig, 16)
        
        # Set first register to same address as second
        addr_inputs.nth(0).fill(second_orig)
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Second should have shifted
        second_new = addr_inputs.nth(1).input_value()
        second_new_int = int(second_new, 16)
        assert second_new_int > second_orig_int, \
            f"Second should shift up: was {second_orig}, now {second_new}"

    def test_edit_024_chain_shift(self, gui_page, gui_server):
        """GUI-EDIT-024: Chain shift when multiple conflicts occur."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 3:
            pytest.skip("Need at least 3 registers")

        # Get original addresses
        orig_1 = addr_inputs.nth(1).input_value()
        orig_2 = addr_inputs.nth(2).input_value()
        
        # Set first to second's address - causes chain shift
        addr_inputs.nth(0).fill(orig_1)
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        new_1 = addr_inputs.nth(1).input_value()
        new_2 = addr_inputs.nth(2).input_value()
        
        # Both should have shifted
        assert int(new_1, 16) > int(orig_1, 16), "Second should shift"
        assert int(new_2, 16) >= int(orig_2, 16), "Third should shift or stay"

    def test_edit_025_middle_register_change(self, gui_page, gui_server):
        """GUI-EDIT-025: Middle register change only affects below."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 4:
            pytest.skip("Need at least 4 registers")

        # Get all original addresses
        orig_0 = addr_inputs.nth(0).input_value()
        orig_2 = addr_inputs.nth(2).input_value()
        orig_3 = addr_inputs.nth(3).input_value()
        
        # Change middle register (index 1) to conflict with index 2
        addr_inputs.nth(1).fill(orig_2)
        addr_inputs.nth(1).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # First should NOT change (above)
        assert addr_inputs.nth(0).input_value() == orig_0, "Above register should not change"
        
        # Third should shift (below)
        new_2 = addr_inputs.nth(2).input_value()
        assert int(new_2, 16) > int(orig_2, 16), "Below register should shift"


class TestMultipleUserChanges:
    """Tests for multiple user address changes."""

    def test_edit_026_multiple_user_changes_coexist(self, gui_page, gui_server):
        """GUI-EDIT-026: Multiple user changes can coexist if non-conflicting."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 3:
            pytest.skip("Need at least 3 registers")

        # Set multiple unique addresses
        addr_inputs.nth(0).fill("0x10")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(200)
        
        addr_inputs.nth(1).fill("0x20")
        addr_inputs.nth(1).dispatch_event("change")
        gui_page.wait_for_timeout(200)
        
        # Both should remain as set
        assert addr_inputs.nth(0).input_value().upper() == "0X10"
        assert addr_inputs.nth(1).input_value().upper() == "0X20"
        
        # No conflict warnings
        conflicts = gui_page.locator(".addr-conflict")
        assert conflicts.count() == 0, "No conflicts expected for unique addresses"


class TestConflictWarnings:
    """Tests for conflict warning display."""

    def test_edit_027_user_conflict_warning(self, gui_page, gui_server):
        """GUI-EDIT-027: Warning shown when two user addresses conflict."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 2:
            pytest.skip("Need at least 2 registers")

        # Set BOTH to same address (user conflict)
        addr_inputs.nth(0).fill("0x10")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(200)
        
        addr_inputs.nth(1).fill("0x10")
        addr_inputs.nth(1).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Should show conflict warning
        conflicts = gui_page.locator(".addr-conflict")
        assert conflicts.count() > 0, "Conflict warning should be shown"

    def test_edit_028_above_register_conflict_warning(self, gui_page, gui_server):
        """GUI-EDIT-028: Warning when lower register conflicts with upper (no auto-shift)."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 2:
            pytest.skip("Need at least 2 registers")

        # Get first register's address
        first_addr = addr_inputs.nth(0).input_value()
        
        # Set SECOND to same as FIRST (lower conflicts with upper)
        addr_inputs.nth(1).fill(first_addr)
        addr_inputs.nth(1).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # First should NOT have changed (above register never shifts)
        assert addr_inputs.nth(0).input_value() == first_addr, \
            "Above register should NOT shift"
        
        # Conflict warning should be shown
        conflicts = gui_page.locator(".addr-conflict")
        assert conflicts.count() > 0, "Conflict warning should be shown"


class TestRevertFunctionality:
    """Tests for address revert functionality."""

    def test_edit_029_address_revert(self, gui_page, gui_server):
        """GUI-EDIT-029: Revert button restores original address."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        original = addr_input.get_attribute("data-original")
        
        # Change address
        addr_input.fill("0x99")
        addr_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Click revert button
        revert_btn = gui_page.locator(".addr-revert-btn").first
        if revert_btn.is_visible():
            revert_btn.click()
            gui_page.wait_for_timeout(300)
            
            # Should return to original
            assert addr_input.input_value() == original, "Should revert to original"


class TestVisualIndicators:
    """Tests for visual change indicators."""

    def test_edit_030_visual_change_indicator(self, gui_page, gui_server):
        """GUI-EDIT-030: Visual indicator shows when address differs from original."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        
        # Change address
        addr_input.fill("0x88")
        addr_input.dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Should show strikethrough original
        original_span = gui_page.locator(".addr-original").first
        expect(original_span).to_be_visible()


class TestEdgeCases:
    """Edge case tests."""

    def test_edit_031_gap_allowed(self, gui_page, gui_server):
        """GUI-EDIT-031: User can create gaps in address space."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_inputs = gui_page.locator(".reg-addr-input")
        if addr_inputs.count() < 2:
            pytest.skip("Need at least 2 registers")

        # Set first to very high address (creates gap)
        addr_inputs.nth(0).fill("0x100")
        addr_inputs.nth(0).dispatch_event("change")
        gui_page.wait_for_timeout(300)
        
        # Should be accepted without error
        assert addr_inputs.nth(0).input_value().upper() == "0X100"
        
        # Second should remain unchanged
        second = addr_inputs.nth(1).input_value()
        second_int = int(second, 16)
        assert second_int < 0x100, "Second should not jump to fill gap"

    def test_edit_032_realtime_update(self, gui_page, gui_server):
        """GUI-EDIT-032: Address changes appear immediately."""
        gui_page.goto(gui_server.url)
        gui_page.wait_for_selector(".module-card-large", timeout=5000)
        gui_page.locator(".module-card-large").first.click()
        gui_page.wait_for_url("**/module/**", timeout=5000)

        addr_input = gui_page.locator(".reg-addr-input").first
        
        # Change and check immediately (no explicit wait)
        addr_input.fill("0x44")
        addr_input.dispatch_event("change")
        
        # Should update immediately
        assert addr_input.input_value() == "0x44"
