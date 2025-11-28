// PZSpec Auto-Export Helper
// ==========================
// This module provides comptime utilities to automatically export C-compatible
// functions from Zig modules for FFI testing with PZSpec.
//
// Usage:
//   const pzspec = @import("pzspec_exports.zig");
//
//   comptime {
//       pzspec.exportModule(@import("my_module.zig"), .{});
//   }
//
// This will automatically create `export fn` wrappers for all public functions
// that have C-compatible signatures.

const std = @import("std");
const builtin = @import("builtin");

/// Configuration options for auto-export
pub const ExportOptions = struct {
    /// Prefix to add to exported function names (e.g., "pzspec_")
    prefix: []const u8 = "",

    /// Suffix to add to exported function names
    suffix: []const u8 = "",

    /// If true, also export struct type information as metadata
    export_metadata: bool = true,

    /// If true, skip functions that take pointer-to-struct parameters
    /// (these often need manual wrappers that dereference)
    skip_struct_pointers: bool = false,
};

/// Type categories for metadata generation
pub const TypeCategory = enum(u8) {
    void = 0,
    bool_ = 1,
    int_signed = 2,
    int_unsigned = 3,
    float = 4,
    pointer = 5,
    struct_ = 6,
    array = 7,
    optional = 8,
    c_string = 9,
    unknown = 255,
};

/// Metadata for a single parameter or return type
pub const TypeMeta = extern struct {
    category: TypeCategory,
    size_bits: u16,
    is_const: bool,
    pointee_category: TypeCategory, // For pointers
    _padding: [2]u8 = .{ 0, 0 },
};

/// Metadata for an exported function
pub const FunctionMeta = extern struct {
    name_ptr: [*:0]const u8,
    param_count: u8,
    return_type: TypeMeta,
    // Followed by param_types array (accessed via getFunctionParams)
};

/// Check if a type is compatible with C ABI for FFI
pub fn isCAbiCompatible(comptime T: type) bool {
    const info = @typeInfo(T);
    return switch (info) {
        .void => true,
        .bool => true,
        .int => true,
        .float => true,
        .pointer => |ptr| blk: {
            // C-compatible pointers
            if (ptr.size == .C or ptr.size == .One or ptr.size == .Many) {
                // Check if pointee is C-compatible (or is u8 for strings)
                if (ptr.child == u8) break :blk true;
                break :blk isCAbiCompatibleType(ptr.child);
            }
            break :blk false;
        },
        .optional => |opt| blk: {
            // Optional pointers are C-compatible (nullable)
            const child_info = @typeInfo(opt.child);
            break :blk child_info == .pointer;
        },
        .@"struct" => |s| s.layout == .@"extern",
        .@"enum" => |e| e.tag_type != null, // Must have explicit backing type
        .array => false, // Arrays as values are not C-compatible
        else => false,
    };
}

/// Check if a type is C-compatible (for struct fields and pointees)
fn isCAbiCompatibleType(comptime T: type) bool {
    const info = @typeInfo(T);
    return switch (info) {
        .void => true,
        .bool => true,
        .int => true,
        .float => true,
        .@"struct" => |s| s.layout == .@"extern",
        .@"enum" => |e| e.tag_type != null,
        .pointer => true, // Nested pointers are ok
        else => false,
    };
}

/// Check if a function type is fully C ABI compatible
pub fn isFunctionCAbiCompatible(comptime Fn: type) bool {
    const info = @typeInfo(Fn);
    if (info != .@"fn") return false;

    const func = info.@"fn";

    // Check calling convention
    if (func.calling_convention != .auto and
        func.calling_convention != .c)
    {
        return false;
    }

    // Check return type
    if (func.return_type) |ret| {
        if (!isCAbiCompatible(ret)) return false;
    }

    // Check all parameters
    for (func.params) |param| {
        if (param.type) |ptype| {
            if (!isCAbiCompatible(ptype)) return false;
        } else {
            return false; // Generic parameter
        }
    }

    return true;
}

