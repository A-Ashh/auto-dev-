"""Concrete graders for each MVP task with dense, dynamic reward accumulation.

PHASE 1: Multi-step trajectories with intermediate rewards.
PHASE 2: State-dict awareness (disk_usage, memory_usage, services_running, ports).
PHASE 3: CascadeGrader for t7_cascading_meltdown.

STRICT MATH RULE:
  - Use dynamic accumulation: total_reward += step_reward
  - Pass final score through _safe_score() — never 0.0 or 1.0.
"""

from __future__ import annotations

import math
from typing import Any

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from grader.base import BaseGrader

# --- Safe score clamp: strictly in open interval (0, 1) ---
_SCORE_MIN = 0.01
_SCORE_MAX = 0.989


def _safe_score(raw: float) -> float:
    """Clamp a raw score to the open interval (0, 1).
    Handles None, NaN, negative, and out-of-range values.
    """
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _SCORE_MIN
    score = float(raw)
    score = max(_SCORE_MIN, min(_SCORE_MAX, score))
    assert 0 < score < 1, f"Score out of range: {score}"
    return score


class ConfigGrader(BaseGrader):
    """Grader for t1_config — misnamed config file.

    Multi-step trajectory:
      Step 1 (+0.15): Diagnose — run ls/cat/find to discover conf.bak
      Step 2 (+0.35): Attempt rename — run mv command
      Step 3 (+0.35): Verify service — run systemctl restart app OR confirm file exists
      Success: /etc/app/conf exists → done=True
    """

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        state = state or {}

        config_fixed = filesystem.exists("/etc/app/conf")
        app_running = state.get("services_running", {}).get("app", False)

        # Final success condition
        if config_fixed and app_running:
            return _safe_score(0.97), True, "Config fixed and service restored"

        # Dynamic reward accumulation across milestones
        total_reward = 0.0

        # Milestone 1: Exploration/diagnosis (ls, cat, find)
        if any(cmd.startswith(("ls", "cat", "find")) for cmd in command_history):
            total_reward += 0.10

        # Milestone 2: Attempted rename with mv
        if any(cmd.startswith("mv") for cmd in command_history):
            total_reward += 0.25

        # Milestone 3: Config fixed
        if config_fixed:
            total_reward += 0.20

        # Milestone 4: Restart service
        if any("systemctl restart" in cmd or "systemctl start" in cmd for cmd in command_history):
            if app_running:
                total_reward += 0.20
            else:
                total_reward += 0.05  # Attempted but failed

        # Efficiency bonus: solved in <=5 commands
        if len(command_history) <= 5 and total_reward > 0.3:
            total_reward += 0.05

        # Penalty for excessive commands
        if len(command_history) > 10:
            total_reward -= 0.08

        return _safe_score(total_reward), False, "Partial progress on config fix"


class PortGrader(BaseGrader):
    """Grader for t2_port — port occupied.

    Multi-step trajectory:
      Step 1 (+0.15): Diagnose — netstat/lsof/ps to find port binding
      Step 2 (+0.15): Identify PID — check which process owns the port
      Step 3 (+0.40): Kill rogue process
      Step 4 (+0.20): Verify port free (state.ports updated)
      Success: target port is free → done=True
    """

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        state = state or {}
        target_port = state.get("target_port", 8080)

        app_running = state.get("services_running", {}).get("app", False)
        rogue_killed = process_manager.is_port_free(target_port)

        # Final success condition
        if rogue_killed and app_running:
            return _safe_score(0.97), True, f"Port {target_port} freed and app restarted successfully"

        total_reward = 0.0

        # Milestone 1: Diagnose with network tools
        if any(cmd.startswith(("netstat", "lsof", "ss")) for cmd in command_history):
            total_reward += 0.10

        # Milestone 2: Inspect with ps
        if any(cmd.startswith("ps") for cmd in command_history):
            total_reward += 0.10

        # Milestone 3: Kill attempt
        if any(cmd.startswith("kill") for cmd in command_history):
            if rogue_killed:
                total_reward += 0.40
            else:
                total_reward += 0.05

        # Milestone 4: State reflects freed port
        ports = state.get("ports", {})
        if str(target_port) not in ports or rogue_killed:
            total_reward += 0.15

        # Milestone 5: Restart service attempt
        if any("systemctl restart" in cmd or "systemctl start" in cmd for cmd in command_history):
            total_reward += 0.05


        # Penalty for excessive commands
        if len(command_history) > 10:
            total_reward -= 0.08

        return _safe_score(total_reward), False, "Investigated port, partial progress"


