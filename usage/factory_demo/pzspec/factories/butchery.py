"""
Factories for Butchery and MeatProduct test data.

Demonstrates factories for Zig comptime generic types.
"""

import ctypes
from enum import IntEnum

from pzspec import StructFactory, factory_field, sequence, trait


# ============================================================================
# Enum Definitions (matching Zig types)
# ============================================================================

class RoomLevel(IntEnum):
    """Mirrors Zig's RoomLevel enum."""
    SMALL = 1
    MEDIUM = 2
    LARGE = 3


class MeatType(IntEnum):
    """Mirrors Zig's MeatType enum."""
    BEEF = 0
    PORK = 1
    POULTRY = 2
    GAME = 3


# ============================================================================
# Struct Definitions (matching Zig types)
# ============================================================================

class SmallButchery(ctypes.Structure):
    """Corresponds to Zig's ButcheryFactory(.small)."""
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("workers", ctypes.c_uint32),
        ("meat_stored", ctypes.c_uint32),
        ("efficiency", ctypes.c_float),
        ("is_active", ctypes.c_bool),
    ]


class MediumButchery(ctypes.Structure):
    """Corresponds to Zig's ButcheryFactory(.medium)."""
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("workers", ctypes.c_uint32),
        ("meat_stored", ctypes.c_uint32),
        ("efficiency", ctypes.c_float),
        ("is_active", ctypes.c_bool),
    ]


class LargeButchery(ctypes.Structure):
    """Corresponds to Zig's ButcheryFactory(.large)."""
    _fields_ = [
        ("id", ctypes.c_uint32),
        ("workers", ctypes.c_uint32),
        ("meat_stored", ctypes.c_uint32),
        ("efficiency", ctypes.c_float),
        ("is_active", ctypes.c_bool),
    ]


class MeatProduct(ctypes.Structure):
    """Corresponds to Zig's MeatProduct struct."""
    _fields_ = [
        ("meat_type", ctypes.c_uint8),
        ("weight", ctypes.c_float),
        ("quality", ctypes.c_float),
        ("processed", ctypes.c_bool),
    ]


# ============================================================================
# Factory Definitions
# ============================================================================

class SmallButcheryFactory(StructFactory):
    """Factory for creating SmallButchery test instances."""
    struct_class = SmallButchery

    id = sequence(lambda n: n)
    workers = factory_field(default=0)
    meat_stored = factory_field(default=0)
    efficiency = factory_field(default=1.0)
    is_active = factory_field(default=False)

    @trait
    def active(self):
        """A running butchery with workers."""
        return {"workers": 2, "is_active": True}

    @trait
    def full(self):
        """A butchery at capacity."""
        return {"meat_stored": 10, "is_active": True}  # small capacity = 10

    @trait
    def efficient(self):
        """High efficiency butchery."""
        return {"efficiency": 1.5, "workers": 3, "is_active": True}


class MediumButcheryFactory(StructFactory):
    """Factory for creating MediumButchery test instances."""
    struct_class = MediumButchery

    id = sequence(lambda n: n + 100)  # IDs start at 101
    workers = factory_field(default=0)
    meat_stored = factory_field(default=0)
    efficiency = factory_field(default=1.0)
    is_active = factory_field(default=False)

    @trait
    def active(self):
        return {"workers": 5, "is_active": True}

    @trait
    def full(self):
        return {"meat_stored": 25, "is_active": True}  # medium capacity = 25


class LargeButcheryFactory(StructFactory):
    """Factory for creating LargeButchery test instances."""
    struct_class = LargeButchery

    id = sequence(lambda n: n + 200)  # IDs start at 201
    workers = factory_field(default=0)
    meat_stored = factory_field(default=0)
    efficiency = factory_field(default=1.0)
    is_active = factory_field(default=False)

    @trait
    def active(self):
        return {"workers": 10, "is_active": True}

    @trait
    def full(self):
        return {"meat_stored": 50, "is_active": True}  # large capacity = 50

    @trait
    def industrial(self):
        """High-capacity industrial operation."""
        return {"workers": 20, "efficiency": 1.2, "is_active": True}


class MeatProductFactory(StructFactory):
    """Factory for creating MeatProduct test instances."""
    struct_class = MeatProduct

    meat_type = factory_field(default=MeatType.BEEF)
    weight = factory_field(default=1.0)
    quality = factory_field(default=1.0)
    processed = factory_field(default=False)

    @trait
    def beef(self):
        return {"meat_type": MeatType.BEEF, "weight": 5.0}

    @trait
    def pork(self):
        return {"meat_type": MeatType.PORK, "weight": 3.0}

    @trait
    def poultry(self):
        return {"meat_type": MeatType.POULTRY, "weight": 1.5}

    @trait
    def game(self):
        return {"meat_type": MeatType.GAME, "weight": 4.0}

    @trait
    def premium(self):
        """High quality meat."""
        return {"quality": 1.5, "weight": 2.0}

    @trait
    def processed_beef(self):
        """Already processed beef."""
        return {"meat_type": MeatType.BEEF, "weight": 5.0, "processed": True}
