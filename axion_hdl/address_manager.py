"""
Address Manager Module

Provides automatic address assignment and management for register spaces.
Handles address alignment, conflict detection, and address map generation.
"""

from typing import Dict, List, Optional, Set


class AddressManager:
    """
    Manages register address allocation and validation.
    
    Features:
    - Automatic address assignment with alignment
    - Manual address specification and conflict detection
    - Address range validation
    - Address map generation
    """
    
    def __init__(self, start_addr: int = 0x00, alignment: int = 4):
        """
        Initialize AddressManager.
        
        Args:
            start_addr: Starting address for auto-assignment (default: 0x00)
            alignment: Address alignment in bytes (default: 4)
        """
        self.start_addr = start_addr
        self.alignment = alignment
        self.auto_counter = start_addr
        self.assigned_addresses: Set[int] = set()
        
    def reset(self):
        """Reset the address counter and assigned addresses."""
        self.auto_counter = self.start_addr
        self.assigned_addresses.clear()
        
    def allocate_address(self, manual_addr: Optional[int] = None) -> int:
        """
        Allocate an address, either manually specified or auto-assigned.
        
        Args:
            manual_addr: Manual address specification (hex or decimal)
            
        Returns:
            Allocated address as integer
            
        Raises:
            ValueError: If address conflicts or is invalid
        """
        if manual_addr is not None:
            # Manual address assignment
            addr = self._validate_address(manual_addr)
            if addr in self.assigned_addresses:
                raise ValueError(f"Address conflict: 0x{addr:02X} already assigned")
            self.assigned_addresses.add(addr)
            # Update auto counter if needed
            self.auto_counter = max(self.auto_counter, addr + self.alignment)
            return addr
        else:
            # Auto address assignment
            addr = self._align_address(self.auto_counter)
            while addr in self.assigned_addresses:
                addr += self.alignment
            self.assigned_addresses.add(addr)
            self.auto_counter = addr + self.alignment
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
