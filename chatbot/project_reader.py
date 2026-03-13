import os

MAX_FILE_SIZE = 10000

SUPPORTED_EXT = (
    ".py", ".js", ".ts", ".java", ".json",
    ".yaml", ".yml", ".md", ".txt"
)

IGNORE_DIRS = {
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv"
}


def read_project_code(base_path="."):

    collected = []

    for root, dirs, files in os.walk(base_path):

        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:

            if file.endswith(SUPPORTED_EXT):

                path = os.path.join(root, file)

                try:

                    if os.path.getsize(path) > MAX_FILE_SIZE:
                        continue

                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        code = f.read()

                    collected.append(f"\nFILE: {path}\n{code}\n")

                except Exception:
                    pass

    return "\n".join(collected)


def read_single_file(path):

    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    except Exception as e:
        return f"Error reading file: {e}"


def build_project_tree(base_path="."):

    tree = []

    for root, dirs, files in os.walk(base_path):

        level = root.replace(base_path, "").count(os.sep)

        indent = " " * 4 * level

        tree.append(f"{indent}{os.path.basename(root)}/")

        subindent = " " * 4 * (level + 1)

        for f in files:
            tree.append(f"{subindent}{f}")

    return "\n".join(tree)