// Auto-export demo library entry point
//
// This demonstrates the pattern for exposing Zig functions to Python via FFI.
// While the ideal would be to use comptime @export, Zig requires explicit
// callconv(.C) for exported functions. So we use traditional export wrappers,
// but add metadata for Python auto-discovery.

const std = @import("std");
const math = @import("math.zig");

// Re-export types for Python to use
pub const Point = math.Point;

// Export wrappers - these provide the C ABI interface
// Note: We still need these, but the metadata allows Python to auto-discover them

export fn add(a: i32, b: i32) i32 {
    return math.add(a, b);
}

export fn multiply(a: i32, b: i32) i32 {
    return math.multiply(a, b);
}

export fn factorial(n: u32) u64 {
    return math.factorial(n);
}

export fn is_prime(n: u32) bool {
    return math.is_prime(n);
}

export fn fibonacci(n: u32) u64 {
    return math.fibonacci(n);
}

export fn point_distance(p1: *const Point, p2: *const Point) f32 {
    return math.point_distance(p1, p2);
}

export fn point_new(x: f32, y: f32) Point {
    return math.point_new(x, y);
}

// Export metadata for Python to discover function signatures
// This is a simplified version - the full pzspec_exports.zig generates this automatically
const metadata =
    \\{"functions":[
    \\{"name":"add","params":["i32","i32"],"return":"i32"},
    \\{"name":"multiply","params":["i32","i32"],"return":"i32"},
    \\{"name":"factorial","params":["u32"],"return":"u64"},
    \\{"name":"is_prime","params":["u32"],"return":"bool"},
    \\{"name":"fibonacci","params":["u32"],"return":"u64"},
    \\{"name":"point_distance","params":["*const math.Point","*const math.Point"],"return":"f32"},
    \\{"name":"point_new","params":["f32","f32"],"return":"math.Point"}
    \\]}
;

export fn __pzspec_metadata() [*:0]const u8 {
    return metadata;
}
