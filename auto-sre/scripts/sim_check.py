"""Run 20 simulation episodes and verify all scores are strictly in (0, 1)."""
import httpx
import sys
import json

BASE = "http://localhost:8000"

SOLUTIONS = {
    "t1_config": ["mv /etc/app/conf.bak /etc/app/conf"],
    "t2_port": ["kill -9 512"],
    "t3_dep": ["cd /home/user/app", "npm install"],
    "t4_trap": ["ls /etc/app"],
}

TASKS = ["t1_config", "t2_port", "t3_dep", "t4_trap"]

def safe_score(x):
    import math
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return 0.01
    val = float(x)
    if val >= 0.995:
        val = 0.989
    if val <= 0.0:
        val = 0.01
    return val

violations = []
all_scores = []

with httpx.Client(timeout=30.0) as client:
    for run in range(1, 21):
        for task_id in TASKS:
            # Reset
            resp = client.post(f"{BASE}/reset", json={"task_id": task_id})
            if resp.status_code != 200:
                print(f"[RUN {run}] {task_id}: RESET FAILED (status {resp.status_code})")
                continue

            # Execute solution steps
            last_reward = None
            last_done = False
            for cmd in SOLUTIONS[task_id]:
                resp = client.post(f"{BASE}/step", json={"tool": "run_command", "arguments": cmd})
                if resp.status_code == 200:
                    data = resp.json()
                    last_reward = data.get("reward")
                    last_done = data.get("done", False)

            raw = last_reward
            clamped = safe_score(raw)
            formatted = f"{clamped:.2f}"

            # Check raw API reward
            if raw is not None and (raw <= 0.0 or raw >= 1.0):
                violations.append(f"[RUN {run}] {task_id}: RAW API reward={raw} OUT OF RANGE!")

            # Check clamped value
            if clamped <= 0.0 or clamped >= 1.0:
                violations.append(f"[RUN {run}] {task_id}: CLAMPED score={clamped} OUT OF RANGE!")

            # Check .2f formatted string
            if formatted == "0.00" or formatted == "1.00":
                violations.append(f"[RUN {run}] {task_id}: FORMATTED '{formatted}' EQUALS BOUNDARY!")

            all_scores.append({
                "run": run,
                "task": task_id,
                "raw": raw,
                "clamped": clamped,
                "formatted": formatted,
                "done": last_done,
            })

            print(f"[RUN {run:2d}] {task_id:12s} raw={raw:<22} clamped={clamped:<10} fmt={formatted}  done={last_done}")

print("\n" + "=" * 70)
print(f"TOTAL SCORES CHECKED: {len(all_scores)}")
print(f"VIOLATIONS FOUND: {len(violations)}")

if violations:
    print("\n🚨 VIOLATIONS:")
    for v in violations:
        print(f"  ❌ {v}")
    sys.exit(1)
else:
    # Summary stats
    raw_min = min(s["raw"] for s in all_scores if s["raw"] is not None)
    raw_max = max(s["raw"] for s in all_scores if s["raw"] is not None)
    fmts = set(s["formatted"] for s in all_scores)
    print(f"\n✅ ALL {len(all_scores)} SCORES PASSED VALIDATION")
    print(f"   Raw range: [{raw_min}, {raw_max}]")
    print(f"   Unique formatted values: {sorted(fmts)}")
    print(f"   0.00 present: {'0.00' in fmts}")
    print(f"   1.00 present: {'1.00' in fmts}")
    sys.exit(0)
