#!/bin/bash
# Build script to create shared library for Python FFI
# This is a workaround for Zig build system limitations

set -e

OPTIMIZE="${1:-ReleaseSafe}"

echo "Building shared library with optimization: $OPTIMIZE"

zig build-lib \
    -dynamic \
    -O "$OPTIMIZE" \
    -fPIC \
    src/lib.zig \
    --name ziglib

# Move to expected location
mkdir -p zig-out/lib

# Find and move the created library (Zig creates lib<name>.dylib/.so/.dll)
if [ -f libziglib.dylib ]; then
    mv libziglib.dylib zig-out/lib/
    echo "Moved libziglib.dylib to zig-out/lib/"
elif [ -f libziglib.so ]; then
    mv libziglib.so zig-out/lib/
    echo "Moved libziglib.so to zig-out/lib/"
elif [ -f libziglib.dll ]; then
    mv libziglib.dll zig-out/lib/
    echo "Moved libziglib.dll to zig-out/lib/"
elif [ -f liblib.dylib ]; then
    # Fallback: if created as liblib.dylib, rename it
    mv liblib.dylib zig-out/lib/libziglib.dylib
    echo "Moved and renamed liblib.dylib to zig-out/lib/libziglib.dylib"
else
    echo "Warning: Shared library not found. Checking current directory..."
    ls -la *.dylib *.so *.dll 2>/dev/null || echo "No library files found"
fi

echo "Shared library built successfully in zig-out/lib/"

