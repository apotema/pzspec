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
│   └── test_math.py     # Example test file
└── usage/               # Example projects demonstrating PZSpec usage
    └── vector_math/     # 2D/3D vector math library example
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
