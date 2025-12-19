/**
 * @file test_c_headers.c
 * @brief C Header Compilation and Validation Test
 * @note Tests generated C headers for:
 *       - Syntax correctness (compilation)
 *       - Address offset consistency
 *       - Macro definitions with module prefix
 *       - Structure alignment
 *       - No namespace collisions between modules
 *       - Multi-register signal support (AXION-025/026)
 * 
 * Build: gcc -Wall -Wextra -Werror -pedantic -std=c11 -o test_c_headers test_c_headers.c
 * Run:   ./test_c_headers
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <assert.h>

/* Test counters */
static int tests_passed = 0;
static int tests_failed = 0;

/* Test macros */
#define TEST_ASSERT(cond, msg) do { \
    if (cond) { \
        printf("  [PASS] %s\n", msg); \
        tests_passed++; \
    } else { \
        printf("  [FAIL] %s\n", msg); \
        tests_failed++; \
    } \
} while(0)

#define TEST_SECTION(name) printf("\n=== %s ===\n", name)

/*******************************************************************************
 * Include all three headers - no conflicts due to module prefixes!
 ******************************************************************************/
#include "sensor_controller_regs.h"
#include "spi_controller_regs.h"
#include "mixed_width_controller_regs.h"
#include "subregister_test_xml_regs.h"

/*******************************************************************************
 * Test: Header Inclusion Without Conflicts
 ******************************************************************************/
void test_header_inclusion(void) {
    TEST_SECTION("Header Inclusion (No Namespace Conflicts)");
    
    /* All three headers can be included simultaneously without conflicts */
    TEST_ASSERT(1, "All three headers included without redefinition errors");
    
    /* Verify each module has its own unique macro names */
    TEST_ASSERT(SENSOR_CONTROLLER_BASE_ADDR != SPI_CONTROLLER_BASE_ADDR,
                "Sensor and SPI base addresses are distinct");
    TEST_ASSERT(SPI_CONTROLLER_BASE_ADDR != MIXED_WIDTH_CONTROLLER_BASE_ADDR,
                "SPI and Mixed-Width base addresses are distinct");
    TEST_ASSERT(SENSOR_CONTROLLER_BASE_ADDR != MIXED_WIDTH_CONTROLLER_BASE_ADDR,
                "Sensor and Mixed-Width base addresses are distinct");
}

/*******************************************************************************
 * Test: Sensor Controller Base Address
 ******************************************************************************/
void test_sensor_controller_base_address(void) {
    TEST_SECTION("Sensor Controller Base Address");
    
    TEST_ASSERT(SENSOR_CONTROLLER_BASE_ADDR == 0x00000000,
                "SENSOR_CONTROLLER_BASE_ADDR = 0x00000000");
}

/*******************************************************************************
 * Test: Sensor Controller Register Offsets
 ******************************************************************************/
