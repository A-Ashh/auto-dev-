"""Abstract base class for task graders."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

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
    ) -> tuple[float, bool, str]:
        """
        Evaluate the current environment state.

        Returns:
            reward:  float in (0.01, 0.99)
            done:    True if the task is fully solved
            message: Human-readable grader message
        """
        ...
