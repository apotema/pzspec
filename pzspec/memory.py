"""
Memory leak detection for Zig allocations.

This module provides tools to track Zig memory allocations during tests
and detect leaks. It requires Zig-side support via a tracking allocator.

Zig Side Requirements:
----------------------
To use memory tracking, your Zig code must export the following functions:

```zig
// In your Zig library (e.g., src/lib.zig)
const std = @import("std");

// Tracking allocator for test instrumentation
var gpa = std.heap.GeneralPurposeAllocator(.{
    .enable_memory_limit = true,
    .stack_trace_frames = 8,
}){};

// Export for Python to query
export fn __pzspec_get_allocation_count() usize {
    return gpa.allocation_count;
}

export fn __pzspec_get_leaked_bytes() usize {
    const leaked = gpa.detectLeaks();
    return if (leaked) gpa.total_requested_bytes else 0;
}

export fn __pzspec_reset_tracking() void {
    _ = gpa.deinit();
    gpa = std.heap.GeneralPurposeAllocator(.{
        .enable_memory_limit = true,
        .stack_trace_frames = 8,
    }){};
}

// Use the tracking allocator in your code
pub const allocator = gpa.allocator();
```
"""

import ctypes
from typing import Optional, List, Callable
from dataclasses import dataclass, field
from contextlib import contextmanager


@dataclass
class AllocationInfo:
    """Information about a memory allocation."""
    address: int
    size: int
    source_file: Optional[str] = None
    source_line: Optional[int] = None


@dataclass
class LeakReport:
    """Report of memory leaks detected during a test."""
    leaked_bytes: int
    allocation_count: int
    allocations: List[AllocationInfo] = field(default_factory=list)

    @property
    def has_leaks(self) -> bool:
        """Check if there are any leaks."""
        return self.leaked_bytes > 0


class MemoryTracker:
    """
    Tracks memory allocations in Zig code via FFI.

    This class interfaces with Zig's tracking allocator exports to detect
    memory leaks during tests.
    """

    def __init__(self, lib: ctypes.CDLL):
        """
        Initialize the memory tracker.

        Args:
            lib: The loaded Zig library (ctypes.CDLL)
        """
        self._lib = lib
        self._has_tracking = self._check_tracking_support()
        self._initial_allocation_count = 0
        self._initial_leaked_bytes = 0

    def _check_tracking_support(self) -> bool:
        """Check if the Zig library has memory tracking support."""
        try:
            # Try to access the tracking functions
            _ = self._lib.__pzspec_get_allocation_count
            _ = self._lib.__pzspec_get_leaked_bytes
            _ = self._lib.__pzspec_reset_tracking
            return True
        except AttributeError:
            return False

    @property
    def is_available(self) -> bool:
        """Check if memory tracking is available."""
        return self._has_tracking

    def get_allocation_count(self) -> int:
        """Get the current number of allocations."""
        if not self._has_tracking:
            return 0
        func = self._lib.__pzspec_get_allocation_count
        func.restype = ctypes.c_size_t
        return func()

    def get_leaked_bytes(self) -> int:
        """Get the number of leaked bytes."""
        if not self._has_tracking:
            return 0
        func = self._lib.__pzspec_get_leaked_bytes
        func.restype = ctypes.c_size_t
        return func()

    def reset(self):
        """Reset the memory tracking state."""
        if not self._has_tracking:
            return
        func = self._lib.__pzspec_reset_tracking
        func.restype = None
        func()

    def start_tracking(self):
        """Start tracking allocations (record initial state)."""
        self._initial_allocation_count = self.get_allocation_count()
        self._initial_leaked_bytes = self.get_leaked_bytes()

    def stop_tracking(self) -> LeakReport:
        """
        Stop tracking and return a leak report.

        Returns:
            LeakReport with leak information
        """
        current_count = self.get_allocation_count()
        leaked_bytes = self.get_leaked_bytes()

        return LeakReport(
            leaked_bytes=leaked_bytes,
            allocation_count=current_count - self._initial_allocation_count,
        )


# Global memory tracker instance
_memory_tracker: Optional[MemoryTracker] = None


def get_memory_tracker() -> Optional[MemoryTracker]:
    """Get the global memory tracker instance."""
    return _memory_tracker


def set_memory_tracker(tracker: MemoryTracker):
    """Set the global memory tracker instance."""
    global _memory_tracker
    _memory_tracker = tracker


def init_memory_tracker_from_library(lib: ctypes.CDLL):
    """Initialize the memory tracker from a loaded Zig library."""
    global _memory_tracker
    _memory_tracker = MemoryTracker(lib)
    return _memory_tracker


@contextmanager
def track_memory():
    """
    Context manager to track memory allocations during a block of code.

    Usage:
        with track_memory() as report:
            # Run code that allocates memory
            result = create_resource()
            process(result)
            destroy_resource(result)

        if report.has_leaks:
            print(f"Leaked {report.leaked_bytes} bytes!")

    Note:
        The report is populated when the context exits, not during.
        Access report.has_leaks and report.leaked_bytes after the with block.
    """
    tracker = get_memory_tracker()

    report = LeakReport(leaked_bytes=0, allocation_count=0)

    if tracker is None or not tracker.is_available:
        # No tracking available, yield empty report
        yield report
        return

    tracker.start_tracking()

    try:
        yield report
    finally:
        # Populate the report with actual values
        final_report = tracker.stop_tracking()
        report.leaked_bytes = final_report.leaked_bytes
        report.allocation_count = final_report.allocation_count
        report.allocations = final_report.allocations


class MemoryLeakError(AssertionError):
    """Raised when a memory leak is detected."""

    def __init__(self, report: LeakReport, test_name: str = ""):
        self.report = report
        self.test_name = test_name
        msg = self._format_message()
        super().__init__(msg)

    def _format_message(self) -> str:
        """Format the error message."""
        lines = []
        if self.test_name:
            lines.append(f"Memory Leak Detected in \"{self.test_name}\":")
        else:
            lines.append("Memory Leak Detected:")

        lines.append(f"  Total: {self.report.leaked_bytes} bytes leaked")
        lines.append(f"  Allocations: {self.report.allocation_count}")

        for alloc in self.report.allocations:
            loc = ""
            if alloc.source_file:
                loc = f" at {alloc.source_file}"
                if alloc.source_line:
                    loc += f":{alloc.source_line}"
            lines.append(f"  - {alloc.size} bytes{loc}")

        return "\n".join(lines)


def assert_no_leaks(report: LeakReport, test_name: str = ""):
    """
    Assert that a memory report has no leaks.

    Args:
        report: The LeakReport to check
        test_name: Optional test name for error messages

    Raises:
        MemoryLeakError: If leaks are detected
    """
    if report.has_leaks:
        raise MemoryLeakError(report, test_name)


def check_leaks(func: Callable) -> Callable:
    """
    Decorator to check for memory leaks in a test function.

    Usage:
        @check_leaks
        @it("should free all allocations")
        def test_cleanup():
            handle = create_resource()
            process(handle)
            destroy_resource(handle)
            # Test fails if any allocations weren't freed
    """
    def wrapper(*args, **kwargs):
        with track_memory() as report:
            result = func(*args, **kwargs)

        assert_no_leaks(report, func.__name__)
        return result

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper
