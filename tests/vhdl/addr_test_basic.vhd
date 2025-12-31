-- VHDL Test Fixture: Basic sequential addresses
-- 5 registers at 0x00, 0x04, 0x08, 0x0C, 0x10
-- Used for: Scenario 1 (unique address), Scenario 9 (revert)

library ieee;
use ieee.std_logic_1164.all;

entity addr_test_basic is
    port (
        clk : in std_logic;
        -- @axion BASE_ADDR=0x0000
        -- @axion RW ADDR=0x00
        reg_a : inout std_logic_vector(31 downto 0);
        -- @axion RW ADDR=0x04
        reg_b : inout std_logic_vector(31 downto 0);
        -- @axion RW ADDR=0x08
        reg_c : inout std_logic_vector(31 downto 0);
        -- @axion RW ADDR=0x0C
        reg_d : inout std_logic_vector(31 downto 0);
        -- @axion RW ADDR=0x10
        reg_e : inout std_logic_vector(31 downto 0)
    );
end entity addr_test_basic;

architecture rtl of addr_test_basic is
begin
end architecture rtl;
