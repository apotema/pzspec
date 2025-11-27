"""
Test suite for Vector Math library using PZSpec DSL.

This demonstrates how to test a real Zig project using the Python DSL.
"""

import sys
import os
from pathlib import Path

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from the framework package
from pzspec.zig_ffi import ZigLibrary
from pzspec.dsl import describe, it, expect, assert_almost_equal
import ctypes

# Import factories from the factories folder
from factories import Vec2Factory, Vec3Factory
from factories.vectors import Vec2, Vec3


# Load the Zig library (auto-builds if needed)
zig = ZigLibrary()


# Helper functions for working with Vec2
def vec2_new(x, y):
    """Create a Vec2 struct."""
    func = zig.get_function("vec2_new", [ctypes.c_float, ctypes.c_float], Vec2)
    return func(x, y)


def vec2_add(a, b):
    """Add two Vec2 vectors."""
    func = zig.get_function("vec2_add", [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], Vec2)
    return func(ctypes.byref(a), ctypes.byref(b))


def vec2_subtract(a, b):
    """Subtract two Vec2 vectors."""
    func = zig.get_function("vec2_subtract", [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], Vec2)
    return func(ctypes.byref(a), ctypes.byref(b))


def vec2_scale(v, scalar):
    """Scale a Vec2 by a scalar."""
    func = zig.get_function("vec2_scale", [ctypes.POINTER(Vec2), ctypes.c_float], Vec2)
    return func(ctypes.byref(v), scalar)


def vec2_dot(a, b):
    """Calculate dot product of two Vec2 vectors."""
    func = zig.get_function("vec2_dot", [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], ctypes.c_float)
    return func(ctypes.byref(a), ctypes.byref(b))


def vec2_magnitude(v):
    """Calculate magnitude of a Vec2."""
    func = zig.get_function("vec2_magnitude", [ctypes.POINTER(Vec2)], ctypes.c_float)
    return func(ctypes.byref(v))


def vec2_normalize(v):
    """Normalize a Vec2 to unit length."""
    func = zig.get_function("vec2_normalize", [ctypes.POINTER(Vec2)], Vec2)
    return func(ctypes.byref(v))


def vec2_distance(a, b):
    """Calculate distance between two Vec2 vectors."""
    func = zig.get_function("vec2_distance", [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], ctypes.c_float)
    return func(ctypes.byref(a), ctypes.byref(b))


# Helper functions for working with Vec3
def vec3_new(x, y, z):
    """Create a Vec3 struct."""
    func = zig.get_function("vec3_new", [ctypes.c_float, ctypes.c_float, ctypes.c_float], Vec3)
    return func(x, y, z)


def vec3_add(a, b):
    """Add two Vec3 vectors."""
    func = zig.get_function("vec3_add", [ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)], Vec3)
    return func(ctypes.byref(a), ctypes.byref(b))


def vec3_cross(a, b):
    """Calculate cross product of two Vec3 vectors."""
    func = zig.get_function("vec3_cross", [ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)], Vec3)
    return func(ctypes.byref(a), ctypes.byref(b))


def vec3_dot(a, b):
    """Calculate dot product of two Vec3 vectors."""
    func = zig.get_function("vec3_dot", [ctypes.POINTER(Vec3), ctypes.POINTER(Vec3)], ctypes.c_float)
    return func(ctypes.byref(a), ctypes.byref(b))


def vec3_magnitude(v):
    """Calculate magnitude of a Vec3."""
    func = zig.get_function("vec3_magnitude", [ctypes.POINTER(Vec3)], ctypes.c_float)
    return func(ctypes.byref(v))


# Test suites using PZSpec DSL
with describe("Vec2 - Basic Operations"):
    
    @it("should create a new 2D vector")
    def test_vec2_new():
        v = vec2_new(3.0, 4.0)
        expect(v.x).to_equal(3.0)
        expect(v.y).to_equal(4.0)
    
    @it("should add two 2D vectors")
    def test_vec2_add():
        a = vec2_new(1.0, 2.0)
        b = vec2_new(3.0, 4.0)
        result = vec2_add(a, b)
        expect(result.x).to_equal(4.0)
        expect(result.y).to_equal(6.0)
    
    @it("should subtract two 2D vectors")
    def test_vec2_subtract():
        a = vec2_new(5.0, 7.0)
        b = vec2_new(2.0, 3.0)
        result = vec2_subtract(a, b)
        expect(result.x).to_equal(3.0)
        expect(result.y).to_equal(4.0)
    
    @it("should scale a 2D vector by a scalar")
    def test_vec2_scale():
        v = vec2_new(2.0, 3.0)
        result = vec2_scale(v, 2.5)
        expect(result.x).to_equal(5.0)
        expect(result.y).to_equal(7.5)


with describe("Vec2 - Advanced Operations"):
    
    @it("should calculate dot product of two 2D vectors")
    def test_vec2_dot():
        a = vec2_new(1.0, 2.0)
        b = vec2_new(3.0, 4.0)
        result = vec2_dot(a, b)
        expect(result).to_equal(11.0)  # 1*3 + 2*4 = 11
    
    @it("should calculate magnitude of a 2D vector")
    def test_vec2_magnitude():
        v = vec2_new(3.0, 4.0)
        result = vec2_magnitude(v)
        expect(result).to_equal(5.0)  # sqrt(3^2 + 4^2) = 5
    
    @it("should normalize a 2D vector to unit length")
    def test_vec2_normalize():
        v = vec2_new(3.0, 4.0)
        result = vec2_normalize(v)
        mag = vec2_magnitude(result)
        assert_almost_equal(mag, 1.0, delta=0.001)
        assert_almost_equal(result.x, 0.6, delta=0.001)
        assert_almost_equal(result.y, 0.8, delta=0.001)
    
    @it("should handle normalization of zero vector")
    def test_vec2_normalize_zero():
        v = vec2_new(0.0, 0.0)
        result = vec2_normalize(v)
        expect(result.x).to_equal(0.0)
        expect(result.y).to_equal(0.0)
    
    @it("should calculate distance between two 2D vectors")
    def test_vec2_distance():
        a = vec2_new(0.0, 0.0)
        b = vec2_new(3.0, 4.0)
        result = vec2_distance(a, b)
        expect(result).to_equal(5.0)  # sqrt(3^2 + 4^2) = 5


