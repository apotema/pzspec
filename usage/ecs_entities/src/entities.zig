const std = @import("std");

// =============================================================================
// Sentinel Values
// =============================================================================
// In ECS systems, entity IDs are typically indices (0, 1, 2, ...) where 0 is a
// valid entity. We can't use 0 or null to indicate "no entity", so we use
// sentinel values - special values that represent "no valid value".

/// Sentinel value for "no entity" - maximum u32 value (can never be a valid index)
pub const NO_ENTITY: u32 = std.math.maxInt(u32); // 0xFFFFFFFF

/// Sentinel value for "no index" - commonly -1 for signed integers
pub const NO_INDEX: i32 = -1;

/// Sentinel value for "invalid generation" - used to detect stale references
pub const INVALID_GENERATION: u32 = std.math.maxInt(u32);

// Export sentinel getters for Python to retrieve the actual values
export fn get_no_entity_sentinel() u32 {
    return NO_ENTITY;
}

export fn get_no_index_sentinel() i32 {
    return NO_INDEX;
}

export fn get_invalid_generation_sentinel() u32 {
    return INVALID_GENERATION;
}

// =============================================================================
// Entity System
// =============================================================================

/// Maximum number of entities in our simple ECS
const MAX_ENTITIES: usize = 1000;

/// Entity component data
const EntityData = struct {
    alive: bool = false,
    generation: u32 = 0,
    name: [32]u8 = [_]u8{0} ** 32,
    health: i32 = 0,
    position_x: f32 = 0.0,
    position_y: f32 = 0.0,
    parent: u32 = NO_ENTITY,
};

/// Global entity storage
var entities: [MAX_ENTITIES]EntityData = [_]EntityData{.{}} ** MAX_ENTITIES;
var entity_count: u32 = 0;

/// Create a new entity and return its ID
export fn create_entity() u32 {
    if (entity_count >= MAX_ENTITIES) {
        return NO_ENTITY; // No space left
    }

    // Find first free slot
    for (&entities, 0..) |*entity, i| {
        if (!entity.alive) {
            entity.alive = true;
            entity.generation += 1;
            entity.health = 100;
            entity.parent = NO_ENTITY;
            entity_count += 1;
            return @intCast(i);
        }
    }

    return NO_ENTITY; // Should not reach here
}

/// Create an entity with a name
export fn create_named_entity(name_ptr: [*:0]const u8) u32 {
    const entity_id = create_entity();
    if (entity_id == NO_ENTITY) {
        return NO_ENTITY;
    }

    // Copy name into entity
    var i: usize = 0;
    while (name_ptr[i] != 0 and i < 31) : (i += 1) {
        entities[entity_id].name[i] = name_ptr[i];
    }
    entities[entity_id].name[i] = 0;

    return entity_id;
}

/// Destroy an entity
export fn destroy_entity(entity_id: u32) bool {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return false;
    }

    if (!entities[entity_id].alive) {
        return false;
    }

    // Clear all children's parent references
    for (&entities) |*entity| {
        if (entity.alive and entity.parent == entity_id) {
            entity.parent = NO_ENTITY;
        }
    }

    entities[entity_id].alive = false;
    entities[entity_id].name = [_]u8{0} ** 32;
    entities[entity_id].health = 0;
    entity_count -= 1;
    return true;
}

/// Check if an entity is alive
export fn is_entity_alive(entity_id: u32) bool {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return false;
    }
    return entities[entity_id].alive;
}

/// Get entity count
export fn get_entity_count() u32 {
    return entity_count;
}

/// Reset all entities (for testing)
export fn reset_entities() void {
    for (&entities) |*entity| {
        entity.* = .{};
    }
    entity_count = 0;
}

// =============================================================================
// Entity Queries - Return sentinel values when not found
// =============================================================================

/// Find entity by name - returns NO_ENTITY if not found
export fn find_entity_by_name(name_ptr: [*:0]const u8) u32 {
    for (entities, 0..) |entity, i| {
        if (entity.alive) {
            // Compare names
            var match = true;
            var j: usize = 0;
            while (name_ptr[j] != 0 and j < 31) : (j += 1) {
                if (entity.name[j] != name_ptr[j]) {
                    match = false;
                    break;
                }
            }
            if (match and entity.name[j] == 0) {
                return @intCast(i);
            }
        }
    }
    return NO_ENTITY; // Not found
}

/// Find entity with highest health - returns NO_ENTITY if no entities exist
export fn find_healthiest_entity() u32 {
    var best_id: u32 = NO_ENTITY;
    var best_health: i32 = std.math.minInt(i32);

    for (entities, 0..) |entity, i| {
        if (entity.alive and entity.health > best_health) {
            best_health = entity.health;
            best_id = @intCast(i);
        }
    }

    return best_id;
}

