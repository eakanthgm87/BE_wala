from core.executor import run_command
import re
from healing.file_ops import (
    create_folder,
    create_file,
    delete_folder,
    delete_file,
    copy_file,
    move_file,
    rename_file,
    open_folder
)

# ---------------------------------------------------------
# WORD VARIATIONS
# ---------------------------------------------------------

CREATE_WORDS = ["create", "make", "generate", "build", "add"]

DELETE_WORDS = ["delete", "remove", "destroy", "erase"]

FOLDER_WORDS = ["folder", "directory", "dir"]

FILE_WORDS = ["file", "document"]


# ---------------------------------------------------------
# CLEAN INPUT
# ---------------------------------------------------------

def normalize_query(query):

    q = query.lower()

    replacements = {
        "initialize": "init",
        "initialise": "init",
        "repository": "repo",
        "directory": "folder",
        "start": "run",
        "execute": "run",
        "launch": "run",
        "container": "docker container"
    }

    for k, v in replacements.items():
        q = q.replace(k, v)

    fillers = ["a", "new", "called", "named", "the"]

    for f in fillers:
        q = q.replace(f" {f} ", " ")

    return q.strip()


# ---------------------------------------------------------
# CREATE FOLDER
# ---------------------------------------------------------

def try_create_folder(q):

    for action in CREATE_WORDS:
        for target in FOLDER_WORDS:

            pattern = rf"{action} .*{target} (.+)"
            m = re.search(pattern, q)

            if m:
                name = m.group(1).strip()
                return create_folder(name)

    return None


# ---------------------------------------------------------
# CREATE FILE
# ---------------------------------------------------------

def try_create_file(q):

    for action in CREATE_WORDS:
        for target in FILE_WORDS:

            pattern = rf"{action} .*{target} (.+)"
            m = re.search(pattern, q)

            if m:

                name = m.group(1).strip()

                if "python file" in q and not name.endswith(".py"):
                    name += ".py"

                return create_file(name)

    return None


# ---------------------------------------------------------
# DELETE FILE
# ---------------------------------------------------------

def try_delete_file(q):

    for action in DELETE_WORDS:
        for target in FILE_WORDS:

            pattern = rf"{action} .*{target} (.+)"
            m = re.search(pattern, q)

            if m:
                name = m.group(1).strip()
                return delete_file(name)

    return None


# ---------------------------------------------------------
# DELETE FOLDER
# ---------------------------------------------------------

def try_delete_folder(q):

    for action in DELETE_WORDS:
        for target in FOLDER_WORDS:

            pattern = rf"{action} .*{target} (.+)"
            m = re.search(pattern, q)

            if m:
                name = m.group(1).strip()
                return delete_folder(name)

    return None


# ---------------------------------------------------------
# COPY FILE
# ---------------------------------------------------------

def try_copy_file(q):

    m = re.search(r"copy .*file (.+) to (.+)", q)

    if m:
        src = m.group(1).strip()
        dst = m.group(2).strip()
        return copy_file(src, dst)

    return None


# ---------------------------------------------------------
# MOVE FILE
# ---------------------------------------------------------

def try_move_file(q):

    m = re.search(r"move .*file (.+) to (.+)", q)

    if m:
        src = m.group(1).strip()
        dst = m.group(2).strip()
        return move_file(src, dst)

    return None


# ---------------------------------------------------------
# RENAME FILE
# ---------------------------------------------------------

def try_rename_file(q):

    m = re.search(r"rename .*file (.+) to (.+)", q)

    if m:
        src = m.group(1).strip()
        dst = m.group(2).strip()
        return rename_file(src, dst)

    return None


# ---------------------------------------------------------
# OPEN FOLDER
# ---------------------------------------------------------

def try_open_folder(q):

    m = re.search(r"open .*folder (.+)", q)

    if m:
        name = m.group(1).strip()
        return open_folder(name)

    return None


# ---------------------------------------------------------
# PYTHON COMMANDS
# ---------------------------------------------------------

def try_python_commands(q, stream_callback=None):

    m = re.search(r"run python file (.+)", q)
    if m:
        name = m.group(1).strip()
        if not name.endswith(".py"):
            name += ".py"
        return run_command(f"python {name}", stream_callback)

    m = re.search(r"create python file (.+)", q)
    if m:
        name = m.group(1).strip()
        if not name.endswith(".py"):
            name += ".py"
        return run_command(f"type nul > {name}", stream_callback)

    m = re.search(r"install python package (.+)", q)
    if m:
        pkg = m.group(1).strip()
        return run_command(f"pip install {pkg}", stream_callback)

    return None


# ---------------------------------------------------------
# DOCKER COMMANDS
# ---------------------------------------------------------

def try_docker_commands(q, stream_callback=None):

    if "docker build" in q or "build docker image" in q:
        return run_command("docker build .", stream_callback)

    if "run docker container" in q or "docker run" in q:
        return run_command("docker run", stream_callback)

    if "docker images" in q or "show docker images" in q:
        return run_command("docker images", stream_callback)

    if "docker ps" in q or "list docker containers" in q:
        return run_command("docker ps", stream_callback)

    return None


# ---------------------------------------------------------
# GIT COMMANDS
# ---------------------------------------------------------

def try_git_commands(q, stream_callback=None):

    if "init git" in q or "create git repo" in q or "make git repo" in q:
        return run_command("git init", stream_callback)

    if "git status" in q or "show git status" in q:
        return run_command("git status", stream_callback)

    if "commit changes" in q:
        return run_command('git commit -m "update"', stream_callback)

    if "push changes" in q:
        return run_command("git push", stream_callback)

    if "pull changes" in q:
        return run_command("git pull", stream_callback)

    return None


# ---------------------------------------------------------
# DEPENDENCY COMMANDS
# ---------------------------------------------------------

def try_dependency_commands(q, stream_callback=None):

    if "install requirements" in q or "install python dependencies" in q:
        return run_command("pip install -r requirements.txt", stream_callback)

    if "install node dependencies" in q or "install npm dependencies" in q:
        return run_command("npm install", stream_callback)

    m = re.search(r"install npm package (.+)", q)
    if m:
        pkg = m.group(1).strip()
        return run_command(f"npm install {pkg}", stream_callback)

    m = re.search(r"(install|add) dependency (.+)", q)
    if m:
        pkg = m.group(2).strip()
        return run_command(f"pip install {pkg}", stream_callback)

    m = re.search(r"install (.+)", q)
    if m:
        pkg = m.group(1).strip()
        return run_command(f"pip install {pkg}", stream_callback)

    return None


# ---------------------------------------------------------
# MAIN PARSER
# ---------------------------------------------------------

def parse_natural_command(query, stream_callback=None):

    q = normalize_query(query)

    result = try_create_folder(q)
    if result:
        return result

    result = try_create_file(q)
    if result:
        return result

    result = try_delete_file(q)
    if result:
        return result

    result = try_delete_folder(q)
    if result:
        return result

    result = try_copy_file(q)
    if result:
        return result

    result = try_move_file(q)
    if result:
        return result

    result = try_rename_file(q)
    if result:
        return result

    result = try_open_folder(q)
    if result:
        return result

    result = try_python_commands(q, stream_callback)
    if result:
        return result

    result = try_git_commands(q, stream_callback)
    if result:
        return result

    result = try_dependency_commands(q, stream_callback)
    if result:
        return result

    result = try_docker_commands(q, stream_callback)
    if result:
        return result

    return None