"""
Test suite for ECS Entity System demonstrating PZSpec Sentinel values.

This example shows how to use PZSpec's Sentinel class to handle FFI patterns
where 0 is a valid value (like entity IDs) and you need special values to
represent "no entity" or "not found".
"""

import sys
from pathlib import Path

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from the framework package
from pzspec.zig_ffi import ZigLibrary
from pzspec.dsl import describe, it, expect, before_each
from pzspec.sentinel import Sentinel, NO_ENTITY, NO_INDEX
import ctypes

# Load the Zig library (auto-builds if needed)
zig = ZigLibrary()


# =============================================================================
# Sentinel Value Setup
# =============================================================================
# Option 1: Use pre-defined sentinels from pzspec (convenient defaults)
# NO_ENTITY = Sentinel.max_uint32("NO_ENTITY")  # Already imported

# Option 2: Get sentinel values directly from Zig (ensures consistency)
NO_ENTITY_FROM_ZIG = Sentinel.from_zig_function(
    zig, "get_no_entity_sentinel", ctypes.c_uint32, "NO_ENTITY"
)

NO_INDEX_FROM_ZIG = Sentinel.from_zig_function(
    zig, "get_no_index_sentinel", ctypes.c_int32, "NO_INDEX"
)

INVALID_GENERATION = Sentinel.from_zig_function(
    zig, "get_invalid_generation_sentinel", ctypes.c_uint32, "INVALID_GENERATION"
)


# =============================================================================
# Helper Functions
# =============================================================================
def create_entity():
    """Create a new entity and return its ID."""
    func = zig.get_function("create_entity", [], ctypes.c_uint32)
    return func()


def create_named_entity(name: str):
    """Create an entity with a name."""
    func = zig.get_function("create_named_entity", [ctypes.c_char_p], ctypes.c_uint32)
    return func(name.encode("utf-8"))


def destroy_entity(entity_id: int):
    """Destroy an entity."""
    func = zig.get_function("destroy_entity", [ctypes.c_uint32], ctypes.c_bool)
    return func(entity_id)


def is_entity_alive(entity_id: int):
    """Check if an entity is alive."""
    func = zig.get_function("is_entity_alive", [ctypes.c_uint32], ctypes.c_bool)
    return func(entity_id)


def get_entity_count():
    """Get the current entity count."""
    func = zig.get_function("get_entity_count", [], ctypes.c_uint32)
    return func()


def reset_entities():
    """Reset all entities (for test isolation)."""
    func = zig.get_function("reset_entities", [], None)
    func()


def find_entity_by_name(name: str):
    """Find an entity by name - returns NO_ENTITY if not found."""
    func = zig.get_function("find_entity_by_name", [ctypes.c_char_p], ctypes.c_uint32)
    return func(name.encode("utf-8"))


def find_healthiest_entity():
    """Find the entity with highest health - returns NO_ENTITY if none exist."""
    func = zig.get_function("find_healthiest_entity", [], ctypes.c_uint32)
    return func()


def find_nearest_entity(x: float, y: float):
    """Find nearest entity to position - returns NO_ENTITY if none exist."""
    func = zig.get_function(
        "find_nearest_entity", [ctypes.c_float, ctypes.c_float], ctypes.c_uint32
    )
    return func(x, y)


def get_entity_parent(entity_id: int):
    """Get entity's parent - returns NO_ENTITY if no parent."""
    func = zig.get_function("get_entity_parent", [ctypes.c_uint32], ctypes.c_uint32)
    return func(entity_id)


def set_entity_parent(entity_id: int, parent_id: int):
    """Set entity's parent."""
    func = zig.get_function(
        "set_entity_parent", [ctypes.c_uint32, ctypes.c_uint32], ctypes.c_bool
    )
    return func(entity_id, parent_id)


def find_first_child(parent_id: int):
    """Find first child of entity - returns NO_ENTITY if no children."""
    func = zig.get_function("find_first_child", [ctypes.c_uint32], ctypes.c_uint32)
    return func(parent_id)


def get_entity_health(entity_id: int):
    """Get entity health - returns NO_INDEX if entity doesn't exist."""
    func = zig.get_function("get_entity_health", [ctypes.c_uint32], ctypes.c_int32)
    return func(entity_id)


def set_entity_health(entity_id: int, health: int):
    """Set entity health."""
    func = zig.get_function(
        "set_entity_health", [ctypes.c_uint32, ctypes.c_int32], ctypes.c_bool
    )
    return func(entity_id, health)


def set_entity_position(entity_id: int, x: float, y: float):
    """Set entity position."""
    func = zig.get_function(
        "set_entity_position",
        [ctypes.c_uint32, ctypes.c_float, ctypes.c_float],
        ctypes.c_bool,
    )
    return func(entity_id, x, y)


