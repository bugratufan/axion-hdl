# Axion-HDL GUI Requirements

This document tracks all functional and non-functional requirements for the Axion-HDL Interactive GUI.
Testing is automated via Playwright browser tests mapped back to these requirement IDs.

## Requirement Categories

| Prefix | Category | Definition |
|--------|----------|------------|
| **GUI-LAUNCH** | Server Launch | GUI server startup and browser opening |
| **GUI-DASH** | Dashboard | Module listing and summary display |
| **GUI-EDIT** | Editor | Register editing functionality |
| **GUI-GEN** | Generation | Output generation interface |
| **GUI-RULE** | Rule Check | Design rule checking interface |
| **GUI-DIFF** | Diff/Review | Change preview and confirmation |

---

## 1. Server Launch (GUI-LAUNCH)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GUI-LAUNCH-001 | Start Web Server | `axion-hdl --gui` starts Flask server on port 5000. | Playwright (`gui.test_launch_001`) |
| GUI-LAUNCH-002 | Auto-Open Browser | Browser opens automatically to dashboard URL. | Playwright (`gui.test_launch_002`) |
| GUI-LAUNCH-003 | Flask Dependency Check | Missing Flask shows clear install instructions. | Python Unit Test (`gui.test_launch_003`) |
| GUI-LAUNCH-004 | Port Configuration | Server uses default port 5000, configurable via code. | Playwright (`gui.test_launch_004`) |

---

## 2. Dashboard (GUI-DASH)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GUI-DASH-001 | Module List Display | Dashboard lists all parsed modules with names. | Playwright (`gui.test_dash_001`) |
| GUI-DASH-002 | Module Count | Dashboard shows total module count. | Playwright (`gui.test_dash_002`) |
| GUI-DASH-003 | Register Count | Dashboard shows total register count across all modules. | Playwright (`gui.test_dash_003`) |
| GUI-DASH-004 | Module Card Info | Each module card shows base address, register count, source file. | Playwright (`gui.test_dash_004`) |
| GUI-DASH-005 | CDC Badge | Modules with CDC enabled show CDC badge. | Playwright (`gui.test_dash_005`) |
| GUI-DASH-006 | Register Preview | Module card shows up to 5 registers preview. | Playwright (`gui.test_dash_006`) |
| GUI-DASH-007 | Module Navigation | Clicking module card opens editor page. | Playwright (`gui.test_dash_007`) |
| GUI-DASH-008 | Empty State | Shows appropriate message when no modules loaded. | Playwright (`gui.test_dash_008`) |
| GUI-DASH-009 | Statistics Cards | Dashboard shows summary cards for modules, registers, CDC count, and sources. | Playwright (`gui.test_dash_009`) |
| GUI-DASH-010 | CDC Count Display | Dashboard statistics show count of CDC-enabled modules. | Playwright (`gui.test_dash_010`) |


---

## 3. Module Editor (GUI-EDIT)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GUI-EDIT-001 | Breadcrumb Navigation | Editor shows breadcrumb: Dashboard > Module Name. | Playwright (`gui.test_edit_001`) |
| GUI-EDIT-002 | Base Address Edit | Base address input accepts hex values. | Playwright (`gui.test_edit_002`) |
| GUI-EDIT-003 | CDC Toggle | CDC enable/disable switch works correctly. | Playwright (`gui.test_edit_003`) |
| GUI-EDIT-004 | CDC Stages | CDC stages input (2-5) visible when CDC enabled. | Playwright (`gui.test_edit_004`) |
| GUI-EDIT-005 | Register Table Display | Register table shows all columns: Name, Width, Access, Default, Description, Address, Action. | Playwright (`gui.test_edit_005`) |
| GUI-EDIT-006 | Register Name Edit | Register name input accepts valid signal names. | Playwright (`gui.test_edit_006`) |
| GUI-EDIT-007 | Width Edit | Width input accepts values 1-1024. | Playwright (`gui.test_edit_007`) |
| GUI-EDIT-008 | Access Mode Select | Dropdown shows RW/RO/WO options with color coding. | Playwright (`gui.test_edit_008`) |
| GUI-EDIT-009 | Default Value Edit | Default value input accepts hex format (0x...). | Playwright (`gui.test_edit_009`) |
| GUI-EDIT-010 | Description Edit | Description input accepts free-form text. | Playwright (`gui.test_edit_010`) |
| GUI-EDIT-011 | Address Display | Address column shows calculated register address. | Playwright (`gui.test_edit_011`) |
| GUI-EDIT-012 | Add Register | New Register button adds blank row to table. | Playwright (`gui.test_edit_012`) |
| GUI-EDIT-013 | Delete Register | Delete button removes register with confirmation. | Playwright (`gui.test_edit_013`) |
| GUI-EDIT-014 | R_STROBE Toggle | Read strobe checkbox enables/disables R_STROBE generation. | Playwright (`gui.test_edit_014`) |
| GUI-EDIT-015 | W_STROBE Toggle | Write strobe checkbox enables/disables W_STROBE generation. | Playwright (`gui.test_edit_015`) |
| GUI-EDIT-016 | Save Changes | Review & Save button triggers diff view. | Playwright (`gui.test_edit_016`) |
| GUI-EDIT-017 | Empty State | Shows empty state message when no registers. | Playwright (`gui.test_edit_017`) |
| GUI-EDIT-018 | Validation Feedback | Invalid inputs show visual error indication. | Playwright (`gui.test_edit_018`) |
| GUI-EDIT-019 | Duplicate Register | Duplicate button creates copy of register row. | Playwright (`gui.test_edit_019`) |

