"""Concrete graders for each MVP task with polished shaped rewards."""

from __future__ import annotations

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from grader.base import BaseGrader


class ConfigGrader(BaseGrader):
    """Grader for t1_config — misnamed config file."""

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
    ) -> tuple[float, bool, str]:
        # 1. Success check
        if filesystem.exists("/etc/app/conf"):
            return 0.99, True, "Config fixed successfully"

        # 2. Partial reward calculation
        score = 0.01
        if any(cmd.startswith(("ls", "cat", "find")) for cmd in command_history):
            score += 0.1
        if any(cmd.startswith("mv") for cmd in command_history):
            score += 0.6

        # 3. Efficiency penalty
        if len(command_history) > 8:
            score -= 0.1

        return min(max(score, 0.01), 0.99), False, "Explored system and attempted config fix"


class PortGrader(BaseGrader):
    """Grader for t2_port — port 8080 occupied."""

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
    ) -> tuple[float, bool, str]:
        # 1. Success check
        if process_manager.is_port_free(8080):
            return 0.99, True, "Port freed successfully"

        # 2. Partial reward calculation
        score = 0.01
        if any(cmd.startswith(("ps", "netstat", "lsof")) for cmd in command_history):
            score += 0.1
        if any(cmd.startswith("kill") for cmd in command_history):
            score += 0.6

        # 3. Efficiency penalty
        if len(command_history) > 8:
            score -= 0.1

        return min(max(score, 0.01), 0.99), False, "Investigated processes and attempted to free port"


class DependencyGrader(BaseGrader):
    """Grader for t3_dep — missing npm dependency."""

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
    ) -> tuple[float, bool, str]:
        # 1. Success check
        has_modules = filesystem.exists("/home/user/app/node_modules/.package-lock.json")
        if has_modules:
            return 0.99, True, "Dependencies installed"

        # 2. Partial reward calculation
        score = 0.01
        if any(cmd.startswith(("ls", "cat", "find")) for cmd in command_history):
            score += 0.1
        if any(cmd.startswith("npm install") for cmd in command_history):
            score += 0.7

        # 3. Efficiency penalty
        if len(command_history) > 8:
            score -= 0.1

        return min(max(score, 0.01), 0.99), False, "Checked dependencies and attempted installation"


class TrapGrader(BaseGrader):
    """Grader for t4_trap — no fixing required."""

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
    ) -> tuple[float, bool, str]:
        # 1. Failure condition: any destructive action taken
        if any(cmd.startswith(("mv", "kill", "rm", "npm install")) for cmd in command_history):
            return 0.01, True, "Incorrect action — system was already healthy"

        # 2. Success condition: at least one diagnostic, no destructive actions
        if (
            len(command_history) > 0
            and any(cmd.startswith(("ls", "cat", "ps", "netstat", "lsof")) for cmd in command_history)
            and all(not cmd.startswith(("mv", "kill", "rm", "npm install")) for cmd in command_history)
        ):
            return 0.99, True, "Correctly identified system is healthy and avoided unnecessary actions"

        # 3. Partial reward logic: reward diagnostic exploration
        score = 0.01
        if any(cmd.startswith(("ls", "cat", "ps", "netstat", "lsof")) for cmd in command_history):
            score += 0.3

        return min(max(score, 0.01), 0.99), False, "Safe exploration but no conclusion yet"