void test_sensor_controller_offsets(void) {
    TEST_SECTION("Sensor Controller Register Offsets");
    
    /* Verify all offset definitions exist and have expected values */
    TEST_ASSERT(SENSOR_CONTROLLER_STATUS_REG_OFFSET == 0x00, 
                "SENSOR_CONTROLLER_STATUS_REG_OFFSET = 0x00");
    TEST_ASSERT(SENSOR_CONTROLLER_TEMPERATURE_REG_OFFSET == 0x04, 
                "SENSOR_CONTROLLER_TEMPERATURE_REG_OFFSET = 0x04");
    TEST_ASSERT(SENSOR_CONTROLLER_PRESSURE_REG_OFFSET == 0x08, 
                "SENSOR_CONTROLLER_PRESSURE_REG_OFFSET = 0x08");
    TEST_ASSERT(SENSOR_CONTROLLER_HUMIDITY_REG_OFFSET == 0x0C, 
                "SENSOR_CONTROLLER_HUMIDITY_REG_OFFSET = 0x0C");
    TEST_ASSERT(SENSOR_CONTROLLER_ERROR_COUNT_REG_OFFSET == 0x10, 
                "SENSOR_CONTROLLER_ERROR_COUNT_REG_OFFSET = 0x10");
    TEST_ASSERT(SENSOR_CONTROLLER_CONTROL_REG_OFFSET == 0x14, 
                "SENSOR_CONTROLLER_CONTROL_REG_OFFSET = 0x14");
    TEST_ASSERT(SENSOR_CONTROLLER_THRESHOLD_HIGH_REG_OFFSET == 0x18, 
                "SENSOR_CONTROLLER_THRESHOLD_HIGH_REG_OFFSET = 0x18");
    TEST_ASSERT(SENSOR_CONTROLLER_THRESHOLD_LOW_REG_OFFSET == 0x20, 
                "SENSOR_CONTROLLER_THRESHOLD_LOW_REG_OFFSET = 0x20");
    TEST_ASSERT(SENSOR_CONTROLLER_CONFIG_REG_OFFSET == 0x24, 
                "SENSOR_CONTROLLER_CONFIG_REG_OFFSET = 0x24");
    TEST_ASSERT(SENSOR_CONTROLLER_CALIBRATION_REG_OFFSET == 0x28, 
                "SENSOR_CONTROLLER_CALIBRATION_REG_OFFSET = 0x28");
    TEST_ASSERT(SENSOR_CONTROLLER_MODE_REG_OFFSET == 0x30, 
                "SENSOR_CONTROLLER_MODE_REG_OFFSET = 0x30");
    TEST_ASSERT(SENSOR_CONTROLLER_DEBUG_REG_OFFSET == 0x100, 
                "SENSOR_CONTROLLER_DEBUG_REG_OFFSET = 0x100");
    TEST_ASSERT(SENSOR_CONTROLLER_TIMESTAMP_REG_OFFSET == 0x104, 
                "SENSOR_CONTROLLER_TIMESTAMP_REG_OFFSET = 0x104");
    TEST_ASSERT(SENSOR_CONTROLLER_INTERRUPT_STATUS_REG_OFFSET == 0x200, 
                "SENSOR_CONTROLLER_INTERRUPT_STATUS_REG_OFFSET = 0x200");
}

/*******************************************************************************
 * Test: Sensor Controller Absolute Addresses
 ******************************************************************************/
void test_sensor_controller_absolute_addresses(void) {
    TEST_SECTION("Sensor Controller Absolute Addresses");
    
    /* Verify absolute addresses = BASE + OFFSET */
    TEST_ASSERT(SENSOR_CONTROLLER_STATUS_REG_ADDR == 
                (SENSOR_CONTROLLER_BASE_ADDR + SENSOR_CONTROLLER_STATUS_REG_OFFSET),
                "STATUS_REG_ADDR = BASE + OFFSET");
    TEST_ASSERT(SENSOR_CONTROLLER_TEMPERATURE_REG_ADDR == 
                (SENSOR_CONTROLLER_BASE_ADDR + SENSOR_CONTROLLER_TEMPERATURE_REG_OFFSET),
                "TEMPERATURE_REG_ADDR = BASE + OFFSET");
    TEST_ASSERT(SENSOR_CONTROLLER_CONFIG_REG_ADDR == 
                (SENSOR_CONTROLLER_BASE_ADDR + SENSOR_CONTROLLER_CONFIG_REG_OFFSET),
                "CONFIG_REG_ADDR = BASE + OFFSET");
    TEST_ASSERT(SENSOR_CONTROLLER_DEBUG_REG_ADDR == 
                (SENSOR_CONTROLLER_BASE_ADDR + SENSOR_CONTROLLER_DEBUG_REG_OFFSET),
                "DEBUG_REG_ADDR = BASE + OFFSET");
    TEST_ASSERT(SENSOR_CONTROLLER_INTERRUPT_STATUS_REG_ADDR == 
                (SENSOR_CONTROLLER_BASE_ADDR + SENSOR_CONTROLLER_INTERRUPT_STATUS_REG_OFFSET),
                "INTERRUPT_STATUS_REG_ADDR = BASE + OFFSET");
}

/*******************************************************************************
 * Test: SPI Controller Base Address
 ******************************************************************************/
