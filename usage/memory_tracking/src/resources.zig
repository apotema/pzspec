const std = @import("std");

// =============================================================================
// Memory Tracking Example - Demonstrating Leak Detection
// =============================================================================
// This example shows how to set up memory tracking for PZSpec tests.
// It demonstrates both proper cleanup (no leaks) and intentional leaks.

// =============================================================================
// Tracking Allocator Setup (Required for memory leak detection)
// =============================================================================

var gpa = std.heap.GeneralPurposeAllocator(.{}){};
const allocator = gpa.allocator();

// Track allocation statistics manually since GPA doesn't expose counts directly
var allocation_count: usize = 0;
var total_allocated: usize = 0;
var total_freed: usize = 0;

// Export functions for PZSpec memory tracking
export fn __pzspec_get_allocation_count() usize {
    return allocation_count;
}

export fn __pzspec_get_leaked_bytes() usize {
    if (total_allocated > total_freed) {
        return total_allocated - total_freed;
    }
    return 0;
}

export fn __pzspec_reset_tracking() void {
    allocation_count = 0;
    total_allocated = 0;
    total_freed = 0;
}

// =============================================================================
// Resource Types
// =============================================================================

/// A simple buffer resource that allocates memory
const Buffer = struct {
    data: []u8,
    size: usize,
};

/// A handle to a buffer (opaque pointer for FFI)
const BufferHandle = *Buffer;

// Store allocated buffers to track them
var buffers: [100]?*Buffer = [_]?*Buffer{null} ** 100;
var next_handle: usize = 0;

// =============================================================================
// Resource Management Functions
// =============================================================================

/// Create a new buffer of the specified size
/// Returns a handle (index) or max value on failure
export fn create_buffer(size: usize) usize {
    if (next_handle >= 100) return std.math.maxInt(usize);
    if (size == 0) return std.math.maxInt(usize);

    // Allocate the buffer struct
    const buffer = allocator.create(Buffer) catch return std.math.maxInt(usize);

    // Allocate the data
    const data = allocator.alloc(u8, size) catch {
        allocator.destroy(buffer);
        return std.math.maxInt(usize);
    };

    buffer.* = .{
        .data = data,
        .size = size,
    };

    // Track allocation
    allocation_count += 2; // buffer struct + data array
    total_allocated += @sizeOf(Buffer) + size;

    const handle = next_handle;
    buffers[handle] = buffer;
    next_handle += 1;

    return handle;
}

/// Destroy a buffer and free its memory
export fn destroy_buffer(handle: usize) bool {
    if (handle >= 100) return false;

    const buffer = buffers[handle] orelse return false;

    // Track deallocation
    total_freed += @sizeOf(Buffer) + buffer.size;

    // Free the data
    allocator.free(buffer.data);

    // Free the buffer struct
    allocator.destroy(buffer);

    buffers[handle] = null;
    return true;
}

/// Get the size of a buffer
export fn get_buffer_size(handle: usize) usize {
    if (handle >= 100) return 0;
    const buffer = buffers[handle] orelse return 0;
    return buffer.size;
}

/// Write a byte to a buffer at the specified index
export fn buffer_write(handle: usize, index: usize, value: u8) bool {
    if (handle >= 100) return false;
    const buffer = buffers[handle] orelse return false;
    if (index >= buffer.size) return false;
    buffer.data[index] = value;
    return true;
}

/// Read a byte from a buffer at the specified index
export fn buffer_read(handle: usize, index: usize) i32 {
    if (handle >= 100) return -1;
    const buffer = buffers[handle] orelse return -1;
    if (index >= buffer.size) return -1;
    return @intCast(buffer.data[index]);
}

// =============================================================================
// Functions that demonstrate proper cleanup vs leaks
// =============================================================================

/// Create a buffer, use it, and properly destroy it - NO LEAK
export fn process_with_cleanup(size: usize) bool {
    const handle = create_buffer(size);
    if (handle == std.math.maxInt(usize)) return false;

    // Use the buffer
    _ = buffer_write(handle, 0, 42);
    _ = buffer_read(handle, 0);

    // Properly cleanup
    return destroy_buffer(handle);
}

/// Create a buffer but "forget" to destroy it - INTENTIONAL LEAK
export fn process_with_leak(size: usize) bool {
    const handle = create_buffer(size);
    if (handle == std.math.maxInt(usize)) return false;

    // Use the buffer
    _ = buffer_write(handle, 0, 42);
    _ = buffer_read(handle, 0);

    // Oops! Forgot to destroy_buffer(handle)
    // This will be detected as a leak
    return true;
}

/// Create multiple buffers and only clean up some - PARTIAL LEAK
export fn process_partial_cleanup(count: usize) usize {
    var handles: [10]usize = undefined;
    var created: usize = 0;

    // Create buffers
    for (0..@min(count, 10)) |_| {
        const handle = create_buffer(64);
        if (handle != std.math.maxInt(usize)) {
            handles[created] = handle;
            created += 1;
        }
    }

    // Only clean up half of them (intentional leak)
    const cleanup_count = created / 2;
    for (0..cleanup_count) |i| {
        _ = destroy_buffer(handles[i]);
    }

    // Return how many were leaked
    return created - cleanup_count;
}

// =============================================================================
// Utility Functions
// =============================================================================

/// Get current allocation statistics
export fn get_allocation_stats(out_count: *usize, out_allocated: *usize, out_freed: *usize) void {
    out_count.* = allocation_count;
    out_allocated.* = total_allocated;
    out_freed.* = total_freed;
}

/// Clean up all remaining buffers (for test reset)
export fn cleanup_all_buffers() usize {
    var cleaned: usize = 0;
    for (0..100) |i| {
        if (buffers[i] != null) {
            _ = destroy_buffer(i);
            cleaned += 1;
        }
    }
    next_handle = 0;
    return cleaned;
}
