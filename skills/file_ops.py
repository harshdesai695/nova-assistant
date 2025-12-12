import os
from core.registry import skill

@skill
def read_file(file_path: str):
    """
    Reads the complete text content of a file.
    Args:
        file_path: The full absolute path to the file (e.g., "C:/Users/Name/Documents/note.txt").
    """
    try:
        if not os.path.exists(file_path):
            return f"Error: File not found at {file_path}"
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@skill
def write_file(file_path: str, content: str):
    """
    Creates a new file or overwrites an existing one with the provided content.
    Args:
        file_path: The full absolute path for the file.
        content: The text to write inside the file.
    """
    try:
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: File saved at {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@skill
def create_folder(folder_path: str):
    """
    Creates a new folder (directory).
    Args:
        folder_path: The full absolute path of the folder to create.
    """
    try:
        os.makedirs(folder_path, exist_ok=True)
        return f"Success: Folder created at {folder_path}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"

@skill
def list_files(folder_path: str):
    """
    Lists all files and folders inside a specific directory. 
    Useful to see what is inside a folder before reading.
    Args:
        folder_path: The full absolute path of the directory.
    """
    try:
        if not os.path.exists(folder_path):
            return f"Error: Directory not found at {folder_path}"
            
        items = os.listdir(folder_path)
        if not items:
            return "The directory is empty."
            
        return f"Contents of {folder_path}:\n" + "\n".join(items)
    except Exception as e:
        return f"Error listing files: {str(e)}"