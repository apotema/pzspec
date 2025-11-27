# Factory Demo - PZSpec Factory Framework with Zig Comptime Generics

This example demonstrates how to use PZSpec's factory framework to test Zig code that uses comptime generics.

## The Pattern

Zig's comptime generics allow creating parameterized types at compile time:

```zig
pub fn ButcheryFactory(comptime L: RoomLevel) type {
    return extern struct {
        pub const level: RoomLevel = L;
        pub const base_capacity: u32 = L.capacity();

        id: u32,
        workers: u32,
        // ...
    };
}

// Concrete instantiations
pub const SmallButchery = ButcheryFactory(.small);
pub const MediumButchery = ButcheryFactory(.medium);
pub const LargeButchery = ButcheryFactory(.large);
```

Since comptime generics can't be directly exported via FFI, we export concrete instantiations and create corresponding Python factories for each.

## Python Factories

```python
class SmallButcheryFactory(StructFactory):
    struct_class = SmallButchery

    id = sequence(lambda n: n)
    workers = factory_field(default=0)
    efficiency = factory_field(default=1.0)

    @trait
    def active(self):
        return {"workers": 2, "is_active": True}

    @trait
    def efficient(self):
        return {"efficiency": 1.5, "workers": 3}

# Usage
b = SmallButcheryFactory()           # defaults
b = SmallButcheryFactory.active()    # trait
b = SmallButcheryFactory(workers=5)  # override
```

## Running Tests

```bash
cd usage/factory_demo
pzspec
```

## Key Concepts

1. **Comptime to Runtime**: Zig comptime generics become concrete types for FFI
2. **Matching Structures**: Python ctypes.Structure must match Zig extern struct layout
3. **Factory per Type**: Each concrete Zig type gets its own Python factory
4. **Traits for Scenarios**: Use traits to create common test scenarios (active, full, efficient)
5. **Sequences for IDs**: Auto-incrementing sequences ensure unique IDs

## Project Structure

```
factory_demo/
├── src/
│   └── lib.zig           # Zig code with ButcheryFactory comptime generic
├── pzspec/
│   └── test_butchery.py  # Tests using Python factories
├── .pzspec               # Configuration
└── README.md
```
