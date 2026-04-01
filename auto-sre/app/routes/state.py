"""GET /state — return rich environment snapshot."""

from __future__ import annotations

from fastapi import APIRouter

from app.schemas.observation import CommandEntry, RichStateResponse
from app.routes._session import get_session

router = APIRouter()


@router.get("/state", response_model=RichStateResponse)
async def get_state() -> Any:
    """Return the current environment state snapshot."""
    try:
        session = get_session()
        task_id = session.task_def.task_id if session.task_def else None
        
        return {
            "task_id": task_id,
            "step_count": session.step_count,
            "health_status": session.is_done,
            "is_done": session.is_done,
            "cwd": session.sandbox.cwd if session.task_def else "/home/user",
            "observation": {
                "stdout": session.last_entry["stdout"] if session.last_entry else "",
                "stderr": session.last_entry["stderr"] if session.last_entry else "",
            }
        }
    except Exception as e:
        return {"error": str(e)}
