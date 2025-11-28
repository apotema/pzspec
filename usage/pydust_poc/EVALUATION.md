# Ziggy-Pydust Evaluation Report

This document provides a comprehensive evaluation of using Ziggy-Pydust as an alternative to PZSpec's current ctypes-based FFI approach.

## Executive Summary

**Recommendation**: Add Pydust as an **opt-in backend** alongside the current ctypes approach.

| Criterion | Score (1-5) | Notes |
|-----------|-------------|-------|
| Developer Experience | ⭐⭐⭐⭐⭐ | Eliminates all boilerplate |
| Performance | ⭐⭐⭐⭐⭐ | Native C extension (no FFI overhead) |
| Build Complexity | ⭐⭐ | Requires Poetry/maturin setup |
| Dependencies | ⭐⭐ | Adds several dependencies |
| Maintenance | ⭐⭐⭐⭐ | Active project (65 releases) |
| Integration Risk | ⭐⭐⭐ | Moderate architecture changes |

## Task 1: Proof-of-Concept Analysis

### Current PZSpec Approach (ctypes)

**Files required:**
1. `src/vector.zig` - Zig library with explicit `export fn` wrappers
2. `pzspec/factories/vectors.py` - ctypes.Structure definitions
3. `pzspec/test_vectors.py` - Tests with manual FFI setup

**Zig code characteristics:**
- Must use `extern struct` for C ABI compatibility
- Must create `export fn` wrapper for each function
- Pointer arguments require explicit pointer types

**Python code characteristics:**
- Must define ctypes.Structure for each Zig struct
- Must use `zig.get_function()` with explicit type annotations
- Must handle pointers with `ctypes.byref()`

**Lines of boilerplate per function:**
- Zig: ~3-5 lines (export fn wrapper)
- Python: ~3 lines (get_function call)
- Total: ~6-8 lines per exposed function

### Pydust Approach

**Files required:**
1. `src/vector_pydust.zig` - Standard Zig code with comptime registration

**Zig code characteristics:**
- Regular Zig structs (no `extern struct`)
- Standard Zig methods (no `export fn`)
- Named arguments via anonymous struct parameters

**Python code characteristics:**
- Direct import (`import vector_math`)
- Direct method calls (`a.add(b)`)
- No type annotations needed

**Lines of boilerplate per function:**
- Zig: 0 (Pydust generates FFI at comptime)
- Python: 0 (direct module import)
- Total: 0 lines per exposed function

### Code Comparison

#### Zig: Adding Two Vectors

**ctypes (current):**
```zig
// Must be extern for C ABI
pub const Vec2 = extern struct {
    x: f32,
    y: f32,
};

// Must create export wrapper
export fn vec2_add(a: *const Vec2, b: *const Vec2) Vec2 {
    return Vec2{ .x = a.x + b.x, .y = a.y + b.y };
}
```

**Pydust:**
```zig
const py = @import("pydust");

// Regular Zig struct
pub const Vec2 = struct {
    x: f32,
    y: f32,

    // Regular Zig method
    pub fn add(self: Vec2, other: Vec2) Vec2 {
        return Vec2{ .x = self.x + other.x, .y = self.y + other.y };
    }
};

comptime { py.rootmodule(@This()); }
```

#### Python: Using the Vector

**ctypes (current):**
```python
import ctypes
from pzspec import ZigLibrary

class Vec2(ctypes.Structure):
    _fields_ = [("x", ctypes.c_float), ("y", ctypes.c_float)]

zig = ZigLibrary()

def vec2_add(a, b):
    func = zig.get_function("vec2_add", 
        [ctypes.POINTER(Vec2), ctypes.POINTER(Vec2)], Vec2)
    return func(ctypes.byref(a), ctypes.byref(b))

# Usage
a = Vec2(x=1.0, y=2.0)
b = Vec2(x=3.0, y=4.0)
result = vec2_add(a, b)
```

**Pydust:**
```python
import vector_math

# Usage - that's it!
a = vector_math.Vec2(x=1.0, y=2.0)
b = vector_math.Vec2(x=3.0, y=4.0)
result = a.add(b)
```

## Task 2: Performance Analysis

### Theoretical Performance

| Metric | ctypes | Pydust | Difference |
|--------|--------|--------|------------|
| Call Overhead | ~100-500ns | ~10-50ns | 5-10x faster |
| Type Marshaling | Runtime | Compile-time | No runtime cost |
| Struct Access | Copy via ctypes | Direct memory | No copy overhead |
| Array Handling | Manual pointer | Buffer protocol | Zero-copy possible |

### Expected Benchmark Results

Based on similar FFI comparisons (cffi vs ctypes vs Cython):

1. **Empty function call**: Pydust ~10x faster than ctypes
2. **Struct passing**: Pydust ~5x faster (no copy overhead)
3. **Array operations**: Pydust ~20x faster with buffer protocol
4. **Complex operations**: Similar (computation dominates)

### Benchmark Recommendation

