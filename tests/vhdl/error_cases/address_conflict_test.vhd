--------------------------------------------------------------------------------
-- File: address_conflict_test.vhd
-- Description: INTENTIONALLY BROKEN - Test module with duplicate addresses
-- Purpose: This file is used to test address conflict detection
-- DO NOT FIX - The address conflicts are intentional for testing
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- @axion_def BASE_ADDR=0x3000

entity address_conflict_test is
    port (
        clk   : in  std_logic;
        rst_n : in  std_logic
    );
end entity address_conflict_test;

architecture rtl of address_conflict_test is

    -- INTENTIONAL ADDRESS CONFLICT #1: Two registers at same address 0x00
    signal reg_alpha : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x00 DESC="First register at 0x00"
    signal reg_beta  : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00 DESC="Second register at 0x00 - CONFLICT!"
    
    -- Normal register for reference
    signal reg_gamma : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x04 DESC="Normal register"

begin
    -- Minimal logic
    process(clk)
    begin
        if rising_edge(clk) then
            if rst_n = '0' then
                reg_alpha <= (others => '0');
            end if;
        end if;
    end process;
end architecture rtl;
