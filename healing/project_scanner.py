import os
import ast


def scan_python_file(file_path):
    """Check a Python file for syntax errors"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        ast.parse(source)
        return None

    except SyntaxError as e:
        return {
            "file": file_path,
            "line": e.lineno,
            "error": e.msg,
            "fix": "Check syntax near this line. Possible missing colon, bracket, or indentation."
        }


def scan_project(root="."):
    """Scan entire project directory"""
    errors = []

    for folder, _, files in os.walk(root):
        for file in files:

            if file.endswith(".py"):
                path = os.path.join(folder, file)

                result = scan_python_file(path)

                if result:
                    errors.append(result)

    return errors