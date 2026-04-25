"""Phase 5: RL Training Script using Unsloth GRPO.

Trains on ALL tasks (t1–t10) via round-robin curriculum.
Designed to run in Google Colab.

Usage:
    AUTO_SRE_URL=http://localhost:8000 python scripts/train_grpo.py
"""

import os
import requests
import torch
from datasets import Dataset
from trl import GRPOConfig, GRPOTrainer
from unsloth import FastLanguageModel, PatchFastRL
PatchFastRL("GRPO", FastLanguageModel)

# --- Reward History (for plotting) ---
reward_history: list[float] = []
per_task_rewards: dict[str, list[float]] = {}

# --- Configuration ---
MODEL_NAME = "unsloth/Qwen2.5-1.5B-Instruct"
MAX_SEQ_LENGTH = 1024
LORA_RANK = 16
ENV_URL = "https://goated1-auto-sre.hf.space"
MAX_STEPS = 8

# --- Dynamic task list (loaded from registry, no hardcoding) ---
def _fetch_task_ids() -> list[str]:
    try:
        resp = requests.get(f"{ENV_URL}/tasks", timeout=5)
        if resp.status_code == 200:
            return [t["task_id"] for t in resp.json().get("tasks", [])]
    except Exception:
        pass
    # Fallback order matches curriculum (easy → hard)
    return [
        "t1_config", "t2_port", "t3_dep",
        "t4_trap", "t5_disk_full", "t6_oom_killer",
        "t7_cascading_meltdown", "t8_memory_leak_loop",
        "t9_dependency_chain_failure", "t10_config_secret_failure",
    ]

TASKS = _fetch_task_ids()

# --- Episode counter for round-robin ---
_episode: list[int] = [0]


# --- Environment Interface ---
def run_env_episode(task_id: str, commands: list[str]) -> float:
    """Run one episode on the Auto-SRE environment."""
    try:
        resp = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=5)
        if resp.status_code != 200:
            return 0.01

        for cmd in commands:
            cmd = cmd.strip()
            if not cmd:
                continue
            step_resp = requests.post(
                f"{ENV_URL}/step",
                json={"tool": "run_command", "arguments": cmd},
                timeout=5,
            )
            if step_resp.status_code != 200:
                break
            if step_resp.json().get("done", False):
                break

        grade_resp = requests.get(f"{ENV_URL}/grader", timeout=5)
        if grade_resp.status_code == 200:
            return grade_resp.json().get("reward", 0.01)
        return 0.01
    except Exception as e:
        print(f"[ENV] Error: {e}")
        return 0.01


# --- Reward Function ---
def openenv_reward_func(prompts, completions, **kwargs) -> list[float]:
    """GRPO reward function — cycles through all tasks round-robin."""
    rewards = []
    for completion in completions:
        try:
            output = completion[0]["content"] if isinstance(completion, list) else completion
            commands = [c.strip() for c in output.split("\n") if c.strip()][:MAX_STEPS]

            # Round-robin task assignment
            task_id = TASKS[_episode[0] % len(TASKS)]
            _episode[0] += 1

            score = run_env_episode(task_id, commands)
            rewards.append(score)

            # Per-task tracking
            if task_id not in per_task_rewards:
                per_task_rewards[task_id] = []
            per_task_rewards[task_id].append(score)

        except Exception:
            rewards.append(0.01)

    avg_reward = sum(rewards) / len(rewards)
    reward_history.append(avg_reward)
    print(f"[REWARD LOG] Avg: {avg_reward:.4f} | Step {len(reward_history)}")
    return rewards


