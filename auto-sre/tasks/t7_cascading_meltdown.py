"""Task t7_cascading_meltdown — enterprise cascade failure scenario.

PHASE 3: The "Golden" cascade task.

Scenario:
  A rogue background process (PID randomized) is writing errors to
  /var/log/syslog in an infinite loop. This fills the disk to 100%,
  causing the primary Database service ('db') to crash.

Agent must:
  1. Run df -h to detect the disk issue.
  2. Clear logs to free space (rm /var/log/syslog).
  3. Find and kill the rogue process causing the logs.
  4. Check and restart the database (systemctl restart db).
"""

from __future__ import annotations

import random

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import CascadeGrader

TASK_ID = "t7_cascading_meltdown"
DESCRIPTION = (
    "ALERT: Disk at 100%. Database service is down. "
    "A rogue process is flooding /var/log/syslog. "
    "Diagnose, clear logs, kill the rogue process, and restore the DB."
)
MAX_STEPS = 20


def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    """Build the cascading meltdown initial state with randomized PID."""
    fs = MockFilesystem()

    # Randomize rogue PID for Phase 4 anti-memorization
    rogue_pid = random.randint(200, 9990)

    # Base layer — standard system files
    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="auto-sre-host"),
        "/etc/os-release": MockFile(path="/etc/os-release", content="NAME=Ubuntu\nVERSION=22.04"),
        "/bin/bash": MockFile(path="/bin/bash", content="binary", permissions="rwxr-xr-x"),
    })

    # Overlay — broken cascade state
    # Disk is full because syslog is enormous
    syslog_content = (
        f"[ERROR] rogue-logger[{rogue_pid}]: FATAL loop iteration 1\n"
        f"[ERROR] rogue-logger[{rogue_pid}]: FATAL loop iteration 2\n"
        f"[ERROR] rogue-logger[{rogue_pid}]: FATAL loop iteration 3\n"
        "... (17GB of repeated errors) ...\n"
        f"[ERROR] rogue-logger[{rogue_pid}]: FATAL loop iteration 999999\n"
    )

    fs.set_overlay({
        "/var/log/syslog": MockFile(
            path="/var/log/syslog",
            content=syslog_content,
        ),
        "/etc/db/db.conf": MockFile(
            path="/etc/db/db.conf",
            content="port=5432\nmax_connections=100\n",
        ),
        "/home/user/README.md": MockFile(
            path="/home/user/README.md",
            content=(
                "# Cascading Meltdown\n\n"
                "Something caused the disk to fill up.\n"
                "The DB service is down. Figure it out.\n"
            ),
        ),
    })

    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1,          command="init",                      port_bindings=[]),
        MockProcess(pid=200,        command="nginx",                     port_bindings=[80]),
        MockProcess(pid=rogue_pid,  command="rogue-logger --infinite",   port_bindings=[]),
    ])

    # Build world model initial state for this task
    # (injected into Sandbox by _session.py via build_initial_state return)
    # We store rogue_pid in a module-level variable so the grader can reference it
    # via session.sandbox.state["rogue_pid"]
    _state_hint.update({
        "disk_usage": 100,
        "memory_usage": 25,
        "ports": {"80": 200},
        "config_valid": False,
        "services_running": {"nginx": True, "db": False},
        "rogue_pid": rogue_pid,
        "target_log": "/var/log/syslog",
        "target_port": 80,
    })

    return fs, pm


# Module-level state hint dict — read by the session to seed sandbox.state
_state_hint: dict = {}

# Grader instance — CascadeGrader reads state from world model
GRADER = CascadeGrader()
