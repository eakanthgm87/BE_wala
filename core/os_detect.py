import platform

def get_os():

    system = platform.system()

    if system == "Windows":
        return "Windows"

    if system == "Darwin":
        return "macOS"

    if system == "Linux":
        return "Linux"

    return "Unknown"

