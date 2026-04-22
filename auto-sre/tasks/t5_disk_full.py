"""Scenario 5: Disk full due to massive log file.

Goal: Identify the large file /var/log/syslog and delete it.
"""

from __future__ import annotations

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import ProcessManager
from grader.health_check import DiskGrader

TASK_ID = "t5_disk_full"
DESCRIPTION = "System unresponsive due to 100% disk utilization. Fix it."
MAX_STEPS = 10

GRADER = DiskGrader()

def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    """Construct the initial mock state."""
    fs = MockFilesystem()
    pm = ProcessManager()

    # Read-only base
    base_files = {
        "/bin/bash": MockFile("/bin/bash", "binary", "rwxr-xr-x"),
        "/usr/bin/ls": MockFile("/usr/bin/ls", "binary", "rwxr-xr-x"),
    }
    fs.set_base(base_files)

    target_log = "/var/log/syslog"

    # Writable overlay
    overlay_files = {
        "/home/user/.bashrc": MockFile("/home/user/.bashrc", "alias ll='ls -l'"),
        target_log: MockFile(target_log, "LARGE_LOG_CONTENT" * 1000000),  # Massive file
    }
    fs.set_overlay(overlay_files)

    global _state_hint
    _state_hint = {
        "disk_usage": 100,
        "target_log": target_log
    }

    return fs, pm

_state_hint: dict = {}

