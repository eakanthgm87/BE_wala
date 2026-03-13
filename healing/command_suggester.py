import difflib
import os


# ==============================
# CUSTOM COMMANDS
# ==============================

CUSTOM_COMMANDS = [

    # BASIC SHELL COMMANDS
    "ls","dir","cd","pwd","mkdir","rmdir","del","copy","move","rename",
    "type","cls","clear","echo","exit",

    # ADMIN COMMANDS
    "admin rmdir","admin delete","admin wipe",

    # AI COMMANDS
    "ai: help","ai: scan project","ai: show errors","ai: explain errors",
    "ai: fix errors","ai: clear errors","ai: create folder",
    "ai: create file","ai: fix file",

    # DEVELOPMENT TOOLS
    "git","docker","python","python3","pip","pip3","java","javac",
    "node","npm","npx","mvn","gradle",

    # GIT SUBCOMMANDS
    "git init","git clone","git pull","git push","git commit","git status",
    "git add","git checkout","git branch","git merge",

    # DOCKER SUBCOMMANDS
    "docker run","docker build","docker pull","docker push",
    "docker images","docker ps","docker stop","docker start",
    "docker rm","docker exec","docker logs",

    # SYSTEM COMMANDS
    "ipconfig","ping","tasklist","taskkill","whoami","netstat",

    # FILE TOOLS
    "notepad","code",
]


# ==============================
# GET SYSTEM COMMANDS
# ==============================

def get_system_commands():

    commands = set()

    paths = os.environ.get("PATH", "").split(os.pathsep)

    for path in paths:

        if os.path.exists(path):

            try:
                for file in os.listdir(path):

                    name = os.path.splitext(file)[0]
                    commands.add(name)

            except:
                pass

    return list(commands)


# ==============================
# MERGE ALL COMMANDS
# ==============================

ALL_COMMANDS = list(set(CUSTOM_COMMANDS + get_system_commands()))


# ==============================
# COMMAND SUGGESTION FUNCTION
def suggest_command(command):

    parts = command.split()

    if not parts:
        return None

    # ------------------------------
    # Try matching full multi-word command
    # ------------------------------
    matches = difflib.get_close_matches(
        command,
        CUSTOM_COMMANDS,
        n=1,
        cutoff=0.6
    )

    if matches:

        suggestion = matches[0]

        # keep arguments
        if len(parts) > len(suggestion.split()):
            suggestion += " " + " ".join(parts[len(suggestion.split()):])

        return suggestion

    # ------------------------------
    # Fix first two words (admin rmdri → admin rmdir)
    # ------------------------------
    if len(parts) >= 2:

        base_two = parts[0] + " " + parts[1]

        matches = difflib.get_close_matches(
            base_two,
            CUSTOM_COMMANDS,
            n=1,
            cutoff=0.6
        )

        if matches:

            suggestion = matches[0]

            if len(parts) > 2:
                suggestion += " " + " ".join(parts[2:])

            return suggestion

    # ------------------------------
    # Fix single command
    # ------------------------------
    base_command = parts[0]

    matches = difflib.get_close_matches(
        base_command,
        ALL_COMMANDS,
        n=1,
        cutoff=0.6
    )

    if matches:

        suggestion = matches[0]

        if len(parts) > 1:
            suggestion += " " + " ".join(parts[1:])

        return suggestion

    return None