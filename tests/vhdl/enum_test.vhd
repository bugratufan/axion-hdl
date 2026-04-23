-- @axion_def BASE_ADDR=0x0000
library ieee;
use ieee.std_logic_1164.all;

entity enum_test_mod is
    port (
        clk   : in  std_logic;
        rst_n : in  std_logic
    );
end entity enum_test_mod;

architecture rtl of enum_test_mod is
    -- Standalone register with enum annotation
    signal status_out : std_logic_vector(1 downto 0);  -- @axion RO ADDR=0x00 ENUM="0:IDLE,1:WAITING,3:READY" DESC="Status output"

    -- Enable bit (1-bit with enum)
    signal enable_sig : std_logic;  -- @axion RW ADDR=0x04 ENUM="0:INACTIVE,1:ACTIVE" DESC="Enable signal"

    -- Sub-register signals with enum
    signal ctrl_enable : std_logic;  -- @axion RW REG_NAME=ctrl_reg ADDR=0x08 BIT_OFFSET=0 ENUM="0:DISABLED,1:ENABLED"
    signal ctrl_mode   : std_logic_vector(1 downto 0);  -- @axion RW REG_NAME=ctrl_reg ADDR=0x08 BIT_OFFSET=1 ENUM="0:IDLE,1:RUN,2:STOP"

begin
    -- RTL logic placeholder
    status_out <= (others => '0');
    enable_sig <= '0';
    ctrl_enable <= '0';
    ctrl_mode <= (others => '0');
end architecture rtl;