def main():
    print(f"Initializing Unsloth RL Pipeline — {len(TASKS)} tasks loaded")
    print(f"Tasks: {TASKS}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=MODEL_NAME,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
        fast_inference=True,
        max_lora_rank=LORA_RANK,
        gpu_memory_utilization=0.6,
    )

    model = FastLanguageModel.get_peft_model(
        model,
        r=LORA_RANK,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                        "gate_proj", "up_proj", "down_proj"],
        lora_alpha=LORA_RANK,
        use_gradient_checkpointing="unsloth",
        random_state=3407,
    )

    system_prompt = (
        "You are an expert SRE agent. Repair Linux infrastructure failures by issuing CLI commands. "
        "Output one command per line. No explanations — commands only."
    )

    # Curriculum dataset: one entry per task so model sees all scenarios
    prompts = []
    task_descriptions = {
        "t1_config": "A config file is misnamed. Find /etc/app/conf.bak and rename it to /etc/app/conf, then restart app.",
        "t2_port": "A port is occupied by a rogue process. Find the PID using ps/netstat and kill it.",
        "t3_dep": "A Node.js app is missing dependencies. Install them with npm install.",
        "t4_trap": "System may already be healthy. Diagnose before taking any action.",
        "t5_disk_full": "Disk is at 100%. Find and delete the large log file in /var/log/.",
        "t6_oom_killer": "A rogue process is consuming all memory. Find its PID using ps/top and kill it.",
        "t7_cascading_meltdown": "Disk full + rogue logger + DB down. Fix in order: clear logs, kill rogue, restart DB.",
        "t8_memory_leak_loop": "Service 'leak-daemon' is in a crash-restart loop. Kill the leaking process and restart the service.",
        "t9_dependency_chain_failure": "App is down due to dependency chain failure. Restart db first, then cache, then app.",
        "t10_config_secret_failure": "App auth fails — wrong DB secret. Inspect /etc/app/secrets.conf, fix it, restart app.",
    }

    for task_id in TASKS:
        desc = task_descriptions.get(task_id, "Diagnose and repair the system failure.")
        prompts.append([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": desc},
        ])

    # Expand to at least 32 examples for training stability
    while len(prompts) < 32:
        prompts.extend(prompts[:max(1, 32 - len(prompts))])

    dataset = Dataset.from_dict({"prompt": prompts[:32]})

    training_args = GRPOConfig(
        use_vllm=True,
        learning_rate=5e-6,
        adam_beta1=0.9,
        adam_beta2=0.99,
        weight_decay=0.1,
        warmup_ratio=0.1,
        lr_scheduler_type="cosine",
        optim="paged_adamw_8bit",
        logging_steps=1,
        bf16=torch.cuda.is_bf16_supported(),
        fp16=not torch.cuda.is_bf16_supported(),
        per_device_train_batch_size=1,
        gradient_accumulation_steps=4,
        num_generations=8,
        max_prompt_length=256,
        max_completion_length=256,
        num_train_epochs=5,
        save_steps=100,
        max_grad_norm=0.1,
        output_dir="outputs",
    )

    trainer = GRPOTrainer(
        model=model,
        processing_class=tokenizer,
        reward_funcs=[openenv_reward_func],
        args=training_args,
        train_dataset=dataset,
    )

    print("Starting GRPO Training...")
    trainer.train()

    print("Saving model...")
    model.save_lora("grpo_auto_sre_lora")
    print("Training complete!")

    # --- Per-task reward summary ---
    print("\n[RESULTS] Per-task average rewards:")
    for tid, scores in per_task_rewards.items():
        avg = sum(scores) / len(scores) if scores else 0.0
        print(f"  {tid}: {avg:.4f} ({len(scores)} episodes)")

    # --- Safe reward curve plotting ---
    try:
        import matplotlib.pyplot as plt

        # Overall curve
        if len(reward_history) > 0:
            plt.figure(figsize=(12, 5))
            plt.subplot(1, 2, 1)
            plt.plot(reward_history, marker="o", linewidth=2, color="#2196F3", label="Avg Reward")
            plt.title("Auto-SRE GRPO Reward Curve", fontsize=14)
            plt.xlabel("Training Steps")
            plt.ylabel("Average Reward")
            plt.ylim(0, 1)
            plt.grid(True, alpha=0.3)
            plt.legend()

            # Per-task bar chart
            plt.subplot(1, 2, 2)
            task_avgs = {tid: sum(s)/len(s) for tid, s in per_task_rewards.items() if s}
            if task_avgs:
                plt.bar(range(len(task_avgs)), list(task_avgs.values()), color="#4CAF50")
                plt.xticks(range(len(task_avgs)), list(task_avgs.keys()), rotation=45, ha="right")
                plt.title("Per-Task Average Reward", fontsize=14)
                plt.ylabel("Average Reward")
                plt.ylim(0, 1)
                plt.grid(True, alpha=0.3, axis="y")

            plt.tight_layout()
            plt.savefig("reward_curve.png", dpi=150)
            print("[PLOT] Reward curve saved as reward_curve.png")
            plt.close()
        else:
            print("[PLOT] No reward data collected — skipping plot.")

    except ImportError:
        print("[PLOT] matplotlib not available, skipping plot generation")


if __name__ == "__main__":
    main()
