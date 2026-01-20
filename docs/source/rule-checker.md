# Rule Checker

Axion-HDL includes a comprehensive rule checker that validates register definitions before generation. This helps catch errors early and ensures generated outputs are correct and consistent.

## Running Rule Check

### CLI

```bash
axion-hdl -s ./rtl --rule-check
```

Or combined with analysis:

```bash
axion-hdl -s ./rtl --rule-check --all
```

### GUI

Navigate to the **Rule Check** page and click **Run Rule Check**.

### Python API

```python
from axion_hdl.rule_checker import RuleChecker
from axion_hdl.axion import AxionHDL

axion = AxionHDL()
axion.add_source_path("./rtl")
modules = axion.analyze()

checker = RuleChecker()
results = checker.run_all_checks(modules)

print(checker.generate_report())
```

---

## Check Categories

### Address Overlap Detection

**Type:** `Address Overlap`  
**Severity:** Error

Detects when multiple modules have overlapping address ranges.

**Example Error:**
```
Address region 0x1000-0x1FFF overlaps with timer_module (0x1800-0x1FFF)
```

**Resolution:**
- Change base addresses to non-overlapping ranges
- Ensure each module has unique address space

---

### Address Alignment

**Type:** `Address Alignment`  
**Severity:** Warning

Warns when registers are not 4-byte aligned.

**Example Warning:**
```
Register 'status' (0x03) not 4-byte aligned
```

**Resolution:**
- Use addresses that are multiples of 4 (0x00, 0x04, 0x08, etc.)
- Let Axion auto-assign addresses

---

### Naming Convention

**Type:** `Naming Convention`  
**Severity:** Error

Validates VHDL identifier rules:
- Must start with a letter
- Can contain letters, numbers, underscores
- Cannot contain special characters

**Example Error:**
```
Register '123_status' invalid identifier
```

**Resolution:**
- Rename to valid identifier (e.g., `status_123`)

---

### Reserved Keywords

**Type:** `Reserved Keyword`  
**Severity:** Error

Detects use of VHDL reserved words as names.

**Reserved Words Include:**
`signal`, `entity`, `architecture`, `process`, `begin`, `end`, `if`, `then`, `else`, `case`, `when`, `loop`, `for`, `while`, `function`, `procedure`, `component`, `generic`, `port`, `in`, `out`, `inout`, `buffer`, `and`, `or`, `not`, `xor`, `nand`, `nor`, `xnor`, etc.

**Example Error:**
```
Module name 'signal' is reserved keyword
```

**Resolution:**
- Rename to non-reserved identifier

---

### Style Guide

**Type:** `Style Guide`  
**Severity:** Warning

Checks for style issues:
- Double underscores (`__`) in names
- Trailing underscores

**Example Warning:**
```
Register 'control__reg' has double underscore
Register 'status_' has trailing underscore
```

**Resolution:**
- Use single underscores
- Remove trailing underscores

---

### Duplicate Names

**Type:** `Duplicate Name`  
**Severity:** Error

Detects duplicate register names within a module.

**Example Error:**
```
Register 'status' defined multiple times
```

**Resolution:**
- Rename one of the duplicates
- Ensure all register names are unique within a module

---

### Duplicate Module Names

**Type:** `Duplicate Module`  
**Severity:** Error

Detects multiple modules with the same name across different files.

**Example Error:**
```
Module name 'uart_controller' is used by multiple files/definitions
```

**Resolution:**
- Rename one of the modules
- Remove duplicate definition

---

### Invalid Default Values

**Type:** `Invalid Default Value`  
**Severity:** Error

Validates that default values fit within register width.

**Example Error:**
```
Register 'counter': 0x1FF exceeds 8-bit range (max 0xFF)
```

**Resolution:**
- Reduce default value to fit width
- Increase register width

---

### Missing Documentation

**Type:** `Missing Documentation`  
**Severity:** Warning

Warns when registers are missing descriptions.

**Example Warning:**
```
3 registers are missing descriptions.
```

**Resolution:**
- Add `description` or `DESC` attribute to registers

---

### Format Issues

**Type:** `Format Issue`  
**Severity:** Warning/Error

Checks source file formats for common mistakes.

#### JSON/YAML Issues