class DependencyGrader(BaseGrader):
    """Grader for t3_dep missing npm dependency.

    Multi-step trajectory:
      Step 1 (+0.10): Navigate to app dir (cd)
      Step 2 (+0.15): Inspect package.json (cat)
      Step 3 (+0.15): Verify error (node app.js)
      Step 4 (+0.45): Install deps (npm install)
      Step 5 (+0.10): Verify app starts (node app.js again)
      Success: node_modules exists → done=True
    """

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        state = state or {}
        has_modules = filesystem.exists("/home/user/app/node_modules/.package-lock.json")
        app_running = state.get("services_running", {}).get("app", False)

        # Final success condition
        if has_modules and app_running:
            return _safe_score(0.97), True, "Dependencies installed and app restarted successfully"

        total_reward = 0.0

        # Milestone 1: Navigate to app directory
        if any("cd" in cmd and "app" in cmd for cmd in command_history):
            total_reward += 0.08

        # Milestone 2: Read package.json
        if any("cat" in cmd and "package.json" in cmd for cmd in command_history):
            total_reward += 0.10

        # Milestone 3: Tried running node (discovering the error)
        if any(cmd.startswith("node") for cmd in command_history):
            total_reward += 0.15

        # Milestone 4: npm install attempted
        if any("npm install" in cmd for cmd in command_history):
            total_reward += 0.45

        # Penalty for excessive commands
        if len(command_history) > 12:
            total_reward -= 0.08

        return _safe_score(total_reward), False, "Partial dependency resolution"


class TrapGrader(BaseGrader):
    """Grader for t4_trap — no fixing required.

    Multi-step trajectory (Reasoning task):
      Step 1 (+0.15): Check config exists (cat /etc/app/conf)
      Step 2 (+0.15): Check processes are healthy (ps)
      Step 3 (+0.20): Check ports (netstat/lsof)
      Step 4 (+0.30): Correctly abstain — no destructive actions
      Failure: any mv/kill/rm/npm install taken → partial reward, done=True
    """

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        state = state or {}

        # Safe diagnostic commands — never penalized, never destructive
        SAFE_COMMANDS = ("ls", "cat", "ps", "netstat", "lsof", "find", "grep", "df", "free", "top", "ss", "pwd", "cd", "echo", "head", "tail", "stat", "du")

        # Strictly destructive commands — only these can end episode with failure
        DESTRUCTIVE_CMDS = ("kill", "rm", "mv", "npm install", "systemctl stop", "systemctl kill")

        def is_destructive(cmd: str) -> bool:
            stripped = cmd.strip()
            # Whitelist takes priority
            if any(stripped.startswith(s) for s in SAFE_COMMANDS):
                return False
            return any(stripped.startswith(d) for d in DESTRUCTIVE_CMDS)

        # Failure condition: destructive action taken on an already-healthy system
        if any(is_destructive(cmd) for cmd in command_history):
            state["health_status"] = False
            return _safe_score(0.05), True, "Incorrect action system was already healthy"

        # Success: diagnosed thoroughly and abstained correctly
        diagnostic_cmds = ("ls", "cat", "ps", "netstat", "lsof", "find", "grep", "df")
        diagnostic_count = sum(
            1 for cmd in command_history
            if any(cmd.startswith(d) for d in diagnostic_cmds)
        )

        if diagnostic_count >= 3:
            return _safe_score(0.97), True, "Correctly identified healthy system and abstained"

        # Dynamic partial rewards for exploration
        total_reward = 0.0

        if any("cat" in cmd and "conf" in cmd for cmd in command_history):
            total_reward += 0.15
        if any(cmd.startswith("ps") for cmd in command_history):
            total_reward += 0.15
        if any(cmd.startswith(("netstat", "lsof", "ss")) for cmd in command_history):
            total_reward += 0.20
        if any(cmd.startswith(("ls", "find")) for cmd in command_history):
            total_reward += 0.10

        return _safe_score(max(total_reward, 0.02)), False, "Diagnosing system, no conclusion yet"


