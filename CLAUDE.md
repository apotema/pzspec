# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PZSpec is a Python DSL for testing Zig code via FFI. It compiles Zig libraries to shared objects and uses Python's `ctypes` to call exported functions, enabling expressive RSpec-style tests.

## Commands

```bash
# Install PZSpec (from project root)
pip install -e .

# Run tests (after installation, from any project directory)
pzspec
pzspec --quiet

# Run tests without installation (from PZSpec root)
python run_tests.py
python run_tests.py --quiet

# Run specific test file
python run_tests.py test_math.py
```

## Architecture

```
pzspec/
├── pzspec/              # Python package
│   ├── __init__.py      # Exports: ZigLibrary, describe, it, expect, assert_*, etc.
│   ├── dsl.py           # Test DSL: describe(), it(), expect() fluent assertions
│   ├── test_runner.py   # TestRunner, TestSuite, TestResult - executes tests
│   ├── zig_ffi.py       # ZigLibrary - loads .so/.dylib/.dll via ctypes
│   ├── builder.py       # ZigBuilder, PZSpecConfig - auto-builds Zig libraries
│   ├── cli.py           # CLI entry point (pzspec command)
│   ├── factory.py       # StructFactory - test data factories for ctypes structs
│   ├── pydust.py        # Ziggy-Pydust integration utilities
│   ├── zig/             # Zig helper modules
│   │   └── pzspec_exports.zig  # Comptime helpers for auto-export metadata
│   └── test_math.py     # Example test file
└── usage/               # Example projects demonstrating PZSpec usage
    ├── vector_math/     # 2D/3D vector math library example
    ├── auto_export_demo/ # Auto-discovery with metadata
    └── pydust_demo/     # Ziggy-Pydust integration example
```

## Key Patterns

**Test file structure** (in `pzspec/` directory, named `test_*.py`):
```python
from pzspec import ZigLibrary, describe, it, expect

zig = ZigLibrary()  # Auto-finds/builds library

with describe("Suite Name"):
    @it("should do something")
    def test_case():
        result = zig.get_function("func", [ctypes.c_int32], ctypes.c_int32)(42)
        expect(result).to_equal(84)
```

**FFI struct passing** - use `ctypes.Structure` and `ctypes.byref()`:
```python
class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

func = zig.get_function("vec2_add", [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], Vec2)
result = func(ctypes.byref(a), ctypes.byref(b))
```

**Zig exports** - use `export` keyword for C ABI:
```zig
export fn my_function(a: i32) i32 {
    return a * 2;
}
```

## Configuration

Optional `.pzspec` file in project root:
```json
{
  "library_name": "mylib",
  "source_file": "src/custom.zig",
  "optimize": "ReleaseSafe",
  "build_dir": "zig-out/lib",
  "build_flags": ["-fstack-protector"]
}
```

Without config, conventions apply:
- Source: `src/lib.zig` or first `.zig` in `src/`
- Library name: project directory name
- Output: `zig-out/lib/lib<name>.<ext>`

## Factory Framework

Create test data factories for ctypes structs with defaults, sequences, and traits:

```python
from pzspec import StructFactory, factory_field, sequence, trait

class Vec2Factory(StructFactory):
    struct_class = Vec2
    x = factory_field(default=0.0)
    y = factory_field(default=0.0)
    id = sequence(lambda n: n)  # Auto-incrementing

    @trait
    def unit_x(self):
        return {"x": 1.0, "y": 0.0}

# Usage
vec = Vec2Factory()              # defaults (0.0, 0.0)
vec = Vec2Factory(x=5.0)         # override x
vec = Vec2Factory.unit_x()       # trait preset
vecs = Vec2Factory.build_batch(5) # batch creation
```

## Type Mapping (Zig → ctypes)

| Zig | ctypes |
|-----|--------|
| `i32`, `i64` | `c_int32`, `c_int64` |
| `f32`, `f64` | `c_float`, `c_double` |
| `bool` | `c_bool` |
| `[*:0]const u8` | `c_char_p` |
| `[*]i32` | `POINTER(c_int32)` |
| `usize` | `c_size_t` |

## Common FFI Patterns

### Sentinel Values (Nullable Types)

When a numeric type needs to represent "no value" (like entity IDs where 0 is valid), use sentinel values:

**Zig side:**
```zig
const std = @import("std");

// Define sentinel as max value (can't be a valid entity index)
pub const NO_ENTITY: u32 = std.math.maxInt(u32);  // 0xFFFFFFFF

// Export for Python
export fn get_no_entity_sentinel() u32 {
    return NO_ENTITY;
}

// Use in functions that may not find an entity
export fn find_entity(name: [*:0]const u8) u32 {
    // ... search logic ...
    return if (found) entity.id else NO_ENTITY;
}
```

