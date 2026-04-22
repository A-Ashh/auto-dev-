"""GET /tasks — list all available tasks and their action schema."""

from __future__ import annotations

from fastapi import APIRouter
import tasks.registry

router = APIRouter()

ACTION_SCHEMA = {
    "tool": {
        "type": "string",
        "description": "The tool to invoke. Currently only 'run_command' is supported.",
        "example": "run_command",
    },
    "arguments": {
        "type": "string",
        "description": "The shell command string to execute inside the sandbox.",
        "example": "ls /etc",
    },
}


@router.get("/tasks", tags=["Environment"])
async def list_tasks() -> dict:
    """Return all registered tasks and the action schema for POST /step."""
    tasks_list = []
    # FIX: Dynamically access TASK_REGISTRY.keys() to prevent stale imports
    for task_id in tasks.registry.TASK_REGISTRY.keys():
        task_def = tasks.registry.TASK_REGISTRY[task_id]
        tasks_list.append({
            "task_id": task_id,
            "description": getattr(task_def, "description", getattr(task_def, "DESCRIPTION", "No description")),
            "max_steps": getattr(task_def, "max_steps", getattr(task_def, "MAX_STEPS", 15)),
            "has_grader": getattr(task_def, "grader", None) is not None,
        })
    return {
        "tasks": tasks_list,
        "action_schema": ACTION_SCHEMA,
    }
