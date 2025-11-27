"""
Factories for Vec2 and Vec3 test data.
"""

import ctypes
import random

from pzspec import StructFactory, factory_field, trait


class Vec2(ctypes.Structure):
    """2D Vector structure."""
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]


class Vec3(ctypes.Structure):
    """3D Vector structure."""
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float), ("z", ctypes.c_float)]


class Vec2Factory(StructFactory):
    """Factory for creating Vec2 test data."""
    struct_class = Vec2

    x = factory_field(default=0.0)
    y = factory_field(default=0.0)

    @trait
    def unit_x(self):
        """Unit vector along X axis."""
        return {"x": 1.0, "y": 0.0}

    @trait
    def unit_y(self):
        """Unit vector along Y axis."""
        return {"x": 0.0, "y": 1.0}

    @trait
    def random(self):
        """Random vector with values between -10 and 10."""
        return {"x": random.uniform(-10, 10), "y": random.uniform(-10, 10)}

    @trait
    def pythagorean(self):
        """Classic 3-4-5 Pythagorean triple."""
        return {"x": 3.0, "y": 4.0}


class Vec3Factory(StructFactory):
    """Factory for creating Vec3 test data."""
    struct_class = Vec3

    x = factory_field(default=0.0)
    y = factory_field(default=0.0)
    z = factory_field(default=0.0)

    @trait
    def unit_x(self):
        """Unit vector along X axis."""
        return {"x": 1.0, "y": 0.0, "z": 0.0}

    @trait
    def unit_y(self):
        """Unit vector along Y axis."""
        return {"x": 0.0, "y": 1.0, "z": 0.0}

    @trait
    def unit_z(self):
        """Unit vector along Z axis."""
        return {"x": 0.0, "y": 0.0, "z": 1.0}

    @trait
    def random(self):
        """Random vector with values between -10 and 10."""
        return {
            "x": random.uniform(-10, 10),
            "y": random.uniform(-10, 10),
            "z": random.uniform(-10, 10),
        }
