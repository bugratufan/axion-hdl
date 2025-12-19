"""
Address Manager Module

Provides automatic address assignment and management for register spaces.
Handles address alignment, conflict detection, and address map generation.
"""

from typing import Dict, List, Optional, Set, Tuple


class AddressConflictError(Exception):
    """
    Exception raised when address conflicts are detected.
    
    This error is raised when two or more registers are assigned to the same
    address, which violates the AXI4-Lite protocol requirements.
    
    Related Requirements:
    - AXION-006: Register Address Mapping - Each register must have a unique address
    - AXION-007: Base Address Offset Calculation - Addresses must be correctly calculated
    - AXION-008: Module Address Space Isolation - No address overlap within a module
    """
    
    def __init__(self, address: int, existing_signal: str, new_signal: str, module_name: str = ""):
        self.address = address
        self.existing_signal = existing_signal
        self.new_signal = new_signal
        self.module_name = module_name
        
        module_info = f" in module '{module_name}'" if module_name else ""
        
        self.clean_message = (
            f"Address Conflict{module_info}: Address 0x{address:04X} is already assigned to '{existing_signal}'. "
            f"Cannot assign to '{new_signal}'."
        )
        
        self.formatted_message = (
            f"\n"
            f"╔══════════════════════════════════════════════════════════════════════════════╗\n"
            f"║                          ADDRESS CONFLICT ERROR                              ║\n"
            f"╠══════════════════════════════════════════════════════════════════════════════╣\n"
            f"║ Address 0x{address:04X} is already assigned{module_info}                     \n"
            f"╠══════════════════════════════════════════════════════════════════════════════╣\n"
            f"║ Existing register: {existing_signal:<56} ║\n"
            f"║ Conflicting register: {new_signal:<53} ║\n"
            f"╠══════════════════════════════════════════════════════════════════════════════╣\n"
            f"║ VIOLATED REQUIREMENTS:                                                       ║\n"
            f"║   • AXION-006: Each register must have a unique address                      ║\n"
            f"║   • AXION-007: Address offsets must be correctly calculated                  ║\n"
            f"║   • AXION-008: No address overlap allowed within a module                    ║\n"
            f"╠══════════════════════════════════════════════════════════════════════════════╣\n"
            f"║ SOLUTION: Change the ADDR attribute for one of the registers:                ║\n"
            f"║   signal {new_signal} : ... -- @axion ... ADDR=0x{address+4:04X}             \n"
            f"║   Or remove ADDR to use auto-assignment                                      ║\n"
            f"╚══════════════════════════════════════════════════════════════════════════════╝\n"
        )
        super().__init__(self.clean_message)


