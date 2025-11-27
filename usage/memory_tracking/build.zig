const std = @import("std");

pub fn build(b: *std.Build) void {
    const target = b.standardTargetOptions(.{});
    const optimize = b.standardOptimizeOption(.{});

    const lib_module = b.addModule("memory_tracking", .{
        .root_source_file = b.path("src/resources.zig"),
        .target = target,
    });

    const lib = b.addLibrary(.{
        .name = "memory_tracking",
        .root_module = lib_module,
    });
    lib.root_module.optimize = optimize;
    lib.linkage = .dynamic;

    b.installArtifact(lib);
}
