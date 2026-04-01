---
title: Auto-SRE
emoji: 🚀
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---
# Auto-SRE: OpenEnv for AI SRE Agent Evaluation

An **OpenEnv-compliant** environment for evaluating AI agents' ability to diagnose and repair simulated Linux infrastructure failures using standard CLI tools.

> **Domain:** Site Reliability Engineering (SRE) — real-world infrastructure repair tasks that DevOps engineers face daily.

---

## 🎯 Environment Description & Motivation

AI agents and LLMs are increasingly used in DevOps automation, but there is no standardized benchmark for evaluating an AI's ability to diagnose and repair live Linux infrastructure issues.

Auto-SRE fills this gap by providing a **sandboxed, deterministic Linux-like environment** where agents must use CLI tools to fix broken systems — exactly like a real junior SRE would.

---

## 📡 API Endpoints

| Method | Endpoint    | Description                                    |
|:-------|:------------|:-----------------------------------------------|
| POST   | `/reset`    | Reset environment to a specific broken state   |
| POST   | `/step`     | Execute a shell command as an agent action     |
| GET    | `/state`    | Get current environment metadata               |
| GET    | `/tasks`    | List all tasks with their action schema        |
| GET    | `/grader`   | Get current grader score for active episode    |
| GET    | `/baseline` | Run the deterministic baseline agent & score   |
| GET    | `/docs`     | Interactive Swagger UI                         |

---

## 🔢 Action Space

Each step action is a JSON object sent to `POST /step`:

```json
{
  "tool": "run_command",
  "arguments": "<shell command string>"
}
```

**Allowed tools:** `run_command` (the only tool currently available)

**Allowed commands:** `ls`, `cat`, `pwd`, `echo`, `ps`, `mv`, `kill`, `find`, `grep`, `mkdir`, `touch`, `head`, `tail`, `systemctl`, `npm install`, `cd`

---

## 👁️ Observation Space

Each step returns an `Observation` object:

```json
{
  "observation": {
    "stdout": "<command stdout>",
    "stderr": "<command stderr>",
    "cwd": "<current working directory>",
    "health_status": "<boolean: true if environment is repaired>"
  },
  "reward": 0.0,
  "done": false,
  "info": {
    "steps_taken": 1,
    "max_steps": 10,
    "grader_message": "<human-readable grader feedback>"
  }
}
```

---

## 🎯 Tasks

| Task ID     | Failure                           | Solution            | Difficulty | Max Steps |
|:------------|:----------------------------------|:--------------------|:-----------|:----------|
| `t1_config` | Config file misnamed `.conf.bak`  | `mv conf.bak conf`  | Easy       | 10        |
| `t2_port`   | Rogue process occupies port 8080  | `kill -9 <pid>`     | Medium     | 15        |
| `t3_dep`    | Missing Node.js npm dependencies  | `npm install`       | Hard       | 20        |

### Reward Function
- **Full credit (1.0):** The target repair has been successfully completed.
- **Partial credit (0.1–0.9):** The agent ran the correct diagnostic commands even if repair is incomplete.
- **No credit (0.0):** Nothing meaningful was done.

---

## 📊 Baseline Scores

Scores produced by the deterministic hardcoded agent (reproducible, `OPENAI_API_KEY` not required):

| Task        | Reward | Steps |
|:------------|:-------|:------|
| `t1_config` | 1.0    | 1     |
| `t2_port`   | 1.0    | 1     |
| `t3_dep`    | 1.0    | 2     |
| **Average** | **1.0**|       |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Docker (optional)

### Local Development
```bash
git clone https://huggingface.co/spaces/goated1/auto-sre
cd auto-sre
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -e ".[dev]"

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Docker
```bash
docker build -t auto-sre .
docker run -p 8000:8000 auto-sre
```

---

## 🤖 Baseline Inference Script

```bash
# Hardcoded deterministic agent (no API key needed)
python scripts/run_baseline_agent.py

# OpenAI LLM agent
export OPENAI_API_KEY=sk-...
export OPENAI_MODEL=gpt-4o-mini
python scripts/run_baseline_agent.py
```

---

## 🧪 Testing

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=app --cov=engine --cov=grader -v

# Agent tests
python scripts/run_null_agent.py       # Crash testing
python scripts/run_hardcoded_agent.py  # Solution verification
python scripts/run_baseline_agent.py   # Baseline scoring
```

---

## 📁 Project Structure
```
auto-sre/
├── app/            # FastAPI application & routes
├── engine/         # Sandbox engine (filesystem, processes, security)
├── grader/         # Deterministic health-check graders
├── tasks/          # Task scenario definitions
├── tests/          # Test suite
├── scripts/        # Utility & validation scripts
├── openenv.yaml    # OpenEnv specification metadata
├── Dockerfile      # Container build
└── pyproject.toml  # Project config
```

---

## 📜 License
MIT
