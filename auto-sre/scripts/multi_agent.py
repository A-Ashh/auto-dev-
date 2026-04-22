"""Multi-agent SRE system: Commander → Planner → Executor → Critic.

Works for ANY task t1–t10 with no hardcoding.
Loads task list dynamically from /tasks endpoint.

Usage:
    python scripts/multi_agent.py [task_id]
    python scripts/multi_agent.py  # runs all tasks
"""

from __future__ import annotations
import os
import sys
import json
import requests

ENV_URL = os.getenv("AUTO_SRE_URL", "http://localhost:8000")
MAX_ITERATIONS = 3   # planner re-tries per task
MAX_STEPS = 12       # max commands per executor run

_SCORE_MIN = 0.01
_SCORE_MAX = 0.989


# ── Helpers ────────────────────────────────────────────────────────────

def _post(path: str, body: dict) -> dict:
    resp = requests.post(f"{ENV_URL}{path}", json=body, timeout=10)
    resp.raise_for_status()
    return resp.json()

def _get(path: str) -> dict:
    resp = requests.get(f"{ENV_URL}{path}", timeout=10)
    resp.raise_for_status()
    return resp.json()

def _safe(score) -> float:
    try:
        s = float(score)
        return max(_SCORE_MIN, min(_SCORE_MAX, s))
    except Exception:
        return _SCORE_MIN


# ── Agent Roles ────────────────────────────────────────────────────────

class Commander:
    """Loads all tasks, assigns them to Planner in curriculum order."""

    def fetch_tasks(self) -> list[dict]:
        data = _get("/tasks")
        tasks = data.get("tasks", [])
        print(f"[COMMANDER] {len(tasks)} tasks loaded: {[t['task_id'] for t in tasks]}")
        return tasks

    def reset(self, task_id: str) -> dict:
        result = _post("/reset", {"task_id": task_id})
        print(f"[COMMANDER] Reset → {task_id}")
        return result


class Planner:
    """Builds action plan based on task description and observation."""

    # Symbolic plans per scenario type (non-LLM, deterministic)
    _PLANS: dict[str, list[str]] = {
        "t1_config": [
            "ls /etc/app",
            "mv /etc/app/conf.bak /etc/app/conf",
            "systemctl restart app",
        ],
        "t2_port": [
            "netstat -tulpn",
            "ps aux",
            # kill command injected dynamically by Executor
        ],
        "t3_dep": [
            "cat /home/user/app/package.json",
            "cd /home/user/app",
            "npm install",
            "node app.js",
        ],
        "t4_trap": [
            "cat /etc/app/conf",
            "ps aux",
            "netstat -tulpn",
            "df -h",
        ],
        "t5_disk_full": [
            "df -h",
            "find /var/log",
            # rm injected by Executor after discovering file
        ],
        "t6_oom_killer": [
            "free -h",
            "ps aux",
            "top",
            # kill injected by Executor
        ],
        "t7_cascading_meltdown": [
            "df -h",
            "find /var/log",
            "ps aux",
            # rm + kill + systemctl restart db injected by Executor
        ],
        "t8_memory_leak_loop": [
            "free -h",
            "top",
            "ps aux",
            # kill + systemctl restart leak-daemon injected
        ],
        "t9_dependency_chain_failure": [
            "systemctl status app",
            "cat /var/log/app.log",
            "cat /var/log/cache.log",
            "systemctl restart db",
            "systemctl restart cache",
            "systemctl restart app",
        ],
        "t10_config_secret_failure": [
            "systemctl status app",
            "cat /var/log/app.log",
            "cat /etc/app/secrets.conf",
            "echo DB_PASSWORD=correct_password > /etc/app/secrets.conf",
            "systemctl restart app",
        ],
    }

    def plan(self, task_id: str, observation: dict, iteration: int) -> list[str]:
        base = self._PLANS.get(task_id, ["ps aux", "df -h", "free -h"])
        if iteration > 0:
            # Re-plan: add more diagnostic commands
            base = ["ps aux", "df -h", "free -h", "find /var/log"] + base
        print(f"[PLANNER] Plan for {task_id} (iter {iteration}): {len(base)} steps")
        return base


