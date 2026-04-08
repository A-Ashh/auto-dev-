"""GET /baseline — run the deterministic baseline agent and return reproducible scores."""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()

_SCORE_MIN = 0.01
_SCORE_MAX = 0.989


def _safe_reward(raw) -> float:
    """Clamp reward strictly to (0, 1)."""
    if raw is None or (isinstance(raw, float) and math.isnan(raw)):
        return _SCORE_MIN
    r = float(raw)
    r = max(_SCORE_MIN, min(_SCORE_MAX, r))
    assert 0 < r < 1, f"Score out of range: {r}"
    return r


# ✅ FIX: include ALL tasks (including trap)
SOLUTIONS: dict[str, list[str]] = {
    "t1_config": ["mv /etc/app/conf.bak /etc/app/conf"],
    "t2_port": ["kill -9 512"],
    "t3_dep": ["cd /home/user/app", "npm install"],
    "t4_trap": ["ls /etc/app"],  # 🔥 important
}


def _run_task_internally(task_id: str, commands: list[str]) -> dict:
    """Run a task using the internal session engine (no HTTP self-call)."""
    from tasks.registry import get_task
    from engine.sandbox import Sandbox
    from engine.security import CommandNotAllowedError, StepTimeoutError

    try:
        task_def = get_task(task_id)
    except KeyError as e:
        return {"task_id": task_id, "reward": _SCORE_MIN, "done": False, "error": str(e)}

    fs, pm = task_def.build_initial_state()
    sandbox = Sandbox(fs, pm)

    step_count = 0
    last_reward = _SCORE_MIN
    done = False

    for cmd in commands:
        try:
            sandbox.execute(cmd)
        except (CommandNotAllowedError, StepTimeoutError):
            pass

        step_count += 1

        last_reward, done, _ = task_def.grader.grade(
            sandbox.fs, sandbox.pm, sandbox.command_history
        )

        # 🔒 HARD CLAMP EVERY STEP
        last_reward = _safe_reward(last_reward)

        if done:
            break

    return {
        "task_id": task_id,
        "reward": last_reward,
        "score": last_reward,
        "done": done,
        "steps_taken": step_count,
    }


@router.get("/baseline", tags=["Evaluation"])
async def run_baseline() -> dict:
    """
    Run deterministic baseline across ALL tasks.
    Ensures all rewards strictly in (0, 1).
    """

    start_ts = time.monotonic()
    results = []

    for task_id, commands in SOLUTIONS.items():
        result = _run_task_internally(task_id, commands)
        results.append(result)

    # 🔒 FINAL SAFETY CLAMP
    for r in results:
        r["reward"] = _safe_reward(r.get("reward"))

    elapsed = float(time.monotonic() - start_ts)

    # 🔒 SAFE AGGREGATION (NO ROUNDING)
    total_reward = sum(r["reward"] for r in results)
    total_reward = max(_SCORE_MIN, min(_SCORE_MAX * len(results), total_reward))

    avg_reward = total_reward / len(results) if results else _SCORE_MIN
    avg_reward = _safe_reward(avg_reward)

    return {
        "baseline_agent": "hardcoded_deterministic",
        "description": "Reproducible baseline using known-correct solutions.",
        "tasks": results,
        "aggregate": {
            # ❗ NO rounding anywhere
            "total_reward": total_reward,
            "average_reward": avg_reward,
            "tasks_solved": sum(1 for r in results if r["reward"] >= 0.98),
            "total_tasks": len(results),
            "all_passed": all(r["reward"] >= 0.98 for r in results),
            "evaluation_time_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }