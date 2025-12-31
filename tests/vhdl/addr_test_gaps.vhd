-- VHDL Test Fixture: Gap preservation scenario
-- 4 registers with gaps: 0x00, 0x10, 0x20, 0x24

library ieee;
use ieee.std_logic_1164.all;

entity addr_test_gaps is
    port (
        clk : in std_logic;
        -- @axion BASE_ADDR=0x0000
        -- @axion RW ADDR=0x00
        gap_reg_a : inout std_logic_vector(31 downto 0);
        -- @axion RW ADDR=0x10
        gap_reg_b : inout std_logic_vector(31 downto 0);
        -- @axion RW ADDR=0x20
        gap_reg_c : inout std_logic_vector(31 downto 0);
        -- @axion RW ADDR=0x24
        gap_reg_d : inout std_logic_vector(31 downto 0)
    );
end entity addr_test_gaps;

architecture rtl of addr_test_gaps is
begin
end architecture rtl;