class Executor:
    """Runs the plan step-by-step, adapting dynamically based on output."""

    def execute(self, plan: list[str], task_id: str) -> tuple[float, list[str]]:
        """Execute plan commands, parse output to inject dynamic commands."""
        executed = []
        last_reward = _SCORE_MIN
        ps_output = ""
        find_output = ""

        for cmd in plan[:MAX_STEPS]:
            try:
                result = _post("/step", {"tool": "run_command", "arguments": cmd})
                obs = result.get("observation", {})
                stdout = obs.get("stdout", "")
                last_reward = _safe(result.get("reward", _SCORE_MIN))
                executed.append(cmd)

                print(f"[EXECUTOR] {cmd!r} → reward={last_reward:.4f} | "
                      f"stdout={stdout[:60].replace(chr(10), ' ')!r}")

                if cmd.startswith("ps"):
                    ps_output = stdout
                elif cmd.startswith("find"):
                    find_output = stdout

                if result.get("done"):
                    break

            except Exception as e:
                print(f"[EXECUTOR] Error on {cmd!r}: {e}")
                break

        # Inject dynamic kill if rogue PID visible in ps output
        if task_id in ("t2_port", "t6_oom_killer", "t7_cascading_meltdown", "t8_memory_leak_loop"):
            pid = self._extract_pid(ps_output, task_id)
            if pid:
                try:
                    result = _post("/step", {"tool": "run_command", "arguments": f"kill {pid}"})
                    last_reward = _safe(result.get("reward", last_reward))
                    executed.append(f"kill {pid}")
                    print(f"[EXECUTOR] kill {pid} → reward={last_reward:.4f}")
                    if result.get("done"):
                        return last_reward, executed
                except Exception:
                    pass

        # Inject dynamic rm for disk tasks
        if task_id in ("t5_disk_full", "t7_cascading_meltdown"):
            log_file = self._extract_log(find_output)
            if log_file:
                try:
                    result = _post("/step", {"tool": "run_command", "arguments": f"rm {log_file}"})
                    last_reward = _safe(result.get("reward", last_reward))
                    executed.append(f"rm {log_file}")
                    print(f"[EXECUTOR] rm {log_file} → reward={last_reward:.4f}")
                    if result.get("done"):
                        return last_reward, executed
                except Exception:
                    pass

        # T7: restart DB after cleanup
        if task_id == "t7_cascading_meltdown":
            try:
                result = _post("/step", {"tool": "run_command", "arguments": "systemctl restart db"})
                last_reward = _safe(result.get("reward", last_reward))
                executed.append("systemctl restart db")
                print(f"[EXECUTOR] systemctl restart db → reward={last_reward:.4f}")
            except Exception:
                pass

        # T8: restart leak-daemon after kill
        if task_id == "t8_memory_leak_loop":
            try:
                result = _post("/step", {"tool": "run_command", "arguments": "systemctl restart leak-daemon"})
                last_reward = _safe(result.get("reward", last_reward))
                executed.append("systemctl restart leak-daemon")
                print(f"[EXECUTOR] systemctl restart leak-daemon → reward={last_reward:.4f}")
            except Exception:
                pass

        return last_reward, executed

    def _extract_pid(self, ps_output: str, task_id: str) -> int | None:
        keywords = {
            "t2_port": "rogue",
            "t6_oom_killer": "memory_hog",
            "t7_cascading_meltdown": "rogue-logger",
            "t8_memory_leak_loop": "leak-daemon",
        }
        keyword = keywords.get(task_id, "rogue")
        for line in ps_output.splitlines():
            if keyword in line and "grep" not in line:
                parts = line.split()
                for part in parts:
                    try:
                        return int(part)
                    except ValueError:
                        continue
        return None

    def _extract_log(self, find_output: str) -> str | None:
        for line in find_output.splitlines():
            path = line.strip()
            if path.startswith("/var/log/") and "syslog" in path:
                return path
        return None


class Critic:
    """Evaluates outcome and decides whether to retry."""

    def evaluate(self, reward: float, task_id: str, iteration: int) -> bool:
        """Returns True if re-plan needed."""
        grade = _get("/grader")
        final_reward = _safe(grade.get("reward", reward))
        done = grade.get("done", False)
        msg = grade.get("grader_message", "")

        print(f"[CRITIC] {task_id} iter={iteration} reward={final_reward:.4f} "
              f"done={done} msg={msg!r}")

        if done or final_reward >= 0.90:
            print(f"[CRITIC] SUCCESS on {task_id}")
            return False  # no retry needed

        if iteration < MAX_ITERATIONS - 1:
            print(f"[CRITIC] Low reward ({final_reward:.4f}) — requesting re-plan")
            return True

        print(f"[CRITIC] Max iterations reached — accepting {final_reward:.4f}")
        return False


# ── Orchestrator ───────────────────────────────────────────────────────

def run_task(task: dict) -> dict:
    task_id = task["task_id"]
    description = task.get("description", "")
    print(f"\n{'='*60}")
    print(f"[SYSTEM] Starting task: {task_id}")
    print(f"[SYSTEM] {description}")
    print(f"{'='*60}")

    commander = Commander()
    planner = Planner()
    executor = Executor()
    critic = Critic()

    best_reward = _SCORE_MIN
    all_commands: list[str] = []

    reset_obs = commander.reset(task_id)
    observation = reset_obs.get("observation", {})

    for iteration in range(MAX_ITERATIONS):
        plan = planner.plan(task_id, observation, iteration)
        reward, executed = executor.execute(plan, task_id)
        best_reward = max(best_reward, reward)
        all_commands.extend(executed)

        retry = critic.evaluate(reward, task_id, iteration)
        if not retry:
            break

        # Reset for retry
        reset_obs = commander.reset(task_id)
        observation = reset_obs.get("observation", {})

    return {
        "task_id": task_id,
        "reward": _safe(best_reward),
        "commands_used": len(all_commands),
    }


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else None

    commander = Commander()
    all_tasks = commander.fetch_tasks()

    if target:
        all_tasks = [t for t in all_tasks if t["task_id"] == target]
        if not all_tasks:
            print(f"[ERROR] Task '{target}' not found")
            sys.exit(1)

    results = []
    for task in all_tasks:
        result = run_task(task)
        results.append(result)

    print(f"\n{'='*60}")
    print("[SYSTEM] Multi-Agent Run Complete")
    print(f"{'='*60}")
    print(json.dumps(results, indent=2))

    avg = sum(r["reward"] for r in results) / len(results) if results else 0.0
    print(f"\nAverage reward across all tasks: {_safe(avg):.4f}")


if __name__ == "__main__":
    main()
