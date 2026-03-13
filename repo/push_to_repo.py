import os
import subprocess
import sys

def push_to_repo():
    """
    Handle pushing current folder to GitHub repo.
    """
    cwd = os.getcwd()

    # Check if git is initialized
    if not os.path.exists(os.path.join(cwd, '.git')):
        print("Initializing git repository...")
        subprocess.run(['git', 'init'], cwd=cwd, check=True)
        print("Git repository initialized.")

    # Ask user for repo option
    print("Do you want to:")
    print("1. Create a new GitHub repository")
    print("2. Use an existing repository link")

    choice = input("Enter 1 or 2: ").strip()

    if choice == '1':
        # Create new repo
        repo_name = input("Enter repository name: ").strip()
        if not repo_name:
            print("Repository name cannot be empty.")
            return

        description = input("Enter repository description (optional): ").strip()
        private = input("Make repository private? (y/n): ").strip().lower() == 'y'

        # Assume GitHub CLI is installed
        cmd = ['gh', 'repo', 'create', repo_name, '--public']
        if private:
            cmd = ['gh', 'repo', 'create', repo_name, '--private']
        if description:
            cmd.extend(['--description', description])

        print("Creating GitHub repository...")
        try:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
            repo_url = result.stdout.strip()
            print(f"Repository created: {repo_url}")
        except subprocess.CalledProcessError as e:
            print(f"Failed to create repository: {e}")
            print("Make sure GitHub CLI is installed and authenticated.")
            return

    elif choice == '2':
        # Use existing repo
        repo_url = input("Enter repository URL: ").strip()
        if not repo_url:
            print("Repository URL cannot be empty.")
            return
    else:
        print("Invalid choice.")
        return

    # Now push to repo
    try:
        # Check if remote origin exists
        result = subprocess.run(['git', 'remote', 'get-url', 'origin'], cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            print("Remote origin already exists. Updating...")
            subprocess.run(['git', 'remote', 'set-url', 'origin', repo_url], cwd=cwd, check=True)
        else:
            print("Adding remote origin...")
            subprocess.run(['git', 'remote', 'add', 'origin', repo_url], cwd=cwd, check=True)

        # Add all files
        print("Adding files to git...")
        subprocess.run(['git', 'add', '.'], cwd=cwd, check=True)
        print("Files added.")

        # Check status
        status_result = subprocess.run(['git', 'status', '--porcelain'], cwd=cwd, capture_output=True, text=True, check=True)
        if status_result.stdout.strip():
            print("Files staged for commit.")
        else:
            print("No changes to commit.")
            return

        # Commit
        print("Committing files...")
        subprocess.run(['git', 'commit', '-m', 'Initial commit'], cwd=cwd, check=True)
        print("Commit created.")

        # Push
        print("Pushing to repository... (this may take a while depending on file sizes)")
        push_result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], cwd=cwd, capture_output=True, text=True)
        if push_result.returncode == 0:
            print("✅ Successfully pushed to GitHub repository!")
        else:
            print(f"Push failed: {push_result.stderr}")
            # Try with master branch
            print("Trying with 'master' branch...")
            subprocess.run(['git', 'push', '-u', 'origin', 'master'], cwd=cwd, check=True)
            print("✅ Successfully pushed to GitHub repository!")

    except subprocess.CalledProcessError as e:
        print(f"Error during git operations: {e}")
        return