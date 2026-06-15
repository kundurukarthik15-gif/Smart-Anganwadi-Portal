import subprocess
import os

def run_git(args):
    try:
        res = subprocess.run(["git"] + args, capture_output=True, text=True)
        print(f"git {' '.join(args)} -> exit {res.returncode}")
        if res.stdout:
            print("STDOUT:\n", res.stdout)
        if res.stderr:
            print("STDERR:\n", res.stderr)
        return res.returncode == 0
    except Exception as e:
        print(f"git {' '.join(args)} failed: {e}")
        return False

print("=== Diagnostic Git Revert ===")
run_git(["status"])

print("\n--- Attempting restore ---")
if not run_git(["restore", "index.html"]):
    print("\n--- Attempting checkout -- ---")
    if not run_git(["checkout", "--", "index.html"]):
        print("\n--- Attempting reset ---")
        run_git(["reset", "HEAD", "index.html"])
        run_git(["checkout", "index.html"])
