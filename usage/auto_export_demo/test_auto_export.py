"""
Auto-export demo test file.

This demonstrates how PZSpec can automatically discover and bind functions
when the Zig library is built with pzspec_exports.zig metadata.
"""

import ctypes
from pzspec import ZigLibrary, describe, it, expect


# Define the Point struct to match Zig's extern struct
class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]


# Load library with struct registry for auto-binding
zig = ZigLibrary(struct_registry={"Point": Point, "math.Point": Point})


# Show what was auto-discovered
print(f"Library has metadata: {zig.has_metadata()}")
print(f"Auto-discovered functions: {zig.get_discovered_functions()}")


with describe("Auto-discovered Math Functions"):

    @it("should add two integers via auto-discovered function")
    def test_add():
        # Can call directly as attribute - types inferred from metadata!
        result = zig.add(10, 20)
        expect(result).to_equal(30)

    @it("should multiply two integers")
    def test_multiply():
        result = zig.multiply(6, 7)
        expect(result).to_equal(42)

    @it("should calculate factorial")
    def test_factorial():
        expect(zig.factorial(0)).to_equal(1)
        expect(zig.factorial(1)).to_equal(1)
        expect(zig.factorial(5)).to_equal(120)
        expect(zig.factorial(10)).to_equal(3628800)

    @it("should check if number is prime")
    def test_is_prime():
        expect(zig.is_prime(2)).to_be_true()
        expect(zig.is_prime(3)).to_be_true()
        expect(zig.is_prime(4)).to_be_false()
        expect(zig.is_prime(17)).to_be_true()
        expect(zig.is_prime(18)).to_be_false()

    @it("should calculate fibonacci numbers")
    def test_fibonacci():
        expect(zig.fibonacci(0)).to_equal(0)
        expect(zig.fibonacci(1)).to_equal(1)
        expect(zig.fibonacci(10)).to_equal(55)
        expect(zig.fibonacci(20)).to_equal(6765)


with describe("Auto-discovered Struct Functions"):

    @it("should create a point")
    def test_point_new():
        p = zig.point_new(3.0, 4.0)
        expect(p.x).to_equal(3.0)
        expect(p.y).to_equal(4.0)

    @it("should calculate distance between points")
    def test_point_distance():
        p1 = Point(0.0, 0.0)
        p2 = Point(3.0, 4.0)

        # Auto-discovered function with pointer params
        distance = zig.point_distance(ctypes.byref(p1), ctypes.byref(p2))
        expect(distance).to_equal(5.0)


with describe("Fallback to Manual Binding"):

    @it("should still support get_function for manual binding")
    def test_manual_binding():
        # The old way still works
        add_func = zig.get_function("add", [ctypes.c_int32, ctypes.c_int32], ctypes.c_int32)
        result = add_func(100, 200)
        expect(result).to_equal(300)

    @it("should support registering structs after initialization")
    def test_register_struct():
        # Can register additional structs later
        class MyPoint(ctypes.Structure):
            _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

        zig.register_struct("MyPoint", MyPoint)
        # This would re-bind any functions using MyPoint type
