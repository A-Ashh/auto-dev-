"""t10_config_secret_failure — app failing due to missing/wrong secret in config.

5-step remediation:
  1. systemctl status app -> detect failure
  2. cat /var/log/app.log -> find "invalid secret" error
  3. cat /etc/app/secrets.conf -> inspect bad value
  4. echo CORRECT_SECRET > /etc/app/secrets.conf -> fix secret
  5. systemctl restart app -> verify recovery
"""
from __future__ import annotations
from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import SecretGrader

TASK_ID = "t10_config_secret_failure"
DESCRIPTION = (
    "Application is down -> authentication failure..."
    "A config secret is invalid. Inspect logs, find the bad secret, update it, and restart the app."
)
MAX_STEPS = 15

_state_hint: dict = {}


def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    fs = MockFilesystem()
    fs.set_base({
        "/etc/hostname": MockFile("/etc/hostname", "auto-sre-host"),
    })
    fs.set_overlay({
        "/etc/app/secrets.conf": MockFile("/etc/app/secrets.conf",
            "DB_PASSWORD=WRONG_SECRET_XYZ\nAPI_KEY=\n"),
        "/var/log/app.log": MockFile("/var/log/app.log",
            "[ERROR] app: database authentication failed\n"
            "[ERROR] app: invalid DB_PASSWORD in /etc/app/secrets.conf\n"
            "[FATAL] app: unable to establish connection pool — exiting\n"),
        "/etc/app/app.conf": MockFile("/etc/app/app.conf",
            "port=8080\ndb_host=localhost\ndb_port=5432\n"),
    })
    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=200, command="nginx", port_bindings=[80]),
    ])
    _state_hint.update({
        "disk_usage": 20,
        "memory_usage": 20,
        "services_running": {"app": False, "nginx": True},
        "config_valid": False,
        "target_log": "/var/log/app.log",
        "secret_file": "/etc/app/secrets.conf",
        "target_port": 80,
    })
    return fs, pm


GRADER = SecretGrader()