| Issue | Suggestion |
|-------|------------|
| Missing `module` field | Add required `module` field |
| Using `name` instead of `module` | Change to `module` |
| Using `base_address` instead of `base_addr` | Change to `base_addr` |
| CDC settings at root level | Move to `config` section |
| Using `mode` instead of `access` | Change to `access` |
| Using `address` instead of `addr` | Change to `addr` |

#### XML Issues

| Issue | Suggestion |
|-------|------------|
| Wrong root element | Use `<register_map>` |
| Missing `module` attribute | Add `module` attribute |
| Using `name` instead of `module` | Change to `module` attribute |

**Example Warning:**
```
Missing 'module' field. Did you mean 'module' instead of 'name'?
```

---

### Parse Errors

**Type:** `Parse Error`  
**Severity:** Error

Reports syntax errors in source files.

**Example Errors:**
```
Invalid JSON: Expecting ',' delimiter
Invalid YAML: mapping values are not allowed here
Invalid XML: not well-formed (invalid token)
```

**Resolution:**
- Fix syntax errors in source file
- Validate file format

---

### Subregister Overlap

**Type:** `Subregister Overlap`  
**Severity:** Error

Detects overlapping bit ranges within a packed register.

**Example Error:**
```
In register 'control': Field 'enable' [0:0] overlaps with 'mode' [1:0]
```

**Resolution:**
- Adjust `BIT_OFFSET` values to ensure fields do not overlap.
- Check signal widths.

---

### Logical Integrity

**Type:** `Logical Integrity`  
**Severity:** Warning

Checks for structural issues, such as modules with no registers.

**Example Warning:**
```
Module has no registers defined.
```

**Resolution:**
- Ensure the module file contains valid register definitions or annotations.

---

## Report Formats

### Text Report

```
================================================================================
                        AXION HDL RULE CHECK REPORT
================================================================================

❌  ERRORS (2)
--------------------------------------------------------------------------------
  [Address Overlap]
    • uart_controller: Address region 0x1000-0x10FF overlaps with timer_module

  [Duplicate Name]
    • spi_master: Register 'status' defined multiple times

⚠️   WARNINGS (3)
--------------------------------------------------------------------------------
  [Address Alignment]
    • gpio_controller: Register 'config' (0x03) not 4-byte aligned

  [Missing Documentation]
    • uart_controller: 5 registers are missing descriptions.

  [Style Guide]
    • spi_master: Register 'control__reg' has double underscore

================================================================================
```

### JSON Report

```json
{
    "errors": [
        {
            "type": "Address Overlap",
            "module": "uart_controller",
            "msg": "Address region 0x1000-0x10FF overlaps with timer_module"
        }
    ],
    "warnings": [
        {
            "type": "Missing Documentation",
            "module": "spi_master",
            "msg": "3 registers are missing descriptions."
        }
    ],
    "summary": {
        "total_errors": 1,
        "total_warnings": 1,
        "passed": false
    }
}
```

---

## Integration with CI/CD

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | All checks passed |
| `1` | Errors detected |

### Example GitHub Actions

```yaml
- name: Run Axion-HDL Rule Check
  run: |
    axion-hdl -s ./rtl --rule-check
    if [ $? -ne 0 ]; then
      echo "Rule check failed"
      exit 1
    fi
```

### Example Makefile

```makefile
check:
	axion-hdl -s ./rtl --rule-check

build: check
	axion-hdl -s ./rtl -o ./output --all
```

---

## Suppressing Warnings

Currently, warnings cannot be individually suppressed. Best practices:
- Fix all errors before generation
- Review warnings and address as appropriate
- Document intentional deviations in your project

---

## VHDL Reserved Words Reference

The rule checker validates against all VHDL-93/2008 reserved words:

```
abs, access, after, alias, all, and, architecture, array, assert, 
attribute, begin, block, body, buffer, bus, case, component, 
configuration, constant, disconnect, downto, else, elsif, end, 
entity, exit, file, for, function, generate, generic, group, 
guarded, if, impure, in, inertial, inout, is, label, library, 
linkage, literal, loop, map, mod, nand, new, next, nor, not, 
null, of, on, open, or, others, out, package, port, postponed, 
procedure, process, pure, range, record, register, reject, rem, 
report, return, rol, ror, select, severity, signal, shared, sla, 
sll, sra, srl, subtype, then, to, transport, type, unaffected, 
units, until, use, variable, wait, when, while, with, xnor, xor
```
