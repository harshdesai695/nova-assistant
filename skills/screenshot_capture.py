from core.registry import skill
from datetime import datetime
import os

try:
    import pyautogui
except ImportError:
    pyautogui = None


@skill
def capture_screenshot(file_path: str, add_timestamp: bool = False) -> str:
    """
    Capture a screenshot of the current screen and save it to the specified file path.

    Args:
        file_path (str): Full file path where the screenshot will be saved (e.g., /path/to/image.png).
        add_timestamp (bool): If True, appends a timestamp to the filename before saving.

    Returns:
        str: Human-readable status message indicating success or failure.
    """
    try:
        if pyautogui is None:
            return "Error: pyautogui library is not installed."

        directory, filename = os.path.split(file_path)
        name, ext = os.path.splitext(filename)

        if not ext:
            ext = ".png"

        if add_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}{ext}"
        else:
            filename = f"{name}{ext}"

        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

        final_path = os.path.join(directory, filename) if directory else filename

        screenshot = pyautogui.screenshot()
        screenshot.save(final_path)

        return "Screenshot captured successfully."

    except Exception as e:
        return f"Error capturing screenshot: {str(e)}"