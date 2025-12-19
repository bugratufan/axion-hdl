--------------------------------------------------------------------------------
-- File: sensor_controller.vhd
-- Description: Example VHDL module demonstrating all Axion features
-- This module showcases different register types and configurations
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Enable CDC with 3 synchronization stages
-- @axion_def CDC_EN CDC_STAGE=3

entity sensor_controller is
    port (
        -- System clocks and reset
        clk           : in  std_logic;
        rst_n         : in  std_logic;
        
        -- Sensor inputs
        temperature   : in  std_logic_vector(15 downto 0);
        pressure      : in  std_logic_vector(15 downto 0);
        humidity      : in  std_logic_vector(15 downto 0);
        
        -- Control outputs
        fan_enable    : out std_logic;
        heater_enable : out std_logic;
        alarm_out     : out std_logic;
        
        -- Data ready signals
        data_valid    : in  std_logic;
        error_flag    : in  std_logic
    );
end entity sensor_controller;

architecture rtl of sensor_controller is

    -- Read-Only Registers (Hardware writes, Software reads)
    signal status_reg : std_logic_vector(31 downto 0); -- @axion: RO description=System status flags
    signal temperature_reg : std_logic_vector(31 downto 0); -- @axion: RO R_STROBE description=Temperature sensor reading
    signal pressure_reg : std_logic_vector(31 downto 0); -- @axion: RO R_STROBE description=Pressure sensor value
    signal humidity_reg : std_logic_vector(31 downto 0); -- @axion: RO description=Humidity sensor value
    signal error_count_reg : std_logic_vector(31 downto 0); -- @axion: RO description=Total error count
    
    -- Write-Only Registers (Software writes, Hardware reads)
    signal control_reg : std_logic_vector(31 downto 0); -- @axion: WO W_STROBE description=Main control register
    signal threshold_high_reg : std_logic_vector(31 downto 0); -- @axion: WO description=High threshold value
    signal threshold_low_reg : std_logic_vector(31 downto 0); -- @axion: WO description=Low threshold value
    
    -- Read-Write Registers (Both can access)
    signal config_reg : std_logic_vector(31 downto 0); -- @axion: RW
    signal calibration_reg : std_logic_vector(31 downto 0); -- @axion: RW R_STROBE W_STROBE
    signal mode_reg : std_logic_vector(31 downto 0); -- @axion: RW
    
    -- Manual address assignment test
    signal debug_reg : std_logic_vector(31 downto 0); -- @axion: RW
    signal timestamp_reg : std_logic_vector(31 downto 0); -- @axion: RO
    
    -- Combined features test
    signal interrupt_status_reg : std_logic_vector(31 downto 0); -- @axion: RW R_STROBE W_STROBE
    
    -- Internal signals
    signal error_counter : unsigned(31 downto 0);
    signal timestamp_counter : unsigned(31 downto 0);
    
    -- Internal copies of output signals (so we can read them)
    signal fan_enable_i    : std_logic;
    signal heater_enable_i : std_logic;
    signal alarm_out_i     : std_logic;
    
begin

    -- Connect internal signals to outputs
    fan_enable <= fan_enable_i;
    heater_enable <= heater_enable_i;
    alarm_out <= alarm_out_i;

    -- Status register composition (bits assignment example)
    status_reg(0) <= data_valid;
    status_reg(1) <= error_flag;
    status_reg(2) <= fan_enable_i;
    status_reg(3) <= heater_enable_i;
    status_reg(4) <= alarm_out_i;
    status_reg(31 downto 5) <= (others => '0');
    
    -- Temperature register (16-bit sensor data + padding)
    temperature_reg(15 downto 0) <= temperature;
    temperature_reg(31 downto 16) <= (others => '0');
    
    -- Pressure register (16-bit sensor data + padding)
    pressure_reg(15 downto 0) <= pressure;
    pressure_reg(31 downto 16) <= (others => '0');
    
    -- Humidity register (16-bit sensor data + padding)
    humidity_reg(15 downto 0) <= humidity;
    humidity_reg(31 downto 16) <= (others => '0');
    
    -- Error counter
    error_count_reg <= std_logic_vector(error_counter);
    
    -- Control outputs from control register
    fan_enable_i <= control_reg(0);
    heater_enable_i <= control_reg(1);
    alarm_out_i <= control_reg(2);
    
    -- Timestamp register
    timestamp_reg <= std_logic_vector(timestamp_counter);
    
    -- Error counter process
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            error_counter <= (others => '0');
        elsif rising_edge(clk) then
            if error_flag = '1' then
                error_counter <= error_counter + 1;
            end if;
        end if;
    end process;
    
    -- Timestamp counter process
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            timestamp_counter <= (others => '0');
        elsif rising_edge(clk) then
            timestamp_counter <= timestamp_counter + 1;
        end if;
    end process;

end architecture rtl;
