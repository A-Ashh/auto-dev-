"""Scenario 6: Rogue process leaking memory until OOM.

Goal: Identify the rogue memory_hog process and kill it.
"""

from __future__ import annotations

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import OOMGrader

TASK_ID = "t6_oom_killer"
DESCRIPTION = "System unresponsive due to rogue process consuming 99% RAM. Fix it."
MAX_STEPS = 10

GRADER = OOMGrader()

def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    """Construct the initial mock state."""
    fs = MockFilesystem()
    pm = ProcessManager()

    # Read-only base
    base_files = {
        "/bin/bash": MockFile("/bin/bash", "binary", "rwxr-xr-x"),
        "/usr/bin/python3": MockFile("/usr/bin/python3", "binary", "rwxr-xr-x"),
    }
    fs.set_base(base_files)

    # Writable overlay
    overlay_files = {
        "/home/user/.bashrc": MockFile("/home/user/.bashrc", "alias ll='ls -l'"),
        "/tmp/memory_hog.py": MockFile("/tmp/memory_hog.py", "while True: leak.append('M' * 1024 * 1024)"),
    }
    fs.set_overlay(overlay_files)

    import random
    rogue_pid = random.randint(300, 9999)

    # Rogue process
    pm.load([
        MockProcess(
            pid=rogue_pid,
            command="python3 /tmp/memory_hog.py",
            port_bindings=[]
        )
    ])

    global _state_hint
    _state_hint = {
        "memory_usage": 99,
        "rogue_pid": rogue_pid
    }

    return fs, pm

_state_hint: dict = {}

