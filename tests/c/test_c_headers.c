/**
 * @file test_c_headers.c
 * @brief C Header Compilation and Validation Test
 * @note Tests generated C headers for:
 *       - Syntax correctness (compilation)
 *       - Address offset consistency
 *       - Macro definitions with module prefix
 *       - Structure alignment
 *       - No namespace collisions between modules
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
 * Include both headers - no conflicts due to module prefixes!
 ******************************************************************************/
#include "../../output/sensor_controller_regs.h"
#include "../../output/spi_controller_regs.h"

/*******************************************************************************
 * Test: Header Inclusion Without Conflicts
 ******************************************************************************/
void test_header_inclusion(void) {
    TEST_SECTION("Header Inclusion (No Namespace Conflicts)");
    
    /* Both headers can be included simultaneously without conflicts */
    TEST_ASSERT(1, "Both headers included without redefinition errors");
    
    /* Verify each module has its own unique macro names */
    TEST_ASSERT(SENSOR_CONTROLLER_BASE_ADDR != SPI_CONTROLLER_BASE_ADDR,
                "Module base addresses are distinct");
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
    
    /* No overlap */
    TEST_ASSERT(SENSOR_CONTROLLER_INTERRUPT_STATUS_REG_ADDR < SPI_CONTROLLER_CTRL_REG_ADDR,
                "No address overlap between modules");
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
}

/*******************************************************************************
 * Main Test Entry Point
 ******************************************************************************/
int main(void) {
    printf("================================================================================\n");
    printf("                   AXION HDL - C Header Test Suite\n");
    printf("                   Testing Module-Prefixed Headers\n");
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
