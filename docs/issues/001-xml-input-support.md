# GitHub Issue: XML Input Support

**Title:** `[FEATURE] Generate register interfaces from XML input files`

**Labels:** `enhancement`, `parser`

---

## Description

Currently, Axion-HDL only accepts VHDL files with `@axion` annotations as input. This feature request is to add support for XML-based register definitions as an alternative input format.

This would allow:
- Teams who define registers in XML to use Axion-HDL without modifying their workflow
- Import from existing IP-XACT or custom XML register maps
- Integration with other EDA tools that export XML register definitions

## Proposed XML Format

### Option 1: Simple Custom Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<axion_registers module="sensor_controller" base_address="0x0000">
    <config>
        <cdc enabled="true" stages="3"/>
    </config>
    
    <registers>
        <register name="status_reg" 
                  address="0x00" 
                  access="RO" 
                  width="32"
                  description="System status flags">
        </register>
        
        <register name="control_reg" 
                  address="0x04" 
                  access="WO" 
                  width="32"
                  write_strobe="true"
                  description="Main control register">
        </register>
        
        <register name="config_reg" 
                  address="0x08" 
                  access="RW" 
                  width="32"
                  read_strobe="true"
                  write_strobe="true"
                  description="Configuration settings">
        </register>
        
        <!-- Wide signal example -->
        <register name="timestamp" 
                  address="0x10" 
                  access="RO" 
                  width="64"
                  description="64-bit timestamp counter">
        </register>
    </registers>
</axion_registers>
```

### Option 2: IP-XACT Compatible Format

Support for standard IP-XACT (IEEE 1685) format would allow importing from other tools:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<spirit:component xmlns:spirit="http://www.spiritconsortium.org/XMLSchema/SPIRIT/1.5">
    <spirit:name>sensor_controller</spirit:name>
    <spirit:memoryMaps>
        <spirit:memoryMap>
            <spirit:addressBlock>
                <spirit:baseAddress>0x0000</spirit:baseAddress>
                <spirit:register>
                    <spirit:name>status_reg</spirit:name>
                    <spirit:addressOffset>0x00</spirit:addressOffset>
                    <spirit:size>32</spirit:size>
                    <spirit:access>read-only</spirit:access>
                </spirit:register>
                <!-- ... -->
            </spirit:addressBlock>
        </spirit:memoryMap>
    </spirit:memoryMaps>
</spirit:component>
```

## Proposed CLI Usage

```bash
# From XML file
axion-hdl --xml-input ./registers.xml -o ./output --all

# Mixed sources (VHDL + XML)
axion-hdl -s ./vhdl_src --xml-input ./extra_regs.xml -o ./output
```

## Proposed Python API

```python
from axion_hdl import AxionHDL

axion = AxionHDL(output_dir="./output")

# Add XML input
axion.add_xml("./registers.xml")

# Or parse XML string directly
axion.parse_xml_string(xml_content)

# Can mix with VHDL sources
axion.add_src("./vhdl")

axion.analyze()
axion.generate_all()
```

## Implementation Considerations

1. **XML Parser**: Use Python's `xml.etree.ElementTree` or `lxml` for parsing
2. **Schema Validation**: Optional XSD schema for validation
3. **Format Detection**: Auto-detect IP-XACT vs custom format
4. **Merge Strategy**: How to handle conflicts when mixing XML and VHDL inputs

## Expected Output

Same outputs as VHDL input:
- `*_axion_reg.vhd` - AXI4-Lite register interface
- `*_regs.h` - C header file
- `*_regs.xml` - XML register map (round-trip)
- `register_map.md` - Documentation

## Acceptance Criteria

- [ ] Parse custom XML format
- [ ] Parse IP-XACT format (basic support)
- [ ] CLI `--xml-input` option
- [ ] Python API `add_xml()` method
- [ ] Generate all outputs from XML input
- [ ] Unit tests for XML parsing
- [ ] Documentation with examples

## Related

- Current XML output: `XMLGenerator` in `doc_generators.py`
- This could enable round-trip: XML → Generate → XML

---

## Additional Notes

Priority: Medium
Estimated Effort: Medium (2-3 days)
Target Version: v0.4.0
