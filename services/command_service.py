import subprocess
import os


def process_user_input(user_input):

    user_input = user_input.strip()

    if not user_input:
        return {
            "command": "",
            "output": ""
        }

    command = user_input

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )

        output = result.stdout + result.stderr

    except Exception as e:
        output = str(e)

    return {
        "command": command,
        "output": output
    }