class DiskGrader(BaseGrader):
    """Grader for t5_disk_full — massive log file.

    Multi-step trajectory:
      Step 1 (+0.15): Run df -h to detect disk full
      Step 2 (+0.15): Run du / find to identify large file
      Step 3 (+0.45): Delete the large log file
      Step 4 (+0.15): Verify disk free (state.disk_usage updated)
      Success: /var/log/syslog gone → done=True
    """

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        state = state or {}
        log_path = state.get("target_log", "/var/log/syslog")

        # Final success condition: file deleted AND disk freed
        file_deleted = not filesystem.exists(log_path)
        disk_freed = state.get("disk_usage", 100) < 80
        if file_deleted and disk_freed:
            return _safe_score(0.97), True, "Disk cleared - large log file deleted"
        if file_deleted and not disk_freed:
            return _safe_score(0.97), True, "Disk cleared - large log file deleted"

        total_reward = 0.0

        # Milestone 1: Detect disk full
        if any(cmd.startswith(("df", "du")) for cmd in command_history):
            total_reward += 0.15

        # Milestone 2: Find the culprit
        if any(cmd.startswith(("find", "ls")) for cmd in command_history):
            total_reward += 0.15

        # Milestone 3: rm attempted — ONLY reward if file is actually gone
        rm_attempted = any(cmd.startswith("rm") for cmd in command_history)
        if rm_attempted and file_deleted:
            # Successful rm
            total_reward += 0.45
        elif rm_attempted and not file_deleted:
            # rm ran but target file still exists — wrong file or failed
            total_reward += 0.03

        # Milestone 4: State awareness — disk_usage reduced
        if disk_freed:
            total_reward += 0.15

        # Penalty for excessive commands
        if len(command_history) > 10:
            total_reward -= 0.08

        return _safe_score(total_reward), False, "Investigating disk usage, partial progress"


class OOMGrader(BaseGrader):
    """Grader for t6_oom_killer — rogue memory hog process.

    Multi-step trajectory:
      Step 1 (+0.15): Run ps/top/free to detect memory issue
      Step 2 (+0.15): Identify the rogue PID
      Step 3 (+0.45): Kill the rogue process
      Step 4 (+0.15): Verify memory recovered (state.memory_usage updated)
      Success: rogue PID dead → done=True
    """

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        state = state or {}
        target_pid = state.get("rogue_pid", 999)

        proc = process_manager.get_by_pid(target_pid)
        rogue_dead = not proc or not proc.is_alive

        # Final success condition: rogue process killed and memory recovered
        if rogue_dead:
            return _safe_score(0.97), True, "Rogue memory hog killed successfully"

        total_reward = 0.0

        # Milestone 1: Detect memory issue
        if any(cmd.startswith(("ps", "top", "free")) for cmd in command_history):
            total_reward += 0.15

        # Milestone 2: List processes to identify rogue PID
        if any("ps" in cmd and ("aux" in cmd or "-e" in cmd) for cmd in command_history):
            total_reward += 0.15

        # Milestone 3: Kill attempt — ONLY reward if rogue process is actually dead
        kill_attempts = [cmd for cmd in command_history if cmd.startswith("kill")]
        if kill_attempts and rogue_dead:
            total_reward += 0.45   # correct kill only

        # Milestone 4: State awareness — memory_usage reduced
        if state.get("memory_usage", 99) < 50:
            total_reward += 0.15

        # Penalty for excessive commands
        if len(command_history) > 10:
            total_reward -= 0.08

        return _safe_score(total_reward), False, "Investigating memory, partial progress"


