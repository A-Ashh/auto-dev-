"""POST /step — execute one agent action in the sandbox."""

from __future__ import annotations

import math

from fastapi import APIRouter, HTTPException, Body
from typing import Any

from app.schemas.action import DevOpsAction
from app.schemas.observation import StepResponse, Observation
from app.routes._session import get_session

router = APIRouter()

_SCORE_MIN = 0.01
_SCORE_MAX = 0.989


def _safe_reward(raw) -> float:
    """Clamp reward to open interval (0, 1). Handles None/NaN."""
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _SCORE_MIN
    r = float(raw)
    r = max(_SCORE_MIN, min(_SCORE_MAX, r))
    assert 0 < r < 1, f"Score out of range: {r}"
    return r


@router.post("/step")
async def step_action(body: dict = Body(...)) -> Any:
    """Execute a shell command and return the resulting observation and reward."""
    try:
        # OpenEnv validator often sends action nested in a dict
        action_input = body.get("action") or body
        
        # Extract arguments and tool
        if isinstance(action_input, dict):
            cmd = action_input.get("arguments") or action_input.get("command") or action_input.get("cmd")
            tool = action_input.get("tool", "run_command")
        else:
            # Fallback for flat strings or other formats
            cmd = action_input
            tool = "run_command"

        if not cmd:
            raise HTTPException(status_code=400, detail="Missing action arguments/command")

        session = get_session()
        if not session.task_def:
             raise HTTPException(status_code=400, detail="NO_TASK_LOADED")

        # Core logic (surgical integration with existing session)
        result = session.sandbox.execute(str(cmd))
        session.step_count += 1
        session.record_step(str(cmd), result.stdout, result.stderr)
        
        raw_reward, done, grader_msg = session.task_def.grader.grade(
            session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history
        )
        # HARD CLAMP — strictly in (0, 1), never 0.0 or 1.0
        reward = _safe_reward(raw_reward)
        session.is_done = done or (session.step_count >= session.task_def.max_steps)

        return {
            "observation": {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "cwd": session.sandbox.cwd,
                "health_status": done
            },
            "reward": reward,
            "score": reward,
            "done": session.is_done,
            "info": {
                "steps_taken": session.step_count,
                "grader_message": grader_msg
            }
        }
    except Exception as e:
        return {
            "observation": {
                "stdout": "",
                "stderr": str(e),
                "cwd": "/",
                "health_status": False
            },
            "reward": _SCORE_MIN,
            "score": _SCORE_MIN,
            "done": True,
            "info": {
                "steps_taken": 0,
                "grader_message": f"Exception occurred: {str(e)}"
            }
        }
