"""Build script for Ziggy-Pydust modules."""

import os
import shutil
from pathlib import Path

import pydust
import pydust.build


def setup_ffi_header():
    """Copy ffi.h from pydust package to local directory for translate-c."""
    pydust_src = Path(pydust.__file__).parent / "src" / "ffi.h"
    local_dir = Path("pydust/src")
    local_ffi = local_dir / "ffi.h"

    if not local_ffi.exists():
        local_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(pydust_src, local_ffi)
        print(f"Copied {pydust_src} to {local_ffi}")


if __name__ == "__main__":
    setup_ffi_header()
    pydust.build.build()
