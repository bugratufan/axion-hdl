--------------------------------------------------------------------------------
-- Subregister Test Module
-- 
-- Tests for Issue #2 (Subregister) and Issue #3 (DEFAULT) features
-- This file demonstrates REG_NAME, BIT_OFFSET, and DEFAULT attributes
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- @axion_def CDC_EN=false BASE_ADDR=0x00

entity subregister_test is
    port (
        -- Clock and Reset
        clk     : in std_logic;
        rst_n   : in std_logic
    );
end entity;

architecture rtl of subregister_test is
    -- Regular register with DEFAULT
    signal version_reg : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x00 DEFAULT=0x00010203 DESC="Version register v1.2.3"
    
    -- Packed register with subregisters (control register at 0x04)
    signal ctrl_enable    : std_logic;                        -- @axion RW ADDR=0x04 REG_NAME=control BIT_OFFSET=0 DEFAULT=1 DESC="Enable bit"
    signal ctrl_mode      : std_logic_vector(1 downto 0);     -- @axion RW ADDR=0x04 REG_NAME=control BIT_OFFSET=1 DEFAULT=2 DESC="Mode selection"
    signal ctrl_prescaler : std_logic_vector(7 downto 0);     -- @axion RW ADDR=0x04 REG_NAME=control BIT_OFFSET=3 DEFAULT=10 DESC="Prescaler value"
    signal ctrl_reserved  : std_logic_vector(19 downto 0);    -- @axion RW ADDR=0x04 REG_NAME=control BIT_OFFSET=11 DEFAULT=0 DESC="Reserved"
    -- Combined control default: enable[0]=1, mode[2:1]=2, prescaler[10:3]=10 = 0x55
    
    -- Another packed register (status at 0x08)
    signal stat_busy     : std_logic;                         -- @axion RO ADDR=0x08 REG_NAME=status BIT_OFFSET=0 DEFAULT=0 DESC="Busy flag"
    signal stat_error    : std_logic;                         -- @axion RO ADDR=0x08 REG_NAME=status BIT_OFFSET=1 DEFAULT=0 DESC="Error flag"
    signal stat_count    : std_logic_vector(7 downto 0);      -- @axion RO ADDR=0x08 REG_NAME=status BIT_OFFSET=8 DEFAULT=0 DESC="Operation count"
    
    -- Standard register with hex default
    signal config_reg : std_logic_vector(31 downto 0);  -- @axion RW ADDR=0x0C DEFAULT=0xDEADBEEF DESC="Configuration register"
    
    -- Single bit with default 
    signal irq_enable : std_logic;  -- @axion RW ADDR=0x10 DEFAULT=0 DESC="IRQ enable"
    
begin
    -- Simple logic for simulation
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            stat_busy <= '0';
            stat_error <= '0';
            stat_count <= (others => '0');
        elsif rising_edge(clk) then
            -- Simulation behavior
            if ctrl_enable = '1' then
                stat_busy <= '1';
                stat_count <= std_logic_vector(unsigned(stat_count) + 1);
            else
                stat_busy <= '0';
            end if;
        end if;
    end process;
    
    -- Version is constant
    version_reg <= x"00010203";
    
end architecture;
