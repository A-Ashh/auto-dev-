from __future__ import annotations
import math
from typing import Any

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from grader.base import BaseGrader

_SCORE_MIN = 0.01
_SCORE_MAX = 0.989


def _safe_score(raw: float) -> float:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _SCORE_MIN
    score = float(raw)
    score = max(_SCORE_MIN, min(_SCORE_MAX, score))
    return score


# 🔥 Common reward template
def base_reward(command_history):
    return 0.12 - 0.01 * len(command_history)

# ---------------- CONFIG ----------------
class ConfigGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state=None):
        state = state or {}

        config_fixed = filesystem.exists("/etc/app/conf")
        app_running = state.get("services_running", {}).get("app", False)

        # 🔥 STEP PENALTY (important)
        reward = base_reward(command_history)

        # ✅ positive signals
        if config_fixed:
            reward += 0.4

        if app_running:
            reward += 0.5

        # ❌ no progress penalty
        if not config_fixed and not app_running:
            reward -= 0.02

        # ⚡ efficiency bonus
        if config_fixed and app_running and len(command_history) <= 5:
            reward += 0.05

        done = config_fixed and app_running

        return _safe_score(reward), done, "State evaluated"
# ---------------- PORT ----------------
class PortGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state=None):
        state = state or {}
        target_port = state.get("target_port", 8080)
        app_running = state.get("services_running", {}).get("app", False)
        rogue_killed = process_manager.is_port_free(target_port)

        reward = base_reward(command_history)

        if rogue_killed:
            reward += 0.40
        if app_running:
            reward += 0.50

        if not rogue_killed and not app_running:
            reward -= 0.02

        if rogue_killed and app_running and len(command_history) <= 5:
            reward += 0.05

        done = (rogue_killed and app_running)
        return _safe_score(reward), done, "State evaluated"


# ---------------- DEPENDENCY ----------------
class DependencyGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state=None):
        state = state or {}
        deps_installed = state.get("dependencies_installed", False)
        app_running = state.get("services_running", {}).get("app", False)

        reward = base_reward(command_history)

        if deps_installed:
            reward += 0.40
        if app_running:
            reward += 0.50

        if not deps_installed:
            reward -= 0.05

        if deps_installed and app_running and len(command_history) <= 6:
            reward += 0.05

        done = (deps_installed and app_running)
        return _safe_score(reward), done, "State evaluated"


# ---------------- TRAP ----------------
class TrapGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state=None):
        state = state or {}
        health = state.get("health_status", True)

        reward = base_reward(command_history)

        if health:
            reward += 0.50
        else:
            reward -= 0.20

        if len(command_history) > 3:
            reward -= 0.05

        done = (health and len(command_history) >= 2) or not health
        return _safe_score(reward), done, "State evaluated"


# ---------------- DISK ----------------
class DiskGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state=None):
        state = state or {}
        log_path = state.get("target_log", "/var/log/syslog")
        file_deleted = not filesystem.exists(log_path)
        disk_freed = state.get("disk_usage", 100) < 80

        reward = base_reward(command_history)

        if file_deleted:
            reward += 0.40
        if disk_freed:
            reward += 0.50

        if not file_deleted:
            reward -= 0.05

        if disk_freed and len(command_history) <= 5:
            reward += 0.05

        done = (file_deleted and disk_freed)
        return _safe_score(reward), done, "State evaluated"


# ---------------- OOM ----------------
class OOMGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state=None):
        state = state or {}
        target_pid = state.get("rogue_pid", 999)
        proc = process_manager.get_by_pid(target_pid)
        rogue_dead = not proc or not proc.is_alive
        mem_freed = state.get("memory_usage", 100) < 80

        reward = base_reward(command_history)

        if rogue_dead:
            reward += 0.40
        if mem_freed:
            reward += 0.50

        if not rogue_dead:
            reward -= 0.05

        if rogue_dead and mem_freed and len(command_history) <= 5:
            reward += 0.05

        done = rogue_dead
        return _safe_score(reward), done, "State evaluated"


# ---------------- CASCADE (IMPORTANT TASK) ----------------
class CascadeGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state=None):
        state = state or {}

        rogue_pid = state.get("rogue_pid", 999)
        log_path = state.get("target_log", "/var/log/syslog")

        proc = process_manager.get_by_pid(rogue_pid)
        rogue_dead = not proc or not proc.is_alive
        log_cleared = not filesystem.exists(log_path)
        db_running = state.get("services_running", {}).get("db", False)

        reward = base_reward(command_history)

        if log_cleared:
            reward += 0.30
        if rogue_dead:
            reward += 0.30
        if db_running:
            reward += 0.30

        # ❗ penalize no progress
        if not (log_cleared or rogue_dead or db_running):
            reward -= 0.03

        # ❗ bonus for efficient solution
        if log_cleared and rogue_dead and db_running and len(command_history) <= 7:
            reward += 0.05

        done = (log_cleared and rogue_dead and db_running)
        return _safe_score(reward), done, "State evaluated"
