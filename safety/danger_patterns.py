# safety/danger_patterns.py

# danger_patterns.py

DANGER_PATTERNS = {
    "rm -rf": "You are deleting files or folders permanently.",
    "rm -rf /": "You are attempting to delete the entire system.",
    "rmdir": "You are deleting a directory.",
    "del": "You are deleting files.",
    "format": "You are formatting a disk. This will erase all data.",
    "shutdown": "You are shutting down the system.",
    "reboot": "You are restarting the system.",
    "mkfs": "You are creating a filesystem which will erase the disk.",
    "dd if=": "You are copying raw disk data. This can destroy disks.",
    "chmod 777": "You are giving full permissions to everyone which is unsafe.",
}