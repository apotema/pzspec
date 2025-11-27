// Calculator Library - Demonstrates partial coverage
// Some functions will be tested, others will remain untested

const std = @import("std");

// Basic arithmetic operations (will be tested)
export fn add(a: i32, b: i32) i32 {
    return a + b;
}

export fn subtract(a: i32, b: i32) i32 {
    return a - b;
}

export fn multiply(a: i32, b: i32) i32 {
    return a * b;
}

// Division with error handling (partially tested)
export fn divide(a: i32, b: i32) i32 {
    if (b == 0) {
        return 0; // Return 0 for division by zero
    }
    return @divTrunc(a, b);
}

// Advanced operations (NOT tested - will show as uncovered)
export fn power(base: i32, exp: i32) i32 {
    if (exp < 0) {
        return 0; // Negative exponents return 0 for integers
    }
    if (exp == 0) {
        return 1;
    }
    var result: i32 = 1;
    var i: i32 = 0;
    while (i < exp) : (i += 1) {
        result *= base;
    }
    return result;
}

export fn factorial(n: i32) i32 {
    if (n < 0) {
        return 0; // Invalid input
    }
    if (n <= 1) {
        return 1;
    }
    var result: i32 = 1;
    var i: i32 = 2;
    while (i <= n) : (i += 1) {
        result *= i;
    }
    return result;
}

export fn fibonacci(n: i32) i32 {
    if (n < 0) {
        return 0;
    }
    if (n <= 1) {
        return n;
    }
    var a: i32 = 0;
    var b: i32 = 1;
    var i: i32 = 2;
    while (i <= n) : (i += 1) {
        const temp = a + b;
        a = b;
        b = temp;
    }
    return b;
}

// Comparison functions (NOT tested)
export fn max(a: i32, b: i32) i32 {
    if (a > b) {
        return a;
    }
    return b;
}

export fn min(a: i32, b: i32) i32 {
    if (a < b) {
        return a;
    }
    return b;
}

export fn abs(n: i32) i32 {
    if (n < 0) {
        return -n;
    }
    return n;
}

// Sign function (NOT tested)
export fn sign(n: i32) i32 {
    if (n > 0) {
        return 1;
    } else if (n < 0) {
        return -1;
    }
    return 0;
}

// Check if number is even/odd (partially tested)
export fn is_even(n: i32) bool {
    return @mod(n, 2) == 0;
}

export fn is_odd(n: i32) bool {
    return @mod(n, 2) != 0;
}

// GCD function (NOT tested)
export fn gcd(a: i32, b: i32) i32 {
    var x = abs(a);
    var y = abs(b);
    while (y != 0) {
        const temp = @mod(x, y);
        x = y;
        y = temp;
    }
    return x;
}
