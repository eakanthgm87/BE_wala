import os
import difflib
from prompt_toolkit.auto_suggest import AutoSuggest, Suggestion


# ----------------------------------------------------
# COMMAND TREE (tool → subcommands)
# ----------------------------------------------------

COMMAND_TREE = {

    "git": [
        "init", "clone", "pull", "push", "commit", "status",
        "add", "checkout", "branch", "merge", "log", "remote"
    ],

    "docker": [
        "run", "build", "pull", "push",
        "images", "ps", "stop", "start",
        "rm", "exec", "logs"
    ],

    "pip": [
        "install", "uninstall", "list", "freeze", "show"
    ],

    "npm": [
        "install", "start", "run", "build", "test"
    ],

    "python": [
        "-m", "--version"
    ],

    "mvn": [
        "clean", "install", "package", "compile", "test"
    ],

    "gradle": [
        "build", "test", "run"
    ]
}


# ----------------------------------------------------
# WORKFLOW SUGGESTIONS (next logical commands)
# ----------------------------------------------------

NEXT_COMMANDS = {

    # ---------------- GIT ----------------

    "git init": [
        "git add .",
        "git branch -M main",
        "git remote add origin <repo-url>"
    ],

    "git add": [
        "git commit -m \"message\"",
        "git status"
    ],

    "git commit": [
        "git push",
        "git status"
    ],

    "git clone": [
        "cd <repo>",
        "git status"
    ],

    "git pull": [
        "git status"
    ],

    "git push": [
        "git status"
    ],

    # ---------------- DOCKER ----------------

    "docker build": [
        "docker run <image>",
        "docker images"
    ],

    "docker run": [
        "docker ps",
        "docker logs <container>",
        "docker stop <container>"
    ],

    "docker stop": [
        "docker ps",
        "docker start <container>"
    ],

    # ---------------- PIP ----------------

    "pip install": [
        "python main.py",
        "pip list",
        "pip freeze"
    ],

    "pip uninstall": [
        "pip list"
    ],

    # ---------------- NPM ----------------

    "npm install": [
        "npm start",
        "npm run build",
        "npm test"
    ],

    "npm run build": [
        "npm start"
    ],

    # ---------------- PYTHON ----------------

    "python main.py": [
        "pytest",
        "python -m unittest"
    ]
}


# ----------------------------------------------------
# GHOST SUGGESTION ENGINE
# ----------------------------------------------------

class GhostSuggest(AutoSuggest):

    def __init__(self):

        self.last_command = None
        self.system_commands = self.get_system_commands()

    # ------------------------------------------------

    def update_last_command(self, command):

        self.last_command = command

    # ------------------------------------------------
    # NEW METHOD (required for ENTER suggestion)
    # ------------------------------------------------

    def get_next_command(self):

        if not self.last_command:
            return None

        for key in NEXT_COMMANDS:

            if self.last_command.startswith(key):

                suggestions = NEXT_COMMANDS[key]

                if suggestions:
                    return suggestions[0]

        return None

    # ------------------------------------------------

    def get_system_commands(self):

        commands = set()

        paths = os.environ.get("PATH", "").split(os.pathsep)

        for path in paths:

            if os.path.exists(path):

                try:

                    for file in os.listdir(path):

                        commands.add(os.path.splitext(file)[0])

                except:
                    pass

        return list(commands)

    # ------------------------------------------------

    def get_suggestion(self, buffer, document):

        text = document.text
        stripped = text.strip()
        parts = stripped.split()

        # --------------------------------------------
        # 1️⃣ Workflow suggestion (after last command)
        # --------------------------------------------

        if self.last_command:

            for key in NEXT_COMMANDS:

                if self.last_command.startswith(key):

                    suggestions = NEXT_COMMANDS[key]

                    if suggestions:

                        suggestion = suggestions[0]

                        if stripped == "":
                            return Suggestion(suggestion)

                        if suggestion.startswith(stripped):

                            remaining = suggestion[len(stripped):]

                            return Suggestion(remaining)

        # --------------------------------------------
        # 2️⃣ Command completion
        # --------------------------------------------

        if len(parts) == 1:

            cmd = parts[0]

            all_cmds = list(COMMAND_TREE.keys()) + self.system_commands

            matches = difflib.get_close_matches(cmd, all_cmds, n=1)

            if matches:

                suggestion = matches[0]

                if suggestion.startswith(cmd):

                    remaining = suggestion[len(cmd):]

                    return Suggestion(remaining)

        # --------------------------------------------
        # 3️⃣ Subcommand completion
        # --------------------------------------------

        if len(parts) >= 2:

            tool = parts[0]
            sub = parts[1]

            if tool in COMMAND_TREE:

                matches = difflib.get_close_matches(
                    sub,
                    COMMAND_TREE[tool],
                    n=1
                )

                if matches:

                    suggestion = matches[0]

                    if suggestion.startswith(sub):

                        remaining = suggestion[len(sub):]

                        return Suggestion(remaining)

        return None