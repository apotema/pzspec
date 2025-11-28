// Math module - Pure Zig code without manual export wrappers
// The pzspec_exports.zig helper will automatically export compatible functions.

const std = @import("std");

/// A 2D point with x and y coordinates
pub const Point = extern struct {
    x: f32,
    y: f32,

    pub fn new(x: f32, y: f32) Point {
        return Point{ .x = x, .y = y };
    }

    pub fn distance(self: Point, other: Point) f32 {
        const dx = other.x - self.x;
        const dy = other.y - self.y;
        return @sqrt(dx * dx + dy * dy);
    }
};

/// Add two integers
pub fn add(a: i32, b: i32) i32 {
    return a + b;
}

/// Multiply two integers
pub fn multiply(a: i32, b: i32) i32 {
    return a * b;
}

/// Calculate factorial (returns 0 for negative input)
pub fn factorial(n: u32) u64 {
    if (n <= 1) return 1;
    var result: u64 = 1;
    var i: u32 = 2;
    while (i <= n) : (i += 1) {
        result *= i;
    }
    return result;
}

/// Check if a number is prime
pub fn is_prime(n: u32) bool {
    if (n < 2) return false;
    if (n == 2) return true;
    if (n % 2 == 0) return false;

    var i: u32 = 3;
    while (i * i <= n) : (i += 2) {
        if (n % i == 0) return false;
    }
    return true;
}

/// Calculate the nth Fibonacci number
pub fn fibonacci(n: u32) u64 {
    if (n <= 1) return n;
    var a: u64 = 0;
    var b: u64 = 1;
    var i: u32 = 2;
    while (i <= n) : (i += 1) {
        const temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

/// Calculate distance between two points
pub fn point_distance(p1: *const Point, p2: *const Point) f32 {
    return p1.distance(p2.*);
}

/// Create a new point (returns by value)
pub fn point_new(x: f32, y: f32) Point {
    return Point.new(x, y);
}

// This function uses a slice - NOT C ABI compatible, will be skipped
pub fn sum_slice(values: []const i32) i32 {
    var total: i32 = 0;
    for (values) |v| {
        total += v;
    }
    return total;
}

// This function uses an allocator - NOT C ABI compatible, will be skipped
pub fn allocate_buffer(allocator: std.mem.Allocator, size: usize) ![]u8 {
    return allocator.alloc(u8, size);
}
