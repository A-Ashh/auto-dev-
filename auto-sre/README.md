---
title: Auto-SRE
emoji: 🚨
colorFrom: indigo
colorTo: slate
sdk: gradio
sdk_version: "4.26.0"
app_file: app.py
pinned: false
---

# 🚨 Auto-SRE — AI-Powered SRE Training Platform

[![OpenEnv Compliant](https://img.shields.io/badge/OpenEnv-Phase%201%20%26%202%20Compliant-brightgreen)](https://huggingface.co/spaces/goated1/auto-sre)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Hugging%20Face%20Spaces-blue)](https://huggingface.co/spaces/goated1/auto-sre)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **An OpenEnv-compliant, interactive SRE diagnostic sandbox powered by AI.** Evaluate LLM agents on realistic Linux infrastructure repair tasks — with a full web terminal, AI Copilot hints, and a one-click Demo Mode.

---

## 🌐 Live Demo

**[→ Try it on Hugging Face Spaces](https://huggingface.co/spaces/goated1/auto-sre)**

---

## 🎯 What is Auto-SRE?

Auto-SRE is an interactive Site Reliability Engineering (SRE) training and evaluation environment built for the OpenEnv hackathon. It provides:

- A **mock Linux sandbox** where AI agents or humans diagnose and fix broken infrastructure
- A **FastAPI backend** fully compliant with OpenEnv Phase 1 & Phase 2 validation
- An **interactive web terminal UI** built with Gradio
- An **AI Copilot** that provides context-aware debugging hints on demand
- A **Demo Mode** that auto-plays the optimal solution for each task

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

```python
_SCORE_MIN = 0.01
_SCORE_MAX = 0.989

def _safe_score(raw: float) -> float:
    score = float(raw)
    return max(_SCORE_MIN, min(_SCORE_MAX, score))
```

This prevents the `0.0` or `1.0` boundary values that cause OpenEnv Phase 2 validation failures.

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

### 3. Configure environment
```bash
cp .env.example .env
# Edit .env — add OPENAI_API_KEY if you want live AI Copilot hints
```

### 4. Run locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860
```

Then open **http://localhost:7860** in your browser.

---

## 🧪 Validation

### Run all tests
```bash
pytest tests/
```

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

---

## 🏆 OpenEnv Compliance

- ✅ Phase 1: STDOUT format `[STEP] ... reward=X.XX` / `[END] ... rewards=...`
- ✅ Phase 2: All rewards strictly in open interval `(0, 1)` — no `0.0` or `1.0` values
- ✅ All 10 tasks registered in `openenv.yaml` with correct grader paths
- ✅ `/reset`, `/step`, `/grader`, `/healthz` endpoints functional

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
