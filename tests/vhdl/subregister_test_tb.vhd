--------------------------------------------------------------------------------
-- Subregister/Default Test Testbench
-- 
-- Verifies:
-- 1. Default/Reset values (SUB/DEF feature)
-- 2. Subregister bit packing/unpacking
-- 3. Read/Write access to packed registers
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;
use ieee.std_logic_textio.all;

entity subregister_test_tb is
end entity;

architecture testbench of subregister_test_tb is

    -- Clock/Reset
    signal axi_aclk    : std_logic := '0';
    signal axi_aresetn : std_logic := '0';
    signal module_clk  : std_logic := '0';
    
    constant C_CLK_PERIOD : time := 10 ns;

    -- AXI Signals
    signal s_axi_awaddr  : std_logic_vector(31 downto 0);
    signal s_axi_awvalid : std_logic;
    signal s_axi_awready : std_logic;
    signal s_axi_wdata   : std_logic_vector(31 downto 0);
    signal s_axi_wstrb   : std_logic_vector(3 downto 0);
    signal s_axi_wvalid  : std_logic;
    signal s_axi_wready  : std_logic;
    signal s_axi_bresp   : std_logic_vector(1 downto 0);
    signal s_axi_bvalid  : std_logic;
    signal s_axi_bready  : std_logic;
    signal s_axi_araddr  : std_logic_vector(31 downto 0);
    signal s_axi_arvalid : std_logic;
    signal s_axi_arready : std_logic;
    signal s_axi_rdata   : std_logic_vector(31 downto 0);
    signal s_axi_rresp   : std_logic_vector(1 downto 0);
    signal s_axi_rvalid  : std_logic;
    signal s_axi_rready  : std_logic;

    -- DUT Signals (from subregister_test.vhd entity)
    signal version_reg    : std_logic_vector(31 downto 0);
    signal ctrl_enable    : std_logic;
    signal ctrl_mode      : std_logic_vector(1 downto 0);
    signal ctrl_prescaler : std_logic_vector(7 downto 0);
    signal ctrl_reserved  : std_logic_vector(19 downto 0);
    signal stat_busy      : std_logic := '0';
    signal stat_error     : std_logic := '0';
    signal stat_count     : std_logic_vector(7 downto 0) := (others => '0');
    signal config_reg     : std_logic_vector(31 downto 0);
    signal irq_enable     : std_logic;
    
    signal test_done : boolean := false;
    
