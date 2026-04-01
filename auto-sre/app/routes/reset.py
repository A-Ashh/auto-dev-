"""POST /reset — reset the environment to a task's broken baseline."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Body
from typing import Optional

from app.schemas.action import ResetRequest
from app.schemas.observation import Observation, ResetResponse
from app.routes._session import get_session

router = APIRouter()


@router.post("/reset", response_model=ResetResponse)
async def reset_environment(body: Optional[dict] = Body(default=None)) -> ResetResponse:
    """Reset the environment to the specified task's initial state."""
    # Mapping for easy/medium/hard to internal task IDs
    task_map = {
        "easy": "t1_config",
        "medium": "t2_port",
        "hard": "t3_dep"
    }

    task_id = "t1_config" # Default fallback
    if body and "task_id" in body:
        requested = body["task_id"]
        task_id = task_map.get(requested, requested) # Use map or direct ID

    return _do_reset(task_id)

@router.get("/reset", response_model=ResetResponse)
async def reset_environment_get(task_id: str | None = None) -> ResetResponse:
    """Reset the environment using a GET request (defaulting to t1_config)."""
    if not task_id:
        task_id = "t1_config"
    return _do_reset(task_id)

def _do_reset(task_id: str) -> ResetResponse:
    try:
        session = get_session()
        session.load_task(task_id)

        observation = Observation(
            stdout=f"Environment reset to task {task_id}.",
            stderr="",
            cwd="/home/user",
            health_status=False,
        )
        return ResetResponse(
            observation=observation,
            info={
                "task_id": task_id,
                "description": session.task_def.description,
                "max_steps": session.task_def.max_steps,
            },
        )
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
