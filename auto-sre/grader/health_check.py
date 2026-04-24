"""Concrete graders for each MVP task with STRICT state-based dense rewards.

PHASE 1 & 2 & 3: Strictly state-based, bounded (0.01, 0.989), zero command string matching.
"""
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

class ConfigGrader(BaseGrader):
    def grade(self, filesystem: MockFilesystem, process_manager: ProcessManager, command_history: list[str], state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        config_fixed = filesystem.exists("/etc/app/conf")
        app_running = state.get("services_running", {}).get("app", False)
        
        reward = 0.01
        
        if config_fixed:
            reward += 0.40
        if app_running:
            reward += 0.50
        if config_fixed and app_running and len(command_history) <= 5:
            reward += 0.05
        if not config_fixed and not app_running:
            reward -= 0.00
            
        done = (config_fixed and app_running)
        return _safe_score(reward), done, "State evaluated"

class PortGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        target_port = state.get("target_port", 8080)
        app_running = state.get("services_running", {}).get("app", False)
        rogue_killed = process_manager.is_port_free(target_port)
        
        reward = 0.01
        if rogue_killed:
            reward += 0.40
        if app_running:
            reward += 0.50
        if rogue_killed and app_running and len(command_history) <= 5:
            reward += 0.05
            
        done = (rogue_killed and app_running)
        return _safe_score(reward), done, "State evaluated"

class DependencyGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        deps_installed = state.get("dependencies_installed", False)
        app_running = state.get("services_running", {}).get("app", False)
        
        reward = 0.01
        if deps_installed:
            reward += 0.40
        if app_running:
            reward += 0.50
        if deps_installed and app_running and len(command_history) <= 6:
            reward += 0.05
            
        done = (deps_installed and app_running)
        return _safe_score(reward), done, "State evaluated"

class TrapGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        health = state.get("health_status", True)
        
        reward = 0.01
        if health:
            reward += 0.50
        if len(command_history) > 0 and health:
            reward += 0.40
        if not health:
            reward -= 0.50
            
        done = (len(command_history) >= 2 and health) or not health
        return _safe_score(reward), done, "State evaluated"

class DiskGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        log_path = state.get("target_log", "/var/log/syslog")
        file_deleted = not filesystem.exists(log_path)
        disk_freed = state.get("disk_usage", 100) < 80
        
        reward = 0.01
        if file_deleted:
            reward += 0.40
        if disk_freed:
            reward += 0.50
        if disk_freed and len(command_history) <= 5:
            reward += 0.05
            
        done = (file_deleted and disk_freed)
        return _safe_score(reward), done, "State evaluated"

class OOMGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        target_pid = state.get("rogue_pid", 999)
        proc = process_manager.get_by_pid(target_pid)
        rogue_dead = not proc or not proc.is_alive
        mem_freed = state.get("memory_usage", 100) < 80
        
        reward = 0.01
        if rogue_dead:
            reward += 0.40
        if mem_freed:
            reward += 0.50
        if rogue_dead and mem_freed and len(command_history) <= 5:
            reward += 0.05
            
        done = rogue_dead
        return _safe_score(reward), done, "State evaluated"

class CascadeGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        rogue_pid = state.get("rogue_pid", 999)
        log_path = state.get("target_log", "/var/log/syslog")
        
        proc = process_manager.get_by_pid(rogue_pid)
        rogue_dead = not proc or not proc.is_alive
        log_cleared = not filesystem.exists(log_path)
        db_running = state.get("services_running", {}).get("db", False)
        
        reward = 0.01
        if log_cleared:
            reward += 0.30
        if rogue_dead:
            reward += 0.30
        if db_running:
            reward += 0.30
        if log_cleared and rogue_dead and db_running and len(command_history) <= 7:
            reward += 0.05
            
        done = (log_cleared and rogue_dead and db_running)
        return _safe_score(reward), done, "State evaluated"

class MemLeakGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        rogue_pid = state.get("rogue_pid", 999)
        proc = process_manager.get_by_pid(rogue_pid)
        rogue_dead = not proc or not proc.is_alive
        daemon_up = state.get("services_running", {}).get("leak-daemon", False)
        
        reward = 0.01
        if rogue_dead:
            reward += 0.45
        if daemon_up:
            reward += 0.45
        if rogue_dead and daemon_up and len(command_history) <= 6:
            reward += 0.05
            
        done = (rogue_dead and daemon_up)
        return _safe_score(reward), done, "State evaluated"

class DepChainGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        svcs = state.get("services_running", {})
        db_up = svcs.get("db", False)
        cache_up = svcs.get("cache", False)
        app_up = svcs.get("app", False)
        
        reward = 0.01
        if db_up:
            reward += 0.30
        if cache_up:
            reward += 0.30
        if app_up:
            reward += 0.30
        if db_up and cache_up and app_up and len(command_history) <= 8:
            reward += 0.05
            
        done = (db_up and cache_up and app_up)
        return _safe_score(reward), done, "State evaluated"

class SecretGrader(BaseGrader):
    def grade(self, filesystem, process_manager, command_history, state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        secret_file = state.get("secret_file", "/etc/app/secrets.conf")
        app_up = state.get("services_running", {}).get("app", False)
        
        try:
            content = filesystem.read(secret_file)
            secret_fixed = "WRONG_SECRET_XYZ" not in content and len(content.strip()) > 0
        except Exception:
            secret_fixed = False
            
        reward = 0.01
        if secret_fixed:
            reward += 0.45
        if app_up:
            reward += 0.45
        if secret_fixed and app_up and len(command_history) <= 6:
            reward += 0.05
            
        done = (secret_fixed and app_up)
        return _safe_score(reward), done, "State evaluated"
