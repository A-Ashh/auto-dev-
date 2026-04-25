import os
import requests
import torch
import math
import random
from datasets import Dataset
from trl import GRPOConfig, GRPOTrainer
from unsloth import FastLanguageModel, PatchFastRL

PatchFastRL("GRPO", FastLanguageModel)

# ---------------- CONFIG ----------------
MODEL_NAME = "unsloth/Qwen2.5-1.5B-Instruct"
ENV_URL = "http://localhost:8000"
MAX_STEPS = 15

TASK_DESCRIPTIONS = {
    "t1_config": "Fix misnamed config file.",
    "t2_port": "Kill process using a busy port.",
    "t7_cascading_meltdown": "Fix cascading system failure involving disk, process, and database."
}

TASKS = list(TASK_DESCRIPTIONS.keys())

reward_history = []

# ---------------- ENV ----------------
def run_env_episode(task_id, commands):
    try:
        r = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=5)
        if r.status_code != 200:
            return -1.0

        total_reward = 0.0
        steps = 0

        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue

            steps += 1

            step_resp = requests.post(
                f"{ENV_URL}/step",
                json={"tool": "run_command", "arguments": cmd},
                timeout=5
            )

            if step_resp.status_code != 200:
                total_reward -= 0.2
                break

            data = step_resp.json()

            step_reward = data.get("reward", 0.0)

            # ✅ STRONG SIGNAL
            if step_reward > 0.5:
                total_reward += 0.3
            elif step_reward > 0.1:
                total_reward += 0.1
            else:
                total_reward -= 0.1  # penalty

            if data.get("done", False):
                total_reward += 0.5  # success bonus
                break

        # penalty for inefficiency
        total_reward -= 0.02 * steps

        return total_reward

    except Exception as e:
        return -1.0


# ---------------- REWARD ----------------
def reward_func(prompts, completions, **kwargs):
    rewards = []

    for prompt, completion in zip(prompts, completions):
        try:
            # extract task
            user_text = ""
            for msg in prompt:
                if msg["role"] == "user":
                    user_text = msg["content"]

            task_id = random.choice(TASKS)
            for k, v in TASK_DESCRIPTIONS.items():
                if v == user_text:
                    task_id = k

            output = completion[0]["content"] if isinstance(completion, list) else completion

            commands = [c.strip() for c in output.split("\n") if c.strip()][:MAX_STEPS]

            raw_score = run_env_episode(task_id, commands)

            # ✅ SIGMOID NORMALIZATION (keeps (0,1) rule)
            score = 1 / (1 + math.exp(-raw_score))

            rewards.append(score)

        except:
            rewards.append(0.01)

    avg = sum(rewards) / len(rewards)
    reward_history.append(avg)

    print(f"[REWARD] step={len(reward_history)} avg={avg:.4f}")

    return rewards


# ---------------- DATASET ----------------
def build_dataset():
    prompts = []

    for t in TASKS:
        for _ in range(10):  # repeat each task
            prompts.append([
                {"role": "system", "content": "You are an expert SRE. Output only Linux commands."},
                {"role": "user", "content": TASK_DESCRIPTIONS[t]},
            ])

    random.shuffle(prompts)
    return Dataset.from_dict({"prompt": prompts})


# ---------------- MAIN ----------------
def main():

    dataset = build_dataset()

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=1024,
        load_in_4bit=True,
        fast_inference=True,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=16,
        lora_alpha=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        use_gradient_checkpointing="unsloth",
    )

    training_args = GRPOConfig(
        learning_rate=2e-5,
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_generations=12,   # 🔥 important
        max_prompt_length=256,
        max_completion_length=256,
        num_train_epochs=3,
        logging_steps=1,
        temperature=1.0,
        top_p=0.9,
        output_dir="outputs",
    )

    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=[reward_func],
        args=training_args,
        train_dataset=dataset,
    )

    print("Starting training...")
    trainer.train()

    model.save_lora("grpo_sre_lora")

    print("Training complete!")


if __name__ == "__main__":
    main()
