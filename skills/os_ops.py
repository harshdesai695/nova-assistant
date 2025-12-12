import os
import platform
import subprocess
from core.registry import skill

@skill
def open_calculator():
    """
    Opens the calculator application on the user's computer.
    """
    system = platform.system()
    if system == "Windows":
        subprocess.Popen("calc.exe")
    elif system == "Darwin": # macOS
        subprocess.Popen(["open", "-a", "Calculator"])
    elif system == "Linux":
        subprocess.Popen(["gnome-calculator"])
    return "Calculator opened successfully."

@skill
def get_system_info():
    """
    Returns details about the current operating system, release version, and processor.
    Useful for answering 'what computer is this' or 'specs'.
    """
    return {
        "os": platform.system(),
        "release": platform.release(),
        "processor": platform.processor()
    }