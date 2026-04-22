"""Shared session state for the single-tenant MVP."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Optional

from engine.sandbox import Sandbox
from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from tasks.registry import TaskDefinition, get_task

MAX_HISTORY = 10


@dataclass
class Session:
    """Holds the mutable runtime state for the current episode."""

    sandbox: Sandbox = field(default_factory=lambda: Sandbox(MockFilesystem(), ProcessManager()))
    task_def: Optional[TaskDefinition] = None
    step_count: int = 0
    is_done: bool = False
    # Rich command history: last N entries of {command, stdout, stderr}
    command_history_full: deque[dict[str, Any]] = field(
        default_factory=lambda: deque(maxlen=MAX_HISTORY)
    )

    def load_task(self, task_id: str) -> None:
        """Reset the session to a fresh episode for the given task."""
        self.task_def = get_task(task_id)  # raises KeyError if not found
        assert self.task_def is not None  # type guard for static analysis
        fs, pm = self.task_def.build_initial_state()

        # Inject task-specific world model state if provided
        import importlib
        try:
            task_module = importlib.import_module(f"tasks.{task_id}")
            initial_state = getattr(task_module, "_state_hint", {})
        except Exception:
            initial_state = {}

        self.sandbox = Sandbox(fs, pm, initial_state=dict(initial_state))
        self.step_count = 0
        self.is_done = False
        self.command_history_full.clear()

    def record_step(self, command: str, stdout: str, stderr: str) -> None:
        """Append a command result to the rolling history (capped at MAX_HISTORY)."""
        self.command_history_full.append({
            "command": command,
            "stdout": stdout,
            "stderr": stderr,
        })

    @property
    def last_entry(self) -> Optional[dict[str, Any]]:
        """Return the most recent command entry, or None if history is empty."""
        return self.command_history_full[-1] if self.command_history_full else None


# Singleton session (single-tenant MVP)
_session: Session | None = None


def get_session() -> Session:
    """Return the global session, creating one if needed."""
    global _session
    if _session is None:
        _session = Session()
    return _session
