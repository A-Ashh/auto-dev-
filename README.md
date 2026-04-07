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
    AI agents that can debug and fix real production systems — not toy problems.
    ## 🌐 Live Demo
👉 https://huggingface.co/spaces/goated1/auto-sre

> *"The server is down. You have 10 steps. Go."*

**Auto-SRE** is an [OpenEnv](https://huggingface.co/openenv)-compliant environment where AI agents learn to diagnose and repair broken Linux infrastructure — just like an on-call Site Reliability Engineer.

Unlike toy benchmarks, agents must execute real shell commands inside a sandboxed system, read actual error signals, and apply the correct fix. Wrong guesses don't score. Half-correct attempts earn partial credit. Systematic diagnosis earns full marks.

---

## 🧠 Why This Environment Exists

Production infrastructure breaks in predictable ways. Every day, engineers spend hours on:

- Misconfigured files that block application startup
- Rogue processes holding ports hostage
- Missing dependencies that crash deployments

**Today:** A human engineer SSHs in, runs `ps aux`, reads logs, and fixes it manually.  
**Tomorrow:** An AI agent does the same — faster, at 3 AM, without waking anyone up.

Auto-SRE is the training and evaluation ground for that agent. It is the **It is one of the first OpenEnv environments focused on real-world DevOps/SRE infrastructure repair.**, filling a gap that currently has no equivalent.

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

Three tasks spanning easy → hard, each requiring progressively more diagnostic steps before the correct repair action.

### 🟢 T1 — Config File Repair (`t1_config`) · Easy · 10 steps

**Scenario:** The application cannot start. Its config file was accidentally renamed to `/etc/app/conf.bak` during a deploy. The system is looking for `/etc/app/conf`.

**What the agent must do:**
1. Discover the filesystem state (`ls /etc/app/`)
2. Identify the misnamed file
3. Rename it: `mv /etc/app/conf.bak /etc/app/conf`

**Grader (`ConfigGrader`):** Checks if `/etc/app/conf` exists in the sandbox filesystem. Binary outcome — but partial credit is awarded for correct diagnostic commands.

---

### 🟡 T2 — Rogue Process Port Occupation (`t2_port`) · Medium · 15 steps

| Task ID     | Failure                           | Solution            | Difficulty | Max Steps |
|:------------|:----------------------------------|:--------------------|:-----------|:----------|
| `t1_config` | Config file misnamed `.conf.bak`  | `mv conf.bak conf`  | Easy       | 10        |
| `t2_port`   | Rogue process occupies port 8080  | `kill -9 <pid>`     | Medium     | 15        |
| `t3_dep`    | Missing Node.js npm dependencies  | `npm install`       | Hard       | 20        |
| `t4_trap`   | Healthy System Trap               | `ls /etc/app`       | Hard       | 10        |

**What the agent must do:**
1. List running processes (`ps aux`) or check ports
2. Identify which PID owns port 8080
3. Terminate it: `kill -9 <pid>`

**Grader (`PortGrader`):** Calls `process_manager.is_port_free(8080)`. Returns 1.0 only when the port is genuinely freed in the mock process table — the agent cannot fake it.

---

### 🔴 T3 — Missing Application Dependencies (`t3_dep`) · Hard · 20 steps

**Scenario:** A Node.js application crashes immediately on startup. The `dotenv` package (and its dependencies) are missing from `node_modules`. The package.json exists but `npm install` was never run.

**What the agent must do:**
1. Identify the application directory (`ls`, `find`)
2. Confirm the absence of `node_modules` (`ls /home/user/app/`)
3. Install dependencies: `npm install` (run from correct directory)

| Task        | Reward | Steps |
|:------------|:-------|:------|
| `t1_config` | 1.0    | 1     |
| `t2_port`   | 1.0    | 1     |
| `t3_dep`    | 1.0    | 2     |
| `t4_trap`   | 1.0    | 1     |
| **Average** | **1.0**|       |

---

## 🏆 Reward Function

Rewards are shaped across the full trajectory to provide useful signal even when repair is incomplete:

| Condition | Score |
|---|---|
| Target repair complete (grader passes) | **1.0** |
| Correct diagnostic commands run, repair attempted incorrectly | **0.3 – 0.7** |
| Correct tool used, wrong arguments | **0.1 – 0.3** |
| No meaningful commands / permission violations | **0.0** |

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
─────────────────────────────────────
Average      1.0       1.3      All tasks solved
```

> The hardcoded agent exists to prove the environment and graders are correct — it knows the exact answer. It is not a performance claim.

### LLM Baseline Agent (GPT-4o-mini, Zero-Shot)

```
Task         Reward    Steps    Notes
t1_config    0.85      4        Found file, applied correct rename
t2_port      0.60      8        Identified PID but killed wrong process first
t3_dep       0.30      12       Ran npm install in wrong directory twice
─────────────────────────────────────
Average      0.58      8.0      Significant room for RL improvement
```

> Set `OPENAI_API_KEY` and `OPENAI_MODEL=gpt-4o-mini` before running the LLM baseline.

The gap between hardcoded (1.0) and LLM (0.58) demonstrates that the tasks are genuinely non-trivial — there is meaningful signal for an RL agent to learn from.

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
curl -X POST https://your-space.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "t1_config"}'

# 2. Discover the filesystem
curl -X POST https://your-space.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"tool": "run_command", "arguments": "ls /etc/app/"}'
# → {"stdout": "conf.bak\n", "stderr": "", "health_status": false}

# 3. Apply the fix
curl -X POST https://your-space.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"tool": "run_command", "arguments": "mv /etc/app/conf.bak /etc/app/conf"}'
# → {"stdout": "", "stderr": "", "health_status": true, "reward": 1.0, "done": true}
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
│   ├── health_check.py       # ConfigGrader, PortGrader, DependencyGrader
│   └── registry.py           # Maps task IDs to grader instances
├── tasks/
│   ├── registry.py           # TASK_REGISTRY with initial broken states
│   ├── t1_config.py          # Config file misname scenario
│   ├── t2_port.py            # Rogue process scenario
│   └── t3_dep.py             # Missing npm dependencies scenario
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

This means the environment is **fully deterministic and reproducible** — the same agent actions always produce the same observations and rewards.

---

## 📜 License

MIT — see `LICENSE` for details.

---

