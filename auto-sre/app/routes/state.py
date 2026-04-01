"""GET /state — return rich environment snapshot."""

from __future__ import annotations

from fastapi import APIRouter
from typing import Any

from app.schemas.observation import CommandEntry, RichStateResponse
from app.routes._session import get_session

router = APIRouter()


@router.get("/state", response_model=RichStateResponse)
async def get_state() -> Any:
    """Return the current environment state snapshot."""
    try:
        session = get_session()
        task_id = session.task_def.task_id if session.task_def else None
        last = session.last_entry

        return {
            "task_id": task_id,
            "step_count": session.step_count,
            "health_status": session.is_done,
            "is_done": session.is_done,
            "cwd": session.sandbox.cwd if session.task_def else "/home/user",
            "current_task": task_id,
            "task_description": session.task_def.description if session.task_def else None,
            "max_steps": session.task_def.max_steps if session.task_def else 0,
            "last_stdout": last["stdout"] if last else "",
            "last_stderr": last["stderr"] if last else "",
            "last_command": last["command"] if last else None,
            "history": list(session.command_history_full),
            "files": [],
            "processes": [],
        }
    except Exception as e:
        return {"error": str(e)}

