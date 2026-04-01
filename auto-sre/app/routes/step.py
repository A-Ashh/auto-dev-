"""POST /step — execute one agent action in the sandbox."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Body
from typing import Any

from app.schemas.action import DevOpsAction
# ... existing imports ...


@router.post("/step", response_model=StepResponse)
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
            return {"error": "Missing action arguments/command"}

        session = get_session()
        if not session.task_def:
             return {"error": "NO_TASK_LOADED"}

        # Core logic (surgical integration with existing session)
        result = session.sandbox.execute(str(cmd))
        session.step_count += 1
        session.record_step(str(cmd), result.stdout, result.stderr)
        
        reward, done, grader_msg = session.task_def.grader.grade(
            session.sandbox.fs, session.sandbox.pm, session.sandbox.command_history
        )
        session.is_done = done or (session.step_count >= session.task_def.max_steps)

        return {
            "observation": {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "cwd": session.sandbox.cwd,
                "health_status": done
            },
            "reward": reward,
            "done": session.is_done,
            "info": {
                "steps_taken": session.step_count,
                "grader_message": grader_msg
            }
        }
    except Exception as e:
        return {"error": str(e)}
