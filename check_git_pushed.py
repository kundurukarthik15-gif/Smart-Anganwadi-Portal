import subprocess

print("=== Checking Git Status & Push State ===")

try:
    # Check git status
    status = subprocess.run(["git", "status"], capture_output=True, text=True, check=True)
    # Check latest commit
    log = subprocess.run(["git", "log", "-n", "2", "--oneline"], capture_output=True, text=True, check=True)
    # Check remote branches
    remote = subprocess.run(["git", "remote", "-v"], capture_output=True, text=True, check=True)
    
    with open("git_state.txt", "w", encoding="utf-8") as out:
        out.write("--- GIT STATUS ---\n")
        out.write(status.stdout)
        out.write("\n--- LATEST COMMITS ---\n")
        out.write(log.stdout)
        out.write("\n--- REMOTE CONFIG ---\n")
        out.write(remote.stdout)
        
    print("Generated git_state.txt successfully.")
except Exception as e:
    print(f"Error checking git: {e}")
