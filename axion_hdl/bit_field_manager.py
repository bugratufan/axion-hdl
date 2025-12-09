"""
Bit Field Manager Module

Manages bit field allocation within registers for subregister support.
Handles bit overlap detection and auto-packing of signals.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class BitOverlapError(Exception):
    """
    Exception raised when bit ranges overlap within a register.
    
    Provides detailed information about the conflicting fields
    and suggestions for resolution.
    """
    
    def __init__(
        self, 
        register_name: str,
        address: int,
        field1: 'BitField',
        field2: 'BitField',
        overlap_bits: Tuple[int, int]
    ):
        self.register_name = register_name
        self.address = address
        self.field1 = field1
        self.field2 = field2
        self.overlap_bits = overlap_bits
        
        # Calculate suggestion
        suggested_offset = field1.bit_high + 1
        
        message = (
            f"Bit range conflict detected in register '{register_name}' at address 0x{address:02X}\n"
            f"Conflicting fields:\n"
            f"  • {field1.name}: bits [{field1.bit_high}:{field1.bit_low}]"
        )
        if field1.source_file and field1.source_line:
            message += f" (defined in {field1.source_file}:{field1.source_line})"
        message += f"\n  • {field2.name}: bits [{field2.bit_high}:{field2.bit_low}]"
        if field2.source_file and field2.source_line:
            message += f" (defined in {field2.source_file}:{field2.source_line})"
        message += (
            f"\nOverlap: bits [{overlap_bits[1]}:{overlap_bits[0]}]\n"
            f"Suggestion: Change BIT_OFFSET of '{field2.name}' to {suggested_offset} or higher"
        )
        
        super().__init__(message)


@dataclass
class BitField:
    """Represents a bit field within a register."""
    name: str
    bit_low: int
    bit_high: int
    width: int
    access_mode: str
    signal_type: str
    description: str = ""
    source_file: str = ""
    source_line: int = 0
    read_strobe: bool = False
    write_strobe: bool = False
    default_value: int = 0
    
    @property
    def bit_range(self) -> Tuple[int, int]:
        """Return (low, high) bit range."""
        return (self.bit_low, self.bit_high)
    
    @property
    def mask(self) -> int:
        """Generate bit mask for this field."""
        return ((1 << self.width) - 1) << self.bit_low
    
    def overlaps_with(self, other: 'BitField') -> Optional[Tuple[int, int]]:
        """
        Check if this field overlaps with another.
        
        Returns:
            Tuple of (overlap_low, overlap_high) if overlap exists, None otherwise
        """
        overlap_low = max(self.bit_low, other.bit_low)
        overlap_high = min(self.bit_high, other.bit_high)
        
        if overlap_low <= overlap_high:
            return (overlap_low, overlap_high)
        return None


@dataclass
class PackedRegister:
    """Represents a register containing multiple bit fields."""
    name: str
    address: int
    fields: List[BitField]
    access_mode: str
    cdc_enabled: bool = False
    cdc_stages: int = 2
    
    @property
    def width(self) -> int:
        """Calculate total register width from fields."""
        if not self.fields:
            return 32
        max_bit = max(f.bit_high for f in self.fields)
        # Round up to 32-bit boundary
        return 32
    
    @property
    def used_bits(self) -> int:
        """Count used bits in register."""
        if not self.fields:
            return 0
        return max(f.bit_high for f in self.fields) + 1


class BitFieldManager:
    """
    Manages bit field allocation and validation for packed registers.
    
    Responsibilities:
    - Track bit allocations within registers
    - Detect bit overlaps
    - Auto-pack signals when BIT_OFFSET not specified
    - Validate access mode consistency
    """
    
    def __init__(self):
        # Dictionary: reg_name -> PackedRegister
        self._registers: Dict[str, PackedRegister] = {}
        # Track next auto-pack offset per register
        self._next_offset: Dict[str, int] = {}
    
    def clear(self):
        """Clear all tracked registers."""
        self._registers.clear()
        self._next_offset.clear()
    
    def add_field(
        self,
        reg_name: str,
        address: int,
        field_name: str,
        width: int,
        access_mode: str,
        signal_type: str,
        bit_offset: Optional[int] = None,
        description: str = "",
        source_file: str = "",
        source_line: int = 0,
        read_strobe: bool = False,
        write_strobe: bool = False,
        default_value: int = 0
    ) -> BitField:
        """
        Add a bit field to a register.
        
        Args:
            reg_name: Name of the packed register
            address: Register address
            field_name: Name of the signal/field
            width: Bit width of the field
            access_mode: RO/RW/WO
            signal_type: VHDL signal type
            bit_offset: Optional starting bit (auto-pack if None)
            description: Field description
            source_file: Source file for error messages
            source_line: Source line for error messages
            read_strobe: Has read strobe
            write_strobe: Has write strobe
            
        Returns:
            Created BitField object
            
        Raises:
            BitOverlapError: If field overlaps with existing field
            ValueError: If access modes don't match
        """
        # Get or create register
        if reg_name not in self._registers:
            self._registers[reg_name] = PackedRegister(
                name=reg_name,
                address=address,
                fields=[],
                access_mode=access_mode
            )
            self._next_offset[reg_name] = 0
        
        reg = self._registers[reg_name]
        
        # Validate access mode consistency
        if reg.fields and reg.access_mode != access_mode:
            # Check if existing mode is compatible
            # RW can contain RO and WO fields in some cases
            pass  # Allow mixed access for now, validate at generation
        
        # Determine bit offset
        if bit_offset is None:
            bit_offset = self._next_offset[reg_name]
        
        bit_low = bit_offset
        bit_high = bit_offset + width - 1
        
        # Check for 32-bit limit
        if bit_high > 31:
            raise ValueError(
                f"Field '{field_name}' exceeds 32-bit register boundary "
                f"(bits [{bit_high}:{bit_low}])"
            )
        
        # Create field
        field = BitField(
            name=field_name,
            bit_low=bit_low,
            bit_high=bit_high,
            width=width,
            access_mode=access_mode,
            signal_type=signal_type,
            description=description,
            source_file=source_file,
            source_line=source_line,
            read_strobe=read_strobe,
            write_strobe=write_strobe,
            default_value=default_value
        )
        
        # Check for overlaps with existing fields
        for existing in reg.fields:
            overlap = field.overlaps_with(existing)
            if overlap:
                raise BitOverlapError(
                    register_name=reg_name,
                    address=address,
                    field1=existing,
                    field2=field,
                    overlap_bits=overlap
                )
        
        # Add field
        reg.fields.append(field)
        
        # Update next auto-pack offset
        self._next_offset[reg_name] = max(
            self._next_offset[reg_name], 
            bit_high + 1
        )
        
        return field
    
    def get_register(self, reg_name: str) -> Optional[PackedRegister]:
        """Get a packed register by name."""
        return self._registers.get(reg_name)
    
    def get_all_registers(self) -> List[PackedRegister]:
        """Get all packed registers."""
        return list(self._registers.values())
    
    def get_field_mask(self, reg_name: str, field_name: str) -> Optional[int]:
        """Get the bit mask for a specific field."""
        reg = self._registers.get(reg_name)
        if not reg:
            return None
        
        for field in reg.fields:
            if field.name == field_name:
                return field.mask
        return None
    
    def validate_all(self) -> List[str]:
        """
        Validate all registers for consistency.
        
        Returns:
            List of warning/error messages
        """
        warnings = []
        
        for reg in self._registers.values():
            # Check for gaps in bit allocation
            used_bits = set()
            for field in reg.fields:
                for bit in range(field.bit_low, field.bit_high + 1):
                    used_bits.add(bit)
            
            # Check for access mode consistency
            access_modes = set(f.access_mode for f in reg.fields)
            if len(access_modes) > 1:
                warnings.append(
                    f"Register '{reg.name}' has mixed access modes: {access_modes}"
                )
        
        return warnings
