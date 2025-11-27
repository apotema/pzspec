const std = @import("std");

/// Room levels representing different sizes/capacities
pub const RoomLevel = enum(u8) {
    small = 1,
    medium = 2,
    large = 3,

    pub fn capacity(self: RoomLevel) u32 {
        return switch (self) {
            .small => 10,
            .medium => 25,
            .large => 50,
        };
    }

    pub fn processingSpeed(self: RoomLevel) f32 {
        return switch (self) {
            .small => 1.0,
            .medium => 2.5,
            .large => 5.0,
        };
    }
};

/// Comptime generic factory that creates room types based on level
pub fn ButcheryFactory(comptime L: RoomLevel) type {
    return extern struct {
        const Self = @This();

        // Base stats determined by room level
        pub const level: RoomLevel = L;
        pub const base_capacity: u32 = L.capacity();
        pub const base_speed: f32 = L.processingSpeed();

        // Instance fields (C ABI compatible)
        id: u32,
        workers: u32,
        meat_stored: u32,
        efficiency: f32,
        is_active: bool,

        pub fn init(id: u32) Self {
            return Self{
                .id = id,
                .workers = 0,
                .meat_stored = 0,
                .efficiency = 1.0,
                .is_active = false,
            };
        }

        pub fn effectiveCapacity(self: *const Self) u32 {
            const base: f32 = @floatFromInt(base_capacity);
            const eff_cap = base * self.efficiency;
            return @intFromFloat(eff_cap);
        }

        pub fn effectiveSpeed(self: *const Self) f32 {
            const worker_bonus: f32 = @floatFromInt(self.workers);
            return base_speed * self.efficiency * (1.0 + worker_bonus * 0.1);
        }

        pub fn canStore(self: *const Self, amount: u32) bool {
            return self.meat_stored + amount <= self.effectiveCapacity();
        }
    };
}

// Concrete types for FFI export (Zig comptime generics can't be directly exported)
pub const SmallButchery = ButcheryFactory(.small);
pub const MediumButchery = ButcheryFactory(.medium);
pub const LargeButchery = ButcheryFactory(.large);

// FFI exports for SmallButchery
export fn small_butchery_new(id: u32) SmallButchery {
    return SmallButchery.init(id);
}

export fn small_butchery_effective_capacity(b: *const SmallButchery) u32 {
    return b.effectiveCapacity();
}

export fn small_butchery_effective_speed(b: *const SmallButchery) f32 {
    return b.effectiveSpeed();
}

export fn small_butchery_can_store(b: *const SmallButchery, amount: u32) bool {
    return b.canStore(amount);
}

export fn small_butchery_base_capacity() u32 {
    return SmallButchery.base_capacity;
}

export fn small_butchery_base_speed() f32 {
    return SmallButchery.base_speed;
}

// FFI exports for MediumButchery
export fn medium_butchery_new(id: u32) MediumButchery {
    return MediumButchery.init(id);
}

export fn medium_butchery_effective_capacity(b: *const MediumButchery) u32 {
    return b.effectiveCapacity();
}

export fn medium_butchery_effective_speed(b: *const MediumButchery) f32 {
    return b.effectiveSpeed();
}

export fn medium_butchery_can_store(b: *const MediumButchery, amount: u32) bool {
    return b.canStore(amount);
}

export fn medium_butchery_base_capacity() u32 {
    return MediumButchery.base_capacity;
}

export fn medium_butchery_base_speed() f32 {
    return MediumButchery.base_speed;
}

// FFI exports for LargeButchery
export fn large_butchery_new(id: u32) LargeButchery {
    return LargeButchery.init(id);
}

export fn large_butchery_effective_capacity(b: *const LargeButchery) u32 {
    return b.effectiveCapacity();
}

export fn large_butchery_effective_speed(b: *const LargeButchery) f32 {
    return b.effectiveSpeed();
}

export fn large_butchery_can_store(b: *const LargeButchery, amount: u32) bool {
    return b.canStore(amount);
}

export fn large_butchery_base_capacity() u32 {
    return LargeButchery.base_capacity;
}

export fn large_butchery_base_speed() f32 {
    return LargeButchery.base_speed;
}

// Resource types that butcheries process
pub const MeatType = enum(u8) {
    beef = 0,
    pork = 1,
    poultry = 2,
    game = 3,
};

pub const MeatProduct = extern struct {
    meat_type: MeatType,
    weight: f32,
    quality: f32,
    processed: bool,
};

export fn meat_product_new(meat_type: MeatType, weight: f32) MeatProduct {
    return MeatProduct{
        .meat_type = meat_type,
        .weight = weight,
        .quality = 1.0,
        .processed = false,
    };
}

export fn meat_product_process(product: *MeatProduct, efficiency: f32) void {
    if (!product.processed) {
        product.quality = product.quality * efficiency;
        product.processed = true;
    }
}

export fn meat_product_value(product: *const MeatProduct) f32 {
    const base_value: f32 = switch (product.meat_type) {
        .beef => 10.0,
        .pork => 7.0,
        .poultry => 5.0,
        .game => 15.0,
    };
    return base_value * product.weight * product.quality;
}
