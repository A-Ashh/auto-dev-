"""Task t4_trap — reasoning / trap scenario."""

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import TrapGrader


TASK_ID = "t4_trap"
DESCRIPTION = "A system report suggests a failure, but the system may already be healthy. Verify before taking action."
MAX_STEPS = 10


def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    """Create a healthy state for this task."""
    fs = MockFilesystem()

    # Base layer
    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="auto-sre-host"),
        "/etc/os-release": MockFile(path="/etc/os-release", content="NAME=Ubuntu\nVERSION=22.04"),
        "/var/log/syslog": MockFile(path="/var/log/syslog", content="system boot ok\n"),
    })

    # Overlay — healthy system
    fs.set_overlay({
        "/etc/app/conf": MockFile(path="/etc/app/conf", content="DB_HOST=localhost\nPORT=3000\n"),
        "/home/user/README.md": MockFile(path="/home/user/README.md", content="# My App\nRun with: node app.js\n"),
    })

    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=200, command="nginx", port_bindings=[80]),
    ])

    return fs, pm


GRADER = TrapGrader()
