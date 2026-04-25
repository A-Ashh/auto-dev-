"""GET /grader — return the grader score for the current episode."""

from __future__ import annotations
import math

from fastapi import APIRouter
from auto_sre.app.routes._session import get_session

router = APIRouter()

_SCORE_MIN = 0.01
_SCORE_MAX = 1.0  # allow full success


# ---------------- SAFETY ----------------
def _safe_reward(raw) -> float:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _SCORE_MIN

    r = float(raw)
    r = max(_SCORE_MIN, min(_SCORE_MAX, r))

    return r


# ---------------- CORE GRADER ----------------
@router.get("/grader", tags=["Environment"])
async def get_grader_score() -> dict:
    """Return current task score WITHOUT modifying environment."""

    session = get_session()

    if session.task_def is None:
        return {
            "task_id": None,
            "reward": _SCORE_MIN,
            "score": _SCORE_MIN,
            "done": True,
            "grader_message": "No task loaded",
            "step_count": 0,
            "max_steps": 0,
        }

    try:
        reward, done, grader_message = session.task_def.grader.grade(
            session.sandbox.fs,
            session.sandbox.pm,
            session.sandbox.command_history,
            session.sandbox.state,
        )

        reward = _safe_reward(reward)

        return {
            "task_id": session.task_def.task_id,
            "reward": reward,
            "score": reward,
            "done": done,
            "grader_message": grader_message,
            "step_count": session.step_count,
            "max_steps": session.task_def.max_steps,
        }

    except Exception as e:
        print("GRADER ERROR:", e)
        return {
            "task_id": session.task_def.task_id,
            "reward": _SCORE_MIN,
            "score": _SCORE_MIN,
            "done": False,
            "grader_message": "Grader failed",
            "step_count": session.step_count,
            "max_steps": session.task_def.max_steps,
        }


# ---------------- GENERIC TASK GRADER ----------------
@router.get("/grade/{task_id}", tags=["Environment"])
async def grade_task(task_id: str) -> dict:
    """
    Evaluate ANY task.
    DOES NOT mutate session silently.
    """

    session = get_session()

    if session.task_def is None or session.task_def.task_id != task_id:
        return {
            "error": f"Task '{task_id}' not active. Call /reset first."
        }

    try:
        reward, done, _ = session.task_def.grader.grade(
            session.sandbox.fs,
            session.sandbox.pm,
            session.sandbox.command_history,
            session.sandbox.state,
        )

        reward = _safe_reward(reward)

        return {
            "task_id": task_id,
            "reward": reward,
            "score": reward,
            "done": done,
        }

    except Exception as e:
        print("GRADER ERROR:", e)
        return {
            "task_id": task_id,
            "reward": _SCORE_MIN,
            "score": _SCORE_MIN,
            "done": False,
        }
