import os

from core.executor import run_command
from ai.ai_engine import ask_ai
from context.detector import detect_context
from core.os_detect import get_os
from safety.danger_detector import check_dangerous_command
from healing.error_agent import error_agent
from ai.natural_commands import parse_natural_command


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

    if query.startswith("fix file"):

        parts = query.split(" ", 2)

        if len(parts) < 3:
            return "Usage: ai: fix file <path>"

        filepath = parts[2]

        return error_agent.cmd_fix_file(filepath, os.getcwd())

    if query == "clear errors":
        return error_agent.cmd_clear_errors(os.getcwd())

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