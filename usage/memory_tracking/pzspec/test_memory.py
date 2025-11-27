"""
Test suite for Memory Tracking demonstrating PZSpec Leak Detection.

This example shows how to detect memory leaks in Zig code using:
1. Direct Zig tracking allocator functions (__pzspec_* exports)
2. PZSpec's track_memory() context manager
3. PZSpec's @check_leaks decorator

The example demonstrates both successful tests (proper cleanup) and
tests that intentionally detect leaks to show the feature works.
"""

import sys
from pathlib import Path

# Add the parent PZSpec to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Import from the framework package
from pzspec.zig_ffi import ZigLibrary
from pzspec.dsl import describe, it, expect, before_each
from pzspec.memory import (
    track_memory,
    check_leaks,
    assert_no_leaks,
    init_memory_tracker_from_library,
    MemoryLeakError,
    LeakReport,
)
import ctypes

# Load the Zig library
zig = ZigLibrary()

# Initialize memory tracker with the Zig library
tracker = init_memory_tracker_from_library(zig._lib)


# =============================================================================
# Helper Functions - Resource Management
# =============================================================================
def create_buffer(size: int) -> int:
    """Create a buffer and return its handle."""
    func = zig.get_function("create_buffer", [ctypes.c_size_t], ctypes.c_size_t)
    return func(size)


def destroy_buffer(handle: int) -> bool:
    """Destroy a buffer by handle."""
    func = zig.get_function("destroy_buffer", [ctypes.c_size_t], ctypes.c_bool)
    return func(handle)


def get_buffer_size(handle: int) -> int:
    """Get buffer size."""
    func = zig.get_function("get_buffer_size", [ctypes.c_size_t], ctypes.c_size_t)
    return func(handle)


def buffer_write(handle: int, index: int, value: int) -> bool:
    """Write to buffer."""
    func = zig.get_function("buffer_write", [ctypes.c_size_t, ctypes.c_size_t, ctypes.c_uint8], ctypes.c_bool)
    return func(handle, index, value)


def buffer_read(handle: int, index: int) -> int:
    """Read from buffer."""
    func = zig.get_function("buffer_read", [ctypes.c_size_t, ctypes.c_size_t], ctypes.c_int32)
    return func(handle, index)


def process_with_cleanup(size: int) -> bool:
    """Process with proper cleanup - no leak."""
    func = zig.get_function("process_with_cleanup", [ctypes.c_size_t], ctypes.c_bool)
    return func(size)


def process_with_leak(size: int) -> bool:
    """Process without cleanup - intentional leak."""
    func = zig.get_function("process_with_leak", [ctypes.c_size_t], ctypes.c_bool)
    return func(size)


def cleanup_all_buffers() -> int:
    """Clean up all remaining buffers."""
    func = zig.get_function("cleanup_all_buffers", [], ctypes.c_size_t)
    return func()


# =============================================================================
# Helper Functions - Direct Memory Tracking (Zig exports)
# =============================================================================
def reset_tracking():
    """Reset memory tracking statistics."""
    func = zig.get_function("__pzspec_reset_tracking", [], None)
    func()


def get_leaked_bytes() -> int:
    """Get current leaked bytes from Zig."""
    func = zig.get_function("__pzspec_get_leaked_bytes", [], ctypes.c_size_t)
    return func()


def get_allocation_count() -> int:
    """Get current allocation count from Zig."""
    func = zig.get_function("__pzspec_get_allocation_count", [], ctypes.c_size_t)
    return func()


# =============================================================================
# Tests - Successful (No Leaks)
# =============================================================================

with describe("Memory Management - Proper Cleanup (Success Cases)"):

    @before_each
    def setup():
        cleanup_all_buffers()
        reset_tracking()

    @it("should create and destroy buffer without leaking")
    def test_create_destroy():
        # Check initial state
        expect(get_leaked_bytes()).to_equal(0)

        handle = create_buffer(256)
        expect(handle).to_not_equal(0xFFFFFFFFFFFFFFFF)

        # Memory is allocated - should show leaked bytes
        leaked_during = get_leaked_bytes()
        expect(leaked_during > 0).to_be_true()

        # Use the buffer
        expect(buffer_write(handle, 0, 42)).to_be_true()
        expect(buffer_read(handle, 0)).to_equal(42)

        # Properly destroy
        expect(destroy_buffer(handle)).to_be_true()

        # Should have no leaks after cleanup
        expect(get_leaked_bytes()).to_equal(0)

    @it("should handle multiple buffers with proper cleanup")
    def test_multiple_buffers():
        handles = []
        for size in [64, 128, 256]:
            handle = create_buffer(size)
            handles.append(handle)

        # All allocated - should have leaked bytes
        expect(get_leaked_bytes() > 0).to_be_true()

        # Use buffers
        for i, handle in enumerate(handles):
            buffer_write(handle, 0, i)

        # Clean up all
        for handle in handles:
            destroy_buffer(handle)

        # No leaks
        expect(get_leaked_bytes()).to_equal(0)

    @it("should work with process_with_cleanup helper")
    def test_process_with_cleanup():
        expect(get_leaked_bytes()).to_equal(0)

        result = process_with_cleanup(512)
        expect(result).to_be_true()

        # Function cleans up internally
        expect(get_leaked_bytes()).to_equal(0)

    @it("should pass with track_memory when no leaks")
    def test_track_memory_success():
        with track_memory() as report:
            handle = create_buffer(128)
            buffer_write(handle, 0, 99)
            value = buffer_read(handle, 0)
            expect(value).to_equal(99)
            destroy_buffer(handle)

        # After context, report shows no leaks
        expect(report.leaked_bytes).to_equal(0)