**Python side:**
```python
from pzspec import ZigLibrary, Sentinel, expect, NO_ENTITY
import ctypes

zig = ZigLibrary()

# Option 1: Use pre-defined sentinel
# NO_ENTITY is max u32 (0xFFFFFFFF)

# Option 2: Load sentinel from Zig
NO_ENTITY = Sentinel.from_zig_function(zig, "get_no_entity_sentinel", ctypes.c_uint32)

# Use in tests
entity_id = zig.get_function("find_entity", [ctypes.c_char_p], ctypes.c_uint32)(b"player")

# Check validity
if NO_ENTITY.is_valid(entity_id):
    process_entity(entity_id)

# Use expect() assertions
expect(entity_id).to_not_be_sentinel(NO_ENTITY)  # Assert found
expect(entity_id).to_be_valid(NO_ENTITY)         # Alias for above
expect(missing_id).to_be_sentinel(NO_ENTITY)     # Assert not found
```

### Optional Results Pattern

For functions that may fail or return nothing:

**Zig side:**
```zig
pub const Result = extern struct {
    value: i32,
    success: bool,
};

export fn try_parse(input: [*:0]const u8) Result {
    // ... parsing logic ...
    return if (valid)
        Result{ .value = parsed, .success = true }
    else
        Result{ .value = 0, .success = false };
}
```

**Python side:**
```python
class Result(ctypes.Structure):
    _fields_ = [("value", ctypes.c_int32), ("success", ctypes.c_bool)]

result = zig.get_function("try_parse", [ctypes.c_char_p], Result)(b"42")
expect(result.success).to_be_true()
expect(result.value).to_equal(42)
```

### Error Code Pattern

For functions that can fail with specific errors:

**Zig side:**
```zig
pub const ErrorCode = enum(i32) {
    Success = 0,
    NotFound = -1,
    InvalidInput = -2,
    OutOfMemory = -3,
};

export fn process_data(data: [*]const u8, len: usize) i32 {
    // ... processing ...
    return @intFromEnum(ErrorCode.Success);
}
```

**Python side:**
```python
class ErrorCode:
    SUCCESS = 0
    NOT_FOUND = -1
    INVALID_INPUT = -2
    OUT_OF_MEMORY = -3

result = zig.get_function("process_data", [ctypes.c_char_p, ctypes.c_size_t], ctypes.c_int32)(data, len(data))
expect(result).to_equal(ErrorCode.SUCCESS)
```

## Auto-Discovery with Metadata

When Zig libraries export `__pzspec_metadata`, Python can auto-discover function signatures:

**Zig side (lib.zig):**
```zig
// Export metadata JSON with function signatures
const metadata =
    \\{"functions":[
    \\{"name":"add","params":["i32","i32"],"return":"i32"},
    \\{"name":"multiply","params":["i32","i32"],"return":"i32"}
    \\]}
;

export fn __pzspec_metadata() [*:0]const u8 {
    return metadata;
}
```

**Python side:**
```python
from pzspec import ZigLibrary

# Auto-discovers functions from metadata
zig = ZigLibrary()

# Call directly as attributes (types inferred from metadata)
result = zig.add(10, 20)  # No get_function() needed!
result = zig.multiply(6, 7)

# Check what was discovered
print(zig.get_discovered_functions())  # ['add', 'multiply']
```

## Ziggy-Pydust Integration

For zero-boilerplate FFI, use [Ziggy-Pydust](https://github.com/spiraldb/ziggy-pydust):

**Zig side (no export wrappers needed!):**
```zig
const py = @import("pydust");

pub fn add(a: i64, b: i64) i64 {
    return a + b;
}

pub const Point = struct {
    x: f64,
    y: f64,

    pub fn magnitude(self: Point) f64 {
        return @sqrt(self.x * self.x + self.y * self.y);
    }
};

comptime {
    py.rootmodule(@This());  // Auto-export everything
}
```

**Python side:**
```python
import mathlib  # Direct import, no ZigLibrary needed!
from pzspec import describe, it, expect

with describe("Math"):
    @it("should add")
    def test_add():
        expect(mathlib.add(10, 20)).to_equal(30)

    @it("should calculate magnitude")
    def test_magnitude():
        p = mathlib.Point(x=3.0, y=4.0)
        expect(p.magnitude()).to_equal(5.0)
```

**PZSpec utilities for Pydust:**
```python
from pzspec import try_import_pydust_module, is_pydust_available

# Optional module loading
mathlib = try_import_pydust_module("mathlib")
if mathlib:
    result = mathlib.add(1, 2)

# Check if Pydust is installed
if is_pydust_available():
    print("Pydust available")
```
