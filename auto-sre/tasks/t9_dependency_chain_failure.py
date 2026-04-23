"""t9_dependency_chain_failure — cascading service failure due to dependency ordering.

5-step remediation:
  1. systemctl status app -> detect app failure
  2. cat /var/log/app.log -> trace to db dependency
  3. systemctl restart db -> fix root service first
  4. systemctl restart cache -> fix middle tier
  5. systemctl restart app -> restore top service
"""
from __future__ import annotations
from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import DepChainGrader

TASK_ID = "t9_dependency_chain_failure"
DESCRIPTION = (
    "ALERT: Application service 'app' is down. Dependency chain failure detected. "
    "Trace the dependency chain (app -> cache -> db), fix root cause, restart in correct order."
)
MAX_STEPS = 18

_state_hint: dict = {}


def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    fs = MockFilesystem()
    fs.set_base({
        "/etc/hostname": MockFile("/etc/hostname", "auto-sre-host"),
        "/etc/app/service.conf": MockFile("/etc/app/service.conf",
            "depends_on=cache\n"),
        "/etc/cache/service.conf": MockFile("/etc/cache/service.conf",
            "depends_on=db\n"),
    })
    fs.set_overlay({
        "/var/log/app.log": MockFile("/var/log/app.log",
            "[ERROR] app: cannot connect to cache:6379\n"
            "[ERROR] app: service dependency failed — aborting startup\n"),
        "/var/log/cache.log": MockFile("/var/log/cache.log",
            "[ERROR] cache: cannot connect to db:5432\n"
            "[ERROR] cache: database backend unavailable\n"),
        "/var/log/db.log": MockFile("/var/log/db.log",
            "[ERROR] db: data directory /var/lib/db corrupted\n"
            "[INFO] db: attempting recovery...\n"),
    })
    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=100, command="nginx", port_bindings=[80]),
    ])
    _state_hint.update({
        "disk_usage": 20,
        "memory_usage": 30,
        "services_running": {"db": False, "cache": False, "app": False, "nginx": True},
        "target_log": "/var/log/app.log",
        "target_port": 3000,
        "dep_chain_order": ["db", "cache", "app"],
    })
    return fs, pm


GRADER = DepChainGrader()
