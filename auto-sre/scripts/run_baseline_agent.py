"""
Baseline inference script for Auto-SRE.

Uses the OpenAI-compatible API client to run a language model as an SRE agent.
Reads credentials from environment variables:
  - OPENAI_API_KEY (required for LLM mode)
  - OPENAI_BASE_URL (optional, defaults to https://api.openai.com/v1)
  - OPENAI_MODEL   (optional, defaults to gpt-4o-mini)
  - AUTO_SRE_URL   (optional, defaults to http://localhost:8000)

Falls back to a deterministic hardcoded agent if OPENAI_API_KEY is not set.
"""

from __future__ import annotations

import json
import os
import sys
import httpx  # type: ignore[import-untyped]


BASE_URL = os.getenv("AUTO_SRE_URL", "http://localhost:8000")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_STEPS = 10


SYSTEM_PROMPT = """You are an expert Site Reliability Engineer (SRE) diagnosing and repairing Linux infrastructure failures.

You must interact with a sandboxed Linux environment using ONLY the following tools:
- ls, cat, pwd, echo, ps, ps aux, mv, kill, find, grep, mkdir, touch, head, tail, systemctl, npm install, cd

At each step, you will receive an observation showing the stdout/stderr of your last command.
Your goal is to fix the broken environment as efficiently as possible.

Respond with ONLY a single shell command. Nothing else. No explanation, no markdown, no prefix."""


TASK_HINTS = {
    "t1_config": "A config file at /etc/app/conf is missing. It may exist under a backup name. Use ls to explore.",
    "t2_port": "Port 8080 is occupied by a rogue process. Use ps aux to investigate, then kill the process.",
    "t3_dep": "A Node.js application at /home/user/app is missing dependencies. Install them.",
    "t4_trap": "A system report suggests a failure, but the system may already be healthy. Verify before taking action.",
}

HARDCODED_SOLUTIONS: dict[str, list[str]] = {
    "t1_config": ["mv /etc/app/conf.bak /etc/app/conf"],
    "t2_port": ["kill -9 512"],
    "t3_dep": ["cd /home/user/app", "npm install"],
    "t4_trap": ["ls /etc/app"],
}


def run_llm_episode(client: httpx.Client, task_id: str, task_desc: str) -> dict:
    """Run a single task using the OpenAI API as the agent brain."""
    try:
        from openai import OpenAI  # type: ignore
    except ImportError:
        print("  [WARN] openai package not installed. pip install openai")
        return {"task_id": task_id, "reward": 0.0, "done": False, "error": "openai not installed"}

    llm = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

    # Reset environment
    resp = client.post(f"{BASE_URL}/reset", json={"task_id": task_id})
    if resp.status_code != 200:
        return {"task_id": task_id, "reward": 0.0, "done": False, "error": resp.text}

    hint = TASK_HINTS.get(task_id, "")
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Task: {task_desc}\n\nHint: {hint}\n\nBegin. Output only a shell command."},
    ]

    last: dict = {}
    for step_num in range(MAX_STEPS):
        completion = llm.chat.completions.create(model=OPENAI_MODEL, messages=messages, max_tokens=64)
        command = completion.choices[0].message.content.strip()

        resp = client.post(f"{BASE_URL}/step", json={"tool": "run_command", "arguments": command})
        if resp.status_code not in (200, 400):
            break

        if resp.status_code == 200:
            last = resp.json()
            observation = last.get("observation", {}).get("stdout", "") or last.get("observation", {}).get("stderr", "")
            messages.append({"role": "assistant", "content": command})
            messages.append({"role": "user", "content": f"Output:\n{observation}\n\nContinue or stop if done. Output only a shell command."})

            if last.get("done"):
                break

    return {
        "task_id": task_id,
        "reward": last.get("reward", 0.0),
        "done": last.get("done", False),
        "steps_taken": last.get("info", {}).get("steps_taken", step_num + 1),
    }


def run_hardcoded_episode(client: httpx.Client, task_id: str) -> dict:
    """Run a single task using the deterministic hardcoded solution."""
    commands = HARDCODED_SOLUTIONS[task_id]
    resp = client.post(f"{BASE_URL}/reset", json={"task_id": task_id})
    if resp.status_code != 200:
        return {"task_id": task_id, "reward": 0.0, "done": False, "error": resp.text}

    last: dict = {}
    for cmd in commands:
        resp = client.post(f"{BASE_URL}/step", json={"tool": "run_command", "arguments": cmd})
        if resp.status_code == 200:
            last = resp.json()

    return {
        "task_id": task_id,
        "reward": last.get("reward", 0.0),
        "done": last.get("done", False),
        "steps_taken": last.get("info", {}).get("steps_taken", len(commands)),
    }


def main() -> None:
    tasks_resp = httpx.get(f"{BASE_URL}/tasks", timeout=10.0)
    if tasks_resp.status_code != 200:
        print(f"[ERROR] Could not reach server at {BASE_URL}. Is it running?")
        sys.exit(1)

    tasks_data = tasks_resp.json()["tasks"]
    use_llm = bool(OPENAI_API_KEY)

    print("=" * 60)
    print(f"Auto-SRE Baseline Agent")
    print(f"Mode: {'OpenAI LLM (' + OPENAI_MODEL + ')' if use_llm else 'Hardcoded Deterministic'}")
    print(f"Server: {BASE_URL}")
    print("=" * 60)

    results = []
    with httpx.Client(timeout=60.0) as client:
        for task in tasks_data:
            task_id = task["task_id"]
            print(f"\nRunning task: {task_id}")
            print(f"  Description: {task['description']}")

            if use_llm:
                result = run_llm_episode(client, task_id, task["description"])
            else:
                result = run_hardcoded_episode(client, task_id)

            results.append(result)
            print(f"  Reward: {result['reward']} | Done: {result['done']}")

    total = sum(r["reward"] for r in results)
    avg = total / len(results) if results else 0.0

    print("\n" + "=" * 60)
    print("BASELINE RESULTS")
    print("=" * 60)
    print(json.dumps({
        "agent": "openai-llm" if use_llm else "hardcoded",
        "model": OPENAI_MODEL if use_llm else "N/A",
        "results": results,
        "aggregate": {
            "average_reward": round(float(avg), 4),
            "tasks_solved": sum(1 for r in results if r["reward"] == 1.0),
            "total_tasks": len(results),
        },
    }, indent=2))


if __name__ == "__main__":
    main()
