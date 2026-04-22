"""Task t3_dep — missing npm dependency scenario."""

from engine.filesystem import MockFile, MockFilesystem
from engine.process_manager import MockProcess, ProcessManager
from grader.health_check import DependencyGrader


TASK_ID = "t3_dep"
DESCRIPTION = "The app fails to start because the 'dotenv' package is missing. Run npm install."
MAX_STEPS = 15


def build_initial_state() -> tuple[MockFilesystem, ProcessManager]:
    """Create the broken baseline state for this task."""
    fs = MockFilesystem()

    fs.set_base({
        "/etc/hostname": MockFile(path="/etc/hostname", content="auto-sre-host"),
        "/var/log/syslog": MockFile(path="/var/log/syslog", content="system boot ok\n"),
    })

    fs.set_overlay({
        "/home/user/app/package.json": MockFile(
            path="/home/user/app/package.json",
            content='{"name":"myapp","dependencies":{"dotenv":"^16.0.0","express":"^4.18.0"}}',
        ),
        "/home/user/app/app.js": MockFile(
            path="/home/user/app/app.js",
            content="require('dotenv').config();\nconst express = require('express');\n"
                    "const app = express();\napp.listen(3000);\n",
        ),
        "/home/user/app/README.md": MockFile(
            path="/home/user/app/README.md",
            content="# MyApp\n\nInstall deps: `npm install`\nRun: `node app.js`\n",
        ),
    })

    pm = ProcessManager()
    pm.load([
        MockProcess(pid=1, command="init", port_bindings=[]),
    ])

    return fs, pm

_state_hint: dict = {
    "dependencies_installed": False,
    "services_running": {"app": False}
}


GRADER = DependencyGrader()