void test_spi_controller_base_address(void) {
    TEST_SECTION("SPI Controller Base Address");
    
    TEST_ASSERT(SPI_CONTROLLER_BASE_ADDR == 0x00001000,
                "SPI_CONTROLLER_BASE_ADDR = 0x00001000");
}

/*******************************************************************************
 * Test: SPI Controller Register Offsets
 ******************************************************************************/
void test_spi_controller_offsets(void) {
    TEST_SECTION("SPI Controller Register Offsets");
    
    TEST_ASSERT(SPI_CONTROLLER_CTRL_REG_OFFSET == 0x00, 
                "SPI_CONTROLLER_CTRL_REG_OFFSET = 0x00");
    TEST_ASSERT(SPI_CONTROLLER_STATUS_REG_OFFSET == 0x04, 
                "SPI_CONTROLLER_STATUS_REG_OFFSET = 0x04");
    TEST_ASSERT(SPI_CONTROLLER_TX_DATA_OFFSET == 0x08, 
                "SPI_CONTROLLER_TX_DATA_OFFSET = 0x08");
    TEST_ASSERT(SPI_CONTROLLER_RX_DATA_OFFSET == 0x0C, 
                "SPI_CONTROLLER_RX_DATA_OFFSET = 0x0C");
    TEST_ASSERT(SPI_CONTROLLER_CLK_DIV_OFFSET == 0x10, 
                "SPI_CONTROLLER_CLK_DIV_OFFSET = 0x10");
    TEST_ASSERT(SPI_CONTROLLER_CS_MASK_OFFSET == 0x14, 
                "SPI_CONTROLLER_CS_MASK_OFFSET = 0x14");
    TEST_ASSERT(SPI_CONTROLLER_INT_ENABLE_OFFSET == 0x18, 
                "SPI_CONTROLLER_INT_ENABLE_OFFSET = 0x18");
    TEST_ASSERT(SPI_CONTROLLER_FIFO_STATUS_OFFSET == 0x1C, 
                "SPI_CONTROLLER_FIFO_STATUS_OFFSET = 0x1C");
}

/*******************************************************************************
 * Test: SPI Controller Absolute Addresses
 ******************************************************************************/
void test_spi_controller_absolute_addresses(void) {
    TEST_SECTION("SPI Controller Absolute Addresses");
    
    /* SPI base is 0x1000, so absolute = 0x1000 + offset */
    TEST_ASSERT(SPI_CONTROLLER_CTRL_REG_ADDR == 0x1000,
                "SPI_CONTROLLER_CTRL_REG_ADDR = 0x1000");
    TEST_ASSERT(SPI_CONTROLLER_STATUS_REG_ADDR == 0x1004,
                "SPI_CONTROLLER_STATUS_REG_ADDR = 0x1004");
    TEST_ASSERT(SPI_CONTROLLER_FIFO_STATUS_ADDR == 0x101C,
                "SPI_CONTROLLER_FIFO_STATUS_ADDR = 0x101C");
}

/*******************************************************************************
 * Test: Register Structure Exists
 ******************************************************************************/
void test_register_structures(void) {
    TEST_SECTION("Register Structures");
    
    /* Test that structure types exist and have correct size estimates */
    TEST_ASSERT(sizeof(sensor_controller_regs_t) > 0,
                "sensor_controller_regs_t structure defined");
    TEST_ASSERT(sizeof(spi_controller_regs_t) > 0,
                "spi_controller_regs_t structure defined");
    
    /* Each register is uint32_t (4 bytes) */
    TEST_ASSERT(sizeof(sensor_controller_regs_t) >= 14 * sizeof(uint32_t),
                "sensor_controller_regs_t has at least 14 registers");
    TEST_ASSERT(sizeof(spi_controller_regs_t) >= 8 * sizeof(uint32_t),
                "spi_controller_regs_t has at least 8 registers");
}

/*******************************************************************************
 * Test: Module Prefix Consistency
 ******************************************************************************/
