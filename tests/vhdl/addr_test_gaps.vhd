-- VHDL Test Fixture: Gap preservation scenario
-- 4 registers with gaps: 0x00, 0x10, 0x20, 0x24

library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity addr_test_gaps is
    port (
        clk : in std_logic;
        rst_n : in std_logic
    );
end entity addr_test_gaps;

architecture rtl of addr_test_gaps is
    signal gap_reg_a : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x00
    signal gap_reg_b : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x10
    signal gap_reg_c : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x20
    signal gap_reg_d : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x24
begin
end architecture rtl;
