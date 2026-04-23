"""Hardcoded Agent — submits the known correct solution for each task."""

import httpx
import sys

BASE_URL = "http://localhost:8000"

DEMO_SOLUTIONS = {
    "t1_config": ["ls /etc/app", "mv /etc/app/conf.bak /etc/app/conf", "systemctl restart app"],
    "t2_port": ["ps", "kill -9 {rogue_pid}", "systemctl restart app"],
    "t3_dep": ["cd /home/user/app", "npm install", "systemctl restart app"],
    "t4_trap": ["ls /etc/app", "cat /etc/app/conf", "ps"],
    "t5_disk_full": ["df -h", "rm /var/log/syslog"],
    "t6_oom_killer": ["ps", "kill -9 {rogue_pid}"],
    "t7_cascading_meltdown": ["df -h", "rm /var/log/syslog", "ps", "kill -9 {rogue_pid}", "systemctl restart db"],
    "t8_memory_leak_loop": ["ps", "kill -9 {rogue_pid}", "systemctl restart leak-daemon"],
    "t9_dependency_chain_failure": ["systemctl restart db", "systemctl restart cache", "systemctl restart app"],
    "t10_config_secret_failure": ["systemctl status app", "cat /var/log/app.log", "cat /etc/app/secrets.conf", "echo DB_PASSWORD=CORRECT_SECRET > /etc/app/secrets.conf", "systemctl restart app"],
}

def run_hardcoded_agent() -> None:
    """Run the solution agent and verify >=0.97 reward for every task."""
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)
    all_passed = True

    for task_id, commands in DEMO_SOLUTIONS.items():
        print(f"\n{'='*60}")
        print(f"Solving task: {task_id}")
        print(f"{'='*60}")

        resp = client.post("/reset", json={"task_id": task_id})
        assert resp.status_code == 200, f"Reset failed: {resp.text}"

        last_response = None
        known_rogue_pid = None

        for cmd in commands:
            if "{rogue_pid}" in cmd:
                cmd = cmd.replace("{rogue_pid}", str(known_rogue_pid) if known_rogue_pid else "999")

            resp = client.post(
                "/step",
                json={"tool": "run_command", "arguments": cmd},
            )
            assert resp.status_code == 200, f"Step failed: {resp.text}"
            last_response = resp.json()
            print(f"  > {cmd}")
            print(f"    reward={last_response['reward']}, done={last_response['done']}")

            if "ps" in cmd and "state" in last_response:
                procs = last_response["state"].get("processes", [])
                for p in procs:
                    cmd_str = p.get("command", "").lower()
                    if any(k in cmd_str for k in ("rogue", "leak-daemon --no-limit", "rogue-logger", "rogue-server", "memory_hog")):
                        known_rogue_pid = p["pid"]
                        break

            if last_response["done"]:
                break

        # Expect 0.97 or higher for success
        if last_response and last_response["reward"] >= 0.97 and last_response["done"]:
            print(f"  [PASS] {task_id}: PASSED (reward>=0.97)")
        else:
            reward_val = last_response["reward"] if last_response else "N/A"
            print(f"  [FAIL] {task_id}: FAILED (reward={reward_val})")
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("HARDCODED AGENT: ALL 10 TASKS PASSED [SUCCESS]")
        sys.exit(0)
    else:
        print("HARDCODED AGENT: SOME TASKS FAILED [ERROR]")
        sys.exit(1)

if __name__ == "__main__":
    run_hardcoded_agent()
