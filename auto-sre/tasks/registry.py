"""Task registry — lookup tasks by task_id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from grader.base import BaseGrader

from tasks import t1_config, t2_port, t3_dep, t4_trap


@dataclass
class TaskDefinition:
    """Blueprint for a scenario."""

    task_id: str
    description: str
    max_steps: int
    build_initial_state: Callable[[], tuple[MockFilesystem, ProcessManager]]
    grader: BaseGrader


# ── Registry ────────────────────────────────────────────────────────

TASK_REGISTRY: dict[str, TaskDefinition] = {
    t1_config.TASK_ID: TaskDefinition(
        task_id=t1_config.TASK_ID,
        description=t1_config.DESCRIPTION,
        max_steps=t1_config.MAX_STEPS,
        build_initial_state=t1_config.build_initial_state,
        grader=t1_config.GRADER,
    ),
    t2_port.TASK_ID: TaskDefinition(
        task_id=t2_port.TASK_ID,
        description=t2_port.DESCRIPTION,
        max_steps=t2_port.MAX_STEPS,
        build_initial_state=t2_port.build_initial_state,
        grader=t2_port.GRADER,
    ),
    t3_dep.TASK_ID: TaskDefinition(
        task_id=t3_dep.TASK_ID,
        description=t3_dep.DESCRIPTION,
        max_steps=t3_dep.MAX_STEPS,
        build_initial_state=t3_dep.build_initial_state,
        grader=t3_dep.GRADER,
    ),
    t4_trap.TASK_ID: TaskDefinition(
        task_id=t4_trap.TASK_ID,
        description=t4_trap.DESCRIPTION,
        max_steps=t4_trap.MAX_STEPS,
        build_initial_state=t4_trap.build_initial_state,
        grader=t4_trap.GRADER,
    ),
}


def get_task(task_id: str) -> TaskDefinition:
    """Lookup a task by ID.  Raises KeyError if not found."""
    if task_id not in TASK_REGISTRY:
        raise KeyError(f"Unknown task_id: '{task_id}'. Available: {list(TASK_REGISTRY.keys())}")
    return TASK_REGISTRY[task_id]


def list_tasks() -> list[str]:
    """Return all registered task IDs."""
    return list(TASK_REGISTRY.keys())