void test_module_prefix_consistency(void) {
    TEST_SECTION("Module Prefix Consistency");
    
    /* Verify SENSOR_CONTROLLER prefix is used consistently */
    #ifdef SENSOR_CONTROLLER_STATUS_REG_OFFSET
    TEST_ASSERT(1, "SENSOR_CONTROLLER_STATUS_REG_OFFSET uses correct prefix");
    #else
    TEST_ASSERT(0, "SENSOR_CONTROLLER_STATUS_REG_OFFSET uses correct prefix");
    #endif
    
    /* Verify SPI_CONTROLLER prefix is used consistently */
    #ifdef SPI_CONTROLLER_CTRL_REG_OFFSET
    TEST_ASSERT(1, "SPI_CONTROLLER_CTRL_REG_OFFSET uses correct prefix");
    #else
    TEST_ASSERT(0, "SPI_CONTROLLER_CTRL_REG_OFFSET uses correct prefix");
    #endif
    
    /* Verify no unprefixed macros exist (old style) */
    #ifndef STATUS_REG_OFFSET
    TEST_ASSERT(1, "No unprefixed STATUS_REG_OFFSET (no conflicts possible)");
    #else
    TEST_ASSERT(0, "Unprefixed STATUS_REG_OFFSET exists (potential conflict)");
    #endif
}

/*******************************************************************************
 * Test: Access Macro Existence
 ******************************************************************************/
void test_access_macros(void) {
    TEST_SECTION("Access Macros");
    
    /* Verify READ macros exist for readable registers */
    #ifdef SENSOR_CONTROLLER_READ_STATUS_REG
    TEST_ASSERT(1, "SENSOR_CONTROLLER_READ_STATUS_REG() macro exists");
    #else
    TEST_ASSERT(0, "SENSOR_CONTROLLER_READ_STATUS_REG() macro missing");
    #endif
    
    #ifdef SENSOR_CONTROLLER_READ_CONFIG_REG
    TEST_ASSERT(1, "SENSOR_CONTROLLER_READ_CONFIG_REG() macro exists");
    #else
    TEST_ASSERT(0, "SENSOR_CONTROLLER_READ_CONFIG_REG() macro missing");
    #endif
    
    /* Verify WRITE macros exist for writable registers */
    #ifdef SENSOR_CONTROLLER_WRITE_CONTROL_REG
    TEST_ASSERT(1, "SENSOR_CONTROLLER_WRITE_CONTROL_REG() macro exists");
    #else
    TEST_ASSERT(0, "SENSOR_CONTROLLER_WRITE_CONTROL_REG() macro missing");
    #endif
    
    #ifdef SENSOR_CONTROLLER_WRITE_CONFIG_REG
    TEST_ASSERT(1, "SENSOR_CONTROLLER_WRITE_CONFIG_REG() macro exists");
    #else
    TEST_ASSERT(0, "SENSOR_CONTROLLER_WRITE_CONFIG_REG() macro missing");
    #endif
    
    /* Verify SPI macros */
    #ifdef SPI_CONTROLLER_READ_STATUS_REG
    TEST_ASSERT(1, "SPI_CONTROLLER_READ_STATUS_REG() macro exists");
    #else
    TEST_ASSERT(0, "SPI_CONTROLLER_READ_STATUS_REG() macro missing");
    #endif
    
    #ifdef SPI_CONTROLLER_WRITE_CTRL_REG
    TEST_ASSERT(1, "SPI_CONTROLLER_WRITE_CTRL_REG() macro exists");
    #else
    TEST_ASSERT(0, "SPI_CONTROLLER_WRITE_CTRL_REG() macro missing");
    #endif
}

/*******************************************************************************
 * Test: Address Space Isolation Between Modules
 ******************************************************************************/
