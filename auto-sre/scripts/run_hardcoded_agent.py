"""Hardcoded Agent — submits the known correct solution for each task."""

import httpx

BASE_URL = "http://localhost:8000"

SOLUTIONS: dict[str, list[str]] = {
    "t1_config": [
        "mv /etc/app/conf.bak /etc/app/conf",
    ],
    "t2_port": [
        "kill -9 512",
    ],
    "t3_dep": [
        "cd /home/user/app",
        "npm install",
    ],
}


def run_hardcoded_agent() -> None:
    """Run the solution agent and verify 0.99 reward for every task."""
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)
    all_passed = True

    for task_id, commands in SOLUTIONS.items():
        print(f"\n{'='*60}")
        print(f"Solving task: {task_id}")
        print(f"{'='*60}")

        resp = client.post("/reset", json={"task_id": task_id})
        assert resp.status_code == 200, f"Reset failed: {resp.text}"

        last_response = None
        for cmd in commands:
            resp = client.post(
                "/step",
                json={"tool": "run_command", "arguments": cmd},
            )
            assert resp.status_code == 200, f"Step failed: {resp.text}"
            last_response = resp.json()
            print(f"  > {cmd}")
            print(f"    reward={last_response['reward']}, done={last_response['done']}")

        if last_response and last_response["reward"] >= 1 - 1e-6 and last_response["done"]:
            print(f"  [PASS] {task_id}: PASSED (reward>=1-1e-6)")
        else:
            print(f"  [FAIL] {task_id}: FAILED (reward={last_response['reward'] if last_response else 'N/A'})")
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("HARDCODED AGENT: ALL TASKS PASSED ✓")
    else:
        print("HARDCODED AGENT: SOME TASKS FAILED ✗")
    print(f"{'='*60}")


if __name__ == "__main__":
    run_hardcoded_agent()
