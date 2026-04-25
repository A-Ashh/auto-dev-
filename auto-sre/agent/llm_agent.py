import requests
from openai import OpenAI
from agent.prompts import SYSTEM_PROMPT

client = OpenAI()

BASE_URL = "http://127.0.0.1:7860"


def call_llm(history):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history,
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


def run_episode(task_id="t1_config", max_steps=6):
    res = requests.post(f"{BASE_URL}/reset", json={"task_id": task_id}).json()

    history = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": str(res["observation"])}
    ]

    total_reward = 0

    for step in range(max_steps):
        action = call_llm(history)

        print(f"\nSTEP {step+1}: {action}")

        result = requests.post(
            f"{BASE_URL}/step",
            json={"arguments": action}
        ).json()

        print("REWARD:", result["reward"])

        total_reward += result["reward"]

        history.append({"role": "assistant", "content": action})
        history.append({"role": "user", "content": str(result["observation"])})

        if result["done"]:
            print("✅ TASK SOLVED")
            return total_reward, step + 1, True

    return total_reward, max_steps, False