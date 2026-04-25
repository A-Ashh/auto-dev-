import matplotlib.pyplot as plt
from agent.llm_agent import run_episode

episode_rewards = []
episode_steps = []
success_flags = []

for i in range(10):
    reward, steps, success = run_episode()

    episode_rewards.append(reward)
    episode_steps.append(steps)
    success_flags.append(1 if success else 0)

    print(f"Episode {i+1}: Reward={reward}, Steps={steps}, Success={success}")


# 📈 Reward graph
plt.figure()
plt.plot(episode_rewards)
plt.title("Reward vs Episodes")
plt.xlabel("Episode")
plt.ylabel("Reward")
plt.show()


# 📉 Steps graph
plt.figure()
plt.plot(episode_steps)
plt.title("Steps vs Episodes")
plt.xlabel("Episode")
plt.ylabel("Steps")
plt.show()


# ✅ Success graph
plt.figure()
plt.plot(success_flags)
plt.title("Success Rate")
plt.xlabel("Episode")
plt.ylabel("Success")
plt.show()