with describe("Vec3 - Basic Operations"):
    
    @it("should create a new 3D vector")
    def test_vec3_new():
        v = vec3_new(1.0, 2.0, 3.0)
        expect(v.x).to_equal(1.0)
        expect(v.y).to_equal(2.0)
        expect(v.z).to_equal(3.0)
    
    @it("should add two 3D vectors")
    def test_vec3_add():
        a = vec3_new(1.0, 2.0, 3.0)
        b = vec3_new(4.0, 5.0, 6.0)
        result = vec3_add(a, b)
        expect(result.x).to_equal(5.0)
        expect(result.y).to_equal(7.0)
        expect(result.z).to_equal(9.0)


with describe("Vec3 - Advanced Operations"):
    
    @it("should calculate dot product of two 3D vectors")
    def test_vec3_dot():
        a = vec3_new(1.0, 2.0, 3.0)
        b = vec3_new(4.0, 5.0, 6.0)
        result = vec3_dot(a, b)
        expect(result).to_equal(32.0)  # 1*4 + 2*5 + 3*6 = 32
    
    @it("should calculate cross product of two 3D vectors")
    def test_vec3_cross():
        a = vec3_new(1.0, 0.0, 0.0)  # Unit vector along x-axis
        b = vec3_new(0.0, 1.0, 0.0)  # Unit vector along y-axis
        result = vec3_cross(a, b)
        expect(result.x).to_equal(0.0)
        expect(result.y).to_equal(0.0)
        expect(result.z).to_equal(1.0)  # Should be unit vector along z-axis
    
    @it("should calculate magnitude of a 3D vector")
    def test_vec3_magnitude():
        v = vec3_new(2.0, 3.0, 6.0)
        result = vec3_magnitude(v)
        expect(result).to_equal(7.0)  # sqrt(2^2 + 3^2 + 6^2) = sqrt(49) = 7


with describe("Vec3 - Cross Product Properties"):
    
    @it("should satisfy anti-commutativity: a × b = -(b × a)")
    def test_vec3_cross_anticommutative():
        a = vec3_new(1.0, 2.0, 3.0)
        b = vec3_new(4.0, 5.0, 6.0)
        cross_ab = vec3_cross(a, b)
        cross_ba = vec3_cross(b, a)
        expect(cross_ab.x).to_equal(-cross_ba.x)
        expect(cross_ab.y).to_equal(-cross_ba.y)
        expect(cross_ab.z).to_equal(-cross_ba.z)
    
    @it("should produce orthogonal vector (a · (a × b) = 0)")
    def test_vec3_cross_orthogonal():
        a = vec3_new(1.0, 2.0, 3.0)
        b = vec3_new(4.0, 5.0, 6.0)
        cross = vec3_cross(a, b)
        dot_product = vec3_dot(a, cross)
        assert_almost_equal(dot_product, 0.0, delta=0.001)


# Factory-based tests demonstrating the new factory framework
with describe("Factory - Vec2 Creation"):

    @it("should create zero vector with defaults")
    def test_factory_defaults():
        v = Vec2Factory()
        expect(v.x).to_equal(0.0)
        expect(v.y).to_equal(0.0)

    @it("should create vector with overrides")
    def test_factory_overrides():
        v = Vec2Factory(x=5.0, y=3.0)
        expect(v.x).to_equal(5.0)
        expect(v.y).to_equal(3.0)

    @it("should create unit_x vector using trait")
    def test_factory_unit_x_trait():
        v = Vec2Factory.unit_x()
        expect(v.x).to_equal(1.0)
        expect(v.y).to_equal(0.0)

    @it("should create pythagorean vector using trait")
    def test_factory_pythagorean_trait():
        v = Vec2Factory.pythagorean()
        mag = vec2_magnitude(v)
        expect(mag).to_equal(5.0)

    @it("should create batch of vectors")
    def test_factory_batch():
        vecs = Vec2Factory.build_batch(3, x=1.0)
        expect(len(vecs)).to_equal(3)
        for v in vecs:
            expect(v.x).to_equal(1.0)
            expect(v.y).to_equal(0.0)


with describe("Factory - Vec3 Creation"):

    @it("should create unit vectors using traits")
    def test_factory_unit_vectors():
        # Cross product of unit_x and unit_y should be unit_z
        x = Vec3Factory.unit_x()
        y = Vec3Factory.unit_y()
        result = vec3_cross(x, y)
        expect(result.x).to_equal(0.0)
        expect(result.y).to_equal(0.0)
        expect(result.z).to_equal(1.0)

    @it("should allow trait with overrides")
    def test_factory_trait_with_override():
        v = Vec3Factory.unit_x(z=5.0)
        expect(v.x).to_equal(1.0)
        expect(v.y).to_equal(0.0)
        expect(v.z).to_equal(5.0)

