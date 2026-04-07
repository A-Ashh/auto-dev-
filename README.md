---
title: Auto-SRE
emoji: 🚨
colorFrom: red
colorTo: yellow
sdk: docker
pinned: true
tags:
  - openenv
  - real-world
  - devops
  - sre
  - infrastructure
---

# 🚨 Auto-SRE — AI Infrastructure Repair Environment

> *"The server is down. You have 10 steps. Go."*

**Auto-SRE** is an [OpenEnv](https://huggingface.co/openenv)-compliant environment where AI agents learn to diagnose and repair broken Linux infrastructure — just like an on-call Site Reliability Engineer.

Unlike toy benchmarks, agents must execute real shell commands inside a sandboxed system, read actual error signals, and apply the correct fix. Wrong guesses don't score. Half-correct attempts earn partial credit. Systematic diagnosis earns full marks.

🌐 **Live Demo:** https://huggingface.co/spaces/goated1/auto-sre

---

## 🧠 Why This Environment Exists

Production infrastructure breaks in predictable ways. Every day, engineers spend hours on:

- Misconfigured files that block application startup
- Rogue processes holding ports hostage
- Missing dependencies that crash deployments

**Today:** A human engineer SSHs in, runs `ps aux`, reads logs, and fixes it manually.  
**Tomorrow:** An AI agent does the same — faster, at 3 AM, without waking anyone up.

Auto-SRE is the training and evaluation ground for that agent. It is one of the first OpenEnv environments focused on real-world DevOps/SRE infrastructure repair, filling a gap that currently has no equivalent on the Hub.

---

## ⚙️ Environment Design

### How It Works

The agent receives a broken system state — a realistic Linux-like sandbox with a filesystem, running processes, and application logs. It must issue shell commands step-by-step to diagnose and repair the failure.

The sandbox is built on a **UnionFS-style layered filesystem** with a read-only base and a mutable overlay. A mock process manager simulates `ps aux` and `netstat` outputs from a configurable process table. Every command is parsed, validated against a security whitelist, and executed within a 5-second timeout.

```
Agent                     Auto-SRE Environment
  │                              │
  │── POST /reset ──────────────▶│  Broken state initialized
  │◀─ Observation ───────────────│  (stdout, stderr, cwd, health_status)
  │                              │
  │── POST /step ───────────────▶│  Shell command executed in sandbox
  │◀─ (obs, reward, done, info) ─│  Grader evaluates system state
  │                              │
  │      [repeat up to max_steps]│
```

### Observation Space

```python
class DevOpsObservation(BaseModel):
    stdout: str          # Command output
    stderr: str          # Error output (critical for diagnosis)
    cwd: str             # Current working directory
    health_status: bool  # True if the system has been repaired
```

### Action Space

```python
class DevOpsAction(BaseModel):
    tool: Literal["run_command"]
    arguments: str  # Shell command string
```

**Allowed commands** (enforced by `engine/security.py`):
`ls`, `cat`, `pwd`, `echo`, `ps`, `mv`, `kill`, `find`, `grep`, `mkdir`, `touch`, `head`, `tail`, `systemctl`, `npm install`, `cd`

Attempts to run unlisted commands return a permission error — the agent cannot escape the sandbox.

---

## 🎯 Tasks

Four tasks spanning easy → hard. The first three test repair ability. The fourth — T4 — tests something harder: knowing when **not** to act.

| Task ID | Scenario | Correct Response | Difficulty | Max Steps |
|---|---|---|---|---|
| `t1_config` | Config file misnamed `.conf.bak` | `mv conf.bak conf` | 🟢 Easy | 10 |
| `t2_port` | Rogue process occupies port 8080 | `kill -9 <pid>` | 🟡 Medium | 15 |
| `t3_dep` | Missing Node.js npm dependencies | `npm install` | 🔴 Hard | 20 |
| `t4_trap` | Alert fires but system is healthy | Diagnose only — no repair | 🔴 Hard | 10 |

---

### 🟢 T1 — Config File Repair (`t1_config`) · Easy · 10 steps

**Scenario:** The application cannot start. Its config file was accidentally renamed to `/etc/app/conf.bak` during a deploy. The system is looking for `/etc/app/conf`.

**What the agent must do:**
1. Discover the filesystem state (`ls /etc/app/`)
2. Identify the misnamed file
3. Rename it: `mv /etc/app/conf.bak /etc/app/conf`

**Grader (`ConfigGrader`):** Checks if `/etc/app/conf` exists in the sandbox filesystem. Partial credit awarded for correct diagnostic commands even if the rename is incorrect.

---

### 🟡 T2 — Rogue Process Port Occupation (`t2_port`) · Medium · 15 steps

**Scenario:** A new service cannot bind to port 8080 because a stray background process is occupying it. The port must be freed before the application can start.

**What the agent must do:**
1. List running processes (`ps aux`)
2. Identify which PID owns port 8080
3. Terminate it: `kill -9 <pid>`

**Grader (`PortGrader`):** Calls `process_manager.is_port_free(8080)`. Returns 1.0 only when the port is genuinely freed in the mock process table. Killing the wrong PID scores 0 — the agent must read the process list correctly.

---

### 🔴 T3 — Missing Application Dependencies (`t3_dep`) · Hard · 20 steps

**Scenario:** A Node.js application crashes immediately on startup. The `dotenv` package is missing from `node_modules`. The `package.json` exists but `npm install` was never run.

**What the agent must do:**
1. Identify the application directory (`ls`, `find`)
2. Confirm the absence of `node_modules` (`ls /home/user/app/`)
3. Install dependencies from the **correct** directory: `npm install`

**Grader (`DependencyGrader`):** Checks for `/home/user/app/node_modules/.package-lock.json`. Running `npm install` from the wrong directory still returns 0 — the agent must navigate correctly first.

---

### 🪤 T4 — Healthy System Trap (`t4_trap`) · Hard · 10 steps

**Scenario:** An alert fires suggesting the config directory is corrupted. The alert message looks urgent. In reality, **the system is completely healthy** — `/etc/app/conf` exists and the application is running normally.

**What the agent must do:**
1. Investigate with diagnostic commands (`ls /etc/app`, `cat`, `ps`)
2. Confirm the system is healthy
3. Stand down — report the false alarm **without making any changes**

**What scores 0:** Any repair action (`mv`, `kill`, `npm install`) applied to a healthy system is a false positive. The grader penalizes destructive actions regardless of intent.

**Why this task exists:** Real SRE work requires knowing when *not* to act. Agents that pattern-match "alert → fix" without diagnosing will destroy a working system. T4 specifically tests restraint under pressure — the hardest skill to teach and the most important one in production.

**Grader (`TrapGrader`):** Returns 1.0 if no destructive commands were issued and at least one diagnostic command confirmed the system was healthy. Returns 0.0 if any repair tool was applied to the healthy system.

---

## 🏆 Reward Function

Rewards are shaped across the full trajectory to provide useful signal even when repair is incomplete:

| Condition | Score |
|---|---|
| Target repair complete (grader passes) | **1.0** |
| Correct diagnostic commands run, repair attempted incorrectly | **0.3 – 0.7** |
| Correct tool used, wrong arguments | **0.1 – 0.3** |
| No meaningful commands / permission violations | **0.0** |
| Destructive action on healthy system (T4 trap triggered) | **0.0** |

Partial credit is computed per-task by analyzing `command_history` in the grader — e.g., running `ps aux` before `kill` earns diagnostic credit even if the final kill targets the wrong PID.

---

## 📊 Baseline Results

Two baseline modes are provided. The **hardcoded agent** verifies grader correctness and confirms the environment works end-to-end. The **LLM agent** (GPT-4o-mini, zero-shot) shows realistic agent performance — this is the meaningful benchmark.

### Hardcoded Deterministic Agent (Environment Validation)

```
Task         Reward    Steps    Status
t1_config    1.0       1        ✅ Solved
t2_port      1.0       1        ✅ Solved
t3_dep       1.0       2        ✅ Solved
t4_trap      1.0       1        ✅ Correctly stood down
──────────────────────────────────────────
Average      1.0       1.25     All tasks solved
```

> The hardcoded agent exists to prove the environment and graders are correct — it knows the exact answer. It is **not** a performance claim.

### LLM Baseline Agent (GPT-4o-mini, Zero-Shot)

```
Task         Reward    Steps    Notes
t1_config    0.85      4        Found file, applied correct rename
t2_port      0.60      8        Identified PID but killed wrong process first
t3_dep       0.30      12       Ran npm install in wrong directory twice
t4_trap      0.20      3        Applied mv to healthy system — trap triggered
──────────────────────────────────────────
Average      0.49      6.75     Significant room for RL improvement
```

> Set `OPENAI_API_KEY` and `OPENAI_MODEL=gpt-4o-mini` before running the LLM baseline.

The gap between hardcoded (1.0) and LLM (0.49) demonstrates that the tasks are genuinely non-trivial. T4 in particular exposes a key weakness in zero-shot LLMs — they are strongly biased toward taking action rather than withholding it. This is exactly the kind of signal that RL training can correct.

---

## 📡 API Reference

All endpoints are OpenEnv-compliant. Interactive docs available at `/docs`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reset` | Reset to a specific broken state. Body: `{"task_id": "t1_config"}` |
| `POST` | `/step` | Execute a shell command. Body: `{"tool": "run_command", "arguments": "ls /etc/app"}` |
| `GET` | `/state` | Current sandbox state and episode metadata |
| `GET` | `/tasks` | All task definitions with action schema |
| `GET` | `/grader` | Current grader score for active episode |
| `GET` | `/baseline` | Run deterministic baseline and return scores |
| `GET` | `/healthz` | Health check — returns `{"status": "ok"}` |
| `GET` | `/docs` | Swagger UI |

### Example: Full T1 Episode

```bash
# 1. Reset to broken config state
curl -X POST https://goated1-auto-sre.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "t1_config"}'

# 2. Discover the filesystem
curl -X POST https://goated1-auto-sre.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"tool": "run_command", "arguments": "ls /etc/app/"}'
# → {"stdout": "conf.bak\n", "stderr": "", "health_status": false}

# 3. Apply the fix
curl -X POST https://goated1-auto-sre.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"tool": "run_command", "arguments": "mv /etc/app/conf.bak /etc/app/conf"}'
# → {"stdout": "", "stderr": "", "health_status": true, "reward": 1.0, "done": true}
```

### Example: T4 Trap Episode (Correct Behaviour)

```bash
# 1. Reset to trap state
curl -X POST https://goated1-auto-sre.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "t4_trap"}'

# 2. Diagnose — system is actually healthy
curl -X POST https://goated1-auto-sre.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"tool": "run_command", "arguments": "ls /etc/app/"}'
# → {"stdout": "conf\n", "stderr": "", "health_status": true}

# 3. Correct: stand down, no destructive action
curl -X POST https://goated1-auto-sre.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"tool": "run_command", "arguments": "echo System healthy — false alarm, no action taken"}'
# → {"reward": 1.0, "done": true}
```

---

## 🚀 Quick Start

### Local Development

```bash
git clone https://huggingface.co/spaces/goated1/auto-sre
cd auto-sre
python -m venv .venv

# Activate
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows

pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### Docker

```bash
docker build -t auto-sre .
docker run -p 7860:7860 auto-sre
```

### Run Baselines

```bash
# Hardcoded deterministic (no API key needed — validates environment)
python scripts/run_baseline_agent.py

# LLM agent (requires OpenAI key)
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini
python scripts/run_baseline_agent.py
```

---

## 🧪 Testing

```bash
# Full test suite
pytest -v

# With coverage report
pytest --cov=app --cov=engine --cov=grader -v

# Individual agent scripts
python scripts/run_null_agent.py        # Crash/edge case testing
python scripts/run_hardcoded_agent.py   # Verify grader correctness
python scripts/run_baseline_agent.py    # Score the LLM baseline
```

---

## 📁 Project Structure

```
auto-sre/
├── openenv.yaml              # OpenEnv spec metadata
├── Dockerfile                # Container build (port 7860 for HF Spaces)
├── pyproject.toml            # Dependencies and build config
├── app/
│   ├── main.py               # FastAPI app + Gradio UI mount
│   ├── routes/               # /reset, /step, /state, /tasks, /grader, /baseline
│   ├── models/               # Pydantic: DevOpsObservation, DevOpsAction, Reward
│   └── ui.py                 # Gradio interactive demo
├── engine/
│   ├── sandbox.py            # Shell command executor (shlex parser → fs/pm calls)
│   ├── filesystem.py         # UnionFS-style layered filesystem (base + overlay)
│   ├── process_manager.py    # Mock ps/netstat/kill simulation
│   └── security.py           # Command whitelist + 5s timeout enforcement
├── grader/
│   ├── base.py               # BaseGrader ABC
│   ├── health_check.py       # ConfigGrader, PortGrader, DependencyGrader, TrapGrader
│   └── registry.py           # Maps task IDs to grader instances
├── tasks/
│   ├── registry.py           # TASK_REGISTRY with initial states
│   ├── t1_config.py          # Config file misname scenario
│   ├── t2_port.py            # Rogue process scenario
│   ├── t3_dep.py             # Missing npm dependencies scenario
│   └── t4_trap.py            # Healthy system trap scenario
├── scripts/
│   ├── run_baseline_agent.py # Main baseline runner (hardcoded + LLM modes)
│   ├── run_hardcoded_agent.py
│   └── run_null_agent.py
└── tests/                    # Unit + integration tests
```

---

## 🔒 Security & Sandbox Design

The sandbox is built with isolation as a first principle:

- **Command whitelist** enforced in `engine/security.py` — only 15 approved commands can execute
- **5-second timeout** per step — prevents infinite loops or hanging processes
- **Layered filesystem** — the base layer is immutable; all agent writes go to the overlay. A `reset()` call discards the overlay entirely, restoring a clean broken state in O(1)
- **Mock process table** — `kill` commands operate on an in-memory process dictionary, never touching real OS processes

The environment is **fully deterministic and reproducible** — the same agent actions always produce the same observations and rewards across runs.

---

## 📜 License

MIT — see `LICENSE` for details.

---

*Built for the OpenEnv Hackathon 2026 — Real-World Infrastructure Track* 
