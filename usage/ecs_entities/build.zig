const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    // Create a module from the source file with target
    const lib_module = b.addModule("ecs_entities", .{
        .root_source_file = b.path("src/entities.zig"),
        .target = target,
    });

    // Create a shared library that can be loaded by Python via FFI
    const lib = b.addLibrary(.{
        .name = "ecs_entities",
        .root_module = lib_module,
    });
    lib.root_module.optimize = optimize;

    // Set to dynamic linkage for shared library
    lib.linkage = .dynamic;

    // Install the library
    b.installArtifact(lib);
}
