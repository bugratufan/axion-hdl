"""
Python Register Model

Provides FieldModel, RegisterModel, and RegisterSpaceModel classes that simulate
hardware register behavior. Intended for use in golden models (software simulation
of hardware register spaces).

Usage:
    from axion_hdl import AxionHDL, RegisterSpaceModel

    axion = AxionHDL()
    axion.add_source("my_regs.yaml")
    axion.analyze()
    space = axion.get_model("my_module")

    space.write(0x1000, 0x1)
    val = space.read(0x1000)
    print(space.control.value)
    print(space.status.ready.enum_name)
"""

from typing import Dict, List, Optional, Callable, Tuple


class ReadOnlyError(Exception):
    """Raised when a write is attempted on a read-only register or field."""

    def __init__(self, register_name: str, field_name: str = None):
        if field_name:
            msg = f"Field '{field_name}' in register '{register_name}' is read-only"
        else:
            msg = f"Register '{register_name}' is read-only"
        super().__init__(msg)
        self.register_name = register_name
        self.field_name = field_name


class AddressError(KeyError):
    """Raised when a bus access targets an address not in the register space."""

    def __init__(self, address: int, space_name: str):
        msg = f"No register at address 0x{address:04X} in space '{space_name}'"
        super().__init__(msg)
        self.address = address
        self.space_name = space_name


class FieldModel:
    """
    Represents a single bit field within a packed register.

    Reads and writes operate on the parent RegisterModel's raw value through
    bit masking. Access mode (RO/RW/WO) is enforced on writes.
    """

    def __init__(self, field_dict: dict, parent: 'RegisterModel'):
        self._name: str = field_dict['name']
        self._bit_low: int = int(field_dict.get('bit_low', 0))
        self._bit_high: int = int(field_dict.get('bit_high', 0))
        self._width: int = int(field_dict.get('width', self._bit_high - self._bit_low + 1))
        self._access_mode: str = field_dict.get('access_mode', 'RW')
        self._default_value: int = int(field_dict.get('default_value', 0))
        self._enum_values: Optional[Dict[int, str]] = field_dict.get('enum_values')
        self._read_strobe: bool = bool(field_dict.get('read_strobe', False))
        self._write_strobe: bool = bool(field_dict.get('write_strobe', False))
        self._description: str = field_dict.get('description', '')
        self._mask: int = ((1 << self._width) - 1) << self._bit_low
        self._parent: 'RegisterModel' = parent

    @property
    def name(self) -> str:
        return self._name

    @property
    def bit_low(self) -> int:
        return self._bit_low

    @property
    def bit_high(self) -> int:
        return self._bit_high

    @property
    def width(self) -> int:
        return self._width

    @property
    def access_mode(self) -> str:
        return self._access_mode

    @property
    def mask(self) -> int:
        return self._mask

    @property
    def default_value(self) -> int:
        return self._default_value

    @property
    def description(self) -> str:
        return self._description

    @property
    def value(self) -> int:
        """Current field value extracted from parent register raw value."""
        parent_raw = object.__getattribute__(self._parent, '_raw_value')
        return (parent_raw & self._mask) >> self._bit_low

    @value.setter
    def value(self, new_val: int) -> None:
        if self._access_mode == 'RO':
            raise ReadOnlyError(self._parent.name, self._name)
        max_val = (1 << self._width) - 1
        if new_val < 0 or new_val > max_val:
            raise ValueError(
                f"Value {new_val} out of range [0, {max_val}] for field '{self._name}' (width={self._width})"
            )
        self._parent._write_field(self, new_val)

    @property
    def raw_value(self) -> int:
        """Always returns the actual bits regardless of access mode (golden model inspection)."""
        parent_raw = object.__getattribute__(self._parent, '_raw_value')
        return (parent_raw & self._mask) >> self._bit_low

    @property
    def enum_name(self) -> Optional[str]:
        """Return enum string for current value, or None if no mapping exists."""
        if self._enum_values is None:
            return None
        return self._enum_values.get(self.value)

    def reset(self) -> None:
        """Restore field to default value without RO check and without triggering callbacks."""
        self._parent._force_write_field(self, self._default_value)

    def __repr__(self) -> str:
        enum_str = f", enum='{self.enum_name}'" if self.enum_name is not None else ""
        return (
            f"FieldModel(name='{self._name}', bits=[{self._bit_high}:{self._bit_low}], "
            f"value={self.value}{enum_str})"
        )