def get_entity_generation(entity_id: int):
    """Get entity generation - returns INVALID_GENERATION if invalid."""
    func = zig.get_function("get_entity_generation", [ctypes.c_uint32], ctypes.c_uint32)
    return func(entity_id)


# =============================================================================
# Tests
# =============================================================================

with describe("Entity Creation"):
    @before_each
    def setup():
        reset_entities()

    @it("should create an entity with valid ID (starting from 0)")
    def test_create_entity():
        entity_id = create_entity()
        # Entity ID 0 is valid - this is why we need sentinels!
        expect(entity_id).to_equal(0)
        expect(is_entity_alive(entity_id)).to_be_true()

    @it("should create multiple entities with sequential IDs")
    def test_create_multiple():
        id1 = create_entity()
        id2 = create_entity()
        id3 = create_entity()

        expect(id1).to_equal(0)
        expect(id2).to_equal(1)
        expect(id3).to_equal(2)
        expect(get_entity_count()).to_equal(3)

    @it("should create named entities")
    def test_create_named():
        player_id = create_named_entity("player")
        enemy_id = create_named_entity("enemy")

        # Both are valid entities (not sentinel values)
        expect(player_id).to_not_be_sentinel(NO_ENTITY)
        expect(enemy_id).to_not_be_sentinel(NO_ENTITY)
        expect(player_id).to_not_equal(enemy_id)


with describe("Sentinel Values - Finding Entities"):
    @before_each
    def setup():
        reset_entities()

    @it("should return NO_ENTITY when searching empty world")
    def test_find_in_empty():
        result = find_entity_by_name("player")

        # Using sentinel assertions
        expect(result).to_be_sentinel(NO_ENTITY)

        # Equivalent check using is_sentinel method
        expect(NO_ENTITY.is_sentinel(result)).to_be_true()

        # Equivalent check using is_valid method
        expect(NO_ENTITY.is_valid(result)).to_be_false()

    @it("should return NO_ENTITY when entity not found by name")
    def test_find_nonexistent():
        create_named_entity("player")
        create_named_entity("enemy")

        result = find_entity_by_name("boss")  # doesn't exist

        expect(result).to_be_sentinel(NO_ENTITY)

    @it("should return valid ID when entity found")
    def test_find_existing():
        create_named_entity("player")
        enemy_id = create_named_entity("enemy")
        create_named_entity("ally")

        result = find_entity_by_name("enemy")

        expect(result).to_not_be_sentinel(NO_ENTITY)
        expect(result).to_equal(enemy_id)

    @it("should return NO_ENTITY when finding healthiest in empty world")
    def test_healthiest_empty():
        result = find_healthiest_entity()
        expect(result).to_be_sentinel(NO_ENTITY)

    @it("should find healthiest entity when entities exist")
    def test_healthiest_exists():
        e1 = create_entity()
        e2 = create_entity()
        e3 = create_entity()

        set_entity_health(e1, 50)
        set_entity_health(e2, 100)  # healthiest
        set_entity_health(e3, 75)

        result = find_healthiest_entity()

        expect(result).to_not_be_sentinel(NO_ENTITY)
        expect(result).to_equal(e2)


with describe("Sentinel Values - Parent/Child Relationships"):
    @before_each
    def setup():
        reset_entities()

    @it("should have NO_ENTITY as default parent")
    def test_default_parent():
        entity_id = create_entity()
        parent = get_entity_parent(entity_id)

        # Using to_be_invalid (alias for to_be_sentinel)
        expect(parent).to_be_invalid(NO_ENTITY)

    @it("should set and get valid parent")
    def test_valid_parent():
        parent_id = create_named_entity("parent")
        child_id = create_named_entity("child")

        success = set_entity_parent(child_id, parent_id)
        expect(success).to_be_true()

        result = get_entity_parent(child_id)
        # Using to_be_valid (alias for to_not_be_sentinel)
        expect(result).to_be_valid(NO_ENTITY)
        expect(result).to_equal(parent_id)

    @it("should return NO_ENTITY for child search on entity without children")
    def test_no_children():
        parent_id = create_entity()

        result = find_first_child(parent_id)
        expect(result).to_be_sentinel(NO_ENTITY)

    @it("should find child when parent has children")
    def test_has_children():
        parent_id = create_named_entity("parent")
        child_id = create_named_entity("child")
        set_entity_parent(child_id, parent_id)

        result = find_first_child(parent_id)
        expect(result).to_not_be_sentinel(NO_ENTITY)
        expect(result).to_equal(child_id)

    @it("should orphan children when parent is destroyed")
    def test_orphan_on_destroy():
        parent_id = create_named_entity("parent")
        child_id = create_named_entity("child")
        set_entity_parent(child_id, parent_id)

        # Verify parent is set
        expect(get_entity_parent(child_id)).to_equal(parent_id)

        # Destroy parent
        destroy_entity(parent_id)

        # Child should now have NO_ENTITY as parent
        expect(get_entity_parent(child_id)).to_be_sentinel(NO_ENTITY)