# =============================================================================
# Tests - Leak Detection (Detecting Intentional Leaks)
# =============================================================================

with describe("Memory Leak Detection (Detecting Intentional Leaks)"):

    @before_each
    def setup():
        cleanup_all_buffers()
        reset_tracking()

    @it("should detect leak when buffer is not destroyed")
    def test_detect_single_leak():
        expect(get_leaked_bytes()).to_equal(0)

        handle = create_buffer(256)
        expect(handle).to_not_equal(0xFFFFFFFFFFFFFFFF)

        # Use the buffer but DON'T destroy it
        buffer_write(handle, 0, 42)

        # Should detect the leak via direct Zig call
        leaked = get_leaked_bytes()
        expect(leaked > 0).to_be_true()

        # Clean up for next test
        destroy_buffer(handle)
        expect(get_leaked_bytes()).to_equal(0)

    @it("should detect leak from process_with_leak")
    def test_detect_leak_from_helper():
        expect(get_leaked_bytes()).to_equal(0)

        result = process_with_leak(512)
        expect(result).to_be_true()

        # Should detect the leak
        leaked = get_leaked_bytes()
        expect(leaked > 0).to_be_true()

        # Clean up
        cleanup_all_buffers()

    @it("should detect partial leaks")
    def test_detect_partial_leaks():
        # Create 3 buffers
        h1 = create_buffer(64)
        h2 = create_buffer(64)
        h3 = create_buffer(64)

        leaked_all = get_leaked_bytes()

        # Only destroy one
        destroy_buffer(h1)

        # Should have less leaked bytes but still > 0
        leaked_partial = get_leaked_bytes()
        expect(leaked_partial > 0).to_be_true()
        expect(leaked_partial < leaked_all).to_be_true()

        # Clean up remaining
        destroy_buffer(h2)
        destroy_buffer(h3)
        expect(get_leaked_bytes()).to_equal(0)

    @it("should raise MemoryLeakError with assert_no_leaks")
    def test_assert_no_leaks_raises():
        handle = create_buffer(128)

        # Create a report that shows leaks
        report = LeakReport(
            leaked_bytes=get_leaked_bytes(),
            allocation_count=get_allocation_count(),
        )

        # This should raise because report shows leaks
        raised = False
        try:
            assert_no_leaks(report, "test_leak")
        except MemoryLeakError as e:
            raised = True
            expect("Memory Leak Detected" in str(e)).to_be_true()

        expect(raised).to_be_true()

        # Clean up
        destroy_buffer(handle)

    @it("should show leak detection with manual tracking pattern")
    def test_manual_leak_detection_pattern():
        """
        This test demonstrates the recommended pattern for leak detection:
        Check leaked bytes before and after your code runs.
        """
        # Record state before
        reset_tracking()
        before = get_leaked_bytes()
        expect(before).to_equal(0)

        # Run code that leaks
        handle = create_buffer(64)
        # Intentionally don't destroy

        # Check for leak
        after = get_leaked_bytes()
        has_leak = after > before

        expect(has_leak).to_be_true()

        # Clean up
        destroy_buffer(handle)
        expect(get_leaked_bytes()).to_equal(0)


# =============================================================================
# Tests - Edge Cases
# =============================================================================

with describe("Memory Tracking - Edge Cases"):

    @before_each
    def setup():
        cleanup_all_buffers()
        reset_tracking()

    @it("should handle zero-size buffer request")
    def test_zero_size():
        initial_leaked = get_leaked_bytes()

        handle = create_buffer(0)
        # Should fail to create
        expect(handle).to_equal(0xFFFFFFFFFFFFFFFF)

        # No new allocations
        expect(get_leaked_bytes()).to_equal(initial_leaked)

    @it("should handle double-free gracefully")
    def test_double_free():
        handle = create_buffer(64)
        expect(destroy_buffer(handle)).to_be_true()
        # Second destroy should return false but not crash
        expect(destroy_buffer(handle)).to_be_false()

        expect(get_leaked_bytes()).to_equal(0)

    @it("should track allocations across multiple operations")
    def test_allocation_tracking():
        reset_tracking()

        # Initial state
        expect(get_leaked_bytes()).to_equal(0)

        # Create and check leak
        h1 = create_buffer(100)
        leaked1 = get_leaked_bytes()
        expect(leaked1 > 0).to_be_true()

        # Create another - more leaked
        h2 = create_buffer(200)
        leaked2 = get_leaked_bytes()
        expect(leaked2 > leaked1).to_be_true()

        # Free one - less leaked
        destroy_buffer(h1)
        leaked3 = get_leaked_bytes()
        expect(leaked3 < leaked2).to_be_true()

        # Free the other - no leak
        destroy_buffer(h2)
        expect(get_leaked_bytes()).to_equal(0)