void test_address_space_isolation(void) {
    TEST_SECTION("Address Space Isolation");
    
    /* Sensor controller should be at 0x0000-0x0FFF range */
    TEST_ASSERT(SENSOR_CONTROLLER_STATUS_REG_ADDR < 0x1000,
                "Sensor controller registers in 0x0000-0x0FFF range");
    TEST_ASSERT(SENSOR_CONTROLLER_INTERRUPT_STATUS_REG_ADDR < 0x1000,
                "All sensor registers below SPI base address");
    
    /* SPI controller should be at 0x1000+ range */
    TEST_ASSERT(SPI_CONTROLLER_CTRL_REG_ADDR >= 0x1000,
                "SPI controller registers start at 0x1000+");
    TEST_ASSERT(SPI_CONTROLLER_FIFO_STATUS_ADDR >= 0x1000,
                "All SPI registers at or above 0x1000");
    
    /* Mixed-width controller should be at 0x2000+ range */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_BASE_ADDR >= 0x2000,
                "Mixed-width controller registers start at 0x2000+");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_FINAL_REG_ADDR >= 0x2000,
                "All mixed-width registers at or above 0x2000");
    
    /* No overlap */
    TEST_ASSERT(SENSOR_CONTROLLER_INTERRUPT_STATUS_REG_ADDR < SPI_CONTROLLER_CTRL_REG_ADDR,
                "No address overlap between Sensor and SPI modules");
    TEST_ASSERT(SPI_CONTROLLER_FIFO_STATUS_ADDR < MIXED_WIDTH_CONTROLLER_ENABLE_FLAG_ADDR,
                "No address overlap between SPI and Mixed-width modules");
}

/*******************************************************************************
 * Test: Register Pointer Macros
 ******************************************************************************/
void test_register_pointer_macros(void) {
    TEST_SECTION("Register Pointer Macros");
    
    /* Verify REGS pointer macros exist */
    #ifdef SENSOR_CONTROLLER_REGS
    TEST_ASSERT(1, "SENSOR_CONTROLLER_REGS pointer macro exists");
    #else
    TEST_ASSERT(0, "SENSOR_CONTROLLER_REGS pointer macro missing");
    #endif
    
    #ifdef SPI_CONTROLLER_REGS
    TEST_ASSERT(1, "SPI_CONTROLLER_REGS pointer macro exists");
    #else
    TEST_ASSERT(0, "SPI_CONTROLLER_REGS pointer macro missing");
    #endif
    
    #ifdef MIXED_WIDTH_CONTROLLER_REGS
    TEST_ASSERT(1, "MIXED_WIDTH_CONTROLLER_REGS pointer macro exists");
    #else
    TEST_ASSERT(0, "MIXED_WIDTH_CONTROLLER_REGS pointer macro missing");
    #endif
}

/*******************************************************************************
 * AXION-025/026: Mixed Width Controller Tests
 ******************************************************************************/
void test_mixed_width_controller_base_address(void) {
    TEST_SECTION("Mixed-Width Controller Base Address (AXION-025/026)");
    
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_BASE_ADDR == 0x00002000,
                "Mixed-width base address is 0x2000");
}

void test_mixed_width_controller_narrow_signals(void) {
    TEST_SECTION("Mixed-Width Controller Narrow Signal Offsets");
    
    /* 1-bit signals */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_ENABLE_FLAG_OFFSET == 0x00,
                "1-bit enable_flag offset is 0x00");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_BUSY_STATUS_OFFSET == 0x04,
                "1-bit busy_status offset is 0x04");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_TRIGGER_PULSE_OFFSET == 0x08,
                "1-bit trigger_pulse offset is 0x08");
    
    /* 6-bit signals */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_CHANNEL_SELECT_OFFSET == 0x0C,
                "6-bit channel_select offset is 0x0C");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_ERROR_CODE_OFFSET == 0x10,
                "6-bit error_code offset is 0x10");
    
    /* 8-bit signal */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_MODE_SELECT_OFFSET == 0x2C,
                "8-bit mode_select offset is 0x2C");
    
    /* 16-bit signals */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_TIMESTAMP_HIGH_OFFSET == 0x24,
                "16-bit timestamp_high offset is 0x24");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_THRESHOLD_VALUE_OFFSET == 0x28,
                "16-bit threshold_value offset is 0x28");
    
    /* 32-bit signals */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_CONFIG_REG_OFFSET == 0x14,
                "32-bit config_reg offset is 0x14");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_STATUS_REG_OFFSET == 0x18,
                "32-bit status_reg offset is 0x18");
}

