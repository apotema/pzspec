"""
Snapshot testing for PZSpec.

Allows comparing complex outputs against saved snapshots for regression testing.
"""

import json
import hashlib
import os
import ctypes
from pathlib import Path
from typing import Any, Optional, Dict, Union
from dataclasses import dataclass


# Global snapshot manager instance
_snapshot_manager: Optional['SnapshotManager'] = None

# Flag for update mode
_update_snapshots: bool = False


def set_update_snapshots(update: bool):
    """Set whether to update snapshots instead of comparing."""
    global _update_snapshots
    _update_snapshots = update


def get_update_snapshots() -> bool:
    """Get whether we're in update mode."""
    return _update_snapshots


@dataclass
class SnapshotResult:
    """Result of a snapshot comparison."""
    matched: bool
    expected: Optional[str] = None
    actual: Optional[str] = None
    diff: Optional[str] = None
    is_new: bool = False
    was_updated: bool = False


class SnapshotManager:
    """Manages snapshot storage and comparison."""

    def __init__(self, snapshot_dir: Path):
        """
        Initialize the snapshot manager.

        Args:
            snapshot_dir: Directory to store snapshots
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self._snapshots: Dict[str, Dict[str, str]] = {}
        self._current_test_file: Optional[str] = None
        self._current_test_name: Optional[str] = None
        self._snapshot_counters: Dict[str, int] = {}

    def set_current_test(self, test_file: str, test_name: str):
        """Set the current test context for snapshot naming."""
        self._current_test_file = test_file
        self._current_test_name = test_name
        key = f"{test_file}::{test_name}"
        self._snapshot_counters[key] = 0

    def _get_snapshot_key(self, name: Optional[str] = None) -> str:
        """Generate a unique snapshot key."""
        if name:
            return name

        # Auto-generate based on test file/name and counter
        key = f"{self._current_test_file}::{self._current_test_name}"
        counter = self._snapshot_counters.get(key, 0)
        self._snapshot_counters[key] = counter + 1

        if counter == 0:
            return f"{self._current_test_name}"
        return f"{self._current_test_name}_{counter}"

    def _get_snapshot_file(self, test_file: str) -> Path:
        """Get the snapshot file path for a test file."""
        # Use test file name as base for snapshot file
        test_name = Path(test_file).stem
        return self.snapshot_dir / f"{test_name}.snap.json"

    def _load_snapshots(self, test_file: str) -> Dict[str, str]:
        """Load snapshots for a test file."""
        if test_file in self._snapshots:
            return self._snapshots[test_file]

        snapshot_file = self._get_snapshot_file(test_file)
        if snapshot_file.exists():
            with open(snapshot_file, 'r') as f:
                self._snapshots[test_file] = json.load(f)
        else:
            self._snapshots[test_file] = {}

        return self._snapshots[test_file]

    def _save_snapshots(self, test_file: str):
        """Save snapshots for a test file."""
        snapshot_file = self._get_snapshot_file(test_file)
        with open(snapshot_file, 'w') as f:
            json.dump(self._snapshots[test_file], f, indent=2, sort_keys=True)

    def match_snapshot(
        self,
        value: Any,
        name: Optional[str] = None,
        serializer: Optional[callable] = None
    ) -> SnapshotResult:
        """
        Compare a value against its snapshot.

        Args:
            value: The value to compare
            name: Optional name for the snapshot (auto-generated if not provided)
            serializer: Optional custom serializer function

        Returns:
            SnapshotResult with comparison details
        """
        if self._current_test_file is None:
            raise RuntimeError("No test context set. Call set_current_test first.")

        # Serialize the value
        if serializer:
            actual = serializer(value)
        else:
            actual = self._serialize(value)

        snapshot_key = self._get_snapshot_key(name)
        snapshots = self._load_snapshots(self._current_test_file)

        if snapshot_key not in snapshots:
            # New snapshot
            if _update_snapshots or True:  # Always save new snapshots
                snapshots[snapshot_key] = actual
                self._save_snapshots(self._current_test_file)
                return SnapshotResult(
                    matched=True,
                    actual=actual,
                    is_new=True
                )
            else:
                return SnapshotResult(
                    matched=False,
                    actual=actual,
                    is_new=True,
                    diff="New snapshot - run with --update-snapshots to save"
                )

        expected = snapshots[snapshot_key]

        if actual == expected:
            return SnapshotResult(
                matched=True,
                expected=expected,
                actual=actual
            )

        if _update_snapshots:
            # Update the snapshot
            snapshots[snapshot_key] = actual
            self._save_snapshots(self._current_test_file)
            return SnapshotResult(
                matched=True,
                expected=expected,
                actual=actual,
                was_updated=True
            )

        # Generate diff
        diff = self._generate_diff(expected, actual)

        return SnapshotResult(
            matched=False,
            expected=expected,
            actual=actual,
            diff=diff
        )

    def _serialize(self, value: Any) -> str:
        """
        Serialize a value to a string for snapshot comparison.

        Handles:
        - ctypes Structures
        - Primitive types
        - Lists/tuples
        - Dictionaries
        """
        if isinstance(value, ctypes.Structure):
            return self._serialize_struct(value)
        elif isinstance(value, (list, tuple)):
            items = [self._serialize(item) for item in value]
            return json.dumps(items, indent=2)
        elif isinstance(value, dict):
            serialized = {k: json.loads(self._serialize(v)) if isinstance(v, str) and v.startswith('{') else self._serialize(v)
                         for k, v in value.items()}
            return json.dumps(serialized, indent=2, sort_keys=True)
        elif isinstance(value, (int, float, bool, str, type(None))):
            return json.dumps(value)
        else:
            # Try to convert to dict
            try:
                return json.dumps(vars(value), indent=2, sort_keys=True)
            except TypeError:
                return str(value)

    def _serialize_struct(self, struct: ctypes.Structure) -> str:
        """Serialize a ctypes Structure to JSON."""
        result = {}
        for field_name, field_type in struct._fields_:
            value = getattr(struct, field_name)
            if isinstance(value, ctypes.Structure):
                result[field_name] = json.loads(self._serialize_struct(value))
            elif isinstance(value, ctypes.Array):
                result[field_name] = list(value)
            elif isinstance(value, (int, float, bool)):
                result[field_name] = value
            elif isinstance(value, bytes):
                result[field_name] = value.decode('utf-8', errors='replace')
            else:
                result[field_name] = str(value)
        return json.dumps(result, indent=2, sort_keys=True)

    def _generate_diff(self, expected: str, actual: str) -> str:
        """Generate a human-readable diff between expected and actual."""
        expected_lines = expected.splitlines()
        actual_lines = actual.splitlines()

        diff_lines = []
        max_lines = max(len(expected_lines), len(actual_lines))

        for i in range(max_lines):
            exp_line = expected_lines[i] if i < len(expected_lines) else ""
            act_line = actual_lines[i] if i < len(actual_lines) else ""

            if exp_line != act_line:
                if exp_line:
                    diff_lines.append(f"- {exp_line}")
                if act_line:
                    diff_lines.append(f"+ {act_line}")
            else:
                diff_lines.append(f"  {exp_line}")

        return "\n".join(diff_lines)


def get_snapshot_manager() -> SnapshotManager:
    """Get or create the global snapshot manager."""
    global _snapshot_manager
    if _snapshot_manager is None:
        # Default snapshot directory
        _snapshot_manager = SnapshotManager(Path.cwd() / "pzspec" / "__snapshots__")
    return _snapshot_manager


def set_snapshot_manager(manager: SnapshotManager):
    """Set the global snapshot manager."""
    global _snapshot_manager
    _snapshot_manager = manager


def init_snapshot_manager(project_root: Path):
    """Initialize the snapshot manager for a project."""
    global _snapshot_manager
    snapshot_dir = project_root / "pzspec" / "__snapshots__"
    _snapshot_manager = SnapshotManager(snapshot_dir)
