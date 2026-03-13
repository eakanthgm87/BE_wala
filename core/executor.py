import subprocess
import os
from safety.danger_detector import check_dangerous_command
from safety.folder_analyzer import analyze_folder
from healing.command_suggester import suggest_command


def run_command(command, stream_callback=None):

    command = command.strip()

    if not command:
        return ""

    # ==============================
    # COMMAND SUGGESTION SYSTEM
    # ==============================

    suggestion = suggest_command(command)

    if suggestion and suggestion != command:

        print(f"❌ Unknown command: {command}")
        print(f"💡 Did you mean: {suggestion} ?")

        return ""

    # ==============================
    # ADMIN DELETE MODE
    # ==============================

    if command.lower().startswith("admin rmdir "):

        parts = command.split(maxsplit=2)

        if len(parts) > 2:
            folder = parts[2]

            if not os.path.exists(folder):
                print(f"❌ Folder '{folder}' does not exist.")
                return ""

            print("⚡ ADMIN DELETE MODE")

            analyze_folder(folder)

            print("\n🗑 Deleting folder...")

            command = f"rmdir /s /q {folder}"

            subprocess.run(["cmd", "/c", command])
            return ""

    # ==============================
    # DANGER CHECK
    # ==============================

    result = check_dangerous_command(command)

    if result["danger"]:

        print(result["message"])

        # Show folder info before confirmation
        if command.lower().startswith("rmdir "):

            parts = command.split(maxsplit=1)

            if len(parts) > 1:
                folder = parts[1]

                if os.path.exists(folder):
                    analyze_folder(folder)
                else:
                    print(f"❌ Folder '{folder}' does not exist.")

        confirm = input("\nDo you want to continue? (yes/no): ")

        if confirm.lower() != "yes":
            print("❌ Command cancelled.")
            return ""

    # ==============================
    # AUTO FIX FOR RMDIR
    # ==============================

    if command.lower().startswith("rmdir ") and "/s" not in command:
        command = command.replace("rmdir", "rmdir /s /q")

    # ==============================
    # NORMAL COMMAND HANDLING
    # ==============================

    if command == "clear":
        command = "cls"

    if command == "ls":
        command = "dir"

    if command == "cls":
        os.system("cls")
        return ""

    # ==============================
    # HANDLE CD COMMAND
    # ==============================

    if command.startswith("cd"):

        parts = command.split(maxsplit=1)

        if len(parts) == 1:
            out = os.getcwd()
            if stream_callback:
                stream_callback(out + "\n")
            else:
                print(out)
            return out

        try:
            os.chdir(parts[1])
            out = f"Changed directory to {os.getcwd()}"
        except Exception as e:
            out = str(e)

        if stream_callback:
            stream_callback(out + "\n")
        else:
            print(out)

        return out

    # ==============================
    # EXECUTE COMMAND
    # ==============================

    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    output = ""

    for line in iter(process.stdout.readline, ""):

        output += line

        if stream_callback:
            stream_callback(line)
        else:
            print(line, end="")

    process.stdout.close()
    process.wait()

    return output