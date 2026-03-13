import os
import shutil

def create_folder(name):

    try:
        os.makedirs(name, exist_ok=True)
        return f"Folder '{name}' created successfully"
    except Exception as e:
        return f"Error creating folder: {e}"


def create_file(name):

    try:
        with open(name, "w") as f:
            pass
        return f"File '{name}' created successfully"
    except Exception as e:
        return f"Error creating file: {e}"


def delete_folder(name):

    try:
        os.rmdir(name)
        return f"Folder '{name}' deleted successfully"
    except Exception as e:
        return f"Error deleting folder: {e}"


def delete_file(name):

    try:
        os.remove(name)
        return f"File '{name}' deleted successfully"
    except Exception as e:
        return f"Error deleting file: {e}"

def copy_file(src, dst):

    try:
        shutil.copy(src, dst)
        return f"File '{src}' copied to '{dst}'"
    except Exception as e:
        return f"Error copying file: {e}"


def move_file(src, dst):

    try:
        shutil.move(src, dst)
        return f"File '{src}' moved to '{dst}'"
    except Exception as e:
        return f"Error moving file: {e}"


def rename_file(src, dst):

    try:
        os.rename(src, dst)
        return f"File renamed from '{src}' to '{dst}'"
    except Exception as e:
        return f"Error renaming file: {e}"


def open_folder(name):

    try:
        os.startfile(name)
        return f"Opened folder '{name}'"
    except Exception as e:
        return f"Error opening folder: {e}"