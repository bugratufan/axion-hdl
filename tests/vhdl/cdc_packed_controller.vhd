library ieee;
use ieee.std_logic_1164.all;

-- CDC packed/wide register controller.
--
-- Exists purely to give the cocotb CDC suite a DUT whose CDC paths are NOT
-- plain full-width registers: a packed register mixing RW and RO fields in one
-- word, and a >32-bit (64-bit) register that the generator must chunk and
-- synchronize word-by-word. The functional simulation of these two paths
-- (packed-field sync, wide chunk sync) is otherwise only proven structurally
-- in tests/python/test_cdc.py (CDC-010/011/013/014). This DUT is generated and
-- exercised by tests/cocotb/test_cdc_packed.py (GHDL) and
-- test_sv_cdc_packed.py (Verilator).
--
-- CDC_STAGE=3 here; the CDC_STAGE=2 variant lives in
-- cdc_packed_controller_stage2.vhd.
-- @axion_def CDC_EN CDC_STAGE=3
entity cdc_packed_controller is
    port (clk : in std_logic);
end entity;

architecture rtl of cdc_packed_controller is
    -- Packed register (mix_reg @ 0x00): RW and RO fields share one 32-bit word.
    signal go_bit    : std_logic;                     -- @axion RW ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=0
    signal speed     : std_logic_vector(2 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=1
    signal ready_bit : std_logic;                     -- @axion RO ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=8
    signal version   : std_logic_vector(3 downto 0);  -- @axion RO ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=12

    -- Wide 64-bit RW register (big_cfg @ 0x04..0x08): must be chunked into two
    -- 32-bit storage words and synchronized chunk-by-chunk into module_clk.
    signal big_cfg   : std_logic_vector(63 downto 0); -- @axion RW ADDR=0x04

    -- Wide 64-bit RO register (big_stat @ 0x10..0x14): module_clk input,
    -- synchronized chunk-by-chunk into the AXI read path.
    signal big_stat  : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x10
begin
end architecture;