/// Find nearest entity to a position - returns NO_ENTITY if no entities exist
export fn find_nearest_entity(x: f32, y: f32) u32 {
    var nearest_id: u32 = NO_ENTITY;
    var nearest_dist: f32 = std.math.floatMax(f32);

    for (entities, 0..) |entity, i| {
        if (entity.alive) {
            const dx = entity.position_x - x;
            const dy = entity.position_y - y;
            const dist = @sqrt(dx * dx + dy * dy);
            if (dist < nearest_dist) {
                nearest_dist = dist;
                nearest_id = @intCast(i);
            }
        }
    }

    return nearest_id;
}

/// Get entity's parent - returns NO_ENTITY if no parent or invalid entity
export fn get_entity_parent(entity_id: u32) u32 {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return NO_ENTITY;
    }
    if (!entities[entity_id].alive) {
        return NO_ENTITY;
    }
    return entities[entity_id].parent;
}

/// Set entity's parent - returns true on success
export fn set_entity_parent(entity_id: u32, parent_id: u32) bool {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return false;
    }
    if (!entities[entity_id].alive) {
        return false;
    }
    // Parent can be NO_ENTITY (no parent) or a valid alive entity
    if (parent_id != NO_ENTITY) {
        if (parent_id >= MAX_ENTITIES or !entities[parent_id].alive) {
            return false;
        }
        // Prevent self-parenting
        if (parent_id == entity_id) {
            return false;
        }
    }
    entities[entity_id].parent = parent_id;
    return true;
}

/// Find first child of an entity - returns NO_ENTITY if no children
export fn find_first_child(parent_id: u32) u32 {
    if (parent_id >= MAX_ENTITIES or parent_id == NO_ENTITY) {
        return NO_ENTITY;
    }

    for (entities, 0..) |entity, i| {
        if (entity.alive and entity.parent == parent_id) {
            return @intCast(i);
        }
    }

    return NO_ENTITY;
}

// =============================================================================
// Component Access
// =============================================================================

/// Get entity health - returns NO_INDEX (-1) if entity doesn't exist
export fn get_entity_health(entity_id: u32) i32 {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return NO_INDEX;
    }
    if (!entities[entity_id].alive) {
        return NO_INDEX;
    }
    return entities[entity_id].health;
}

/// Set entity health - returns true on success
export fn set_entity_health(entity_id: u32, health: i32) bool {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return false;
    }
    if (!entities[entity_id].alive) {
        return false;
    }
    entities[entity_id].health = health;
    return true;
}

/// Get entity position X - returns NaN if entity doesn't exist
export fn get_entity_position_x(entity_id: u32) f32 {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return std.math.nan(f32);
    }
    if (!entities[entity_id].alive) {
        return std.math.nan(f32);
    }
    return entities[entity_id].position_x;
}

/// Get entity position Y - returns NaN if entity doesn't exist
export fn get_entity_position_y(entity_id: u32) f32 {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return std.math.nan(f32);
    }
    if (!entities[entity_id].alive) {
        return std.math.nan(f32);
    }
    return entities[entity_id].position_y;
}

/// Set entity position - returns true on success
export fn set_entity_position(entity_id: u32, x: f32, y: f32) bool {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return false;
    }
    if (!entities[entity_id].alive) {
        return false;
    }
    entities[entity_id].position_x = x;
    entities[entity_id].position_y = y;
    return true;
}

/// Get entity generation - returns INVALID_GENERATION if entity slot was never used
export fn get_entity_generation(entity_id: u32) u32 {
    if (entity_id >= MAX_ENTITIES or entity_id == NO_ENTITY) {
        return INVALID_GENERATION;
    }
    return entities[entity_id].generation;
}

// =============================================================================
// Batch Operations
// =============================================================================

/// Find all entities within radius - returns count, fills out_ids array
/// out_ids array should be pre-allocated, max_count limits results
export fn find_entities_in_radius(
    center_x: f32,
    center_y: f32,
    radius: f32,
    out_ids: [*]u32,
    max_count: u32,
) u32 {
    var count: u32 = 0;
    const radius_sq = radius * radius;

    for (entities, 0..) |entity, i| {
        if (entity.alive) {
            const dx = entity.position_x - center_x;
            const dy = entity.position_y - center_y;
            const dist_sq = dx * dx + dy * dy;
            if (dist_sq <= radius_sq) {
                if (count < max_count) {
                    out_ids[count] = @intCast(i);
                    count += 1;
                }
            }
        }
    }

    return count;
}
