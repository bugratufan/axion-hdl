--------------------------------------------------------------------------------
-- SPI Master Example - Advanced Level (VHDL Annotations)
-- 
-- This example demonstrates:
-- - @axion annotations in VHDL comments
-- - All access types (RO, WO, RW)
-- - Read and write strobes
-- - Manual address assignment
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- Enable CDC with 2 synchronization stages (default)
-- @axion_def BASE_ADDR=0x0000 CDC_EN

entity spi_master is
    port (
        clk       : in  std_logic;
        rst_n     : in  std_logic;
        -- SPI pins
        spi_clk   : out std_logic;
        spi_mosi  : out std_logic;
        spi_miso  : in  std_logic;
        spi_cs_n  : out std_logic
    );
end entity spi_master;

architecture rtl of spi_master is

    -- Control register: start transfer, clock divider, etc.
    signal control_reg : std_logic_vector(31 downto 0); -- @axion RW W_STROBE DESC="SPI control: bit0=start, bits[15:8]=clk_div"
    
    -- Status register: busy flag, transfer complete, errors
    signal status_reg : std_logic_vector(31 downto 0); -- @axion RO R_STROBE DESC="SPI status: bit0=busy, bit1=done, bit2=error"
    
    -- TX data register (write-only from software perspective)
    signal tx_data_reg : std_logic_vector(31 downto 0); -- @axion WO DESC="Transmit data buffer"
    
    -- RX data register (read-only from software perspective)
    signal rx_data_reg : std_logic_vector(31 downto 0); -- @axion RO DESC="Receive data buffer"
    
    -- Configuration register at specific address
    signal config_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x20 DESC="SPI configuration"
    
    -- Interrupt control
    signal irq_enable_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x30 DESC="Interrupt enable mask"
    signal irq_status_reg : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x34 R_STROBE W_STROBE DESC="Interrupt status"

begin
    -- SPI state machine implementation would go here
    -- This is just an example to demonstrate Axion annotations
    
    spi_clk  <= '0';
    spi_mosi <= '0';
    spi_cs_n <= '1';
    
end architecture rtl;
