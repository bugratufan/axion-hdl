-- VHDL Test Fixture: Basic sequential addresses
-- 5 registers at 0x00, 0x04, 0x08, 0x0C, 0x10
-- Used for: Scenario 1 (unique address), Scenario 9 (revert)

library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity addr_test_basic is
    port (
        clk : in std_logic;
        rst_n : in std_logic
    );
end entity addr_test_basic;

architecture rtl of addr_test_basic is
    signal reg_a : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x00
    signal reg_b : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x04
    signal reg_c : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x08
    signal reg_d : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x0C
    signal reg_e : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x10
begin
end architecture rtl;
