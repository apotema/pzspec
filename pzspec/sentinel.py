"""
Sentinel value helpers for FFI patterns.

When working with Zig code through FFI, certain values like "null" or "no entity"
cannot be represented directly. This module provides helpers for working with
sentinel values - special values that represent the absence of a valid value.

Common use cases:
- Entity IDs where 0 is valid (ECS systems)
- Optional numeric returns
- Error indicators in return values

Zig Side Example:
-----------------
```zig
const std = @import("std");

// Define sentinel as maximum value (can't be a valid entity index)
pub const NO_ENTITY: u32 = std.math.maxInt(u32);  // 0xFFFFFFFF

// Export for Python to retrieve
export fn get_no_entity_sentinel() u32 {
    return NO_ENTITY;
}

// Use in functions that may not find an entity
export fn find_entity_by_name(name: [*:0]const u8) u32 {
    // ... search logic ...
    if (found) {
        return entity.id;
    }
    return NO_ENTITY;  // Not found
}
```

Python Side Example:
--------------------
```python
from pzspec import ZigLibrary, Sentinel
import ctypes

zig = ZigLibrary()

# Create a sentinel for entity IDs
NO_ENTITY = Sentinel.from_zig_function(zig, "get_no_entity_sentinel", ctypes.c_uint32)

# Use in tests
entity_id = zig.get_function("find_entity_by_name", [ctypes.c_char_p], ctypes.c_uint32)(b"player")

if NO_ENTITY.is_valid(entity_id):
    # Found the entity
    process_entity(entity_id)
else:
    # Not found
    handle_missing()

# Or use expect() assertions
expect(entity_id).to_not_be_sentinel(NO_ENTITY)
```
"""

import ctypes
from typing import Any, Optional, Union
from dataclasses import dataclass


@dataclass
class Sentinel:
    """
    Represents a sentinel value for FFI optional/nullable patterns.

    A sentinel is a special value that indicates "no value" or "invalid"
    when the type doesn't have a natural null representation.
    """
    value: Any
    name: str = "SENTINEL"
    description: str = ""

    def is_sentinel(self, val: Any) -> bool:
        """Check if a value equals this sentinel."""
        return val == self.value

    def is_valid(self, val: Any) -> bool:
        """Check if a value is NOT the sentinel (i.e., is valid)."""
        return val != self.value

    def __eq__(self, other: Any) -> bool:
        """Allow direct comparison with values."""
        if isinstance(other, Sentinel):
            return self.value == other.value
        return self.value == other

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"Sentinel({self.name}={self.value})"

    @classmethod
    def from_zig_function(
        cls,
        zig_lib,
        func_name: str,
        restype: Any,
        name: Optional[str] = None,
        description: str = ""
    ) -> "Sentinel":
        """
        Create a Sentinel by calling a Zig export function.

        Args:
            zig_lib: ZigLibrary instance
            func_name: Name of the Zig function that returns the sentinel value
            restype: ctypes return type (e.g., ctypes.c_uint32)
            name: Optional name for the sentinel (defaults to func_name)
            description: Optional description

        Returns:
            Sentinel with the value from the Zig function

        Example:
            NO_ENTITY = Sentinel.from_zig_function(zig, "get_no_entity_sentinel", c_uint32)
        """
        func = zig_lib.get_function(func_name, [], restype)
        value = func()
        return cls(
            value=value,
            name=name or func_name.replace("get_", "").replace("_sentinel", "").upper(),
            description=description
        )

    @classmethod
    def max_uint32(cls, name: str = "NO_VALUE") -> "Sentinel":
        """Create a sentinel using max u32 value (0xFFFFFFFF)."""
        return cls(value=0xFFFFFFFF, name=name, description="Maximum u32 value")

    @classmethod
    def max_uint64(cls, name: str = "NO_VALUE") -> "Sentinel":
        """Create a sentinel using max u64 value."""
        return cls(value=0xFFFFFFFFFFFFFFFF, name=name, description="Maximum u64 value")

    @classmethod
    def max_int32(cls, name: str = "NO_VALUE") -> "Sentinel":
        """Create a sentinel using max i32 value (0x7FFFFFFF)."""
        return cls(value=0x7FFFFFFF, name=name, description="Maximum i32 value")

    @classmethod
    def min_int32(cls, name: str = "NO_VALUE") -> "Sentinel":
        """Create a sentinel using min i32 value (-2147483648)."""
        return cls(value=-2147483648, name=name, description="Minimum i32 value")

    @classmethod
    def negative_one(cls, name: str = "NO_VALUE") -> "Sentinel":
        """Create a sentinel using -1 (common for "not found" returns)."""
        return cls(value=-1, name=name, description="Negative one (-1)")


# Common pre-defined sentinels
NO_ENTITY = Sentinel.max_uint32("NO_ENTITY")
NO_INDEX = Sentinel.negative_one("NO_INDEX")
INVALID_ID = Sentinel.max_uint32("INVALID_ID")


def add_sentinel_assertions(expectation_class):
    """
    Add sentinel-related assertion methods to an Expectation class.

    This is called automatically when pzspec is imported.
    """

    def to_be_sentinel(self, sentinel: Sentinel, msg: Optional[str] = None):
        """Assert that the value IS the sentinel (no valid value)."""
        if not sentinel.is_sentinel(self.actual):
            error_msg = msg or f"Expected {sentinel.name} ({sentinel.value}), but got {self.actual}"
            raise AssertionError(error_msg)

    def to_not_be_sentinel(self, sentinel: Sentinel, msg: Optional[str] = None):
        """Assert that the value is NOT the sentinel (has a valid value)."""
        if sentinel.is_sentinel(self.actual):
            error_msg = msg or f"Expected a valid value, but got {sentinel.name} ({sentinel.value})"
            raise AssertionError(error_msg)

    def to_be_valid(self, sentinel: Sentinel, msg: Optional[str] = None):
        """Alias for to_not_be_sentinel - assert value is valid (not sentinel)."""
        return self.to_not_be_sentinel(sentinel, msg)

    def to_be_invalid(self, sentinel: Sentinel, msg: Optional[str] = None):
        """Alias for to_be_sentinel - assert value is invalid (is sentinel)."""
        return self.to_be_sentinel(sentinel, msg)

    expectation_class.to_be_sentinel = to_be_sentinel
    expectation_class.to_not_be_sentinel = to_not_be_sentinel
    expectation_class.to_be_valid = to_be_valid
    expectation_class.to_be_invalid = to_be_invalid

    return expectation_class


# Automatically add sentinel assertions to Expectation class
def _init_sentinel_assertions():
    """Initialize sentinel assertions on the Expectation class."""
    try:
        from .dsl import Expectation
        add_sentinel_assertions(Expectation)
    except ImportError:
        pass  # Will be initialized later


_init_sentinel_assertions()