/// Get type metadata for serialization
pub fn getTypeMeta(comptime T: type) TypeMeta {
    const info = @typeInfo(T);
    return switch (info) {
        .void => .{
            .category = .void,
            .size_bits = 0,
            .is_const = false,
            .pointee_category = .unknown,
        },
        .bool => .{
            .category = .bool_,
            .size_bits = 8,
            .is_const = false,
            .pointee_category = .unknown,
        },
        .int => |i| .{
            .category = if (i.signedness == .signed) .int_signed else .int_unsigned,
            .size_bits = i.bits,
            .is_const = false,
            .pointee_category = .unknown,
        },
        .float => |f| .{
            .category = .float,
            .size_bits = f.bits,
            .is_const = false,
            .pointee_category = .unknown,
        },
        .pointer => |ptr| blk: {
            // Check for null-terminated string
            if (ptr.child == u8 and ptr.sentinel != null) {
                break :blk .{
                    .category = .c_string,
                    .size_bits = @bitSizeOf(*u8),
                    .is_const = ptr.is_const,
                    .pointee_category = .int_unsigned,
                };
            }
            break :blk .{
                .category = .pointer,
                .size_bits = @bitSizeOf(*anyopaque),
                .is_const = ptr.is_const,
                .pointee_category = getPointeeCategory(ptr.child),
            };
        },
        .@"struct" => .{
            .category = .struct_,
            .size_bits = @bitSizeOf(T),
            .is_const = false,
            .pointee_category = .unknown,
        },
        .optional => |opt| blk: {
            const child_meta = getTypeMeta(opt.child);
            break :blk .{
                .category = .optional,
                .size_bits = @bitSizeOf(T),
                .is_const = false,
                .pointee_category = child_meta.category,
            };
        },
        else => .{
            .category = .unknown,
            .size_bits = 0,
            .is_const = false,
            .pointee_category = .unknown,
        },
    };
}

fn getPointeeCategory(comptime T: type) TypeCategory {
    const info = @typeInfo(T);
    return switch (info) {
        .void => .void,
        .bool => .bool_,
        .int => |i| if (i.signedness == .signed) .int_signed else .int_unsigned,
        .float => .float,
        .@"struct" => .struct_,
        .pointer => .pointer,
        else => .unknown,
    };
}

/// Export all C-compatible public functions from a module
pub fn exportModule(comptime Module: type, comptime opts: ExportOptions) void {
    const decls = switch (@typeInfo(Module)) {
        .@"struct" => |s| s.decls,
        else => @compileError("exportModule requires a struct type (module)"),
    };

    inline for (decls) |decl| {
        const field = @field(Module, decl.name);
        const FieldType = @TypeOf(field);

        if (@typeInfo(FieldType) == .@"fn") {
            if (isFunctionCAbiCompatible(FieldType)) {
                // Generate export name
                const export_name = opts.prefix ++ decl.name ++ opts.suffix;

                // Export the function
                @export(&field, .{ .name = export_name });
            }
        }
    }
}

/// Export multiple modules at once
pub fn exportModules(comptime modules: anytype, comptime opts: ExportOptions) void {
    inline for (modules) |module| {
        exportModule(module, opts);
    }
}

/// Generate a simple JSON-like metadata string for a module's exports
/// This can be embedded in the binary and read by Python
pub fn generateMetadataJson(comptime Module: type, comptime opts: ExportOptions) []const u8 {
    comptime {
        var json: []const u8 = "{\"functions\":[";
        var first = true;

        const decls = switch (@typeInfo(Module)) {
            .@"struct" => |s| s.decls,
            else => return "{}",
        };

        for (decls) |decl| {
            const field = @field(Module, decl.name);
            const FieldType = @TypeOf(field);

            if (@typeInfo(FieldType) == .@"fn") {
                if (isFunctionCAbiCompatible(FieldType)) {
                    if (!first) {
                        json = json ++ ",";
                    }
                    first = false;

                    const func_info = @typeInfo(FieldType).@"fn";
                    const export_name = opts.prefix ++ decl.name ++ opts.suffix;

                    // Build function entry
                    json = json ++ "{\"name\":\"" ++ export_name ++ "\",";
                    json = json ++ "\"params\":[";

                    var first_param = true;
                    for (func_info.params) |param| {
                        if (param.type) |ptype| {
                            if (!first_param) {
                                json = json ++ ",";
                            }
                            first_param = false;
                            json = json ++ "\"" ++ @typeName(ptype) ++ "\"";
                        }
                    }

                    json = json ++ "],\"return\":\"";
                    if (func_info.return_type) |ret| {
                        json = json ++ @typeName(ret);
                    } else {
                        json = json ++ "void";
                    }
                    json = json ++ "\"}";
                }
            }
        }

        json = json ++ "]}";
        return json;
    }
}