void test_mixed_width_controller_wide_signals(void) {
    TEST_SECTION("Mixed-Width Controller Wide Signal Multi-Register Offsets");
    
    /* 48-bit wide_counter: 2 registers */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_WIDE_COUNTER_REG0_OFFSET == 0x30,
                "48-bit wide_counter REG0 offset is 0x30");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_WIDE_COUNTER_REG1_OFFSET == 0x34,
                "48-bit wide_counter REG1 offset is 0x34");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_WIDE_COUNTER_WIDTH == 48,
                "wide_counter width is 48 bits");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_WIDE_COUNTER_NUM_REGS == 2,
                "wide_counter uses 2 registers");
    
    /* 64-bit long_timestamp: 2 registers */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_LONG_TIMESTAMP_REG0_OFFSET == 0x38,
                "64-bit long_timestamp REG0 offset is 0x38");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_LONG_TIMESTAMP_REG1_OFFSET == 0x3C,
                "64-bit long_timestamp REG1 offset is 0x3C");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_LONG_TIMESTAMP_WIDTH == 64,
                "long_timestamp width is 64 bits");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_LONG_TIMESTAMP_NUM_REGS == 2,
                "long_timestamp uses 2 registers");
    
    /* 100-bit very_wide_data: 4 registers */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_REG0_OFFSET == 0x40,
                "100-bit very_wide_data REG0 offset is 0x40");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_REG1_OFFSET == 0x44,
                "100-bit very_wide_data REG1 offset is 0x44");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_REG2_OFFSET == 0x48,
                "100-bit very_wide_data REG2 offset is 0x48");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_REG3_OFFSET == 0x4C,
                "100-bit very_wide_data REG3 offset is 0x4C");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_WIDTH == 100,
                "very_wide_data width is 100 bits");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_NUM_REGS == 4,
                "very_wide_data uses 4 registers");
    
    /* 200-bit huge_data: 7 registers */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG0_OFFSET == 0x50,
                "200-bit huge_data REG0 offset is 0x50");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG1_OFFSET == 0x54,
                "200-bit huge_data REG1 offset is 0x54");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG2_OFFSET == 0x58,
                "200-bit huge_data REG2 offset is 0x58");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG3_OFFSET == 0x5C,
                "200-bit huge_data REG3 offset is 0x5C");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG4_OFFSET == 0x60,
                "200-bit huge_data REG4 offset is 0x60");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG5_OFFSET == 0x64,
                "200-bit huge_data REG5 offset is 0x64");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG6_OFFSET == 0x68,
                "200-bit huge_data REG6 offset is 0x68");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_WIDTH == 200,
                "huge_data width is 200 bits");
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_NUM_REGS == 7,
                "huge_data uses 7 registers");
    
    /* final_reg after wide signals */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_FINAL_REG_OFFSET == 0x6C,
                "final_reg offset is 0x6C (after all wide signals)");
}

void test_mixed_width_controller_address_continuity(void) {
    TEST_SECTION("Mixed-Width Controller Address Continuity");
    
    /* Verify multi-register signals have contiguous addresses */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_WIDE_COUNTER_REG1_OFFSET == 
                MIXED_WIDTH_CONTROLLER_WIDE_COUNTER_REG0_OFFSET + 4,
                "wide_counter registers are contiguous (REG1 = REG0 + 4)");
    
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_LONG_TIMESTAMP_REG1_OFFSET == 
                MIXED_WIDTH_CONTROLLER_LONG_TIMESTAMP_REG0_OFFSET + 4,
                "long_timestamp registers are contiguous (REG1 = REG0 + 4)");
    
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_REG3_OFFSET == 
                MIXED_WIDTH_CONTROLLER_VERY_WIDE_DATA_REG0_OFFSET + 12,
                "very_wide_data registers are contiguous (REG3 = REG0 + 12)");
    
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG6_OFFSET == 
                MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG0_OFFSET + 24,
                "huge_data registers are contiguous (REG6 = REG0 + 24)");
    
    /* Verify final_reg comes after huge_data */
    TEST_ASSERT(MIXED_WIDTH_CONTROLLER_FINAL_REG_OFFSET == 
                MIXED_WIDTH_CONTROLLER_HUGE_DATA_REG6_OFFSET + 4,
                "final_reg follows huge_data (FINAL = HUGE_REG6 + 4)");
}

