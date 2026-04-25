from fastapi import FastAPI

app = FastAPI()

# ---------------- RESET ----------------
@app.post("/reset")
def reset(payload: dict):
    return {
        "message": f"Environment reset for task {payload.get('task_id')}",
        "state": {}
    }

# ---------------- STEP ----------------
@app.post("/step")
def step(payload: dict):
    command = payload.get("arguments", "")

    # 🔥 simple mock reward logic (for training signal)
    if "kill" in command or "rm" in command:
        reward = 0.6
        done = False
    elif "restart" in command:
        reward = 0.9
        done = True
    else:
        reward = 0.1
        done = False

    return {
        "reward": reward,
        "done": done,
        "info": f"Executed {command}"
    }
