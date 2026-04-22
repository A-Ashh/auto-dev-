"""Sandbox engine — parses and executes mock shell commands.

PHASE 2: Stateful World Model.
  self.state tracks disk_usage, memory_usage, ports, config_valid,
  services_running. All command handlers update state as safe mocks.
"""

from __future__ import annotations

import shlex
from dataclasses import dataclass, field
from typing import Any

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from engine.security import (
    CommandNotAllowedError,
    StepTimeoutError,
    validate_command,
    with_timeout,
    STEP_TIMEOUT_SECONDS,
)


@dataclass
class CommandResult:
    """Result of executing a command in the sandbox."""

    stdout: str = ""
    stderr: str = ""
    success: bool = True


class Sandbox:
    """
    Mock shell that intercepts agent commands and applies them
    against the in-memory filesystem, process manager, and world state.

    PHASE 2 ADDITION: self.state is a world-model dict updated by every command.
    Graders read self.state to evaluate system health.
    """

    def __init__(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        initial_state: dict[str, Any] | None = None,
    ) -> None:
        self.fs = filesystem
        self.pm = process_manager
        self.cwd: str = "/home/user"
        self.command_history: list[str] = []

        # ── World Model State (Phase 2) ──────────────────────────────
        self.state: dict[str, Any] = {
            "disk_usage": 100,          # % — starts at 100 for disk tasks
            "memory_usage": 20,         # %
            "ports": {},                # {port_str: pid}
            "services_running": {},     # {service_name: bool}
            "rogue_pid": None,          # set by task build_initial_state
            "target_log": "/var/log/syslog",
            "target_port": 8080,
        }
        if initial_state:
            self.state.update(initial_state)

    # ── Public API ──────────────────────────────────────────────────

    @with_timeout(STEP_TIMEOUT_SECONDS)
    def execute(self, raw_command: str) -> CommandResult:
        """Validate and execute a shell command, returning stdout/stderr."""
        validated = validate_command(raw_command)
        self.command_history.append(validated)

        import os
        parts = shlex.split(validated)
        base = os.path.basename(parts[0])
        args = list(parts[1:])

        # Handle output redirection: cmd > /path  or  cmd >> /path
        redirect_append = False
        redirect_path = None
        if ">>" in args:
            idx = args.index(">>")
            redirect_path = self._resolve(args[idx + 1]) if idx + 1 < len(args) else None
            args = args[:idx]
            redirect_append = True
        elif ">" in args:
            idx = args.index(">")
            redirect_path = self._resolve(args[idx + 1]) if idx + 1 < len(args) else None
            args = args[:idx]

        handler = self._HANDLERS.get(base)
        if handler is None:
            return CommandResult(stderr=f"Command '{base}' is recognized but has no handler yet.")
        result = handler(self, args)

        # Write stdout to file if redirected
        if redirect_path and result.stdout is not None:
            existing = ""
            if redirect_append:
                try:
                    existing = self.fs.read(redirect_path)
                except FileNotFoundError:
                    existing = ""
            self.fs.write(redirect_path, existing + result.stdout + "\n")
            # Update config_valid if writing to secrets/conf file
            if "secret" in redirect_path or redirect_path.endswith("/conf"):
                self.state["config_valid"] = True
            return CommandResult(stdout=f"Written to {redirect_path}", stderr=result.stderr, success=result.success)

        return result

    def reset(self) -> None:
        """Clear command history and reset cwd."""
        self.command_history.clear()
        self.cwd = "/home/user"

    # ── Command handlers ────────────────────────────────────────────

    def _cmd_ls(self, args: list[str]) -> CommandResult:
        import os

        # Separate flags from paths
        paths = [a for a in args if not a.startswith("-")]
        target = paths[0] if paths else self.cwd
        target = self._resolve(target)

        try:
            all_paths = self.fs.get_all_paths()

            prefix = target.rstrip("/") + "/"
            children = set()
            for p in all_paths:
                if p.startswith(prefix):
                    rel_path = p[len(prefix):]
                    if rel_path:
                        children.add(rel_path.split("/")[0])

            if not children:
                return CommandResult(stdout="total 0")

            return CommandResult(stdout="\n".join(sorted(children)))

        except Exception as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_cat(self, args: list[str]) -> CommandResult:
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            return CommandResult(stderr="cat: missing operand", success=False)
        path = self._resolve(paths[-1])
        try:
            content = self.fs.read(path)
            return CommandResult(stdout=content)
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_grep(self, args: list[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(stderr="grep: missing arguments", success=False)
        pattern, path = args[0], self._resolve(args[1])
        try:
            content = self.fs.read(path)
            matches = [line for line in content.splitlines() if pattern in line]
            return CommandResult(stdout="\n".join(matches))
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_pwd(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.cwd)

    def _cmd_cd(self, args: list[str]) -> CommandResult:
        target = args[0] if args else "/home/user"
        self.cwd = self._resolve(target)
        return CommandResult(stdout=f"cd: changed to {self.cwd}")

    def _cmd_mv(self, args: list[str]) -> CommandResult:
        if len(args) < 2:
            return CommandResult(stderr="mv: missing operand", success=False)
        src, dst = self._resolve(args[0]), self._resolve(args[1])
        try:
            self.fs.rename(src, dst)
            # State update: if renamed to /etc/app/conf, mark config valid
            if dst == "/etc/app/conf":
                self.state["config_valid"] = True
            return CommandResult(stdout=f"mv: moved '{src}' to '{dst}'")
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_rm(self, args: list[str]) -> CommandResult:
        # Strip flags like -rf
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            return CommandResult(stderr="rm: missing operand", success=False)
        for p in paths:
            resolved = self._resolve(p)
            try:
                # State update: if removing a log file, free disk space
                if resolved == self.state.get("target_log", "/var/log/syslog"):
                    self.state["disk_usage"] = max(5, self.state.get("disk_usage", 100) - 85)
                self.fs.delete(resolved)
            except FileNotFoundError as e:
                return CommandResult(stderr=str(e), success=False)
        return CommandResult(stdout="rm: deleted targets")

    def _cmd_touch(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stderr="touch: missing operand", success=False)
        path = self._resolve(args[0])
        if not self.fs.exists(path):
            self.fs.write(path, "")
        return CommandResult(stdout=f"touch: created/updated {path}")

    def _cmd_mkdir(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout="mkdir: directory created")

    def _cmd_echo(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=" ".join(args))

    def _cmd_ps(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.pm.ps_output())

    def _cmd_kill(self, args: list[str]) -> CommandResult:
        pids: list[int] = []
        for a in args:
            if a.startswith("-"):
                continue
            try:
                pids.append(int(a))
            except ValueError:
                return CommandResult(stderr=f"kill: invalid PID '{a}'", success=False)
        if not pids:
            return CommandResult(stderr="kill: missing PID", success=False)
        for pid in pids:
            if not self.pm.kill(pid):
                return CommandResult(stderr=f"kill: process {pid} not found", success=False)
            # State update: if rogue PID killed, reduce memory usage
            if pid == self.state.get("rogue_pid"):
                self.state["memory_usage"] = max(5, self.state.get("memory_usage", 99) - 75)
            # State update: remove port bindings from state
            proc = self.pm.get_by_pid(pid)
            if proc:
                for port in proc.port_bindings:
                    self.state["ports"].pop(str(port), None)
        return CommandResult(stdout="kill: signal sent")

    def _cmd_systemctl(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stderr="systemctl: missing argument", success=False)
        action = args[0]
        service = args[1] if len(args) > 1 else "unknown"

        if action == "status":
            # Check state for service health
            running = self.state["services_running"].get(service, True)
            status = "active (running)" if running else "failed"
            return CommandResult(stdout=f"● {service}.service - {status}")

        if action in ("start", "restart"):
            # If disk is full, DB cannot start
            if service == "db":
                if self.state.get("disk_usage", 0) >= 100:
                    self.state["services_running"][service] = False
                    return CommandResult(stderr=f"Job for {service}.service failed because the disk is full.", success=False)
                
                rogue_pid = self.state.get("rogue_pid")
                if rogue_pid:
                    proc = self.pm.get_by_pid(rogue_pid)
                    if proc and proc.is_alive:
                        self.state["services_running"][service] = False
                        return CommandResult(stderr=f"Job for {service}.service failed because rogue process is still active.", success=False)
            
            if service in ("app", "app.service"):
                if "config_valid" in self.state and not self.state["config_valid"]:
                    self.state["services_running"][service] = False
                    return CommandResult(stderr=f"Job for {service}.service failed because config is missing or invalid.", success=False)
                
                if "dependencies_installed" in self.state and not self.state["dependencies_installed"]:
                    self.state["services_running"][service] = False
                    return CommandResult(stderr=f"Job for {service}.service failed. Missing dependency: dotenv", success=False)
                
                target_port = self.state.get("target_port", 8080)
                if not self.pm.is_port_free(target_port):
                    self.state["services_running"][service] = False
                    return CommandResult(stderr=f"Job for {service}.service failed. Address already in use (port {target_port}).", success=False)
            
            # State update: mark service as running
            self.state["services_running"][service] = True
            if service in ("app", "app.service"):
                return CommandResult(stdout=f"{service} started successfully.")
            return CommandResult(stdout=f"{service} started.")

        if action == "stop":
            self.state["services_running"][service] = False
            return CommandResult(stdout=f"{service} stopped.")

        return CommandResult(stdout=f"systemctl {action} {service}: done")

    def _cmd_npm(self, args: list[str]) -> CommandResult:
        if args and args[0] == "install":
            self.fs.write(self._resolve("node_modules/.package-lock.json"), "{}")
            self.state["dependencies_installed"] = True
            return CommandResult(stdout="added 42 packages in 3s")
        return CommandResult(stdout="npm: ok")

    def _cmd_pip(self, args: list[str]) -> CommandResult:
        if len(args) > 1 and args[0] == "install":
            args.pop(0)
            return CommandResult(stdout="Successfully installed " + " ".join(args))
        return CommandResult(stdout="pip: ok")

    def _cmd_find(self, args: list[str]) -> CommandResult:
        root = self._resolve(args[0]) if args else self.cwd
        all_paths = self.fs.get_all_paths()
        matches = [p for p in all_paths if p.startswith(root)]
        return CommandResult(stdout="\n".join(matches))

    def _cmd_head(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stderr="head: missing operand", success=False)
        path = self._resolve(args[-1])
        try:
            content = self.fs.read(path)
            lines = content.splitlines()[:10]
            return CommandResult(stdout="\n".join(lines))
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_tail(self, args: list[str]) -> CommandResult:
        paths = [a for a in args if not a.startswith("-")]
        if not paths:
            return CommandResult(stderr="tail: missing operand", success=False)
        path = self._resolve(paths[-1])
        try:
            content = self.fs.read(path)
            lines = content.splitlines()[-10:]
            return CommandResult(stdout="\n".join(lines))
        except FileNotFoundError as e:
            return CommandResult(stderr=str(e), success=False)

    def _cmd_netstat(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.pm.netstat_output())

    def _cmd_lsof(self, args: list[str]) -> CommandResult:
        return CommandResult(stdout=self.pm.netstat_output())

    def _cmd_df(self, args: list[str]) -> CommandResult:
        """Mock df -h — reports current disk state from world model."""
        disk_usage = self.state.get("disk_usage", 20)
        total_gb = 50
        used_gb = int(total_gb * disk_usage / 100)
        avail_gb = total_gb - used_gb
        output = (
            f"Filesystem      Size  Used Avail Use% Mounted on\n"
            f"/dev/sda1        {total_gb}G   {used_gb}G   {avail_gb}G  {disk_usage}% /"
        )
        return CommandResult(stdout=output)

    def _cmd_du(self, args: list[str]) -> CommandResult:
        """Mock du — list file sizes for given path."""
        paths = [a for a in args if not a.startswith("-")]
        target = paths[0] if paths else self.cwd
        resolved = self._resolve(target)
        all_paths = self.fs.get_all_paths()
        matches = [p for p in all_paths if p.startswith(resolved)]
        lines = [f"1.2G\t{p}" for p in matches]
        if not lines:
            lines = [f"4.0K\t{resolved}"]
        return CommandResult(stdout="\n".join(lines))

    def _cmd_free(self, args: list[str]) -> CommandResult:
        """Mock free -h — reports current memory state from world model."""
        mem_pct = self.state.get("memory_usage", 20)
        total_mb = 8192
        used_mb = int(total_mb * mem_pct / 100)
        free_mb = total_mb - used_mb
        output = (
            f"              total        used        free      shared  buff/cache   available\n"
            f"Mem:           {total_mb}M      {used_mb}M       {free_mb}M       12M      512M      {free_mb}M\n"
            f"Swap:          2048M         0M      2048M"
        )
        return CommandResult(stdout=output)

    def _cmd_top(self, args: list[str]) -> CommandResult:
        """Mock top — shows memory-hungry processes."""
        lines = [
            "top - 09:01:01 up 1 day,  1:23,  1 user,  load average: 4.56, 4.61, 4.72",
            "Tasks: 120 total,   2 running, 118 sleeping,   0 stopped,   0 zombie",
            "Mem:   8192MB total,   7900MB used,    292MB free",
            "",
            "  PID USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND",
        ]
        for p in self.pm.list_alive():
            mem_pct = 95.0 if p.pid == self.state.get("rogue_pid") else 0.2
            lines.append(f"{p.pid:>5} app       20   0  100000  50000   1000 S  5.0 {mem_pct:.1f}   0:15.00 {p.command.split()[0]}")
        return CommandResult(stdout="\n".join(lines))

    def _cmd_node(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(stdout="", stderr="Usage: node [options] [ script.js ] [arguments]", success=False)
        if args[0] == "app.js":
            has_deps = self.fs.exists("/home/user/app/node_modules/.package-lock.json")
            if not has_deps:
                trace = (
                    "internal/modules/cjs/loader.js:902\n"
                    "  throw err;\n"
                    "  ^\n\n"
                    "Error: Cannot find module 'dotenv'\n"
                    "Require stack:\n"
                    "- /home/user/app/app.js\n"
                    "    at Function.Module._resolveFilename (internal/modules/cjs/loader.js:902:15)\n"
                    "    at Function.Module._load (internal/modules/cjs/loader.js:746:27)\n"
                    "    at Module.require (internal/modules/cjs/loader.js:974:19)\n"
                    "    at require (internal/modules/cjs/helpers.js:101:18)\n"
                    "    at Object.<anonymous> (/home/user/app/app.js:1:1)"
                )
                return CommandResult(stderr=trace, success=False)
            return CommandResult(stdout="Server listening on port 3000")
        return CommandResult(stdout="node: interpreted successfully")

    def _cmd_ss(self, args: list[str]) -> CommandResult:
        """Alias for netstat — show socket statistics."""
        return CommandResult(stdout=self.pm.netstat_output())

    # ── Helpers ─────────────────────────────────────────────────────

    def _resolve(self, path: str) -> str:
        """Resolve a path relative to cwd (very simplified)."""
        if path.startswith("/"):
            return path
        return self.cwd.rstrip("/") + "/" + path

    # Map base command names → handler methods
    _HANDLERS: dict[str, Any] = {}


# Register handlers after class is defined
Sandbox._HANDLERS = {
    "ls": Sandbox._cmd_ls,
    "cat": Sandbox._cmd_cat,
    "grep": Sandbox._cmd_grep,
    "pwd": Sandbox._cmd_pwd,
    "cd": Sandbox._cmd_cd,
    "mv": Sandbox._cmd_mv,
    "rm": Sandbox._cmd_rm,
    "touch": Sandbox._cmd_touch,
    "mkdir": Sandbox._cmd_mkdir,
    "echo": Sandbox._cmd_echo,
    "ps": Sandbox._cmd_ps,
    "kill": Sandbox._cmd_kill,
    "systemctl": Sandbox._cmd_systemctl,
    "npm": Sandbox._cmd_npm,
    "pip": Sandbox._cmd_pip,
    "find": Sandbox._cmd_find,
    "head": Sandbox._cmd_head,
    "tail": Sandbox._cmd_tail,
    "netstat": Sandbox._cmd_netstat,
    "lsof": Sandbox._cmd_lsof,
    "df": Sandbox._cmd_df,
    "du": Sandbox._cmd_du,
    "free": Sandbox._cmd_free,
    "top": Sandbox._cmd_top,
    "node": Sandbox._cmd_node,
    "ss": Sandbox._cmd_ss,
}