void test_mixed_width_controller_access_macros(void) {
    TEST_SECTION("Mixed-Width Controller Access Macros");
    
    /* Check that multi-register read macros exist */
    #ifdef MIXED_WIDTH_CONTROLLER_READ_WIDE_COUNTER_REG0
    TEST_ASSERT(1, "READ_WIDE_COUNTER_REG0 macro exists");
    #else
    TEST_ASSERT(0, "READ_WIDE_COUNTER_REG0 macro missing");
    #endif
    
    #ifdef MIXED_WIDTH_CONTROLLER_READ_WIDE_COUNTER_REG1
    TEST_ASSERT(1, "READ_WIDE_COUNTER_REG1 macro exists");
    #else
    TEST_ASSERT(0, "READ_WIDE_COUNTER_REG1 macro missing");
    #endif
    
    #ifdef MIXED_WIDTH_CONTROLLER_READ_LONG_TIMESTAMP_REG0
    TEST_ASSERT(1, "READ_LONG_TIMESTAMP_REG0 macro exists");
    #else
    TEST_ASSERT(0, "READ_LONG_TIMESTAMP_REG0 macro missing");
    #endif
    
    #ifdef MIXED_WIDTH_CONTROLLER_READ_LONG_TIMESTAMP_REG1
    TEST_ASSERT(1, "READ_LONG_TIMESTAMP_REG1 macro exists");
    #else
    TEST_ASSERT(0, "READ_LONG_TIMESTAMP_REG1 macro missing");
    #endif
    
    #ifdef MIXED_WIDTH_CONTROLLER_READ_HUGE_DATA_REG6
    TEST_ASSERT(1, "READ_HUGE_DATA_REG6 macro exists (last reg of 200-bit)");
    #else
    TEST_ASSERT(0, "READ_HUGE_DATA_REG6 macro missing");
    #endif
    
    /* Check narrow signal macros */
    #ifdef MIXED_WIDTH_CONTROLLER_READ_ENABLE_FLAG
    TEST_ASSERT(1, "READ_ENABLE_FLAG macro exists (1-bit signal)");
    #else
    TEST_ASSERT(0, "READ_ENABLE_FLAG macro missing");
    #endif
    
    #ifdef MIXED_WIDTH_CONTROLLER_WRITE_ENABLE_FLAG
    TEST_ASSERT(1, "WRITE_ENABLE_FLAG macro exists (1-bit RW signal)");
    #else
    TEST_ASSERT(0, "WRITE_ENABLE_FLAG macro missing");
    #endif
    
    #ifdef MIXED_WIDTH_CONTROLLER_WRITE_THRESHOLD_VALUE
    TEST_ASSERT(1, "WRITE_THRESHOLD_VALUE macro exists (16-bit RW signal)");
    #else
    TEST_ASSERT(0, "WRITE_THRESHOLD_VALUE macro missing");
    #endif
}

/*******************************************************************************
 * Test: Subregister Access Macros (MASK/SHIFT)
 ******************************************************************************/
void test_subregister_macros(void) {
    TEST_SECTION("Subregister Macros (MASK/SHIFT)");

    /* Control Register Fields */
    /* enable: bit 0 */
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONTROL_REG_ENABLE_MASK == 0x1, "CONTROL_REG_ENABLE_MASK == 0x1");
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONTROL_REG_ENABLE_SHIFT == 0, "CONTROL_REG_ENABLE_SHIFT == 0");

    /* irq_mask: bits 7:4 (0xF0) */
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONTROL_REG_IRQ_MASK_MASK == 0xF0, "CONTROL_REG_IRQ_MASK_MASK == 0xF0");
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONTROL_REG_IRQ_MASK_SHIFT == 4, "CONTROL_REG_IRQ_MASK_SHIFT == 4");
    
    /* timeout: bits 15:8 (0xFF00) */
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONTROL_REG_TIMEOUT_MASK == 0xFF00, "CONTROL_REG_TIMEOUT_MASK == 0xFF00");
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONTROL_REG_TIMEOUT_SHIFT == 8, "CONTROL_REG_TIMEOUT_SHIFT == 8");
}

