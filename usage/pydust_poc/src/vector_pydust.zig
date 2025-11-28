// Vector Math Library - Pydust Version
// 
// This demonstrates how the same vector math library would be written
// using Ziggy-Pydust instead of manual C ABI exports.
//
// Key differences from the ctypes approach:
// 1. No 'export' keyword needed - Pydust handles FFI generation
// 2. No 'extern struct' - regular Zig structs work
// 3. Named arguments via anonymous struct parameters
// 4. Direct method calls instead of wrapper functions

const std = @import("std");
const py = @import("pydust");

// 2D Vector - Regular Zig struct (not extern!)
pub const Vec2 = struct {
    x: f32,
    y: f32,

    // Standard Zig constructor
    pub fn init(x: f32, y: f32) Vec2 {
        return Vec2{ .x = x, .y = y };
    }

    // Methods use idiomatic Zig patterns
    pub fn add(self: Vec2, other: Vec2) Vec2 {
        return Vec2{ .x = self.x + other.x, .y = self.y + other.y };
    }

    pub fn subtract(self: Vec2, other: Vec2) Vec2 {
        return Vec2{ .x = self.x - other.x, .y = self.y - other.y };
    }

    pub fn scale(self: Vec2, scalar: f32) Vec2 {
        return Vec2{ .x = self.x * scalar, .y = self.y * scalar };
    }

    pub fn dot(self: Vec2, other: Vec2) f32 {
        return self.x * other.x + self.y * other.y;
    }

    pub fn magnitude(self: Vec2) f32 {
        return @sqrt(self.x * self.x + self.y * self.y);
    }

    pub fn normalize(self: Vec2) Vec2 {
        const mag = self.magnitude();
        if (mag == 0.0) {
            return Vec2{ .x = 0.0, .y = 0.0 };
        }
        return Vec2{ .x = self.x / mag, .y = self.y / mag };
    }

    pub fn distance(self: Vec2, other: Vec2) f32 {
        const dx = self.x - other.x;
        const dy = self.y - other.y;
        return @sqrt(dx * dx + dy * dy);
    }

    // Pydust: Enable Python str() and repr()
    pub fn __repr__(self: Vec2) !py.PyString {
        return py.PyString.fromFmt("Vec2(x={d:.3}, y={d:.3})", .{ self.x, self.y });
    }
};

// 3D Vector
pub const Vec3 = struct {
    x: f32,
    y: f32,
    z: f32,

    pub fn init(x: f32, y: f32, z: f32) Vec3 {
        return Vec3{ .x = x, .y = y, .z = z };
    }

    pub fn add(self: Vec3, other: Vec3) Vec3 {
        return Vec3{ .x = self.x + other.x, .y = self.y + other.y, .z = self.z + other.z };
    }

    pub fn cross(self: Vec3, other: Vec3) Vec3 {
        return Vec3{
            .x = self.y * other.z - self.z * other.y,
            .y = self.z * other.x - self.x * other.z,
            .z = self.x * other.y - self.y * other.x,
        };
    }

    pub fn dot(self: Vec3, other: Vec3) f32 {
        return self.x * other.x + self.y * other.y + self.z * other.z;
    }

    pub fn magnitude(self: Vec3) f32 {
        return @sqrt(self.x * self.x + self.y * self.y + self.z * self.z);
    }

    pub fn __repr__(self: Vec3) !py.PyString {
        return py.PyString.fromFmt("Vec3(x={d:.3}, y={d:.3}, z={d:.3})", .{ self.x, self.y, self.z });
    }
};

// Module-level functions with named arguments
// Pydust automatically handles type conversion

/// Create a new 2D vector
pub fn vec2_new(args: struct { x: f32, y: f32 }) Vec2 {
    return Vec2.init(args.x, args.y);
}

/// Add two 2D vectors
pub fn vec2_add(args: struct { a: Vec2, b: Vec2 }) Vec2 {
    return args.a.add(args.b);
}

/// Subtract two 2D vectors
pub fn vec2_subtract(args: struct { a: Vec2, b: Vec2 }) Vec2 {
    return args.a.subtract(args.b);
}

/// Scale a 2D vector by a scalar
pub fn vec2_scale(args: struct { v: Vec2, scalar: f32 }) Vec2 {
    return args.v.scale(args.scalar);
}

/// Calculate dot product of two 2D vectors
pub fn vec2_dot(args: struct { a: Vec2, b: Vec2 }) f32 {
    return args.a.dot(args.b);
}

/// Calculate magnitude of a 2D vector
pub fn vec2_magnitude(args: struct { v: Vec2 }) f32 {
    return args.v.magnitude();
}

/// Normalize a 2D vector to unit length
pub fn vec2_normalize(args: struct { v: Vec2 }) Vec2 {
    return args.v.normalize();
}

/// Calculate distance between two 2D vectors
pub fn vec2_distance(args: struct { a: Vec2, b: Vec2 }) f32 {
    return args.a.distance(args.b);
}

/// Create a new 3D vector
pub fn vec3_new(args: struct { x: f32, y: f32, z: f32 }) Vec3 {
    return Vec3.init(args.x, args.y, args.z);
}

/// Add two 3D vectors
pub fn vec3_add(args: struct { a: Vec3, b: Vec3 }) Vec3 {
    return args.a.add(args.b);
}

/// Calculate cross product of two 3D vectors
pub fn vec3_cross(args: struct { a: Vec3, b: Vec3 }) Vec3 {
    return args.a.cross(args.b);
}

/// Calculate dot product of two 3D vectors
pub fn vec3_dot(args: struct { a: Vec3, b: Vec3 }) f32 {
    return args.a.dot(args.b);
}

/// Calculate magnitude of a 3D vector
pub fn vec3_magnitude(args: struct { v: Vec3 }) f32 {
    return args.v.magnitude();
}

// Pydust: Register this module as a Python extension
comptime {
    py.rootmodule(@This());
}
