"""GET /tasks — list all available tasks and their action schema."""

from __future__ import annotations

from fastapi import APIRouter
from tasks.registry import TASK_REGISTRY

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
    tasks = []
    for task_id, task_def in TASK_REGISTRY.items():
        tasks.append({
            "task_id": task_id,
            "description": task_def.description,
            "max_steps": task_def.max_steps,
            "has_grader": True,
        })
    return {
        "tasks": tasks,
        "action_schema": ACTION_SCHEMA,
    }
