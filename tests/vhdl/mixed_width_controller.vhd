--------------------------------------------------------------------------------
-- File: mixed_width_controller.vhd
-- Description: Example module with mixed signal widths for testing Axion HDL
--              Tests: std_logic, 6-bit, 32-bit, and 48-bit signals
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- @axion_def BASE_ADDR=0x2000 CDC_EN CDC_STAGE=2

entity mixed_width_controller is
    port (
        -- Clock and Reset
        clk   : in  std_logic;
        rst_n : in  std_logic;
        
        -- Module I/O (directly controlled, not register-mapped)
        data_in  : in  std_logic_vector(31 downto 0);
        data_out : out std_logic_vector(31 downto 0);
        valid    : out std_logic
    );
end entity mixed_width_controller;

architecture rtl of mixed_width_controller is

    -- 1-bit signals (std_logic)
    signal enable_flag      : std_logic;                      -- @axion RW ADDR=0x00
    signal busy_status      : std_logic;                      -- @axion RO ADDR=0x04
    signal trigger_pulse    : std_logic;                      -- @axion WO ADDR=0x08 W_STROBE
    
    -- 6-bit signals
    signal channel_select   : std_logic_vector(5 downto 0);   -- @axion RW ADDR=0x0C
    signal error_code       : std_logic_vector(5 downto 0);   -- @axion RO ADDR=0x10
    
    -- Standard 32-bit signals
    signal config_reg       : std_logic_vector(31 downto 0);  -- @axion RW ADDR=0x14
    signal status_reg       : std_logic_vector(31 downto 0);  -- @axion RO ADDR=0x18
    signal command_reg      : std_logic_vector(31 downto 0);  -- @axion WO ADDR=0x1C W_STROBE
    
    -- 48-bit signals (wider than AXI data bus)
    signal timestamp_low    : std_logic_vector(31 downto 0);  -- @axion RO 
    signal timestamp_high   : std_logic_vector(15 downto 0);  -- @axion RO ADDR=0x24
    signal counter_48bit    : std_logic_vector(47 downto 0);  -- Internal 48-bit counter
    
    -- 16-bit signal
    signal threshold_value  : std_logic_vector(15 downto 0);  -- @axion RW ADDR=0x28
    
    -- 8-bit signal
    signal mode_select      : std_logic_vector(7 downto 0);   -- @axion RW ADDR=0x2C
    
    -- 48-bit signal (wider than 32-bit AXI bus - testing wide register support)
    signal wide_counter     : std_logic_vector(47 downto 0);  -- @axion RO ADDR=0x30
    
    -- 64-bit signal (requires 2 AXI registers)
    signal long_timestamp   : std_logic_vector(63 downto 0);  -- @axion RO ADDR=0x38
    
    -- 100-bit signal (auto address allocation test)
    signal very_wide_data   : std_logic_vector(99 downto 0);  -- @axion RO
    
    -- 200-bit signal (auto address allocation test)
    signal huge_data        : std_logic_vector(199 downto 0); -- @axion RO
    
    -- Final 32-bit signal (auto address allocation test)
    signal final_reg        : std_logic_vector(31 downto 0);  -- @axion RW

begin

    -- Simple logic for demonstration
    process(clk)
    begin
        if rising_edge(clk) then
            if rst_n = '0' then
                counter_48bit <= (others => '0');
                busy_status <= '0';
                error_code <= (others => '0');
                status_reg <= (others => '0');
            else
                -- Increment 48-bit counter
                counter_48bit <= std_logic_vector(unsigned(counter_48bit) + 1);
                
                -- Split 48-bit counter into two registers for AXI access
                timestamp_low <= counter_48bit(31 downto 0);
                timestamp_high <= counter_48bit(47 downto 32);
                
                -- Update status based on enable
                if enable_flag = '1' then
                    busy_status <= '1';
                    status_reg(0) <= '1';
                else
                    busy_status <= '0';
                    status_reg(0) <= '0';
                end if;
                
                -- Error code from channel select overflow check
                if unsigned(channel_select) > 32 then
                    error_code <= "000001";
                else
                    error_code <= "000000";
                end if;
            end if;
        end if;
    end process;
    
    -- Output assignments
    data_out <= config_reg;
    valid <= enable_flag and (not busy_status);

end architecture rtl;