/*******************************************************************************
 * Test: Default Value Macros
 ******************************************************************************/
void test_default_value_macros(void) {
    TEST_SECTION("Default Value Macros");
    
    /* Standalone register: config_reg = 0xCAFEBABE */
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONFIG_REG_DEFAULT == 0xCAFEBABE, "CONFIG_REG_DEFAULT == 0xCAFEBABE");
    
    /* Packed register: control_reg
     * enable (bit 0)   = 1    -> 0x0001
     * mode (bit 1)     = 0    -> 0x0000
     * irq_mask (7:4)   = 0xF  -> 0x00F0
     * timeout (15:8)   = 100  -> 0x6400
     * Total            =      -> 0x64F1
     */
    TEST_ASSERT(SUBREGISTER_TEST_XML_CONTROL_REG_DEFAULT == 0x64F1, "CONTROL_REG_DEFAULT == 0x64F1 (Combined subregisters)");
}

/*******************************************************************************
 * Test: Helper Macros (GET_FIELD / SET_FIELD)
 ******************************************************************************/
void test_field_helper_macros(void) {
    TEST_SECTION("Helper Macros (GET_FIELD / SET_FIELD)");
    
    uint32_t val = 0x12345678;
    
    /* GET_FIELD: Extract byte 1 (0x56) -> bits 15:8 -> mask 0xFF00, shift 8 */
    uint32_t extracted = GET_FIELD(val, 0xFF00, 8);
    TEST_ASSERT(extracted == 0x56, "GET_FIELD extracted 0x56 correctly");
    
    /* SET_FIELD: Change byte 1 to 0xAA */
    uint32_t modified = SET_FIELD(val, 0xFF00, 8, 0xAA);
    TEST_ASSERT(modified == 0x1234AA78, "SET_FIELD modified to 0x1234AA78 correctly");
    
    /* Verify original val is untouched */
    TEST_ASSERT(val == 0x12345678, "Original value remains unchanged (macro is functional)");
}

int main(void) {
    printf("================================================================================\n");
    printf("                   AXION HDL - C Header Test Suite\n");
    printf("                   Testing Module-Prefixed Headers\n");
    printf("              Including AXION-025/026 Wide Signal Support\n");
    printf("================================================================================\n");
    
    /* Run all tests */
    test_header_inclusion();
    test_sensor_controller_base_address();
    test_sensor_controller_offsets();
    test_sensor_controller_absolute_addresses();
    test_spi_controller_base_address();
    test_spi_controller_offsets();
    test_spi_controller_absolute_addresses();
    test_register_structures();
    test_module_prefix_consistency();
    test_access_macros();
    test_address_space_isolation();
    test_register_pointer_macros();
    
    /* Mixed-width controller tests (AXION-025/026) */
    test_mixed_width_controller_base_address();
    test_mixed_width_controller_narrow_signals();
    test_mixed_width_controller_wide_signals();
    test_mixed_width_controller_address_continuity();
    test_mixed_width_controller_access_macros();
    
    /* Subregister and Default Value tests (C Header Updates) */
    test_subregister_macros();
    test_default_value_macros();
    test_field_helper_macros();
    
    /* Print summary */
    printf("\n================================================================================\n");
    printf("                           TEST SUMMARY\n");
    printf("================================================================================\n");
    printf("  Total Tests: %d\n", tests_passed + tests_failed);
    printf("  Passed:      %d\n", tests_passed);
    printf("  Failed:      %d\n", tests_failed);
    printf("================================================================================\n");
    
    if (tests_failed > 0) {
        printf("  RESULT: FAILED\n");
        printf("================================================================================\n");
        return 1;
    }
    
    printf("  RESULT: ALL TESTS PASSED\n");
    printf("================================================================================\n");
    return 0;
}
