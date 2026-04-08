"""GET /grader — return the grader score for the current episode."""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException
from app.routes._session import get_session

router = APIRouter()

_SCORE_MIN = 0.01
_SCORE_MAX = 0.989


def _safe_reward(raw) -> float:
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _SCORE_MIN
    r = float(raw)
    r = max(_SCORE_MIN, min(_SCORE_MAX, r))
    assert 0 < r < 1, f"Score out of range: {r}"
    return r


@router.get("/grader", tags=["Environment"])
async def get_grader_score() -> dict:
    """Return the current grader score for the active episode without advancing the episode."""
    session = get_session()

    # Safe fallback instead of HTTP error (validator-friendly)
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

    # Run grader
    reward, done, grader_message = session.task_def.grader.grade(
        session.sandbox.fs,
        session.sandbox.pm,
        session.sandbox.command_history,
    )

    # HARD CLAMP (global guarantee)
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


@router.get("/grade/task_1", tags=["Environment"])
async def grade_task_1() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t1_config":
            session.load_task("t1_config")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception:
        return {"score": _SCORE_MIN, "reward": _SCORE_MIN}

@router.get("/grade/task_2", tags=["Environment"])
async def grade_task_2() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t2_port":
            session.load_task("t2_port")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception:
        return {"score": _SCORE_MIN, "reward": _SCORE_MIN}

@router.get("/grade/task_3", tags=["Environment"])
async def grade_task_3() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t3_dep":
            session.load_task("t3_dep")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception:
        return {"score": _SCORE_MIN, "reward": _SCORE_MIN}

@router.get("/grade/task_4", tags=["Environment"])
async def grade_task_4() -> dict:
    session = get_session()
    try:
        if not session.task_def or session.task_def.task_id != "t4_trap":
            session.load_task("t4_trap")
        reward, _, _ = session.task_def.grader.grade(session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history)
        reward = _safe_reward(reward)
        return {"score": reward, "reward": reward}
    except Exception:
        return {"score": _SCORE_MIN, "reward": _SCORE_MIN}@router.get("/grade/t1_config", tags=["Environment"])
async def grade_t1_config() -> dict: return await grade_task_1()
@router.get("/grade/t2_port", tags=["Environment"])
async def grade_t2_port() -> dict: return await grade_task_2()
@router.get("/grade/t3_dep", tags=["Environment"])
async def grade_t3_dep() -> dict: return await grade_task_3()
@router.get("/grade/t4_trap", tags=["Environment"])
async def grade_t4_trap() -> dict: return await grade_task_4()

