const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Create a module from the source file with target
    const lib_module = b.addModule("vector_math", .{
        .root_source_file = b.path("src/vector.zig"),
        .target = target,
    });

    // Create a shared library that can be loaded by Python via FFI
    const lib = b.addLibrary(.{
        .name = "vector_math",
        .root_module = lib_module,
    });
    lib.root_module.optimize = optimize;

    // Set to dynamic linkage for shared library
    lib.linkage = .dynamic;

    // Install the library
    b.installArtifact(lib);
}
