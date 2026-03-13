import os

from core.executor import run_command
from ai.ai_engine import ask_ai
from context.detector import detect_context
from core.os_detect import get_os
from safety.danger_detector import check_dangerous_command
from healing.error_agent import error_agent
from ai.natural_commands import parse_natural_command
from services.github_publisher import publish_project


def handle_command(user_input, stream_callback=None):

    if not user_input.lower().startswith("ai:"):
        return run_command(user_input, stream_callback)

    query = user_input[3:].strip().lower()

    if query == "chat":
        return "__CHAT_MODE__"

    if query == "help":

        return """
ShellMind AI Commands

Project Analysis
----------------
ai: scan project
ai: show errors
ai: explain errors
ai: fix errors
ai: fix file <path>
ai: clear errors

Code Explorer
-------------
ai: where <function>
ai: explain file <file_path>
ai: explain folder <folder_path>

Git Automation
--------------
ai: push
ai: push <repo_url>
ai: pushtorepo
ai: pushtorepo <repo_url>

File Operations
---------------
ai:create folder test
ai:create file test.txt

Chat
----
ai: chat
"""

    if query == "scan project":
        return error_agent.cmd_scan(os.getcwd())

    if query == "show errors":
        return error_agent.cmd_show_errors(os.getcwd())

    if query == "explain errors":
        return error_agent.cmd_explain_errors()

    if query == "fix errors":
        return error_agent.cmd_fix_all(os.getcwd())

    # -------------------------
    # GIT PUBLISH FEATURE
    # -------------------------

    if query == "push":

        repo = input("Enter GitHub repository URL: ")

        if not repo:
            return "Repository URL required."

        return publish_project(repo)

    if query.startswith("push "):

        parts = query.split(" ", 1)
        repo_url = parts[1]

        return publish_project(repo_url)

    if query.startswith("publish"):

        parts = query.split(" ", 1)

        if len(parts) < 2:
            return "Usage: ai: publish <repo_url>"

        repo_url = parts[1]

        return publish_project(repo_url)

    # -------------------------
    # NEW COMMAND
    # -------------------------

    if query.startswith("pushtorepo"):

        # Allow "ai: pushtorepo" (prompts for repo) or
        # "ai: pushtorepo https://github.com/owner/repo" (uses provided repo)
        parts = query.split(" ", 1)

        if len(parts) > 1 and parts[1].strip():
            repo = parts[1].strip()
        else:
            choice = input("Do you want to (1) provide a repo URL or (2) create a new repo? Enter 1 or 2: ")
            if choice == "1":
                repo = input("Enter GitHub repository URL: ")
            elif choice == "2":
                print("Please create a new repo on GitHub first, then provide the URL.")
                repo = input("Enter the new repo URL: ")
            else:
                return "Invalid choice."

        if not repo:
            return "Repository URL required."

        return publish_project(repo)

    # -------------------------

    if query.startswith("fix file"):

        parts = query.split(" ", 2)

        if len(parts) < 3:
            return "Usage: ai: fix file <path>"

        filepath = parts[2]

        return error_agent.cmd_fix_file(filepath, os.getcwd())

    if query == "clear errors":
        return error_agent.cmd_clear_errors(os.getcwd())

    # -------------------------
    # CODE EXPLORER FEATURES
    # -------------------------

    # -------------------------

    natural_result = parse_natural_command(query, stream_callback)

    if natural_result:
        return natural_result

    context = detect_context()
    os_type = get_os()

    command = ask_ai(query, context, os_type)

    if not command:
        return "AI could not generate a command."

    risk = check_dangerous_command(command)

    if risk == "HIGH":
        return f"⚠ Warning: This command may be dangerous:\n{command}"

    return run_command(command, stream_callback)