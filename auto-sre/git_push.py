import os

os.chdir("d:/hackathon")

print("Adding files...")
os.system("git add .")

print("Committing...")
os.system("git commit -m \"chore: remove duplicate inference.py and openenv.yaml from subfolder\"")

print("Pushing to origin...")
os.system("git push origin main")

print("Pushing to huggingface...")
os.system("git push hf main")

print("Done!")
