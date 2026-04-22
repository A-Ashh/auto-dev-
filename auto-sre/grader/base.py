"""Abstract base class for task graders — updated for stateful world model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from engine.filesystem import MockFilesystem
    from engine.process_manager import ProcessManager


class BaseGrader(ABC):
    """Interface that every task grader must implement."""

    @abstractmethod
    def grade(
        self,
        filesystem: MockFilesystem,
        process_manager: ProcessManager,
        command_history: list[str],
        state: dict[str, Any] | None = None,
    ) -> tuple[float, bool, str]:
        """
        Evaluate the current environment state.

        Args:
            filesystem:      Current mock filesystem state.
            process_manager: Current mock process state.
            command_history: List of commands issued this episode.
            state:           World model state dict (disk_usage, memory_usage,
                             services_running, ports, config_valid, rogue_pid,
                             target_log, target_port).

        Returns:
            reward:  float in open interval (0, 1) — strictly 0 < reward < 1
            done:    True if the task is fully solved (or failed with no recovery)
            message: Human-readable grader message
        """
        ...
