--------------------------------------------------------------------------------
-- Subregister/Default XML Test Testbench
-- 
-- Verifies:
-- 1. Default/Reset values from XML input
-- 2. Subregister bit packing/unpacking from XML
-- 3. Read/Write access to XML-generated packed registers
--------------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use std.textio.all;
use ieee.std_logic_textio.all;

entity subregister_xml_test_tb is
end entity;

architecture testbench of subregister_xml_test_tb is

    -- Clock/Reset
    signal axi_aclk    : std_logic := '0';
    signal axi_aresetn : std_logic := '0';
    
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

    -- DUT Signals (from subregister_test.xml)
    -- Config Register (RW)
    signal config_reg    : std_logic_vector(31 downto 0);
    
    -- Status Register (RO) - Inputs
    signal ready         : std_logic := '0';
    signal err_flag      : std_logic := '0';
    signal busy          : std_logic := '0';
    signal state         : std_logic_vector(3 downto 0) := (others => '0');
    signal count         : std_logic_vector(7 downto 0) := (others => '0');
    
    -- Control Register (RW) - Outputs
    signal enable        : std_logic;
    signal mode          : std_logic;
    signal irq_mask      : std_logic_vector(3 downto 0);
    signal timeout       : std_logic_vector(7 downto 0);
    
    signal test_done : boolean := false;
    
begin

    -- Clock Generation
    axi_aclk <= not axi_aclk after C_CLK_PERIOD/2 when not test_done else '0';

    -- DUT Instantiation (The Generated Register Shell from XML)
    dut : entity work.subregister_test_xml_axion_reg
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
            
            -- Register Signals
            config_reg => config_reg,
            
            -- Subregisters
            ready      => ready,
            err_flag   => err_flag,
            busy       => busy,
            state      => state,
            count      => count,
            
            enable     => enable,
            mode       => mode,
            irq_mask   => irq_mask,
            timeout    => timeout
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
        
        -- Helper procedure for AXI Read
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
        
        -- Helper procedure for AXI Write
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
        write(l, string'("--- Starting XML VHDL Simulation ---"));
        writeline(output, l);

        ---------------------------------------------------------
        -- Test 1: Verify Reset Values and Defaults
        ---------------------------------------------------------
        wait for 50 ns;
        
        -- Config Reg (0x00) Default: 0xCAFEBABE
        axi_read(x"00003000", rdata32);
        check_value(rdata32, x"CAFEBABE", "Config Reg Default");
        
        -- Control Reg (0x10) Default:
        -- enable(0):    1
        -- mode(1):      0
        -- irq_mask(7:4): 0xF (15)
        -- timeout(15:8): 100 (0x64)
        -- Total: 0x000064F1
        axi_read(x"00003010", rdata32);
        check_value(rdata32, x"000064F1", "Control Reg Default");
        
        -- Check output ports
        if enable /= '1' then
            write(l, string'("FAIL: output 'enable' default not 1"));
        end if;
        if irq_mask /= x"F" then
            write(l, string'("FAIL: output 'irq_mask' default not 0xF"));
        end if;
        writeline(output, l);

        ---------------------------------------------------------
        -- Test 2: Subregister Read (RO) - Status Reg (0x04)
        ---------------------------------------------------------
        ready <= '1';
        err_flag <= '0';
        busy  <= '1';
        state <= x"A"; -- 1010
        count <= x"55";
        wait for 20 ns;
        
        -- Expected Read Value:
        -- ready(0): 1
        -- error(1): 0
        busy  <= '1';
        state <= x"A"; -- 1010
        count <= x"55";
        wait for 20 ns;
        
        -- Expected Read Value:
        -- ready(0): 1
        -- error(1): 0
        -- busy(2):  1
        -- reserved(3): 0
        -- state(7:4): 1010 (0xA)
        -- count(15:8): 0x55
        -- Total: 0x000055A5 (0101 0101   1010  0 1 0 1)
        
        axi_read(x"00003004", rdata32);
        check_value(rdata32, x"000055A5", "Status Reg (Packed RO) Read");
        
        ---------------------------------------------------------
        -- Test 3: Subregister Write (RW) - Control Reg (0x10)
        ---------------------------------------------------------
        -- Write:
        -- enable(0): 0
        -- mode(1):   1
        -- irq_mask(7:4): 0x5
        -- timeout(15:8): 0x22
        -- Total: 0x00002252 (0010 0010   0101  0 1 0 0) - wait, bit 0 is 0. 2 is 0010.
        -- 0x22 -> 0010 0010
        -- 0x5  -> 0101
        -- mode=1, enable=0 -> 10 => 0x2
        -- So 0x2252 is correct?
        -- 15:8 | 7:4  | 3:2 | 1    | 0
        -- 22   | 5    | 00  | 1    | 0
        
        axi_write(x"00003010", x"00002252");
        wait for 20 ns;
        
        if enable = '0' and mode = '1' and irq_mask = x"5" and timeout = x"22" then
            write(l, string'("PASS: Control Reg Write Outputs Correct"));
        else
            write(l, string'("FAIL: Control Reg Write Outputs Incorrect"));
            write(l, string'("  Enable: ") & std_logic'image(enable));
            write(l, string'("  Mode: ") & std_logic'image(mode));
        end if;
        writeline(output, l);
        
        axi_read(x"00003010", rdata32);
        check_value(rdata32, x"00002252", "Control Reg Readback");

        write(l, string'("--- End of XML Simulation ---"));
        writeline(output, l);
        
        test_done <= true;
        wait;
    end process;

end architecture;
