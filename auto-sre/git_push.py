import os

os.chdir("d:/hackathon")

print("Adding files...")
os.system("git add .")

print("Committing...")
os.system("git commit -m \"feat: deploy Premium UI Web Terminal Dashboard hooked into Backend HTTP API\"")

print("Pushing to origin...")
os.system("git push origin main")

print("Pushing to huggingface...")
os.system("git push hf main")

print("Done!")
