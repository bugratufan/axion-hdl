-- VHDL Test Fixture: Chain shift scenario
-- 8 registers at 0x00-0x1C for chain shift testing

library ieee;
use ieee.std_logic_1164.all;

-- @axion_def BASE_ADDR=0x0000

entity addr_test_chain is
    port (
        clk : in std_logic;
        rst_n : in std_logic
    );
end entity addr_test_chain;

architecture rtl of addr_test_chain is
    signal chain_reg_0 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x00
    signal chain_reg_1 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x04
    signal chain_reg_2 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x08
    signal chain_reg_3 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x0C
    signal chain_reg_4 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x10
    signal chain_reg_5 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x14
    signal chain_reg_6 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x18
    signal chain_reg_7 : std_logic_vector(31 downto 0); -- @axion: RW ADDR=0x1C
begin
end architecture rtl;