class CascadeGrader(BaseGrader):
    """Grader for t7_cascading_meltdown — enterprise cascade scenario.

    Four-step cascade trajectory:
      Step 1 (+0.15): Run df -h to detect disk full
      Step 2 (+0.25): Clear logs (rm /var/log/syslog or truncate)
      Step 3 (+0.25): Kill rogue logger process (PID stored in state.rogue_pid)
      Step 4 (+0.25): Restart DB service (systemctl restart db)
      Success: all four conditions met → done=True

    All rewards accumulated dynamically and passed through _safe_score().
    """

    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        state = state or {}
        rogue_pid = state.get("rogue_pid", 999)
        log_path = state.get("target_log", "/var/log/syslog")

        proc = process_manager.get_by_pid(rogue_pid)
        rogue_dead = not proc or not proc.is_alive
        log_cleared = not filesystem.exists(log_path)
        db_running = state.get("services_running", {}).get("db", False)
        diagnosed_disk = any(cmd.startswith("df") for cmd in command_history)

        # Full success: all four steps completed
        if diagnosed_disk and log_cleared and rogue_dead and db_running:
            return _safe_score(0.97), True, "CASCADE RESOLVED - disk cleared, rogue killed, DB restored"

        # Dynamic accumulation
        total_reward = 0.0

        # Step 1: Diagnosed disk issue with df
        if diagnosed_disk:
            total_reward += 0.15

        # Step 2: Cleared the log file
        if log_cleared:
            total_reward += 0.25

        # Step 3: Killed rogue process
        if rogue_dead:
            total_reward += 0.25

        # Step 4: Restarted DB
        if db_running:
            total_reward += 0.25

        # Efficiency bonus: solved in <=6 commands
        if all([log_cleared, rogue_dead, db_running]) and len(command_history) <= 6:
            total_reward += 0.05

        # Penalty for excessive commands
        if len(command_history) > 15:
            total_reward -= 0.08

        steps_done = sum([diagnosed_disk, log_cleared, rogue_dead, db_running])
        msg = f"Cascade: {steps_done}/4 steps complete"
        return _safe_score(total_reward), False, msg


