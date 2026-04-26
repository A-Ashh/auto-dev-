import requests
import random
import json
import os
import matplotlib.pyplot as plt

# ================= CONFIG =================
BASE_URL = "http://127.0.0.1:7860"
MODEL_PATH = "/content/q_model.json"

ACTIONS = [
    "ls",
    "ls /etc",
    "ls /var/log",
    "cat /var/log/app.log",
    "cat /var/log/syslog",
    "df -h",
    "free -m",
    "ps aux",
    "kill 123",  # placeholder (agent will still learn pattern)
    "rm /var/log/syslog",
    "systemctl restart app",
    "systemctl restart db",
    "systemctl restart cache",
]

TASKS = [
    "t1_config", "t2_port", "t3_dep", "t4_trap",
    "t5_disk_full", "t6_oom_killer", "t7_cascading_meltdown",
    "t8_memory_leak_loop", "t9_dependency_chain_failure",
    "t10_config_secret_failure"
]

ALPHA = 0.5
GAMMA = 0.9

EPSILON = 1.0
EPSILON_DECAY = 0.97
MIN_EPSILON = 0.05


# ================= LOAD/SAVE =================
def save_model(Q):
    with open(MODEL_PATH, "w") as f:
        json.dump(Q, f)


def load_model():
    if os.path.exists(MODEL_PATH):
        return json.load(open(MODEL_PATH))
    return {}


Q = load_model()


# ================= STATE =================
def get_state(obs):
    text = (obs.get("stdout", "") + obs.get("stderr", "")).lower()

    return json.dumps({
        "error": "error" in text,
        "disk": "100%" in text or "no space" in text,
        "memory": "oom" in text or "memory" in text,
        "dep": "cannot connect" in text,
        "auth": "invalid" in text or "authentication" in text,
        "service_down": "failed" in text or "inactive" in text,
    }, sort_keys=True)


# ================= POLICY =================
def choose_action(state, training=True):
    global EPSILON

    if training and random.random() < EPSILON:
        return random.choice(ACTIONS)

    q_vals = [Q.get(f"{state}|{a}", 0.5) for a in ACTIONS]
    return ACTIONS[q_vals.index(max(q_vals))]


# ================= TRAIN =================
def train(episodes=300):
    global EPSILON, Q

    rewards = []
    success_count = 0

    for ep in range(episodes):
        task_id = random.choice(TASKS)

        r = requests.post(f"{BASE_URL}/reset", json={"task_id": task_id})
        obs = r.json()["observation"]

        state = get_state(obs)
        total_reward = 0

        for step in range(15):
            action = choose_action(state)

            r = requests.post(f"{BASE_URL}/step", json={"command": action})
            data = r.json()

            obs = data["observation"]
            reward = data["reward"]
            done = data["done"]

            next_state = get_state(obs)

            key = f"{state}|{action}"
            old_q = Q.get(key, 0.5)

            future_q = max([Q.get(f"{next_state}|a", 0.5) for a in ACTIONS])

            Q[key] = old_q + ALPHA * (reward + GAMMA * future_q - old_q)

            state = next_state
            total_reward += reward

            if done:
                if reward > 0.5:
                    success_count += 1
                break

        rewards.append(total_reward)

        EPSILON = max(MIN_EPSILON, EPSILON * EPSILON_DECAY)

        print(f"Ep {ep+1} | Task {task_id} | Reward {round(total_reward,2)} | Eps {round(EPSILON,2)}")

    save_model(Q)

    print("\n✅ Training Complete")
    print("Success Rate:", success_count / episodes)

    # Plot learning
    plt.plot(rewards)
    plt.title("Training Progress")
    plt.xlabel("Episode")
    plt.ylabel("Reward")
    plt.show()


# ================= EVALUATION =================
def evaluate(episodes=50):
    success = 0

    for _ in range(episodes):
        task_id = random.choice(TASKS)

        r = requests.post(f"{BASE_URL}/reset", json={"task_id": task_id})
        obs = r.json()["observation"]

        state = get_state(obs)

        for _ in range(15):
            action = choose_action(state, training=False)

            r = requests.post(f"{BASE_URL}/step", json={"command": action})
            data = r.json()

            obs = data["observation"]
            reward = data["reward"]
            done = data["done"]

            state = get_state(obs)

            if done:
                if reward > 0.5:
                    success += 1
                break

    print("Evaluation Success Rate:", success / episodes)


# ================= RUN =================
train(episodes=300)
evaluate()
