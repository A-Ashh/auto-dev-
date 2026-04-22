"""Task registry — lookup tasks by task_id."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from engine.filesystem import MockFilesystem
from engine.process_manager import ProcessManager
from grader.base import BaseGrader

from tasks import (
    t1_config, t2_port, t3_dep, t4_trap, t5_disk_full,
    t6_oom_killer, t7_cascading_meltdown,
    t8_memory_leak_loop, t9_dependency_chain_failure, t10_config_secret_failure,
)


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
    t5_disk_full.TASK_ID: TaskDefinition(
        task_id=t5_disk_full.TASK_ID,
        description=t5_disk_full.DESCRIPTION,
        max_steps=t5_disk_full.MAX_STEPS,
        build_initial_state=t5_disk_full.build_initial_state,
        grader=t5_disk_full.GRADER,
    ),
    t6_oom_killer.TASK_ID: TaskDefinition(
        task_id=t6_oom_killer.TASK_ID,
        description=t6_oom_killer.DESCRIPTION,
        max_steps=t6_oom_killer.MAX_STEPS,
        build_initial_state=t6_oom_killer.build_initial_state,
        grader=t6_oom_killer.GRADER,
    ),
    t7_cascading_meltdown.TASK_ID: TaskDefinition(
        task_id=t7_cascading_meltdown.TASK_ID,
        description=t7_cascading_meltdown.DESCRIPTION,
        max_steps=t7_cascading_meltdown.MAX_STEPS,
        build_initial_state=t7_cascading_meltdown.build_initial_state,
        grader=t7_cascading_meltdown.GRADER,
    ),
    t8_memory_leak_loop.TASK_ID: TaskDefinition(
        task_id=t8_memory_leak_loop.TASK_ID,
        description=t8_memory_leak_loop.DESCRIPTION,
        max_steps=t8_memory_leak_loop.MAX_STEPS,
        build_initial_state=t8_memory_leak_loop.build_initial_state,
        grader=t8_memory_leak_loop.GRADER,
    ),
    t9_dependency_chain_failure.TASK_ID: TaskDefinition(
        task_id=t9_dependency_chain_failure.TASK_ID,
        description=t9_dependency_chain_failure.DESCRIPTION,
        max_steps=t9_dependency_chain_failure.MAX_STEPS,
        build_initial_state=t9_dependency_chain_failure.build_initial_state,
        grader=t9_dependency_chain_failure.GRADER,
    ),
    t10_config_secret_failure.TASK_ID: TaskDefinition(
        task_id=t10_config_secret_failure.TASK_ID,
        description=t10_config_secret_failure.DESCRIPTION,
        max_steps=t10_config_secret_failure.MAX_STEPS,
        build_initial_state=t10_config_secret_failure.build_initial_state,
        grader=t10_config_secret_failure.GRADER,
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
