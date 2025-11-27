"""
Test suite demonstrating PZSpec factories with Zig comptime generics.

This example shows how to test Zig's comptime generic pattern:
    pub fn ButcheryFactory(comptime L: RoomLevel) type { ... }

Since Zig comptime generics can't be directly exported via FFI,
we export concrete instantiations (SmallButchery, MediumButchery, LargeButchery)
and use Python factories to create test data for each variant.
"""

import sys
from pathlib import Path
from enum import IntEnum

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from pzspec import (
    ZigLibrary,
    describe,
    it,
    expect,
    assert_almost_equal,
    StructFactory,
    factory_field,
    sequence,
    trait,
)
import ctypes


# ============================================================================
# Enum and Struct Definitions (matching Zig types)
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
# Python Factories for Test Data
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


# ============================================================================
# Load Zig Library
# ============================================================================

zig = ZigLibrary()


# ============================================================================
# FFI Helper Functions
# ============================================================================

def small_butchery_new(id: int) -> SmallButchery:
    func = zig.get_function("small_butchery_new", [ctypes.c_uint32], SmallButchery)
    return func(id)


def small_butchery_effective_capacity(b: SmallButchery) -> int:
    func = zig.get_function(
        "small_butchery_effective_capacity",
        [ctypes.POINTER(SmallButchery)],
        ctypes.c_uint32,
    )
    return func(ctypes.byref(b))


def small_butchery_effective_speed(b: SmallButchery) -> float:
    func = zig.get_function(
        "small_butchery_effective_speed",
        [ctypes.POINTER(SmallButchery)],
        ctypes.c_float,
    )
    return func(ctypes.byref(b))


def small_butchery_can_store(b: SmallButchery, amount: int) -> bool:
    func = zig.get_function(
        "small_butchery_can_store",
        [ctypes.POINTER(SmallButchery), ctypes.c_uint32],
        ctypes.c_bool,
    )
    return func(ctypes.byref(b), amount)


def small_butchery_base_capacity() -> int:
    func = zig.get_function("small_butchery_base_capacity", [], ctypes.c_uint32)
    return func()


def small_butchery_base_speed() -> float:
    func = zig.get_function("small_butchery_base_speed", [], ctypes.c_float)
    return func()


def medium_butchery_base_capacity() -> int:
    func = zig.get_function("medium_butchery_base_capacity", [], ctypes.c_uint32)
    return func()


def medium_butchery_base_speed() -> float:
    func = zig.get_function("medium_butchery_base_speed", [], ctypes.c_float)
    return func()


def large_butchery_base_capacity() -> int:
    func = zig.get_function("large_butchery_base_capacity", [], ctypes.c_uint32)
    return func()


def large_butchery_base_speed() -> float:
    func = zig.get_function("large_butchery_base_speed", [], ctypes.c_float)
    return func()


def meat_product_new(meat_type: MeatType, weight: float) -> MeatProduct:
    func = zig.get_function(
        "meat_product_new",
        [ctypes.c_uint8, ctypes.c_float],
        MeatProduct,
    )
    return func(meat_type, weight)


def meat_product_process(product: MeatProduct, efficiency: float) -> None:
    func = zig.get_function(
        "meat_product_process",
        [ctypes.POINTER(MeatProduct), ctypes.c_float],
        None,
    )
    func(ctypes.byref(product), efficiency)


def meat_product_value(product: MeatProduct) -> float:
    func = zig.get_function(
        "meat_product_value",
        [ctypes.POINTER(MeatProduct)],
        ctypes.c_float,
    )
    return func(ctypes.byref(product))


# ============================================================================
# Test Suites
# ============================================================================

with describe("ButcheryFactory - Comptime Generic Room Levels"):

    @it("should have correct base capacity for each room level")
    def test_base_capacities():
        expect(small_butchery_base_capacity()).to_equal(10)
        expect(medium_butchery_base_capacity()).to_equal(25)
        expect(large_butchery_base_capacity()).to_equal(50)

    @it("should have correct base speed for each room level")
    def test_base_speeds():
        assert_almost_equal(small_butchery_base_speed(), 1.0, delta=0.01)
        assert_almost_equal(medium_butchery_base_speed(), 2.5, delta=0.01)
        assert_almost_equal(large_butchery_base_speed(), 5.0, delta=0.01)


