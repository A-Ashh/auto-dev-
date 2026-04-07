"""GET /baseline — run the deterministic baseline agent and return reproducible scores."""

from __future__ import annotations

import time
from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter()

SOLUTIONS: dict[str, list[str]] = {
    "t1_config": ["mv /etc/app/conf.bak /etc/app/conf"],
    "t2_port": ["kill -9 512"],
    "t3_dep": ["cd /home/user/app", "npm install"],
}

TASK_DESCRIPTIONS: dict[str, str] = {
    "t1_config": "A critical config file has been misnamed. The app cannot find /etc/app/conf.",
    "t2_port": "Port 8080 is occupied by a rogue process. Kill it to free the port.",
    "t3_dep": "The Node.js application is missing npm dependencies. Install them.",
}


def _run_task_internally(task_id: str, commands: list[str]) -> dict:
    """Run a task using the internal session engine (no HTTP self-call)."""
    from tasks.registry import get_task
    from engine.sandbox import Sandbox
    from engine.security import CommandNotAllowedError, StepTimeoutError

    try:
        task_def = get_task(task_id)
    except KeyError as e:
        return {"task_id": task_id, "reward": 0.01, "done": False, "error": str(e)}

    fs, pm = task_def.build_initial_state()
    sandbox = Sandbox(fs, pm)
    step_count = 0
    last_reward = 0.01
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

        # 🔒 HARD CLAMP AFTER EVERY STEP
        last_reward = max(0.01, min(0.99, float(last_reward)))

        if done:
            break

    return {
        "task_id": task_id,
        "reward": last_reward,
        "done": done,
        "steps_taken": step_count,
    }


@router.get("/baseline", tags=["Evaluation"])
async def run_baseline() -> dict:
    """
    Run the deterministic hardcoded baseline agent on all tasks internally.
    Returns reproducible baseline scores without requiring an OpenAI API key.
    """
    start_ts = time.monotonic()
    results = []

    for task_id, commands in SOLUTIONS.items():
        result = _run_task_internally(task_id, commands)
        results.append(result)

    # 🔒 HARDEN ALL RESULTS (CRITICAL SAFETY LAYER)
    for r in results:
        r["reward"] = max(0.01, min(0.99, float(r.get("reward", 0.01))))

    elapsed = round(float(time.monotonic() - start_ts), 4)

    # 🔒 SAFE AGGREGATION
    total_reward = sum(r["reward"] for r in results)
    total_reward = max(0.01, min(0.99, float(total_reward)))

    avg_reward = total_reward / len(results) if results else 0.01
    avg_reward = max(0.01, min(0.99, avg_reward))

    return {
        "baseline_agent": "hardcoded_deterministic",
        "description": "Reproducible baseline using known-correct solutions. Run scripts/run_baseline_agent.py with OPENAI_API_KEY for LLM evaluation.",
        "tasks": results,
        "aggregate": {
            "total_reward": round(total_reward, 4),
            "average_reward": round(avg_reward, 4),
            "tasks_solved": sum(1 for r in results if r["reward"] >= 0.99),
            "total_tasks": len(results),
            "all_passed": all(r["reward"] >= 0.99 for r in results),
            "evaluation_time_seconds": elapsed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    }