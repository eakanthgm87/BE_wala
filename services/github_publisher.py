import os
import subprocess

from ai.ai_engine import ask_ai
from context.detector import detect_context
from core.os_detect import get_os


def run_command(cmd):

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout + result.stderr


def clean_command(ai_output):

    if not ai_output:
        return None

    lines = ai_output.split("\n")

    for line in lines:

        line = line.strip()

        if line.startswith("git"):
            return line

    return None


def ask_ai_fix(error_output):

    context = detect_context()
    os_type = get_os()

    prompt = f"""
A git push command failed.

ERROR:
{error_output}

Return ONLY ONE command that fixes this git issue.

Rules:
- Only return the command
- No explanation
- No list
- No text
- Only a shell command starting with git

Example:
git remote remove origin
"""

    return ask_ai(prompt, context, os_type)


def publish_project(repo_url):

    project_path = os.getcwd()

    gitignore = os.path.join(project_path, ".gitignore")
    readme = os.path.join(project_path, "README.md")

    output = ""

    try:

        if not os.path.exists(gitignore):

            with open(gitignore, "w") as f:
                f.write(
"""__pycache__/
*.pyc
.env
dist/
build/
"""
                )

            output += "Created .gitignore\n"

        if not os.path.exists(readme):

            with open(readme, "w") as f:
                f.write("# Project\n\nPublished using ShellMind AI\n")

            output += "Created README.md\n"

        commands = [

            ["git", "config", "--global", "user.email", "you@example.com"],
            ["git", "config", "--global", "user.name", "Your Name"],
            ["git", "remote", "remove", "origin"],
            ["git", "init"],
            ["git", "add", "."],
            ["git", "commit", "-m", "initial commit"],
            ["git", "branch", "-M", "main"],
            ["git", "remote", "add", "origin", repo_url],
        ]

        for cmd in commands:

            code, out = run_command(cmd)
            output += out

        code, out = run_command(["git", "push", "-u", "origin", "main"])

        output += out

        if code != 0:
            output += "\nPush failed.\n"
        else:
            output += "\nDone.\n"

        return output

    except Exception as e:

        return f"Publish failed: {str(e)}"