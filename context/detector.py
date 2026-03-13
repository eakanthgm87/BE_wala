import os


def detect_context(path="."):

    files = os.listdir(path)

    context = []

    if "requirements.txt" in files:
        context.append("Python")

    if "package.json" in files:
        context.append("Node")

    if "Dockerfile" in files:
        context.append("Docker")

    if "manage.py" in files:
        context.append("Django")

    if ".git" in files:
        context.append("Git")

    if context:
        return " project with ".join(context)

    return "Unknown project"