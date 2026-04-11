//------------------------------------------------------------------------------
// File: sensor_controller.sv
// Description: Example SystemVerilog module demonstrating Axion features
// This module showcases different register types and configurations
//------------------------------------------------------------------------------

// Enable CDC with 3 synchronization stages
// @axion_def CDC_EN CDC_STAGE=3

module sensor_controller (
    // System clocks and reset
    input  logic        clk,
    input  logic        rst_n,

    // Sensor inputs
    input  logic [15:0] temperature,
    input  logic [15:0] pressure,
    input  logic [15:0] humidity,

    // Control outputs
    output logic        fan_enable,
    output logic        heater_enable,
    output logic        alarm_out,

    // Data ready signals
    input  logic        data_valid,
    input  logic        error_flag
);

    // Read-Only Registers (Hardware writes, Software reads)
    logic [31:0] status_reg;           // @axion RO DESC="System status flags"
    logic [31:0] temperature_reg;      // @axion RO R_STROBE DESC="Temperature sensor reading"
    logic [31:0] pressure_reg;         // @axion RO R_STROBE DESC="Pressure sensor value"
    logic [31:0] humidity_reg;         // @axion RO DESC="Humidity sensor value"
    logic [31:0] error_count_reg;      // @axion RO DESC="Total error count"

    // Write-Only Registers (Software writes, Hardware reads)
    logic [31:0] control_reg;          // @axion WO W_STROBE DESC="Main control register"
    logic [31:0] threshold_high_reg;   // @axion WO DESC="High threshold value"
    logic [31:0] threshold_low_reg;    // @axion WO DESC="Low threshold value"

    // Read-Write Registers (Both can access)
    logic [31:0] config_reg;           // @axion RW
    logic [31:0] calibration_reg;      // @axion RW R_STROBE W_STROBE
    logic [31:0] mode_reg;             // @axion RW

    // Manual address assignment test
    logic [31:0] debug_reg;            // @axion RW
    logic [31:0] timestamp_reg;        // @axion RO

    // Combined features test
    logic [31:0] interrupt_status_reg; // @axion RW R_STROBE W_STROBE

    // Internal signals
    logic [31:0] error_counter;
    logic [31:0] timestamp_counter;

    // Status register composition
    assign status_reg = {
        27'h0000000,
        alarm_out,
        heater_enable,
        fan_enable,
        error_flag,
        data_valid
    };

    // Temperature register (16-bit sensor data + padding)
    assign temperature_reg = {16'h0000, temperature};

    // Pressure register (16-bit sensor data + padding)
    assign pressure_reg = {16'h0000, pressure};

    // Humidity register (16-bit sensor data + padding)
    assign humidity_reg = {16'h0000, humidity};

    // Error counter
    assign error_count_reg = error_counter;

    // Control outputs from control register
    assign fan_enable = control_reg[0];
    assign heater_enable = control_reg[1];
    assign alarm_out = control_reg[2];

    // Timestamp register
    assign timestamp_reg = timestamp_counter;

    // Error counter process
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            error_counter <= '0;
        end else begin
            if (error_flag)
                error_counter <= error_counter + 1;
        end
    end

    // Timestamp counter process
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            timestamp_counter <= '0;
        end else begin
            timestamp_counter <= timestamp_counter + 1;
        end
    end

endmodule
