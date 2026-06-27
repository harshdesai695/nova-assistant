import os
from typing import Dict

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IGNORE_DIRS = {".git", "__pycache__", "venv", "env", ".venv", "build", "dist", ".idea", ".vscode"}

FILE_INDEX: Dict[str, str] = {}

def build_index():
    global FILE_INDEX
    FILE_INDEX.clear()
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            FILE_INDEX[file] = os.path.join(root, file)

def get_file_path(filename: str) -> str:
    if not FILE_INDEX:
        build_index()
    if os.path.exists(filename) and os.path.isabs(filename):
        return filename
    if filename in FILE_INDEX:
        return FILE_INDEX[filename]
    build_index()
    if filename in FILE_INDEX:
        return FILE_INDEX[filename]
    for indexed_file, path in FILE_INDEX.items():
        if filename.lower() == indexed_file.lower():
            return path
    for indexed_file, path in FILE_INDEX.items():
        if filename.lower() in indexed_file.lower():
            return path
    return filename