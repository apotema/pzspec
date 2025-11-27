"""
PZSpec tests for Pydust-based math library.

This demonstrates testing Zig code exposed via Ziggy-Pydust.
Note: No ctypes, no manual type declarations, no C ABI wrappers needed!
The Zig code is directly callable as a Python module.
"""

# Import the Pydust-built module directly (after poetry install)
# This replaces ZigLibrary entirely for Pydust projects
try:
    import mathlib
    PYDUST_AVAILABLE = True
except ImportError:
    PYDUST_AVAILABLE = False
    print("Warning: mathlib not built. Run 'poetry install' first.")

from pzspec import describe, it, expect, it_skip


with describe("Pydust Math Functions"):

    @it("should add two integers") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_add():
        # Direct function call - no get_function, no ctypes!
        result = mathlib.add(10, 20)
        expect(result).to_equal(30)

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


with describe("Pydust Point Struct"):

    @it("should create a point") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_point_new():
        # Pydust returns a proper Python object, not a ctypes struct
        p = mathlib.point_new(3.0, 4.0)
        expect(p.x).to_equal(3.0)
        expect(p.y).to_equal(4.0)

    @it("should calculate point magnitude") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_point_magnitude():
        p = mathlib.point_new(3.0, 4.0)
        expect(p.magnitude()).to_equal(5.0)

    @it("should calculate distance between points") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_point_distance():
        p1 = mathlib.point_new(0.0, 0.0)
        p2 = mathlib.point_new(3.0, 4.0)
        # Note: No ctypes.byref() needed - Pydust handles object passing
        distance = mathlib.point_distance(p1, p2)
        expect(distance).to_equal(5.0)


with describe("Pydust String Handling"):

    @it("should greet by name") if PYDUST_AVAILABLE else it_skip("mathlib not built")
    def test_greet():
        # Pydust converts Python str <-> Zig []const u8 automatically
        result = mathlib.greet("World")
        expect(result).to_equal("Hello, World!")


# Comparison with traditional ctypes approach:
#
# Traditional (ZigLibrary + ctypes):
#   class Point(ctypes.Structure):
#       _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]
#
#   zig = ZigLibrary()
#   func = zig.get_function("point_distance", [POINTER(Point), POINTER(Point)], c_float)
#   result = func(ctypes.byref(p1), ctypes.byref(p2))
#
# With Pydust:
#   import mathlib
#   result = mathlib.point_distance(p1, p2)
#
# Benefits:
# - No ctypes boilerplate
# - No manual type declarations
# - No byref() for pointers
# - Native Python objects instead of ctypes structs
# - IDE autocompletion works
# - Type safety at compile time (Zig side)
