import subprocess
import sys
import os

def run_git_command(args):
    """Runs a git command and prints the output."""
    print(f"Executing: git {' '.join(args)}")
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {' '.join(args)}")
        print(f"Exit code: {e.returncode}")
        if e.stdout:
            print(f"Stdout:\n{e.stdout.strip()}")
        if e.stderr:
            print(f"Stderr:\n{e.stderr.strip()}")
        return False

def main():
    print("=== Smart Anganwadi Portal — GitHub Sync Utility ===")
    
    # 1. Check if it's a git repository first
    if not os.path.isdir('.git'):
        print("\n❌ This directory is not a Git repository.")
        print("   To fix this, please run the following command in your terminal:")
        print("\n   git init\n")
        print("   After initializing, you'll need to add a remote origin, for example:")
        print("   git remote add origin https://github.com/your-username/your-repo.git")
        sys.exit(1)
        
    # 2. Check current branch
    try:
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )
        current_branch = branch_res.stdout.strip()
        print(f"Current branch: {current_branch}")
    except subprocess.CalledProcessError:
        # This can happen if it's a new repo with no commits yet.
        print("⚠️  Could not determine current branch. This might be a new repository.")
        print("    Defaulting to branch 'main' for the first push.")
        current_branch = "main"
    except Exception as e:
        print("❌ An unexpected error occurred while checking the git branch.")
        print(e)
        sys.exit(1)
        
    # 3. Git status
    run_git_command(["status"])
    
    # 4. Git add
    if not run_git_command(["add", "."]):
        sys.exit(1)
        
    # 5. Git commit
    # Check if there are changes to commit before attempting
    diff_check = subprocess.run(["git", "diff", "--cached", "--quiet"])
    if diff_check.returncode == 0:
        print("\n✅ No changes staged for commit. Nothing to do.")
    else:
        print("\nCommitting changes...")
        commit_message = "Update project files via sync utility"
        if not run_git_command(["commit", "-m", commit_message]):
            print("\n   Commit failed. Please ensure your git user.name and user.email are configured:")
            print("   git config --global user.name \"Your Name\"")
            print("   git config --global user.email \"you@example.com\"")
            sys.exit(1)
    
    # Ensure the branch is named 'main' (standard for GitHub)
    run_git_command(["branch", "-M", "main"])
    current_branch = "main"

    # 6. Git push
    print(f"\nPushing to GitHub on branch '{current_branch}'...")
    if run_git_command(["push", "-u", "origin", current_branch]):
        print("\n🚀 Code successfully pushed to GitHub!")
    else:
        print("\n❌ Failed to push. If this is the first push for this branch, you may need to set the upstream:")
        print(f"   Try running: git push --set-upstream origin {current_branch}")

if __name__ == "__main__":
    main()
