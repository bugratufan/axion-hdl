// @axion_def BASE_ADDR=0x0000
module enum_test_mod (
    input logic clk,
    input logic rst
);

// Standalone register with enum values
logic [1:0] status_reg; // @axion RO ADDR=0x00 ENUM="0:IDLE,1:WAITING,3:READY" DESC="Status register"

// Another register without enum
logic [31:0] data_reg; // @axion RW ADDR=0x04 DESC="Data register"

endmodule