with describe("SmallButcheryFactory - Python Factory"):

    @it("should create butchery with defaults")
    def test_factory_defaults():
        b = SmallButcheryFactory()
        expect(b.workers).to_equal(0)
        expect(b.meat_stored).to_equal(0)
        assert_almost_equal(b.efficiency, 1.0, delta=0.01)
        expect(b.is_active).to_equal(False)

    @it("should create butchery with overrides")
    def test_factory_overrides():
        b = SmallButcheryFactory(workers=5, meat_stored=3)
        expect(b.workers).to_equal(5)
        expect(b.meat_stored).to_equal(3)

    @it("should create active butchery using trait")
    def test_active_trait():
        b = SmallButcheryFactory.active()
        expect(b.workers).to_equal(2)
        expect(b.is_active).to_equal(True)

    @it("should create full butchery using trait")
    def test_full_trait():
        b = SmallButcheryFactory.full()
        expect(b.meat_stored).to_equal(10)

    @it("should auto-increment IDs using sequence")
    def test_sequence_ids():
        SmallButcheryFactory.reset_sequences()
        b1 = SmallButcheryFactory()
        b2 = SmallButcheryFactory()
        b3 = SmallButcheryFactory()
        expect(b1.id).to_equal(1)
        expect(b2.id).to_equal(2)
        expect(b3.id).to_equal(3)

    @it("should create batch of butcheries")
    def test_batch_creation():
        butcheries = SmallButcheryFactory.build_batch(5, is_active=True)
        expect(len(butcheries)).to_equal(5)
        for b in butcheries:
            expect(b.is_active).to_equal(True)


with describe("SmallButchery - FFI Integration with Factory"):

    @it("should calculate effective capacity with efficiency modifier")
    def test_effective_capacity():
        # Use factory to create test data
        b = SmallButcheryFactory.efficient()
        # Zig function uses the struct data
        cap = small_butchery_effective_capacity(b)
        # 10 * 1.5 = 15
        expect(cap).to_equal(15)

    @it("should calculate effective speed with workers bonus")
    def test_effective_speed():
        b = SmallButcheryFactory(workers=2, efficiency=1.0)
        speed = small_butchery_effective_speed(b)
        # base_speed * efficiency * (1.0 + workers * 0.1)
        # 1.0 * 1.0 * (1.0 + 2 * 0.1) = 1.2
        assert_almost_equal(speed, 1.2, delta=0.01)

    @it("should check storage capacity correctly")
    def test_can_store():
        b = SmallButcheryFactory(meat_stored=5)
        # Base capacity is 10, stored is 5, so can store 5 more
        expect(small_butchery_can_store(b, 5)).to_equal(True)
        expect(small_butchery_can_store(b, 6)).to_equal(False)


with describe("MeatProductFactory - Resource Testing"):

    @it("should create different meat types using traits")
    def test_meat_type_traits():
        beef = MeatProductFactory.beef()
        pork = MeatProductFactory.pork()
        game = MeatProductFactory.game()

        expect(beef.meat_type).to_equal(MeatType.BEEF)
        expect(pork.meat_type).to_equal(MeatType.PORK)
        expect(game.meat_type).to_equal(MeatType.GAME)

    @it("should calculate meat value correctly")
    def test_meat_value():
        # Create with Zig function
        beef = meat_product_new(MeatType.BEEF, 2.0)
        # Value = base_value * weight * quality = 10.0 * 2.0 * 1.0 = 20.0
        value = meat_product_value(beef)
        assert_almost_equal(value, 20.0, delta=0.01)

    @it("should process meat and adjust quality")
    def test_meat_processing():
        product = MeatProductFactory(meat_type=MeatType.BEEF, weight=1.0, quality=1.0)
        expect(product.processed).to_equal(False)

        # Process with 80% efficiency
        meat_product_process(product, 0.8)

        expect(product.processed).to_equal(True)
        assert_almost_equal(product.quality, 0.8, delta=0.01)


with describe("Factory Patterns - Advanced Usage"):

    @it("should combine traits with overrides")
    def test_trait_with_override():
        # Start with efficient trait, but override workers
        b = SmallButcheryFactory.efficient(workers=10)
        expect(b.workers).to_equal(10)
        assert_almost_equal(b.efficiency, 1.5, delta=0.01)

    @it("should support different ID sequences per factory")
    def test_different_sequences():
        SmallButcheryFactory.reset_sequences()
        MediumButcheryFactory.reset_sequences()
        LargeButcheryFactory.reset_sequences()

        small = SmallButcheryFactory()
        medium = MediumButcheryFactory()
        large = LargeButcheryFactory()

        # Each factory has its own sequence offset
        expect(small.id).to_equal(1)      # sequence starts at 1
        expect(medium.id).to_equal(101)   # sequence(n + 100)
        expect(large.id).to_equal(201)    # sequence(n + 200)

    @it("should create test scenarios with multiple factories")
    def test_multi_factory_scenario():
        # Simulate a butchery processing meat
        butchery = SmallButcheryFactory.active()
        products = MeatProductFactory.build_batch(3, meat_type=MeatType.PORK)

        expect(len(products)).to_equal(3)
        expect(butchery.is_active).to_equal(True)

        # Process each product
        for product in products:
            meat_product_process(product, butchery.efficiency)
            expect(product.processed).to_equal(True)
