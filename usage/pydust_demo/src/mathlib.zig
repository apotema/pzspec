// Math library using Ziggy-Pydust
//
// This demonstrates how Pydust eliminates the need for manual C ABI export wrappers.
// Functions are automatically wrapped and exposed to Python with proper type conversion.

const std = @import("std");
const py = @import("pydust");

/// A 2D point structure
/// Pydust automatically converts this to/from Python objects
pub const Point = struct {
    x: f64,
    y: f64,

    /// Calculate distance from origin
    pub fn magnitude(self: Point) f64 {
        return @sqrt(self.x * self.x + self.y * self.y);
    }

    /// Calculate distance to another point
    pub fn distance_to(self: Point, other: Point) f64 {
        const dx = other.x - self.x;
        const dy = other.y - self.y;
        return @sqrt(dx * dx + dy * dy);
    }
};

/// Add two integers
/// Pydust handles the Python-Zig type conversion automatically
pub fn add(a: i64, b: i64) i64 {
    return a + b;
}

/// Multiply two integers
pub fn multiply(a: i64, b: i64) i64 {
    return a * b;
}

/// Calculate factorial
pub fn factorial(n: u64) u64 {
    if (n <= 1) return 1;
    var result: u64 = 1;
    var i: u64 = 2;
    while (i <= n) : (i += 1) {
        result *= i;
    }
    return result;
}

/// Check if a number is prime
pub fn is_prime(n: u64) bool {
    if (n < 2) return false;
    if (n == 2) return true;
    if (n % 2 == 0) return false;

    var i: u64 = 3;
    while (i * i <= n) : (i += 2) {
        if (n % i == 0) return false;
    }
    return true;
}

/// Calculate the nth Fibonacci number
pub fn fibonacci(n: u64) u64 {
    if (n <= 1) return n;
    var a: u64 = 0;
    var b: u64 = 1;
    var i: u64 = 2;
    while (i <= n) : (i += 1) {
        const temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

/// Create a new Point
pub fn point_new(x: f64, y: f64) Point {
    return Point{ .x = x, .y = y };
}

/// Calculate distance between two points
pub fn point_distance(p1: Point, p2: Point) f64 {
    return p1.distance_to(p2);
}

/// Greet someone by name
/// Demonstrates string handling - Pydust converts []const u8 <-> Python str
pub fn greet(name: []const u8) py.PyString {
    return py.PyString.fromSlice("Hello, " ++ name ++ "!") catch py.PyString.fromSlice("Hello!");
}

// Export all public declarations to Python
comptime {
    py.rootmodule(@This());
}