Create benchmarks for:
```python
# 1. Call overhead
for _ in range(1000000):
    func()

# 2. Struct creation
for _ in range(100000):
    Vec2(x=1.0, y=2.0)

# 3. Method chains
for _ in range(100000):
    a.add(b).scale(2.0).normalize()

# 4. Array operations
arr = [1.0] * 10000
result = process_array(arr)
```

## Task 3: Integration Complexity

### Changes Required for Opt-In Pydust Support

#### 1. Configuration Extension

**`.pzspec` additions:**
```json
{
  "backend": "pydust",
  "pydust_module": "vector_math",
  "pydust_build": {
    "tool": "maturin",
    "features": ["pyo3/extension-module"]
  }
}
```

#### 2. New Loader Class

```python
# pzspec/pydust_loader.py
class PydustModule:
    """Loader for Pydust-compiled Zig modules."""
    
    def __init__(self, module_name: str):
        self.module = importlib.import_module(module_name)
    
    def get_function(self, name: str):
        return getattr(self.module, name)
    
    def get_type(self, name: str):
        return getattr(self.module, name)
```

#### 3. Unified Interface

```python
# pzspec/zig_interface.py
class ZigInterface:
    """Unified interface for ctypes and Pydust backends."""
    
    @staticmethod
    def load(config: PZSpecConfig):
        if config.backend == "pydust":
            return PydustModule(config.pydust_module)
        else:
            return ZigLibrary(auto_build_lib=True)
```

#### 4. DSL Compatibility

The PZSpec DSL (`describe`, `it`, `expect`) is **fully compatible** with Pydust:

```python
from pzspec import describe, it, expect
import vector_math  # Pydust module

with describe("Vec2"):
    @it("should add vectors")
    def test():
        result = vector_math.Vec2(1, 2).add(vector_math.Vec2(3, 4))
        expect(result.x).to_equal(4)
```

### Estimated Implementation Effort

| Component | Effort | Risk |
|-----------|--------|------|
| Configuration extension | 2 hours | Low |
| Pydust loader class | 4 hours | Low |
| Unified interface | 4 hours | Medium |
| Documentation | 4 hours | Low |
| Testing | 8 hours | Medium |
| **Total** | **22 hours** | **Medium** |

## Task 4: Coexistence Assessment

### Opt-In Strategy (Recommended)

**Approach**: Keep ctypes as default, add Pydust as optional backend.

**Benefits:**
- Zero impact on existing projects
- Gradual adoption possible
- No dependency increases for ctypes users
- Projects can choose based on needs

**Implementation:**

```python
# Usage remains simple for ctypes (default)
from pzspec import ZigLibrary
zig = ZigLibrary()

# Pydust users explicitly opt-in
from pzspec import PydustModule  # or import module directly
vector = PydustModule("vector_math")
```

### Configuration-Based Selection

**.pzspec file:**
```json
{
  "backend": "ctypes"  // default, no dependencies
}
```

or:

```json
{
  "backend": "pydust",
  "pydust_module": "vector_math"
}
```

### Dependency Management

**ctypes users (current behavior):**
- No additional dependencies
- Works with Python 3.8+ stdlib only

**Pydust users (opt-in):**
- Must install: `pip install ziggy-pydust maturin`
- Build requires: Poetry or pip with build backend

### Test Infrastructure

PZSpec test files can mix approaches:

```python
# Some tests use ctypes
from pzspec import ZigLibrary
zig = ZigLibrary()

# Other tests use Pydust
import vector_math_pydust as vm

with describe("Mixed Backend Testing"):
    @it("should work with ctypes")
    def test_ctypes():
        result = zig.add(1, 2)
        expect(result).to_equal(3)
    
    @it("should work with pydust")
    def test_pydust():
        result = vm.add(a=1, b=2)
        expect(result).to_equal(3)
```

## Conclusion

### When to Use Pydust

✅ **Recommended for:**
- Projects with many Zig functions to expose
- Performance-critical applications
- Projects already using Poetry/maturin
- Teams familiar with Python C extensions
- Projects needing NumPy/buffer protocol integration

❌ **Not recommended for:**
- Simple projects with few Zig functions
- Projects requiring zero dependencies
- Quick prototyping/experimentation
- Projects using `zig build-lib` exclusively

### Implementation Roadmap

1. **Phase 1**: Add opt-in Pydust support
   - Create `PydustModule` loader
   - Extend `.pzspec` configuration
   - Document usage

2. **Phase 2**: Improve ergonomics
   - Auto-detection of Pydust modules
   - Unified factory support
   - Enhanced error messages

3. **Phase 3**: Performance optimization
   - Buffer protocol integration
   - Zero-copy array passing
   - Benchmark suite

### Final Recommendation

**Add Pydust as an opt-in alternative backend** while keeping ctypes as the default. This provides:

1. **Zero-cost abstraction**: No impact on existing projects
2. **Progressive enhancement**: Projects can adopt when ready
3. **Best of both worlds**: Simple ctypes for quick tests, powerful Pydust for production
4. **Maintained simplicity**: PZSpec's core value proposition (zero config) remains intact

The PZSpec DSL works identically with both backends, so the testing experience remains consistent regardless of which backend is used.
