"""
PZSpec tests for Pydust-based math library.

This demonstrates testing Zig code exposed via Ziggy-Pydust.
Note: No ctypes, no manual type declarations, no C ABI wrappers needed!
The Zig code is directly callable as a Python module.
"""

import mathlib
from pzspec import describe, it, expect


with describe("Pydust Math Functions"):

    @it("should add two integers")
    def test_add():
        # Direct function call - no get_function, no ctypes!
        result = mathlib.add(10, 20)
        expect(result).to_equal(30)

        # Multiple test cases
        expect(mathlib.add(0, 0)).to_equal(0)
        expect(mathlib.add(-5, 5)).to_equal(0)
        expect(mathlib.add(100, 200)).to_equal(300)

    @it("should multiply two integers")
    def test_multiply():
        result = mathlib.multiply(6, 7)
        expect(result).to_equal(42)

    @it("should calculate factorial")
    def test_factorial():
        expect(mathlib.factorial(0)).to_equal(1)
        expect(mathlib.factorial(1)).to_equal(1)
        expect(mathlib.factorial(5)).to_equal(120)
        expect(mathlib.factorial(10)).to_equal(3628800)

    @it("should check if number is prime")
    def test_is_prime():
        expect(mathlib.is_prime(2)).to_be_true()
        expect(mathlib.is_prime(3)).to_be_true()
        expect(mathlib.is_prime(4)).to_be_false()
        expect(mathlib.is_prime(17)).to_be_true()
        expect(mathlib.is_prime(18)).to_be_false()

    @it("should calculate fibonacci numbers")
    def test_fibonacci():
        expect(mathlib.fibonacci(0)).to_equal(0)
        expect(mathlib.fibonacci(1)).to_equal(1)
        expect(mathlib.fibonacci(10)).to_equal(55)
        expect(mathlib.fibonacci(20)).to_equal(6765)
