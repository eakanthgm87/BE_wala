from prompt_toolkit import prompt
import os

from core.executor import run_command
from ai.ai_engine import ask_ai
from context.detector import detect_context
from core.os_detect import get_os
from safety.danger_detector import check_dangerous_command
from healing.error_agent import error_agent
from healing.file_ops import create_folder, create_file

from healing.ghost_suggest import GhostSuggest
from safety.file_analyzer import analyze_file
from safety.folder_analyzer import analyze_folder
from repo.push_to_repo import push_to_repo

ghost = GhostSuggest()


def start_terminal():

    while True:

        try:

            user_input = prompt(
                f"{os.getcwd()} > ",
                auto_suggest=ghost
            ).strip()

            if not user_input:
                suggestion = None
                if hasattr(ghost, "get_next_command"):
                    suggestion = ghost.get_next_command()

                if suggestion:
                    user_input = suggestion
                    print(suggestion)
                else:
                    continue

            if user_input.lower() == "exit":
                print("Exiting ShellMind...")
                break

            # =====================================================
            # AI MODE
            # =====================================================

            if user_input.lower().startswith("ai:"):

                query = user_input[3:].strip().lower()

                # ----------------------------------------------
                # AI CHAT MODE
                # ----------------------------------------------

                if query == "chat":

                    print("\n🤖 ShellMind AI Chat Mode")
                    print("Type 'exit' to leave chat.\n")

                    while True:

                        user_msg = input("You > ")

                        if user_msg.lower() in ["exit", "quit"]:
                            print("Leaving AI chat mode...\n")
                            break

                        context = detect_context()
                        os_type = get_os()

                        ai_response = ask_ai(user_msg, context, os_type)

                        if not ai_response:
                            print("⚠️ AI could not generate a response.")
                        else:

                            if ai_response.startswith("echo"):
                                ai_response = ai_response.replace("echo", "").strip().strip('"')

                            print("\n══════════════════════════════")
                            print("🤖 ShellMind AI")
                            print("══════════════════════════════")
                            print(ai_response)
                            print("══════════════════════════════\n")

                    continue

                # ----------------------------------------------
                # HELP
                # ----------------------------------------------

                if query == "help":

                    print("""
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
ai: create folder
ai: create file
ai: pushtorepo

Chat
----
ai: chat
""")
                    continue

                # ----------------------------------------------
                # ERROR AGENT
                # ----------------------------------------------

                if query == "scan project":
                    print(error_agent.cmd_scan(os.getcwd()))
                    continue

                if query == "show errors":
                    print(error_agent.cmd_show_errors(os.getcwd()))
                    continue

                if query == "explain errors":
                    print(error_agent.cmd_explain_errors())
                    continue

                if query == "fix errors":
                    print(error_agent.cmd_fix_all(os.getcwd()))
                    continue

                if query.startswith("fix file"):

                    parts = query.split(" ", 2)

                    if len(parts) < 3:
                        print("Usage: ai: fix file <path>")
                        continue

                    filepath = parts[2]

                    print(error_agent.cmd_fix_file(filepath, os.getcwd()))
                    continue

                if query == "clear errors":
                    print(error_agent.cmd_clear_errors(os.getcwd()))
                    continue

                # ----------------------------------------------
                # FILE OPS
                # ----------------------------------------------

                if query == "create folder":

                    name = prompt("Enter folder name: ").strip()

                    if not name:
                        print("Folder name cannot be empty.")
                        continue

                    create_folder(name)
                    print(f"✔ Folder '{name}' created.")
                    continue

                if query == "create file":

                    name = prompt("Enter file name: ").strip()

                    if not name:
                        print("File name cannot be empty.")
                        continue

                    create_file(name)
                    print(f"✔ File '{name}' created.")
                    continue

                # ----------------------------------------------
                # AI SEARCH COMMAND (local model)
                # ----------------------------------------------
                if query.startswith("search ") or query == "search":
                    from search.agent import ai_search

                    response = ai_search(query, base_path=os.getcwd())
                    print(response)
                    continue

                # ----------------------------------------------
                # SNAPSHOT COMMANDS
                # ----------------------------------------------
                if query.startswith("snapshot "):
                    from snapshot.commands import handle_snapshot_query

                    result = handle_snapshot_query(query)
                    if result is not None:
                        print(result)
                        continue

                # ----------------------------------------------
                # PUSH TO REPO
                # ----------------------------------------------
                if query == "pushtorepo":
                    push_to_repo()
                    continue

                # ----------------------------------------------
                # AI COMMAND GENERATION
                # ----------------------------------------------

                context = detect_context()
                os_type = get_os()

                command = ask_ai(query, context, os_type)

                if not command:
                    print("AI could not generate a command.")
                    continue

                print("\nAI Suggested Command:")
                print(f"  {command}")
                print("──────────────────────────────")

                risk = check_dangerous_command(command)

                if risk == "HIGH":
                    print("⚠ Warning: This command may be dangerous.")

                continue

            # =====================================================
            # NORMAL TERMINAL COMMANDS
            # =====================================================

            parts = user_input.split()

            if parts and parts[0].lower() == "admin":

                if len(parts) < 3:
                    print("Usage: admin del <file> OR admin rmdir <folder>")
                    continue

                action = parts[1].lower()
                target = parts[2]

                if action in ["del", "delete"]:

                    if not os.path.exists(target):
                        print("❌ File does not exist.")
                        continue

                    analyze_file(target)

                    os.remove(target)

                    print(f"✔ File '{target}' deleted.")
                    continue

                if action == "rmdir":

                    if not os.path.exists(target):
                        print("❌ Folder does not exist.")
                        continue

                    analyze_folder(target)

                    os.rmdir(target)

                    print(f"✔ Folder '{target}' deleted.")
                    continue

            run_command(user_input)

            ghost.update_last_command(user_input)

        except KeyboardInterrupt:
            print("\nUse 'exit' to quit ShellMind.")