# Pydust Demo

This example demonstrates using [Ziggy-Pydust](https://github.com/spiraldb/ziggy-pydust) with PZSpec for testing Zig code.

## What is Ziggy-Pydust?

Ziggy-Pydust is a framework for writing Python extension modules in Zig. Unlike the traditional ctypes/FFI approach used by PZSpec, Pydust:

- **Eliminates manual C ABI wrappers** - No `export fn` needed
- **Automatic type conversion** - Python objects ↔ Zig types
- **Native Python modules** - Direct import, no ctypes

## Comparison

### Traditional PZSpec (ctypes)

```python
import ctypes
from pzspec import ZigLibrary

zig = ZigLibrary()

# Manual type declaration for each function
add = zig.get_function("add", [ctypes.c_int64, ctypes.c_int64], ctypes.c_int64)
result = add(10, 20)
```

```zig
// Need explicit export wrappers with C calling convention
export fn add(a: i64, b: i64) i64 {
    return a + b;
}
```

### With Pydust

```python
import mathlib  # Direct import!

# No type declarations needed
result = mathlib.add(10, 20)
```

```zig
// No export wrappers - just regular Zig code with struct args
pub fn add(args: struct { a: i64, b: i64 }) i64 {
    return args.a + args.b;
}

comptime {
    py.rootmodule(@This());  // One line to export everything
}
```

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install ziggy-pydust==0.26.0
   pip install -e ../..  # Install pzspec from parent
   ```

3. Build the Zig module:
   ```bash
   python3 build.py
   ```

4. Run tests:
   ```bash
   pzspec
   ```

## Requirements

- Python 3.11+
- Zig 0.15.1 (must be available in PATH - use `zvm use 0.15.1` if using zvm)
- ziggy-pydust 0.26.0

## Configuration

The `pyproject.toml` contains Pydust configuration:

```toml
[tool.pydust]
zig_exe = "~/.zvm/bin/zig"  # Optional: path to Zig executable

[[tool.pydust.ext_module]]
name = "mathlib"
root = "src/mathlib.zig"
limited_api = true
```

## When to Use Pydust vs Traditional FFI

**Use Pydust when:**
- Building Python packages with Zig backends
- You want the cleanest Python API possible
- You need automatic type conversion

**Use Traditional FFI when:**
- Testing existing Zig libraries without modification
- You need fine-grained control over memory layout
- Working with existing C ABI conventions

## Files

- `src/mathlib.zig` - Zig module using Pydust
- `test_pydust_mathlib.py` - PZSpec tests
- `pyproject.toml` - Pydust configuration
- `build.py` - Pydust build script