class AddressManager:
    """
    Manages register address allocation and validation.
    
    Features:
    - Automatic address assignment with alignment
    - Manual address specification and conflict detection
    - Address range validation
    - Address map generation
    """
    
    def __init__(self, start_addr: int = 0x00, alignment: int = 4, module_name: str = ""):
        """
        Initialize AddressManager.
        
        Args:
            start_addr: Starting address for auto-assignment (default: 0x00)
            alignment: Address alignment in bytes (default: 4)
            module_name: Name of the module (for error messages)
        """
        self.start_addr = start_addr
        self.alignment = alignment
        self.module_name = module_name
        self.auto_counter = start_addr
        self.assigned_addresses: Set[int] = set()
        # Track which signal is at which address
        self.address_to_signal: Dict[int, str] = {}
        
    def reset(self):
        """Reset the address counter and assigned addresses."""
        self.auto_counter = self.start_addr
        self.assigned_addresses.clear()
        self.address_to_signal.clear()
        
    def allocate_address(self, manual_addr: Optional[int] = None, signal_width: int = 32, signal_name: str = "") -> int:
        """
        Allocate an address, either manually specified or auto-assigned.
        
        Args:
            manual_addr: Manual address specification (hex or decimal)
            signal_width: Width of the signal in bits (default: 32)
            signal_name: Name of the signal (for error messages)
            
        Returns:
            Allocated address as integer (base address for wide signals)
            
        Raises:
            AddressConflictError: If address conflicts with existing assignment
            ValueError: If address is invalid
            
        Note:
            For signals wider than 32 bits, multiple consecutive 4-byte
            address slots are reserved. Each 32-bit chunk can be accessed
            at base_addr + (chunk_index * 4).
        """
        # Calculate number of registers needed for this signal
        num_regs = (signal_width + 31) // 32  # Ceiling division
        size_bytes = num_regs * self.alignment
        
        if manual_addr is not None:
            # Manual address assignment
            addr = self._validate_address(manual_addr)
            # Check for conflicts across all addresses this signal will occupy
            for offset in range(0, size_bytes, self.alignment):
                check_addr = addr + offset
                if check_addr in self.assigned_addresses:
                    existing_signal = self.address_to_signal.get(check_addr, "unknown")
                    raise AddressConflictError(
                        address=check_addr,
                        existing_signal=existing_signal,
                        new_signal=signal_name or "unknown",
                        module_name=self.module_name
                    )
            # Mark all addresses as assigned
            for offset in range(0, size_bytes, self.alignment):
                self.assigned_addresses.add(addr + offset)
                self.address_to_signal[addr + offset] = signal_name
            # Update auto counter if needed
            self.auto_counter = max(self.auto_counter, addr + size_bytes)
            return addr
        else:
            # Auto address assignment
            addr = self._align_address(self.auto_counter)
            # Find next available contiguous block
            while any((addr + offset) in self.assigned_addresses for offset in range(0, size_bytes, self.alignment)):
                addr += self.alignment
            # Mark all addresses as assigned
            for offset in range(0, size_bytes, self.alignment):
                self.assigned_addresses.add(addr + offset)
                self.address_to_signal[addr + offset] = signal_name
            self.auto_counter = addr + size_bytes
            return addr
    
    def _align_address(self, addr: int) -> int:
        """Align address to configured alignment."""
        if addr % self.alignment != 0:
            return ((addr // self.alignment) + 1) * self.alignment
        return addr
    
    def _validate_address(self, addr: int) -> int:
        """Validate address alignment and range."""
        if addr < 0:
            raise ValueError(f"Address cannot be negative: {addr}")
        if addr % self.alignment != 0:
            raise ValueError(
                f"Address 0x{addr:02X} not aligned to {self.alignment} bytes"
            )
        return addr
    
    def parse_address_string(self, addr_str: str) -> int:
        """
        Parse address string (supports hex with 0x prefix or decimal).
        
        Args:
            addr_str: Address string (e.g., "0x10" or "16")
            
        Returns:
            Address as integer
        """
        addr_str = addr_str.strip()
        if addr_str.startswith('0x') or addr_str.startswith('0X'):
            return int(addr_str, 16)
        else:
            return int(addr_str)
    
    def format_address(self, addr: int, width: int = 2) -> str:
        """
        Format address as hex string.
        
        Args:
            addr: Address as integer
            width: Minimum hex width (default: 2)
            
        Returns:
            Formatted address string (e.g., "0x10")
        """
        return f"0x{addr:0{width}X}"
    
    def get_address_map(self) -> List[int]:
        """
        Get sorted list of assigned addresses.
        
        Returns:
            Sorted list of addresses
        """
        return sorted(list(self.assigned_addresses))
    
    def get_next_available_address(self) -> int:
        """Get next available auto-assigned address."""
        return self.auto_counter
    
    def check_conflicts(self, addresses: List[int]) -> List[tuple]:
        """
        Check for conflicts in a list of addresses.
        
        Args:
            addresses: List of addresses to check
            
        Returns:
            List of (addr, count) tuples for conflicting addresses
        """
        from collections import Counter
        counts = Counter(addresses)
        conflicts = [(addr, count) for addr, count in counts.items() if count > 1]
        return conflicts
