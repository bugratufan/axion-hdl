# Advanced Features

Axion-HDL automates several complex design tasks commonly found in register map implementation.

## 1. Clock Domain Crossing (CDC)

If your register interface runs on an AXI clock (`aclk`) but your user logic runs on a different clock, you need synchronizers. Axion-HDL can insert these automatically.

### How to Enable
Add the `CDC` attribute to any register definition.

**VHDL:**
```vhdl
signal data_sync : std_logic_vector(31 downto 0); -- @axion RO CDC
```

**YAML:**
```yaml
- name: data_sync
  cdc: true
```

### Implementation Details
- **RO Registers (Status):** A 2-stage flip-flop synchronizer is inserted on the input from user logic to the AXI clock domain.
- **RW/WO Registers (Control):** A 2-stage synchronizer is inserted on the output from the AXI clock domain to the user logic.
- **Handshaking:** For simple scalar registers, Axion uses multi-flop synchronization. For bus synchronization or data coherency, manual handling might still be required for valid/ready signals, though Axion handles the data path synchronization safely for quasi-static configuration signals.

## 2. Auto-Addressing

You do not need to manually calculate addresses.

- **Sequential Assignment:** If you omit the address, Axion assigns the next available 4-byte aligned offset.
- **Conflict Detection:** Axion throws an error if two registers overlap or if a register requires more space than available between two fixed addresses.

## 3. Sub-Registers (Bit Fields)

You can pack multiple fields into a single 32-bit register.

**YAML Only:**
```yaml
- name: control_pack
  fields:
    - name: enable     # Bits 0..0
      bit_offset: 0
      width: 1
    - name: mode       # Bits 4..5
      bit_offset: 4
      width: 2
```

Outputs:
- **VHDL:** The generated VHDL will provide separate ports for `enable` and `mode`.
- **C Header:** Masks and shifts are generated (e.g., `CONTROL_PACK_MODE_MASK`, `CONTROL_PACK_MODE_SHIFT`).

## 4. Wide Signals (> 32 bits)

Axion supports signals larger than 32 bits. It will automatically span them across multiple addresses.

**Example:**
Defining a 64-bit counter:
```vhdl
signal long_cnt : std_logic_vector(63 downto 0); -- @axion RO
```

Axion will:
1.  Assign Base Address `N` for bits `31:0`.
2.  Assign Address `N+4` for bits `63:32`.
3.  In VHDL, present a single 64-bit port `long_cnt_i`.
4.  In C, provide two offsets (`LONG_CNT_L`, `LONG_CNT_H`).
