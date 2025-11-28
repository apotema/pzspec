"""
PZSpec tests for Pydust-based math library.

This demonstrates testing Zig code exposed via Ziggy-Pydust.
Note: No ctypes, no manual type declarations, no C ABI wrappers needed!
The Zig code is directly callable as a Python module.

Usage:
    # Build the module first
    python3 build.py

    # Run tests
    python3 test_pydust_mathlib.py
"""

# Import the Pydust-built module directly (after python3 build.py)
# This replaces ZigLibrary entirely for Pydust projects
try:
    import mathlib
    PYDUST_AVAILABLE = True
except ImportError:
    PYDUST_AVAILABLE = False
    print("Warning: mathlib not built. Run 'python3 build.py' first.")

from pzspec import describe, it, expect, it_skip


with describe("Pydust Math Functions"):

    @it("should add two integers") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_add():
        # Direct function call - no get_function, no ctypes!
        result = mathlib.add(10, 20)
        expect(result).to_equal(30)

        # Multiple test cases
        expect(mathlib.add(0, 0)).to_equal(0)
        expect(mathlib.add(-5, 5)).to_equal(0)
        expect(mathlib.add(100, 200)).to_equal(300)

    @it("should multiply two integers") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_multiply():
        result = mathlib.multiply(6, 7)
        expect(result).to_equal(42)

    @it("should calculate factorial") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_factorial():
        expect(mathlib.factorial(0)).to_equal(1)
        expect(mathlib.factorial(1)).to_equal(1)
        expect(mathlib.factorial(5)).to_equal(120)
        expect(mathlib.factorial(10)).to_equal(3628800)

    @it("should check if number is prime") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_is_prime():
        expect(mathlib.is_prime(2)).to_be_true()
        expect(mathlib.is_prime(3)).to_be_true()
        expect(mathlib.is_prime(4)).to_be_false()
        expect(mathlib.is_prime(17)).to_be_true()
        expect(mathlib.is_prime(18)).to_be_false()

    @it("should calculate fibonacci numbers") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_fibonacci():
        expect(mathlib.fibonacci(0)).to_equal(0)
        expect(mathlib.fibonacci(1)).to_equal(1)
        expect(mathlib.fibonacci(10)).to_equal(55)
        expect(mathlib.fibonacci(20)).to_equal(6765)


# Run tests when executed directly
if __name__ == "__main__":
    from pzspec.dsl import get_runner
    import sys
    runner = get_runner()
    success = runner.run()
    sys.exit(0 if success else 1)


# Comparison with traditional ctypes approach:
#
# Traditional (ZigLibrary + ctypes):
#   zig = ZigLibrary()
#   add = zig.get_function("add", [ctypes.c_int64, ctypes.c_int64], ctypes.c_int64)
#   result = add(10, 20)
#
# With Pydust:
#   import mathlib
#   result = mathlib.add(10, 20)
#
# Zig code comparison:
#
# Traditional (explicit C ABI export):
#   export fn add(a: i64, b: i64) i64 { return a + b; }
#
# With Pydust (automatic Python bindings):
#   pub fn add(args: struct { a: i64, b: i64 }) i64 { return args.a + args.b; }
#
# Benefits:
# - No ctypes boilerplate
# - No manual type declarations
# - Keyword arguments support
# - IDE autocompletion works
# - Type safety at compile time (Zig side)
