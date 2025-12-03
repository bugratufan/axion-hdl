--------------------------------------------------------------------------------
-- SPI Controller Module with Base Address Example
-- This example demonstrates the use of BASE_ADDR in @axion_def
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

-- @axion_def BASE_ADDR=0x1000 CDC_EN CDC_STAGE=3

entity spi_controller is
    port (
        clk       : in  std_logic;
        rst_n     : in  std_logic;
        
        -- SPI interface
        spi_clk   : out std_logic;
        spi_mosi  : out std_logic;
        spi_miso  : in  std_logic;
        spi_cs_n  : out std_logic;
        
        -- Interrupt
        irq       : out std_logic
    );
end entity spi_controller;

architecture rtl of spi_controller is
    
    -- Control Register - Base + 0x00
    signal ctrl_reg    : std_logic_vector(31 downto 0); -- @axion RW ADDR=0x00 W_STROBE
    
    -- Status Register - Base + 0x04  
    signal status_reg  : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x04 R_STROBE
    
    -- TX Data Register - Base + 0x08 (using decimal address)
    signal tx_data     : std_logic_vector(31 downto 0); -- @axion WO ADDR=8 W_STROBE
    
    -- RX Data Register - Base + 0x0C (using hex address)
    signal rx_data     : std_logic_vector(31 downto 0); -- @axion RO ADDR=0x0C
    
    -- Clock Divider - Base + 0x10 (auto-assigned)
    signal clk_div     : std_logic_vector(31 downto 0); -- @axion RW
    
    -- Chip Select Mask - Base + 0x14 (auto-assigned)
    signal cs_mask     : std_logic_vector(31 downto 0); -- @axion RW
    
    -- Interrupt Enable - Base + 0x18 (auto-assigned)  
    signal int_enable  : std_logic_vector(31 downto 0); -- @axion RW
    
    -- FIFO Status - Base + 0x1C (auto-assigned)
    signal fifo_status : std_logic_vector(31 downto 0); -- @axion RO
    
    -- Internal signals
    signal tx_fifo_empty : std_logic;
    signal tx_fifo_full  : std_logic;
    signal rx_fifo_empty : std_logic;
    signal rx_fifo_full  : std_logic;
    signal spi_busy      : std_logic;
    
begin

    -- Status register fields
    status_reg(0) <= tx_fifo_empty;
    status_reg(1) <= tx_fifo_full;
    status_reg(2) <= rx_fifo_empty;
    status_reg(3) <= rx_fifo_full;
    status_reg(4) <= spi_busy;
    status_reg(31 downto 5) <= (others => '0');
    
    -- FIFO Status register
    fifo_status(7 downto 0)   <= x"08";  -- TX FIFO depth
    fifo_status(15 downto 8)  <= x"08";  -- RX FIFO depth
    fifo_status(31 downto 16) <= (others => '0');
    
    -- SPI Controller Logic
    process(clk, rst_n)
    begin
        if rst_n = '0' then
            tx_fifo_empty <= '1';
            tx_fifo_full  <= '0';
            rx_fifo_empty <= '1';
            rx_fifo_full  <= '0';
            spi_busy      <= '0';
            spi_cs_n      <= '1';
            spi_clk       <= '0';
            spi_mosi      <= '0';
        elsif rising_edge(clk) then
            -- SPI controller state machine would go here
            -- This is a simplified placeholder
            null;
        end if;
    end process;
    
    -- Interrupt generation
    irq <= int_enable(0) and (tx_fifo_empty or rx_fifo_full);

end architecture rtl;
