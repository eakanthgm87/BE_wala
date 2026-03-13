# safety/file_analyzer.py

import os
from datetime import datetime


def format_size(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def analyze_file(file_path):

    if not os.path.exists(file_path):
        print("❌ File does not exist.")
        return

    if not os.path.isfile(file_path):
        print("❌ Not a valid file.")
        return

    try:
        size = os.path.getsize(file_path)
        created = datetime.fromtimestamp(os.path.getctime(file_path))
        modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        extension = os.path.splitext(file_path)[1] or "Unknown"

    except (PermissionError, FileNotFoundError, OSError):
        print("❌ Unable to read file information.")
        return


    print("\n📄 File Analysis")
    print("────────────────────────")
    print("File        :", file_path)
    print("Type        :", extension)
    print("Size        :", format_size(size))
    print("Created     :", created)
    print("Last Modify :", modified)
    print("────────────────────────")