class RegisterModel:
    """
    Represents a single hardware register (packed or simple).

    Holds live register state (_raw_value). Enforces RO/WO/RW access semantics
    on bus-level read()/write() operations. Provides field-level access for packed
    registers and strobe callback support.
    """

    def __init__(self, reg_dict: dict, base_address: int = 0):
        self._name: str = reg_dict.get('signal_name') or reg_dict.get('name', '')
        self._access_mode: str = reg_dict.get('access_mode') or reg_dict.get('access', 'RW')
        self._width: int = int(reg_dict.get('width', 32))
        self._default_value: int = int(reg_dict.get('default_value', 0))
        self._description: str = reg_dict.get('description', '')
        self._read_strobe: bool = bool(reg_dict.get('read_strobe') or reg_dict.get('r_strobe', False))
        self._write_strobe: bool = bool(reg_dict.get('write_strobe') or reg_dict.get('w_strobe', False))
        self._is_packed: bool = bool(reg_dict.get('is_packed', False))

        # Resolve absolute address
        if reg_dict.get('address_int') is not None:
            self._address: int = int(reg_dict['address_int'])
        else:
            self._address = base_address + int(reg_dict.get('relative_address_int', 0))

        self._relative_address: int = int(reg_dict.get('relative_address_int', self._address - base_address))

        # Live state
        self._raw_value: int = self._default_value & ((1 << self._width) - 1)

        # Callbacks
        self._on_read_callback: Optional[Callable[[str, int], None]] = None
        self._on_write_callback: Optional[Callable[[str, int], None]] = None

        # Build field models for packed registers
        self._fields: Dict[str, FieldModel] = {}
        if self._is_packed:
            for fd in reg_dict.get('fields', []):
                fm = FieldModel(fd, self)
                self._fields[fm.name] = fm

    @property
    def name(self) -> str:
        return self._name

    @property
    def address(self) -> int:
        return self._address

    @property
    def relative_address(self) -> int:
        return self._relative_address

    @property
    def access_mode(self) -> str:
        return self._access_mode

    @property
    def width(self) -> int:
        return self._width

    @property
    def default_value(self) -> int:
        return self._default_value

    @property
    def description(self) -> str:
        return self._description

    @property
    def read_strobe(self) -> bool:
        return self._read_strobe

    @property
    def write_strobe(self) -> bool:
        return self._write_strobe

    @property
    def is_packed(self) -> bool:
        return self._is_packed

    @property
    def fields(self) -> Dict[str, 'FieldModel']:
        return self._fields

    @property
    def value(self) -> int:
        """Current register value. WO registers return 0 (bus read semantics)."""
        if self._access_mode == 'WO':
            return 0
        return self._raw_value

    @value.setter
    def value(self, new_val: int) -> None:
        if self._access_mode == 'RO':
            raise ReadOnlyError(self._name)
        mask = (1 << self._width) - 1
        self._raw_value = int(new_val) & mask
        if self._write_strobe and self._on_write_callback:
            self._on_write_callback(self._name, self._raw_value)

    @property
    def raw_value(self) -> int:
        """Always returns _raw_value regardless of access mode (golden model inspection)."""
        return self._raw_value

    def read(self) -> int:
        """Simulate a bus read. Fires read-strobe callback if applicable."""
        val = self.value
        if self._read_strobe and self._on_read_callback:
            self._on_read_callback(self._name, self._raw_value)
        return val

    def write(self, value: int) -> None:
        """Simulate a bus write. Raises ReadOnlyError for RO registers."""
        if self._access_mode == 'RO':
            raise ReadOnlyError(self._name)
        mask = (1 << self._width) - 1
        self._raw_value = int(value) & mask
        if self._write_strobe and self._on_write_callback:
            self._on_write_callback(self._name, self._raw_value)

    def reset(self) -> None:
        """Restore register to default value. Does not trigger callbacks or check access mode."""
        self._raw_value = self._default_value & ((1 << self._width) - 1)

    def on_read(self, callback: Callable[[str, int], None]) -> None:
        """Register a read-strobe callback. Signature: callback(register_name, value)."""
        self._on_read_callback = callback

    def on_write(self, callback: Callable[[str, int], None]) -> None:
        """Register a write-strobe callback. Signature: callback(register_name, new_value)."""
        self._on_write_callback = callback

    def _write_field(self, field: FieldModel, field_value: int) -> None:
        """Update field bits in _raw_value; fires write callback if field has write_strobe."""
        self._raw_value = (self._raw_value & ~field.mask) | ((field_value << field.bit_low) & field.mask)
        if field._write_strobe and self._on_write_callback:
            self._on_write_callback(self._name, self._raw_value)

    def _force_write_field(self, field: FieldModel, field_value: int) -> None:
        """Update field bits without triggering callbacks. Used by FieldModel.reset()."""
        self._raw_value = (self._raw_value & ~field.mask) | ((field_value << field.bit_low) & field.mask)

    def dump(self) -> str:
        """Return a human-readable string representation."""
        lines = [f"[0x{self._address:04X}] {self._name} ({self._access_mode}) = 0x{self._raw_value:08X}"]
        if self._is_packed:
            for field in self._fields.values():
                enum_str = f" ({field.enum_name})" if field.enum_name is not None else ""
                lines.append(
                    f"  [{field.bit_high}:{field.bit_low}] {field.name} = {field.raw_value}{enum_str}"
                )
        return "\n".join(lines)

    def __getattr__(self, name: str) -> 'FieldModel':
        # Guard against recursion during __init__ before _fields is set
        try:
            fields = object.__getattribute__(self, '_fields')
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        if name in fields:
            return fields[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __repr__(self) -> str:
        return (
            f"RegisterModel(name='{self._name}', addr=0x{self._address:04X}, "
            f"value=0x{self._raw_value:08X}, access={self._access_mode})"
        )


class RegisterSpaceModel:
    """
    Python model of a complete register space (module).

    Provides address-based bus simulation (read/write by absolute address)
    and named attribute access to registers. Constructed from the internal
    module dict produced by axion-hdl parsers.
    """

    def __init__(self, module_dict: dict):
        self._name: str = module_dict.get('name') or module_dict.get('entity_name', '')
        self._base_address: int = int(module_dict.get('base_address') or module_dict.get('base_addr', 0))

        self._registers_by_name: Dict[str, RegisterModel] = {}
        self._registers_by_address: Dict[int, RegisterModel] = {}

        for reg_dict in module_dict.get('registers', []):
            rm = RegisterModel(reg_dict, base_address=self._base_address)
            self._registers_by_name[rm.name] = rm
            self._registers_by_address[rm.address] = rm

    @classmethod
    def from_module_dict(cls, module_dict: dict) -> 'RegisterSpaceModel':
        """Construct a RegisterSpaceModel from an axion-hdl module dictionary."""
        # Normalize: ensure 'name' key exists
        d = dict(module_dict)
        if 'name' not in d:
            d['name'] = d.get('entity_name', '')
        return cls(d)

    @property
    def name(self) -> str:
        return self._name

    @property
    def base_address(self) -> int:
        return self._base_address

    @property
    def registers(self) -> Dict[str, RegisterModel]:
        return self._registers_by_name

    def read(self, address: int) -> int:
        """Simulate a bus read at the given absolute address."""
        reg = self._registers_by_address.get(address)
        if reg is None:
            raise AddressError(address, self._name)
        return reg.read()

    def write(self, address: int, value: int) -> None:
        """Simulate a bus write at the given absolute address."""
        reg = self._registers_by_address.get(address)
        if reg is None:
            raise AddressError(address, self._name)
        reg.write(value)

    def reset(self) -> None:
        """Restore all registers to their default values."""
        for reg in self._registers_by_name.values():
            reg.reset()

    def on_read(self, register_name: str, callback: Callable[[str, int], None]) -> None:
        """Attach a read-strobe callback to a register by name."""
        reg = self._registers_by_name.get(register_name)
        if reg is None:
            raise KeyError(f"No register named '{register_name}' in space '{self._name}'")
        reg.on_read(callback)

    def on_write(self, register_name: str, callback: Callable[[str, int], None]) -> None:
        """Attach a write-strobe callback to a register by name."""
        reg = self._registers_by_name.get(register_name)
        if reg is None:
            raise KeyError(f"No register named '{register_name}' in space '{self._name}'")
        reg.on_write(callback)

    def get_register(self, name: str) -> RegisterModel:
        """Get a register by name. Raises KeyError if not found."""
        reg = self._registers_by_name.get(name)
        if reg is None:
            raise KeyError(f"No register named '{name}' in space '{self._name}'")
        return reg

    def get_register_at(self, address: int) -> RegisterModel:
        """Get a register by absolute address. Raises AddressError if not found."""
        reg = self._registers_by_address.get(address)
        if reg is None:
            raise AddressError(address, self._name)
        return reg

    def dump(self) -> str:
        """Return a human-readable dump of all registers in address order."""
        header = f"RegisterSpace: {self._name} @ 0x{self._base_address:04X}"
        lines = [header, "-" * len(header)]
        for reg in sorted(self._registers_by_name.values(), key=lambda r: r.address):
            lines.append(reg.dump())
        return "\n".join(lines)

    def __getattr__(self, name: str) -> RegisterModel:
        try:
            by_name = object.__getattribute__(self, '_registers_by_name')
        except AttributeError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")
        if name in by_name:
            return by_name[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __iter__(self):
        return iter(sorted(self._registers_by_name.values(), key=lambda r: r.address))

    def __repr__(self) -> str:
        return (
            f"RegisterSpaceModel(name='{self._name}', base=0x{self._base_address:04X}, "
            f"registers={len(self._registers_by_name)})"
        )