with describe("Sentinel Values - Component Access"):
    @before_each
    def setup():
        reset_entities()

    @it("should return NO_INDEX for health of non-existent entity")
    def test_health_nonexistent():
        # Entity 999 doesn't exist
        health = get_entity_health(999)
        expect(health).to_be_sentinel(NO_INDEX_FROM_ZIG)

    @it("should return NO_INDEX for health when querying sentinel value")
    def test_health_sentinel_query():
        # Querying with NO_ENTITY should return NO_INDEX
        health = get_entity_health(NO_ENTITY.value)
        expect(health).to_be_sentinel(NO_INDEX_FROM_ZIG)

    @it("should return valid health for existing entity")
    def test_health_valid():
        entity_id = create_entity()
        set_entity_health(entity_id, 75)

        health = get_entity_health(entity_id)
        expect(health).to_not_be_sentinel(NO_INDEX_FROM_ZIG)
        expect(health).to_equal(75)


with describe("Sentinel Values - Generation/Staleness"):
    @before_each
    def setup():
        reset_entities()

    @it("should return INVALID_GENERATION for out-of-bounds entity")
    def test_generation_invalid():
        gen = get_entity_generation(NO_ENTITY.value)
        expect(gen).to_be_sentinel(INVALID_GENERATION)

    @it("should track generation across entity lifecycle")
    def test_generation_lifecycle():
        # Create entity at slot 0
        e1 = create_entity()
        gen1 = get_entity_generation(e1)
        expect(gen1).to_equal(1)  # First use of this slot

        # Destroy it
        destroy_entity(e1)

        # Create another entity (reuses slot 0)
        e2 = create_entity()
        expect(e2).to_equal(0)  # Same slot

        gen2 = get_entity_generation(e2)
        expect(gen2).to_equal(2)  # Generation increased


with describe("Sentinel Comparison"):
    @it("should allow direct comparison with sentinel values")
    def test_direct_comparison():
        reset_entities()
        result = find_entity_by_name("nonexistent")

        # Direct equality check works
        expect(result == NO_ENTITY.value).to_be_true()
        expect(result == NO_ENTITY).to_be_true()  # Sentinel.__eq__ supports this

    @it("should verify Zig and Python sentinel values match")
    def test_sentinel_values_match():
        # The sentinel values from Zig should match our pre-defined ones
        expect(NO_ENTITY_FROM_ZIG.value).to_equal(NO_ENTITY.value)
        expect(NO_ENTITY_FROM_ZIG.value).to_equal(0xFFFFFFFF)

        expect(NO_INDEX_FROM_ZIG.value).to_equal(NO_INDEX.value)
        expect(NO_INDEX_FROM_ZIG.value).to_equal(-1)


with describe("Real-World Patterns"):
    @before_each
    def setup():
        reset_entities()

    @it("should handle 'find or create' pattern safely")
    def test_find_or_create():
        """Common pattern: find entity by name, create if not found."""

        def get_or_create_entity(name: str) -> int:
            entity_id = find_entity_by_name(name)
            if NO_ENTITY.is_sentinel(entity_id):
                entity_id = create_named_entity(name)
            return entity_id

        # First call creates
        player1 = get_or_create_entity("player")
        expect(player1).to_not_be_sentinel(NO_ENTITY)

        # Second call finds existing
        player2 = get_or_create_entity("player")
        expect(player2).to_equal(player1)

        # Only one entity should exist
        expect(get_entity_count()).to_equal(1)

    @it("should handle parent chain traversal")
    def test_parent_chain():
        """Traverse up parent chain until we hit NO_ENTITY."""
        root = create_named_entity("root")
        child = create_named_entity("child")
        grandchild = create_named_entity("grandchild")

        set_entity_parent(child, root)
        set_entity_parent(grandchild, child)

        # Count ancestors
        ancestors = []
        current = get_entity_parent(grandchild)
        while NO_ENTITY.is_valid(current):
            ancestors.append(current)
            current = get_entity_parent(current)

        expect(len(ancestors)).to_equal(2)  # child and root
        expect(ancestors[0]).to_equal(child)
        expect(ancestors[1]).to_equal(root)