---

## 4. Output Generation (GUI-GEN)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GUI-GEN-001 | Output Directory | Output directory input shows default path. | Playwright (`gui.test_gen_001`) |
| GUI-GEN-002 | Browse Folder | Browse button opens folder selection dialog. | Playwright (`gui.test_gen_002`) |
| GUI-GEN-003 | VHDL Format Toggle | VHDL modules checkbox toggles VHDL generation. | Playwright (`gui.test_gen_003`) |
| GUI-GEN-004 | JSON Format Toggle | JSON map checkbox toggles JSON generation. | Playwright (`gui.test_gen_004`) |
| GUI-GEN-005 | C Header Toggle | C headers checkbox toggles header generation. | Playwright (`gui.test_gen_005`) |
| GUI-GEN-006 | Documentation Toggle | Documentation checkbox toggles doc generation. | Playwright (`gui.test_gen_006`) |
| GUI-GEN-007 | Generate Button | Generate Files button triggers generation process. | Playwright (`gui.test_gen_007`) |
| GUI-GEN-008 | Activity Log | Live activity log shows generation progress. | Playwright (`gui.test_gen_008`) |
| GUI-GEN-009 | Status Badge | Status badge shows Idle/Running/Success/Error states. | Playwright (`gui.test_gen_009`) |
| GUI-GEN-010 | Success Feedback | Successful generation shows success message. | Playwright (`gui.test_gen_010`) |
| GUI-GEN-011 | Error Feedback | Generation errors display in activity log. | Playwright (`gui.test_gen_011`) |
| GUI-GEN-012 | Markdown Doc Toggle | Markdown docs checkbox toggles Markdown generation, enabled by default. | Playwright (`gui.test_gen_012`) |
| GUI-GEN-013 | HTML Doc Toggle | HTML docs checkbox toggles HTML generation, enabled by default. | Playwright (`gui.test_gen_013`) |

---

## 5. Rule Check (GUI-RULE)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GUI-RULE-001 | Run Check Button | Triggers design rule check execution. | Playwright (`gui.test_rule_001`) |
| GUI-RULE-002 | Error Display | Errors are listed with severity indication. | Playwright (`gui.test_rule_002`) |
| GUI-RULE-003 | Warning Display | Warnings are listed separately from errors. | Playwright (`gui.test_rule_003`) |
| GUI-RULE-004 | Summary Display | Shows total error/warning counts. | Playwright (`gui.test_rule_004`) |
| GUI-RULE-005 | Pass Indication | Shows clear pass indicator when no errors. | Playwright (`gui.test_rule_005`) |

---

## 6. Diff & Review (GUI-DIFF)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GUI-DIFF-001 | Diff Display | Shows unified diff of pending changes. | Playwright (`gui.test_diff_001`) |
| GUI-DIFF-002 | Module Name | Displays which module is being modified. | Playwright (`gui.test_diff_002`) |
| GUI-DIFF-003 | Confirm Button | Confirm button applies changes to source files. | Playwright (`gui.test_diff_003`) |
| GUI-DIFF-004 | Cancel Action | Cancel/back navigation returns to editor. | Playwright (`gui.test_diff_004`) |
| GUI-DIFF-005 | Success Redirect | Successful save redirects to dashboard. | Playwright (`gui.test_diff_005`) |

---

## 7. Navigation & Layout (GUI-NAV)

| ID | Definition | Acceptance Criteria | Test Method |
|----|------------|---------------------|-------------|
| GUI-NAV-001 | Navbar Brand | Navbar shows Axion-HDL GUI branding. | Playwright (`gui.test_nav_001`) |
| GUI-NAV-002 | Modules Link | Modules link navigates to dashboard. | Playwright (`gui.test_nav_002`) |
| GUI-NAV-003 | Rule Check Link | Rule Check link navigates to rule check page. | Playwright (`gui.test_nav_003`) |
| GUI-NAV-004 | Generate Link | Generate link navigates to generation page. | Playwright (`gui.test_nav_004`) |
| GUI-NAV-005 | Footer Version | Footer displays correct version. | Playwright (`gui.test_nav_005`) |
| GUI-NAV-006 | Responsive Design | Layout adapts to different screen widths. | Playwright (`gui.test_nav_006`) |