class MemLeakGrader(BaseGrader):
    """t8_memory_leak_loop — crash-restart loop due to memory leak.

    Step 1 (+0.15): free/top → detect high memory
    Step 2 (+0.15): ps aux → identify leaking PID
    Step 3 (+0.35): kill <rogue_pid> → stop crash loop
    Step 4 (+0.25): systemctl restart leak-daemon → restore service
    Success: rogue dead AND leak-daemon running → done=True
    """

    def grade(self, filesystem, process_manager, command_history,
              state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        rogue_pid = state.get("rogue_pid", 999)
        proc = process_manager.get_by_pid(rogue_pid)
        rogue_dead = not proc or not proc.is_alive
        daemon_up = state.get("services_running", {}).get("leak-daemon", False)

        if rogue_dead and daemon_up:
            return _safe_score(0.97), True, "Memory leak resolved - service restored"

        total = 0.0
        if any(cmd.startswith(("free", "top")) for cmd in command_history):
            total += 0.15
        if any(cmd.startswith("ps") for cmd in command_history):
            total += 0.15
        if any(cmd.startswith("kill") for cmd in command_history):
            total += 0.35
        if rogue_dead:
            total += 0.10
        if any("systemctl restart leak-daemon" in cmd for cmd in command_history):
            total += 0.20
        if len(command_history) > 12:
            total -= 0.08

        steps = sum([
            any(cmd.startswith(("free", "top")) for cmd in command_history),
            any(cmd.startswith("ps") for cmd in command_history),
            rogue_dead,
            daemon_up,
        ])
        return _safe_score(total), False, f"MemLeak: {steps}/4 steps complete"


class DepChainGrader(BaseGrader):
    """t9_dependency_chain_failure — cascading service restart in correct order.

    Step 1 (+0.10): systemctl status app → detect failure
    Step 2 (+0.15): cat log → trace to db
    Step 3 (+0.25): systemctl restart db
    Step 4 (+0.25): systemctl restart cache
    Step 5 (+0.20): systemctl restart app
    Success: db + cache + app all running → done=True
    """

    def grade(self, filesystem, process_manager, command_history,
              state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        svcs = state.get("services_running", {})
        db_up = svcs.get("db", False)
        cache_up = svcs.get("cache", False)
        app_up = svcs.get("app", False)

        if db_up and cache_up and app_up:
            return _safe_score(0.97), True, "Dependency chain restored - all services up"

        total = 0.0
        if any("status" in cmd and "app" in cmd for cmd in command_history):
            total += 0.10
        if any("cat" in cmd and "log" in cmd for cmd in command_history):
            total += 0.15
        if db_up:
            total += 0.25
        if cache_up:
            total += 0.25
        if any("systemctl restart app" in cmd for cmd in command_history):
            total += 0.15
        if len(command_history) > 15:
            total -= 0.08

        # Penalize wrong order: restarting cache before db
        history_str = " ".join(command_history)
        cache_pos = history_str.find("restart cache")
        db_pos = history_str.find("restart db")
        if cache_pos != -1 and db_pos != -1 and cache_pos < db_pos:
            total -= 0.15  # out-of-order penalty

        steps = sum([db_up, cache_up, app_up])
        return _safe_score(total), False, f"DepChain: {steps}/3 services up"


class SecretGrader(BaseGrader):
    """t10_config_secret_failure — bad secret in config brings app down.

    Step 1 (+0.10): systemctl status app → detect failure
    Step 2 (+0.15): cat /var/log/app.log → find auth error
    Step 3 (+0.15): cat /etc/app/secrets.conf → inspect bad value
    Step 4 (+0.35): echo ... > /etc/app/secrets.conf → write correct secret
    Step 5 (+0.20): systemctl restart app → restore service
    Success: app running AND config_valid → done=True
    """

    def grade(self, filesystem, process_manager, command_history,
              state: dict[str, Any] | None = None) -> tuple[float, bool, str]:
        state = state or {}
        secret_file = state.get("secret_file", "/etc/app/secrets.conf")
        app_up = state.get("services_running", {}).get("app", False)

        # Check if secret file was overwritten with a non-WRONG value
        try:
            content = filesystem.read(secret_file)
            secret_fixed = "WRONG_SECRET_XYZ" not in content and len(content.strip()) > 0
        except Exception:
            secret_fixed = False

        if secret_fixed and app_up:
            return _safe_score(0.97), True, "Secret fixed and app restored"

        total = 0.0
        if any("status" in cmd and "app" in cmd for cmd in command_history):
            total += 0.10
        if any("cat" in cmd and "log" in cmd for cmd in command_history):
            total += 0.15
        if any("cat" in cmd and "secrets" in cmd for cmd in command_history):
            total += 0.15
        if any("echo" in cmd and "secrets" in cmd for cmd in command_history):
            total += 0.30
        if secret_fixed:
            total += 0.10
        if any("systemctl restart app" in cmd for cmd in command_history):
            total += 0.15
        if len(command_history) > 12:
            total -= 0.08

        steps = sum([secret_fixed, app_up])
        return _safe_score(total), False, f"SecretFix: {steps}/2 conditions met"