/// Export metadata as a retrievable function
pub fn exportMetadata(comptime Module: type, comptime opts: ExportOptions) void {
    const metadata = generateMetadataJson(Module, opts);

    const S = struct {
        fn getMetadata() [*:0]const u8 {
            return metadata[0..metadata.len :0];
        }
    };

    @export(&S.getMetadata, .{ .name = opts.prefix ++ "__pzspec_metadata" ++ opts.suffix });
}

// =============================================================================
// Convenience Macros / Helpers
// =============================================================================

/// Standard PZSpec export with metadata - the recommended one-liner
pub fn pzspec(comptime Module: type) void {
    const opts = ExportOptions{};
    exportModule(Module, opts);
    exportMetadata(Module, opts);
}

/// Export with custom prefix (useful for namespacing)
pub fn pzspecWithPrefix(comptime Module: type, comptime prefix: []const u8) void {
    const opts = ExportOptions{ .prefix = prefix };
    exportModule(Module, opts);
    exportMetadata(Module, opts);
}

// =============================================================================
// Tests
// =============================================================================

test "isCAbiCompatible" {
    // Primitives
    try std.testing.expect(isCAbiCompatible(void));
    try std.testing.expect(isCAbiCompatible(bool));
    try std.testing.expect(isCAbiCompatible(i32));
    try std.testing.expect(isCAbiCompatible(u64));
    try std.testing.expect(isCAbiCompatible(f32));
    try std.testing.expect(isCAbiCompatible(f64));

    // Pointers
    try std.testing.expect(isCAbiCompatible(*i32));
    try std.testing.expect(isCAbiCompatible(*const i32));
    try std.testing.expect(isCAbiCompatible([*]u8));
    try std.testing.expect(isCAbiCompatible([*:0]const u8)); // C string

    // Extern struct
    const Vec2 = extern struct { x: f32, y: f32 };
    try std.testing.expect(isCAbiCompatible(Vec2));
    try std.testing.expect(isCAbiCompatible(*const Vec2));

    // Non-extern struct (not compatible)
    const NotExtern = struct { x: f32 };
    try std.testing.expect(!isCAbiCompatible(NotExtern));

    // Slices (not compatible)
    try std.testing.expect(!isCAbiCompatible([]u8));
    try std.testing.expect(!isCAbiCompatible([]const u8));
}

test "isFunctionCAbiCompatible" {
    // Compatible functions
    try std.testing.expect(isFunctionCAbiCompatible(fn (i32, i32) i32));
    try std.testing.expect(isFunctionCAbiCompatible(fn (f32) f32));
    try std.testing.expect(isFunctionCAbiCompatible(fn () void));
    try std.testing.expect(isFunctionCAbiCompatible(fn ([*:0]const u8) u32));

    // Extern struct params
    const Vec2 = extern struct { x: f32, y: f32 };
    try std.testing.expect(isFunctionCAbiCompatible(fn (*const Vec2) f32));
    try std.testing.expect(isFunctionCAbiCompatible(fn (Vec2, Vec2) Vec2));

    // Incompatible - slice parameter
    try std.testing.expect(!isFunctionCAbiCompatible(fn ([]const u8) void));
}

test "getTypeMeta" {
    const i32_meta = getTypeMeta(i32);
    try std.testing.expectEqual(TypeCategory.int_signed, i32_meta.category);
    try std.testing.expectEqual(@as(u16, 32), i32_meta.size_bits);

    const f32_meta = getTypeMeta(f32);
    try std.testing.expectEqual(TypeCategory.float, f32_meta.category);
    try std.testing.expectEqual(@as(u16, 32), f32_meta.size_bits);

    const str_meta = getTypeMeta([*:0]const u8);
    try std.testing.expectEqual(TypeCategory.c_string, str_meta.category);
    try std.testing.expect(str_meta.is_const);
}
