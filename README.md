---
title: Auto-SRE
emoji: 🚨
colorFrom: indigo
colorTo: purple
sdk: gradio
sdk_version: "4.44.1"
python_version: "3.11"
app_file: auto-sre/app.py
pinned: false
---

# 🚨 Auto-SRE — AI-Powered SRE Training Platform

[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Phase%201%20%26%202%20Compliant-brightgreen)](https://huggingface.co/spaces/goated1/auto-sre)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Hugging%20Face%20Spaces-blue)](https://huggingface.co/spaces/goated1/auto-sre)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> *"The server is down. You have 15 steps. Go."*

**Auto-SRE** is an [OpenEnv](https://huggingface.co/openenv)-compliant environment where AI agents learn to diagnose and repair broken Linux infrastructure — just like an on-call Site Reliability Engineer.

Unlike toy benchmarks, agents must execute real shell commands inside a sandboxed system, read actual error signals, and apply the correct fix — **in the correct order**. Wrong guesses don't score. Half-correct attempts earn partial credit. Systematic diagnosis earns full marks.

🌐 **Live Demo:** [Try it on Hugging Face Spaces](https://huggingface.co/spaces/goated1/auto-sre)

---

## ✨ What's New (v2.0)

| Feature | Description |
|---|---|
| 🆕 **T7–T10 Hard Tasks** | 4 new enterprise-grade failure scenarios |
| 🤖 **Multi-Agent System** | Commander → Planner → Executor → Critic pipeline |
| 📈 **RL Training Pipeline** | Unsloth + TRL GRPO across all 10 tasks with reward curve |
| 🔗 **Dependency Ordering** | T9: wrong restart sequence is penalized |
| 🔐 **Secret Injection** | T10: echo redirection writes to config files |
| 📊 **Per-Task Metrics** | Training plots per-task reward + overall curve |

---

## 🎯 What is Auto-SRE?

Auto-SRE is an interactive Site Reliability Engineering (SRE) training and evaluation environment built for the OpenEnv hackathon. It provides:

<<<<<<< Updated upstream
- A **mock Linux sandbox** where AI agents or humans diagnose and fix broken infrastructure
- A **FastAPI backend** fully compliant with OpenEnv Phase 1 & Phase 2 validation
- An **interactive web terminal UI** built with Gradio
- An **AI Copilot** that provides context-aware debugging hints on demand
- A **Demo Mode** that auto-plays the optimal solution for each task
=======
- Misconfigured files that block application startup
- Rogue processes holding ports hostage
- Missing dependencies that crash deployments
- Disk-full emergencies from runaway log files
- Memory leaks triggering kernel OOM kills
- Cascading failures across service dependency chains

**Today:** A human engineer SSHs in, runs `ps aux`, reads logs, and fixes it manually.
**Tomorrow:** An AI agent does the same — faster, at 3 AM, without waking anyone up.

Auto-SRE is the training and evaluation ground for that agent.
>>>>>>> Stashed changes

---

## ✨ Features

### 🖥️ Interactive Web Terminal
A fully functional browser-based terminal where you can run shell commands like a real SRE:
- `ls`, `cat`, `ps`, `kill`, `mv`, `rm`, `find`, `grep`, `npm install`, `systemctl`, and more
- Real-time reward score and system health display
- Command history log


### 🎬 Demo Mode
Click **▶ Run Demo** to watch the AI solve any task automatically, showing the optimal command sequence and final reward score. Guarantees judges always see a successful resolution.

### 🤖 AI Copilot
Click **🤖 Ask AI Copilot for Hint** to get a context-aware debugging hint:
- Reads your current task and command history from the UI
- Queries OpenAI (if configured) for a personalized 1-2 line hint
- Falls back gracefully to curated static hints if no API key is set
- **100% UI-isolated** — does not touch the backend or affect rewards

### 📌 Task Descriptions
Each scenario shows its description immediately on selection, so judges and users understand the problem context instantly.

---

## 🗂️ Scenario Tasks

| ID | Name | Difficulty | Description |
|----|------|------------|-------------|
| `t1_config` | Config File Repair | Easy | Rename `conf.bak` → `conf` to restore app startup |
| `t2_port` | Port Occupation | Medium | Kill the rogue process blocking port 8080 |
| `t3_dep` | Missing Dependencies | Hard | Run `npm install` to restore missing Node.js packages |
| `t4_trap` | Healthy System Trap | Hard | Recognize an already-healthy system and avoid unnecessary actions |
| `t5_disk_full` | Disk Full — Log Overflow | Medium | Delete the massive `/var/log/syslog` file consuming all disk space |
| `t6_oom_killer` | OOM Killer — Memory Hog | Hard | Kill the rogue `memory_hog` process (PID 999) leaking RAM |
| `t7_cascading_meltdown` | Cascading Meltdown | Hard | Rogue logger floods disk causing DB crash. 4-step ordered fix required. |
| `t8_memory_leak_loop` | Memory Leak Restart Loop | Hard | Service in crash-restart loop due to memory leak. Kill, stabilize, restore. |
| `t9_dependency_chain_failure` | Dependency Chain Failure | Hard | App fails due to cascade dependency. Trace app->cache->db and restore in order. |
| `t10_config_secret_failure` | Config Secret Failure | Hard | Invalid secret causes auth crash. Find bad secret, fix, restart. |

---

## 📊 Validation Report & Agent Comparison

**Validation Results:**
* API_STATUS: PASS
* TASKS_STATUS: PASS
* EDGE_TESTS: PASS
* DETERMINISM: PASS
* RL_READY: PASS
* OVERALL: PASS

**Agent Comparison:**
- **Null agent** → Performs random or empty behavior (low base reward).
- **Hardcoded agent** → Fixed paths; achieves only partial success with randomized environment states.
- **Multi-agent system** → Demonstrates adaptive reasoning (Commander, Planner, Executor, Critic) to evaluate and recover dynamically.
- **Baseline agent** → Optimal state-machine controller, achieving near-optimal performance (~0.97 average reward) across all tasks.

---

## 🧠 Reinforcement Learning Support

Auto-SRE fully supports training Language Models via reinforcement learning. 
- A **GRPO training pipeline** is already implemented (`scripts/train_grpo.py`).
- The environment natively supports the RL loop: **step-based interaction**, strictly bounded **reward signals**, and **deterministic outcomes**.

⚠️ **Training will be executed during the hackathon using provided compute resources.** (We do not claim training results at this phase).

---

## 🏗️ Architecture

```
auto-sre/
├── app/
│   ├── main.py          # FastAPI app entrypoint + Gradio mount
│   ├── ui.py            # Gradio web terminal UI + AI Copilot + Demo Mode
│   └── routes/
│       ├── reset.py     # POST /reset — initialize task environment
│       ├── step.py      # POST /step — execute shell command
│       ├── grader.py    # GET /grader — evaluate current state
│       ├── state.py     # GET /state — read environment snapshot
│       ├── tasks.py     # GET /tasks — list all registered tasks
│       └── _session.py  # In-memory session singleton
├── tasks/
│   ├── registry.py      # Task registry (t1–t10)
│   ├── t1_config.py     # Config file repair scenario
│   ├── t2_port.py       # Port occupation scenario
│   ├── t3_dep.py        # Missing dependencies scenario
│   ├── t4_trap.py       # Healthy system trap scenario
│   ├── t5_disk_full.py  # Disk full scenario
│   ├── t6_oom_killer.py # OOM killer scenario
│   ├── t7_cascading_meltdown.py # Cascading meltdown scenario
│   ├── t8_memory_leak_loop.py # Memory leak loop scenario
│   ├── t9_dependency_chain_failure.py # Dependency chain scenario
│   └── t10_config_secret_failure.py # Secret configuration scenario
├── grader/
│   ├── base.py          # BaseGrader abstract class
│   └── health_check.py  # All graders (ConfigGrader, PortGrader, ..., DiskGrader, OOMGrader)
├── engine/
│   ├── sandbox.py       # Mock shell command interpreter
│   ├── filesystem.py    # MockFilesystem (union-FS style base + overlay)
│   ├── process_manager.py # MockProcessManager
│   └── security.py      # Command allowlist + timeout guard
├── scripts/
│   ├── run_baseline_agent.py  # Hardcoded + LLM agent runner
│   ├── multi_agent.py         # Advanced multi-agent orchestrator (Commander/Planner/Executor/Critic)
│   └── train_grpo.py          # Unsloth GRPO RL training pipeline
├── inference.py         # OpenEnv validator entry point
└── openenv.yaml         # OpenEnv environment declaration
```

---

## 🔒 Reward Safety

All rewards are strictly clamped to the open interval **(0.01, 0.989)** using a single `_safe_score()` function:
=======
```
Agent                     Auto-SRE Environment
  │                              │
  │── POST /reset ──────────────▶│  Broken state initialized (randomized PIDs/ports)
  │◀─ Observation ───────────────│  (stdout, stderr, cwd, health_status)
  │                              │
  │── POST /step ───────────────▶│  Shell command executed in sandbox
  │◀─ (obs, reward, done, info) ─│  Grader evaluates system state
  │                              │
  │      [repeat up to max_steps]│
```

### World Model

Each episode seeds a **stateful world model** into `sandbox.state`:

```python
{
  "disk_usage": 100,        # 0–100%
  "memory_usage": 97,       # 0–100%
  "services_running": {"db": False, "app": True},
  "rogue_pid": 5329,        # randomized per episode
  "config_valid": False,
}
```

Agent actions mutate this state. The grader reads it to compute reward.

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
`ls`, `cat`, `pwd`, `echo`, `ps`, `mv`, `kill`, `find`, `grep`, `mkdir`, `touch`,
`head`, `tail`, `systemctl`, `npm`, `cd`, `rm`, `df`, `du`, `free`, `top`, `ss`, `netstat`, `lsof`

---

## 🎯 Task Curriculum (t1–t10)

Ten tasks across three difficulty tiers. Each requires **multi-step sequential reasoning** — no single-command shortcuts.

### Difficulty Tiers

| Tier | Tasks | Theme |
|---|---|---|
| 🟢 **Easy** | t1, t2, t3 | Single-failure diagnosis + repair |
| 🟡 **Medium** | t4, t5, t6 | Adversarial + resource exhaustion |
| 🔴 **Hard** | t7, t8, t9, t10 | Cascading failures + ordering constraints |

### Full Task Table

| Task | Scenario | Steps Required | Key Challenge |
|---|---|---|---|
| `t1_config` | Config file misnamed `conf.bak` | 3+ | locate → rename → restart |
| `t2_port` | Randomized rogue process on port | 3+ | netstat → ps → kill |
| `t3_dep` | Missing npm dependencies | 4+ | inspect → cd → install → verify |
| `t4_trap` | Healthy system — alert is false | 3+ | diagnose only, no repair |
| `t5_disk_full` | Randomized log fills disk 100% | 3+ | df → find → rm |
| `t6_oom_killer` | Rogue memory hog, random PID | 3+ | free → ps → kill |
| `t7_cascading_meltdown` | Rogue logger → disk full → DB crash | 4 ordered | df → rm log → kill rogue → restart DB |
| `t8_memory_leak_loop` | Service crash-restart loop, memory at 97% | 4 ordered | free → ps → kill → restart service |
| `t9_dependency_chain_failure` | db→cache→app all down | 5 ordered | log trace → restart db → cache → app |
| `t10_config_secret_failure` | Wrong DB secret in config | 5 ordered | log → inspect → echo secret → restart |

### Anti-Hardcoding: Randomization

Every episode randomizes:
- **Rogue PIDs** (T2, T6, T7, T8): `random.randint(300, 9999)`
- **Port numbers** (T2): `random.randint(8000, 9000)`
- **Log filenames** (T5): `syslog-{random_id}`

Agents **cannot** memorize answers.

---

## 🏆 Reward System

### Multi-Component Dense Rewards

Every task uses **milestone-based accumulation** — reward increases at each correct step:

```python
# Example: T7 CascadeGrader
total = 0.0
if "df" in history:           total += 0.15  # diagnosed disk
if log_cleared:               total += 0.25  # cleared logs
if rogue_dead:                total += 0.25  # killed process
if db_running:                total += 0.25  # restarted DB
```

### Reward Components

| Component | Effect |
|---|---|
| **Progress reward** | +0.10–0.25 per completed step |
| **Correctness reward** | +0.25–0.45 for key action |
| **Sequence correctness** | Out-of-order penalty (T9) |
| **Efficiency bonus** | +0.05 if solved in ≤6 steps |
| **Excessive commands** | −0.08 if >10–15 steps |
| **Invalid command** | reward=0.01, done=False |

### Strict Bounds

All rewards clamped to **(0.01, 0.989)** — never `0.0` or `1.0`:
>>>>>>> Stashed changes

```python
_SCORE_MIN = 0.01
_SCORE_MAX = 0.989

def _safe_score(raw: float) -> float:
    score = float(raw)
    return max(_SCORE_MIN, min(_SCORE_MAX, score))
```

<<<<<<< Updated upstream
This prevents the `0.0` or `1.0` boundary values that cause OpenEnv Phase 2 validation failures.
=======
Double-enforced: at grader level AND at API route level.

---

## 🛡️ Anti-Reward Hacking

| Protection | Mechanism |
|---|---|
| **No step skipping** | T7/T9: prerequisites enforced via state checks |
| **No fake restart** | `systemctl restart db` fails if disk full or rogue alive |
| **Randomized state** | PIDs/ports change every episode |
| **Command whitelist** | `security.py` — only safe commands allowed |
| **Max step limit** | Episode auto-terminates at `max_steps` |
| **Wrong-order penalty** | T9: restarting cache before db = −0.15 |

---

## 🤖 Multi-Agent System

`scripts/multi_agent.py` implements a 4-role pipeline:

```
Commander  →  Planner  →  Executor  →  Critic
    │             │            │           │
  loads         builds       runs      evaluates
  all tasks    action plan  commands   outcome
                             +adapts   → retry?
```

- **Commander**: fetches task list from `/tasks` (no hardcoding)
- **Planner**: builds deterministic symbolic plan per task type
- **Executor**: executes plan, parses `ps` output to dynamically inject `kill <pid>` and `rm <logfile>`
- **Critic**: reads `/grader`, decides re-plan if reward < 0.90 (up to 3 iterations)

```bash
# Run all tasks
python scripts/multi_agent.py

# Run specific task
python scripts/multi_agent.py t7_cascading_meltdown
```

---

## 🚀 RL Training Pipeline

`scripts/train_grpo.py` uses **Unsloth + TRL GRPOTrainer** to fine-tune `Qwen2.5-1.5B-Instruct` across all 10 tasks.

### Training Architecture

```python
# Task selection: round-robin curriculum (easy → hard)
task_id = TASKS[episode % len(TASKS)]  # dynamically loaded

# Reward function: live environment feedback
score = run_env_episode(task_id, commands)  # hits /reset + /step + /grader
```

### Running Training (Google Colab)

```bash
!pip install unsloth trl matplotlib

# Point to your deployed environment
AUTO_SRE_URL=https://goated1-auto-sre.hf.space python scripts/train_grpo.py
```

### Training Results

After training, `reward_curve.png` is saved with:
- **Overall reward curve** across all training steps
- **Per-task bar chart** showing average reward per scenario

```
[REWARD LOG] Avg: 0.0100 | Step 1    ← model starts with random commands
[REWARD LOG] Avg: 0.1523 | Step 8
[REWARD LOG] Avg: 0.3847 | Step 24
[REWARD LOG] Avg: 0.6201 | Step 48   ← model learns systematic diagnosis
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/reset` | Init task. Body: `{"task_id": "t1_config"}` |
| `POST` | `/step` | Run command. Body: `{"tool": "run_command", "arguments": "ls /etc/app"}` |
| `GET` | `/state` | Full sandbox state snapshot |
| `GET` | `/tasks` | All 10 task definitions |
| `GET` | `/grader` | Current grader score (non-destructive) |
| `GET` | `/healthz` | Health check |
| `GET` | `/docs` | Swagger UI |

### Example: T9 Dependency Chain

```bash
# Reset
curl -X POST http://localhost:8000/reset -d '{"task_id": "t9_dependency_chain_failure"}'

# Trace the chain
curl -X POST http://localhost:8000/step -d '{"command": "cat /var/log/app.log"}'
# → stderr mentions cache failure

# Fix root first — wrong order is penalized!
curl -X POST http://localhost:8000/step -d '{"command": "systemctl restart db"}'
curl -X POST http://localhost:8000/step -d '{"command": "systemctl restart cache"}'
curl -X POST http://localhost:8000/step -d '{"command": "systemctl restart app"}'
# → {"reward": 0.989, "done": true}
```
>>>>>>> Stashed changes

---

## 🚀 Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/goatedAreeeb/auto-dev-.git
cd auto-dev-/auto-sre
```

### 2. Install dependencies
```bash
pip install -e ".[dev]"
```

<<<<<<< Updated upstream
### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — add OPENAI_API_KEY if you want live AI Copilot hints
```

### 4. Run locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
=======
# Optional: AI Copilot
cp .env.example .env
# Add OPENAI_API_KEY to .env

python -m uvicorn app.main:app --reload --port 8000
# API: http://localhost:8000
# UI:  http://localhost:8000/
>>>>>>> Stashed changes
```

Then open **http://localhost:7860** in your browser.

---

## 🧪 Validation

### Run all tests
```bash
pytest tests/
```

<<<<<<< Updated upstream
### Run the baseline agent
```bash
python scripts/run_baseline_agent.py
```

Expected output (Deterministic, state-driven rule-based agent):
```json
{
  "results": [
    {"task_id": "t1_config", "reward": 0.989, "done": true},
    {"task_id": "t2_port",   "reward": 0.989, "done": true},
    {"task_id": "t3_dep",    "reward": 0.989, "done": true},
    {"task_id": "t4_trap",   "reward": 0.989, "done": true},
    {"task_id": "t5_disk_full",  "reward": 0.989, "done": true},
    {"task_id": "t6_oom_killer", "reward": 0.989, "done": true},
    {"task_id": "t7_cascading_meltdown", "reward": 0.989, "done": true},
    {"task_id": "t8_memory_leak_loop", "reward": 0.989, "done": true},
    {"task_id": "t9_dependency_chain_failure", "reward": 0.989, "done": true},
    {"task_id": "t10_config_secret_failure", "reward": 0.989, "done": true}
  ],
  "average_reward": 0.989
}
```

### Run the Multi-Agent System
```bash
python scripts/multi_agent.py
```

Expected output (Adaptive Reasoning mode):
```json
[
  {"task_id": "t1_config", "reward": 0.97, "commands_used": 2},
  {"task_id": "t2_port", "reward": 0.75, "commands_used": 17},
  {"task_id": "t3_dep", "reward": 0.97, "commands_used": 3},
  {"task_id": "t4_trap", "reward": 0.97, "commands_used": 3},
  {"task_id": "t5_disk_full", "reward": 0.97, "commands_used": 3},
  {"task_id": "t6_oom_killer", "reward": 0.97, "commands_used": 4},
  {"task_id": "t7_cascading_meltdown", "reward": 0.97, "commands_used": 6},
  {"task_id": "t8_memory_leak_loop", "reward": 0.97, "commands_used": 5},
  {"task_id": "t9_dependency_chain_failure", "reward": 0.9, "commands_used": 6},
  {"task_id": "t10_config_secret_failure", "reward": 0.95, "commands_used": 5}
]

Average reward across all tasks: 0.9390
```

> Unlike the baseline agent which uses deterministic state-machine logic, the Multi-Agent system relies on a **Commander → Planner → Executor → Critic** hierarchy for dynamic self-correction and exploration. It achieves a **highly competitive `0.9390` average reward** across all 10 tasks, successfully demonstrating adaptive reasoning and recovery from failure states.

### Check available tasks
```bash
curl http://localhost:7860/tasks
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Initialize a task environment |
| `POST` | `/step` | Execute a shell command |
| `GET` | `/grader` | Get current reward and done status |
| `GET` | `/state` | Get full environment snapshot |
| `GET` | `/tasks` | List all available task IDs |
| `GET` | `/healthz` | Health check |

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | No | — | Enables live AI Copilot hints |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | LLM proxy URL |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for AI Copilot |
| `STEP_TIMEOUT` | No | `5` | Max seconds per command |
=======
### Run Multi-Agent Demo

```bash
python scripts/multi_agent.py
```

### Run Baseline Agent

```bash
python scripts/run_baseline_agent.py
```
>>>>>>> Stashed changes

---

## 🏆 OpenEnv Compliance

<<<<<<< Updated upstream
- ✅ Phase 1: STDOUT format `[STEP] ... reward=X.XX` / `[END] ... rewards=...`
- ✅ Phase 2: All rewards strictly in open interval `(0, 1)` — no `0.0` or `1.0` values
- ✅ All 10 tasks registered in `openenv.yaml` with correct grader paths
- ✅ `/reset`, `/step`, `/grader`, `/healthz` endpoints functional
=======
```
auto-sre/
├── openenv.yaml              # OpenEnv spec — all 10 tasks
├── app/
│   ├── main.py               # FastAPI + Gradio mount
│   ├── ui.py                 # Web terminal, Demo Mode, AI Copilot
│   └── routes/               # /reset /step /state /tasks /grader
├── engine/
│   ├── sandbox.py            # Shell interpreter + echo redirection
│   ├── filesystem.py         # UnionFS-style layered filesystem
│   ├── process_manager.py    # Mock ps/netstat/kill
│   └── security.py           # Command whitelist (df/du/free/top added)
├── grader/
│   └── health_check.py       # 10 graders — all with _safe_score()
├── tasks/
│   ├── registry.py           # TASK_REGISTRY — single source of truth
│   ├── t1_config.py → t6_oom_killer.py
│   ├── t7_cascading_meltdown.py   # 4-step cascade
│   ├── t8_memory_leak_loop.py     # crash-restart loop
│   ├── t9_dependency_chain_failure.py  # ordered restart
│   └── t10_config_secret_failure.py   # secret injection
└── scripts/
    ├── run_baseline_agent.py  # hardcoded + LLM baselines
    ├── train_grpo.py          # Unsloth GRPO — all 10 tasks
    └── multi_agent.py         # Commander→Planner→Executor→Critic
```
>>>>>>> Stashed changes

---

## 📄 License

<<<<<<< Updated upstream
MIT License — see [LICENSE](LICENSE) for details.
=======
- ✅ **Phase 1**: STDOUT format `[STEP] ... reward=X.XX`
- ✅ **Phase 2**: All rewards strictly in `(0.01, 0.989)` — double-enforced
- ✅ All 10 tasks registered in `openenv.yaml` — synced with `TASK_REGISTRY`
- ✅ `/reset`, `/step`, `/state`, `/tasks`, `/grader`, `/healthz` all functional
- ✅ Invalid commands → `done=False`, `reward=0.01` (no crash)
- ✅ World model state mutated by actions and read by graders

---

## 🔧 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `AUTO_SRE_URL` | No | `http://localhost:8000` | Environment URL for training/agents |
| `OPENAI_API_KEY` | No | — | Enables live AI Copilot hints in UI |
| `OPENAI_BASE_URL` | No | `https://api.openai.com/v1` | LLM proxy endpoint |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | Model for AI Copilot |
| `STEP_TIMEOUT` | No | `5` | Max seconds per sandbox command |

---

## 📜 License

MIT — see `LICENSE` for details.

---

*Built for the OpenEnv Hackathon 2026 — Real-World Infrastructure Track*
>>>>>>> Stashed changes
