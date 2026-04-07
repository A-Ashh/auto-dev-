"""GET /grader — return the grader score for the current episode."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from app.routes._session import get_session

router = APIRouter()


@router.get("/grader", tags=["Environment"])
async def get_grader_score() -> dict:
    """Return the current grader score for the active episode without advancing the episode."""
    session = get_session()

    if session.task_def is None:
        raise HTTPException(status_code=400, detail="No task loaded. Call POST /reset first.")

    reward, done, grader_message = session.task_def.grader.grade(
        session.sandbox.fs,
        session.sandbox.pm,
        session.sandbox.command_history,
    )

    clamped_reward = max(0.01, min(0.99, float(reward)))
    return {
        "task_id": session.task_def.task_id,
        "reward": clamped_reward,
        "done": done,
        "grader_message": grader_message,
        "step_count": session.step_count,
        "max_steps": session.task_def.max_steps,
    }
