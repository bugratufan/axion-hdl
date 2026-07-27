library ieee;
use ieee.std_logic_1164.all;

-- CDC_STAGE=2 variant of cdc_packed_controller (see that file for the rationale).
-- Same packed + wide register layout, different synchronizer depth, so the
-- functional packed/wide CDC tests run against both a 3-stage and a 2-stage
-- chain (CDC-013/019: stage count honored on packed-field and wide-chunk chains).
-- @axion_def CDC_EN CDC_STAGE=2
entity cdc_packed_controller_stage2 is
    port (clk : in std_logic);
end entity;

architecture rtl of cdc_packed_controller_stage2 is
    -- Packed register (mix_reg @ 0x00): RW and RO fields share one 32-bit word.
    signal go_bit    : std_logic;                     -- @axion RW ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=0
    signal speed     : std_logic_vector(2 downto 0);  -- @axion RW ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=1
    signal ready_bit : std_logic;                     -- @axion RO ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=8
    signal version   : std_logic_vector(3 downto 0);  -- @axion RO ADDR=0x00 REG_NAME=mix_reg BIT_OFFSET=12

    -- Wide 64-bit RW register (big_cfg @ 0x04..0x08).
    signal big_cfg   : std_logic_vector(63 downto 0); -- @axion RW ADDR=0x04

    -- Wide 64-bit RO register (big_stat @ 0x10..0x14).
    signal big_stat  : std_logic_vector(63 downto 0); -- @axion RO ADDR=0x10
begin
end architecture;
