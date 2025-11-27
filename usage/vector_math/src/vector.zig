// Vector Math Library - A simple 2D/3D vector math library in Zig
// This demonstrates a real-world use case for PZSpec testing

const std = @import("std");

// 2D Vector structure
pub const Vec2 = extern struct {
    x: f32,
    y: f32,

    // Create a new 2D vector
    pub fn new(x: f32, y: f32) Vec2 {
        return Vec2{ .x = x, .y = y };
    }

    // Add two vectors
    pub fn add(a: Vec2, b: Vec2) Vec2 {
        return Vec2{ .x = a.x + b.x, .y = a.y + b.y };
    }

    // Subtract two vectors
    pub fn subtract(a: Vec2, b: Vec2) Vec2 {
        return Vec2{ .x = a.x - b.x, .y = a.y - b.y };
    }

    // Multiply vector by scalar
    pub fn scale(v: Vec2, scalar: f32) Vec2 {
        return Vec2{ .x = v.x * scalar, .y = v.y * scalar };
    }

    // Calculate dot product
    pub fn dot(a: Vec2, b: Vec2) f32 {
        return a.x * b.x + a.y * b.y;
    }

    // Calculate magnitude (length)
    pub fn magnitude(v: Vec2) f32 {
        return @sqrt(v.x * v.x + v.y * v.y);
    }

    // Normalize vector (unit vector)
    pub fn normalize(v: Vec2) Vec2 {
        const mag = magnitude(v);
        if (mag == 0.0) {
            return Vec2{ .x = 0.0, .y = 0.0 };
        }
        return Vec2{ .x = v.x / mag, .y = v.y / mag };
    }

    // Calculate distance between two vectors
    pub fn distance(a: Vec2, b: Vec2) f32 {
        const dx = a.x - b.x;
        const dy = a.y - b.y;
        return @sqrt(dx * dx + dy * dy);
    }
};

// 3D Vector structure
pub const Vec3 = extern struct {
    x: f32,
    y: f32,
    z: f32,

    // Create a new 3D vector
    pub fn new(x: f32, y: f32, z: f32) Vec3 {
        return Vec3{ .x = x, .y = y, .z = z };
    }

    // Add two vectors
    pub fn add(a: Vec3, b: Vec3) Vec3 {
        return Vec3{ .x = a.x + b.x, .y = a.y + b.y, .z = a.z + b.z };
    }

    // Calculate cross product
    pub fn cross(a: Vec3, b: Vec3) Vec3 {
        return Vec3{
            .x = a.y * b.z - a.z * b.y,
            .y = a.z * b.x - a.x * b.z,
            .z = a.x * b.y - a.y * b.x,
        };
    }

    // Calculate dot product
    pub fn dot(a: Vec3, b: Vec3) f32 {
        return a.x * b.x + a.y * b.y + a.z * b.z;
    }

    // Calculate magnitude (length)
    pub fn magnitude(v: Vec3) f32 {
        return @sqrt(v.x * v.x + v.y * v.y + v.z * v.z);
    }
};

// Exported C-compatible functions for FFI
export fn vec2_new(x: f32, y: f32) Vec2 {
    return Vec2.new(x, y);
}

export fn vec2_add(a: *const Vec2, b: *const Vec2) Vec2 {
    return Vec2.add(a.*, b.*);
}

export fn vec2_subtract(a: *const Vec2, b: *const Vec2) Vec2 {
    return Vec2.subtract(a.*, b.*);
}

export fn vec2_scale(v: *const Vec2, scalar: f32) Vec2 {
    return Vec2.scale(v.*, scalar);
}

export fn vec2_dot(a: *const Vec2, b: *const Vec2) f32 {
    return Vec2.dot(a.*, b.*);
}

export fn vec2_magnitude(v: *const Vec2) f32 {
    return Vec2.magnitude(v.*);
}

export fn vec2_normalize(v: *const Vec2) Vec2 {
    return Vec2.normalize(v.*);
}

export fn vec2_distance(a: *const Vec2, b: *const Vec2) f32 {
    return Vec2.distance(a.*, b.*);
}

export fn vec3_new(x: f32, y: f32, z: f32) Vec3 {
    return Vec3.new(x, y, z);
}

export fn vec3_add(a: *const Vec3, b: *const Vec3) Vec3 {
    return Vec3.add(a.*, b.*);
}

export fn vec3_cross(a: *const Vec3, b: *const Vec3) Vec3 {
    return Vec3.cross(a.*, b.*);
}

export fn vec3_dot(a: *const Vec3, b: *const Vec3) f32 {
    return Vec3.dot(a.*, b.*);
}

export fn vec3_magnitude(v: *const Vec3) f32 {
    return Vec3.magnitude(v.*);
}
