# safety/folder_analyzer.py

import os
from datetime import datetime


def format_size(size):
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"


def analyze_folder(folder_path):

    if not os.path.exists(folder_path):
        print("❌ Folder does not exist.")
        return

    total_size = 0
    total_files = 0
    total_folders = 0
    files_list = []

    for root, dirs, files in os.walk(folder_path):

        total_folders += len(dirs)

        for file in files:

            fp = os.path.join(root, file)

            try:
                size = os.path.getsize(fp)
                total_size += size
                total_files += 1
                files_list.append((file, size))
            except (PermissionError, FileNotFoundError, OSError):
                continue

    try:
        created = datetime.fromtimestamp(os.path.getctime(folder_path))
        modified = datetime.fromtimestamp(os.path.getmtime(folder_path))
    except:
        created = "Unknown"
        modified = "Unknown"

    print("\n📂 Folder Analysis")
    print("────────────────────────")
    print("Folder      :", folder_path)
    print("Created     :", created)
    print("Last Modify :", modified)
    print("Files       :", total_files)
    print("Subfolders  :", total_folders)
    print("Total Size  :", format_size(total_size))

    if files_list:
        print("\nFiles inside:")

        preview = files_list[:10]

        for name, size in preview:
            print(f"  {name} ({format_size(size)})")

        if len(files_list) > 10:
            print(f"  ... and {len(files_list) - 10} more files")

    print("────────────────────────")