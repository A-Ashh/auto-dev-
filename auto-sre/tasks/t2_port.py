"""Task t2_port — port 8080 occupied scenario."""

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import PortGrader


TASK_ID = "t2_port"
DESCRIPTION = "Port 8080 is occupied by a rogue process. The app cannot bind to it."
MAX_STEPS = 10


def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    """Create the broken baseline state for this task."""
    fs = MockFilesystem()

    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="auto-sre-host"),
        "/var/log/syslog": MockFile(path="/var/log/syslog", content="system boot ok\n"),
    })

    import random
    rogue_pid = random.randint(300, 9999)
    target_port = 8080

    fs.set_overlay({
        "/home/user/app.js": MockFile(
            path="/home/user/app.js",
            content=f"const http = require('http');\nhttp.createServer().listen({target_port});\n",
        ),
    })

    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
        MockProcess(pid=200, command="nginx", port_bindings=[80]),
        MockProcess(pid=rogue_pid, command="rogue-server", port_bindings=[target_port]),
    ])

    global _state_hint
    _state_hint = {
        "ports": {str(target_port): rogue_pid},
        "target_port": target_port,
        "rogue_pid": rogue_pid
    }

    return fs, pm

_state_hint: dict = {}



GRADER = PortGrader()