begin

    -- Clock Generation
    axi_aclk <= not axi_aclk after C_CLK_PERIOD/2 when not test_done else '0';

    -- DUT Instantiation (The Generated Register Shell)
    dut : entity work.subregister_test_axion_reg
        port map (
            axi_aclk    => axi_aclk,
            axi_aresetn => axi_aresetn,
            
            axi_awaddr  => s_axi_awaddr,
            axi_awvalid => s_axi_awvalid,
            axi_awready => s_axi_awready,
            axi_wdata   => s_axi_wdata,
            axi_wstrb   => s_axi_wstrb,
            axi_wvalid  => s_axi_wvalid,
            axi_wready  => s_axi_wready,
            axi_bresp   => s_axi_bresp,
            axi_bvalid  => s_axi_bvalid,
            axi_bready  => s_axi_bready,
            axi_araddr  => s_axi_araddr,
            axi_arvalid => s_axi_arvalid,
            axi_arready => s_axi_arready,
            axi_rdata   => s_axi_rdata,
            axi_rresp   => s_axi_rresp,
            axi_rvalid  => s_axi_rvalid,
            axi_rready  => s_axi_rready,
            
            -- Regular Registers
            version_reg => x"00010203", -- RO input
            config_reg => config_reg,   -- RW output
            irq_enable => irq_enable,   -- RW output (single bit)
            
            -- Packed Registers (Subregisters)
            -- Control (RW outputs)
            ctrl_enable => ctrl_enable,
            ctrl_mode => ctrl_mode,
            ctrl_prescaler => ctrl_prescaler,
            ctrl_reserved => ctrl_reserved,
            
            -- Status (RO inputs)
            stat_busy => stat_busy,
            stat_error => stat_error,
            stat_count => stat_count
        );

    -- Test Process
    process
        variable rdata32 : std_logic_vector(31 downto 0);
        variable l : line;
        
        procedure check_value(
            constant actual : in std_logic_vector;
            constant expected : in std_logic_vector;
            constant msg : in string
        ) is
            variable l : line;
        begin
            if actual /= expected then
                write(l, string'("FAIL: ") & msg);
                write(l, string'(" | Expected: 0x"));
                hwrite(l, expected);
                write(l, string'(" Actual: 0x"));
                hwrite(l, actual);
                writeline(output, l);
                assert false report "Check failed" severity error;
            else
                write(l, string'("PASS: ") & msg);
                writeline(output, l);
            end if;
        end procedure;
        
        -- Helper procedure for AXI Read (Impure, uses process variables/signals)
        procedure axi_read (
            constant addr : in std_logic_vector(31 downto 0);
            variable data : out std_logic_vector(31 downto 0)
        ) is
        begin
            wait until rising_edge(axi_aclk);
            s_axi_araddr <= addr;
            s_axi_arvalid <= '1';
            s_axi_rready <= '1';
            
            wait until rising_edge(axi_aclk) and s_axi_arready = '1';
            s_axi_arvalid <= '0';
            
            wait until rising_edge(axi_aclk) and s_axi_rvalid = '1';
            data := s_axi_rdata;
            s_axi_rready <= '0';
        end procedure;
        
        -- Helper procedure for AXI Write (Impure, uses process variables/signals)
        procedure axi_write (
            constant addr : in std_logic_vector(31 downto 0);
            constant data : in std_logic_vector(31 downto 0)
        ) is
        begin
            wait until rising_edge(axi_aclk);
            s_axi_awaddr <= addr;
            s_axi_awvalid <= '1';
            s_axi_wdata <= data;
            s_axi_wstrb <= "1111";
            s_axi_wvalid <= '1';
            s_axi_bready <= '1';
            
            wait until rising_edge(axi_aclk) and s_axi_awready = '1';
            s_axi_awvalid <= '0';
            
            -- Handle case where wready comes later
            if s_axi_wready = '0' then
                wait until rising_edge(axi_aclk) and s_axi_wready = '1';
            end if;
            s_axi_wvalid <= '0';
            
            wait until rising_edge(axi_aclk) and s_axi_bvalid = '1';
            s_axi_bready <= '0';
        end procedure;
    begin
        -- Initial Reset
        axi_aresetn <= '0';
        wait for 100 ns;
        wait until rising_edge(axi_aclk);
        axi_aresetn <= '1';
        write(l, string'("--- Starting VHDL Simulation for Subregisters and Defaults ---"));
        writeline(output, l);

        ---------------------------------------------------------
        -- Test 1: Verify Reset Values (DEFAULT Attribute)
        ---------------------------------------------------------
        wait for 50 ns;
        
        -- Check Control Register Combined Default
        -- Enable=1, Mode=2, Prescaler=10(0xA) -> 0x....55
        axi_read(x"00000004", rdata32); 
        check_value(rdata32, x"00000055", "Control Reg Default Read (0x55)");

        -- Check Config Register Default
        -- DEFAULT=0xDEADBEEF
        axi_read(x"0000000C", rdata32);
        check_value(rdata32, x"DEADBEEF", "Config Reg Default Read (0xDEADBEEF)");

        -- Check output port signals immediately after reset
        -- We can verify the signals driven by the DUT are correct
        if irq_enable /= '0' then
            write(l, string'("FAIL: irq_enable output not 0"));
        else
            write(l, string'("PASS: irq_enable output default is 0"));
        end if;
        writeline(output, l);

        if ctrl_enable /= '1' then
             write(l, string'("FAIL: ctrl_enable output not 1"));
             writeline(output, l);
        end if;
        
        if ctrl_prescaler /= x"0A" then
             write(l, string'("FAIL: ctrl_prescaler output not 10"));
             writeline(output, l);
        end if;

        ---------------------------------------------------------
        -- Test 2: Subregister Access (Write/Read)
        ---------------------------------------------------------
        
        -- Write to Control Register
        -- Set Enable=0, Mode=1, Prescaler=20(0x14)
        -- Binary: ... 0000 0000 1010 0 10 0 = 0x00A4
        -- Prescaler (10:3) = 0x14 (10100) -> shifted left 3 = 1010 0000
        -- Mode (2:1)      = 1 (01)      -> shifted left 1 =       10
        -- Enable (0)      = 0           ->                =        0
        -- Total = 0xA2
        
        axi_write(x"00000004", x"000000A2");
        wait for 20 ns;
        
        -- Verify Output Ports
        if ctrl_enable = '0' and ctrl_mode = "01" and ctrl_prescaler = x"14" then
             write(l, string'("PASS: Subregister Write Outputs Correct (Enable=0, Mode=1, Pre=20)"));
        else
             write(l, string'("FAIL: Subregister Write Outputs Incorrect"));
             write(l, string'("  Enable: ") & std_logic'image(ctrl_enable));
             -- write(l, string'("  Mode: ") & integer'image(to_integer(unsigned(ctrl_mode))));
        end if;
        writeline(output, l);
        
        -- Read Internal Back
        axi_read(x"00000004", rdata32);
        check_value(rdata32, x"000000A2", "Control Reg Readback");

        ---------------------------------------------------------
        -- Test 3: RO Subregister Read
        ---------------------------------------------------------
        -- Status Register inputs
        stat_busy <= '1';
        stat_error <= '0';
        stat_count <= x"FF";
        wait for 20 ns;
        
        -- Expected Read: Count(15:8)=0xFF, Error(1)=0, Busy(0)=1
        -- 0xFF01
        axi_read(x"00000008", rdata32);
        check_value(rdata32, x"0000FF01", "Status Reg Packed Read (0xFF01)");
        
        ---------------------------------------------------------
        -- Test 4: Single Bit Default & Writes
        ---------------------------------------------------------
        axi_write(x"00000010", x"00000001");
        wait for 20 ns;
        if irq_enable = '1' then
             write(l, string'("PASS: IRQ Enable Set"));
        else
             write(l, string'("FAIL: IRQ Enable Not Set"));
        end if;
        writeline(output, l);

        write(l, string'("--- End of Simulation ---"));
        writeline(output, l);
        
        test_done <= true;
        wait;
    end process;

end architecture;
