// Math library using Ziggy-Pydust
//
// This demonstrates how Pydust eliminates the need for manual C ABI export wrappers.
// Functions are automatically wrapped and exposed to Python with proper type conversion.
//
// IMPORTANT: Pydust requires function arguments to be passed as a struct parameter,
// not as individual parameters. This enables Python keyword arguments and defaults.

const std = @import("std");
const py = @import("pydust");

// Root module reference required by Pydust for container types
const root = @This();

/// Add two integers
/// Pydust handles the Python-Zig type conversion automatically
pub fn add(args: struct { a: i64, b: i64 }) i64 {
    return args.a + args.b;
}

/// Multiply two integers
pub fn multiply(args: struct { a: i64, b: i64 }) i64 {
    return args.a * args.b;
}

/// Calculate factorial
pub fn factorial(args: struct { n: u64 }) u64 {
    const n = args.n;
    if (n <= 1) return 1;
    var result: u64 = 1;
    var i: u64 = 2;
    while (i <= n) : (i += 1) {
        result *= i;
    }
    return result;
}

/// Check if a number is prime
pub fn is_prime(args: struct { n: u64 }) bool {
    const n = args.n;
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
pub fn fibonacci(args: struct { n: u64 }) u64 {
    const n = args.n;
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

// Export all public declarations to Python
comptime {
    py.rootmodule(root);
}
