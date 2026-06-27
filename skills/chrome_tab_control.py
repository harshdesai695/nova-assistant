from core.registry import skill
import time
from typing import Optional

@skill
def control_chrome_tabs(action: str, identifier: Optional[str] = None) -> str:
    """
    Control Google Chrome tabs using system automation.

    Supported actions:
    - "new_tab" → Opens a new tab.
    - "close_tab" → Closes the current tab or a specific tab by index.
    - "switch_tab" → Switch to a specific tab by index (1-based).
    - "switch_by_title" → Switch to a tab containing text in its title.

    Args:
        action (str): The action to perform.
        identifier (Optional[str]): Tab index (1-based) or partial title text depending on action.

    Returns:
        str: Human-readable result message.
    """
    try:
        import pyautogui
        import pygetwindow as gw

        # Find Chrome window
        chrome_windows = [w for w in gw.getAllWindows() if "Chrome" in w.title]
        if not chrome_windows:
            return "Google Chrome window not found."

        chrome = chrome_windows[0]
        chrome.activate()
        time.sleep(0.5)

        action = action.lower()

        if action == "new_tab":
            pyautogui.hotkey("ctrl", "t")
            return "Opened a new Chrome tab."

        elif action == "close_tab":
            if identifier and identifier.isdigit():
                index = int(identifier)
                pyautogui.hotkey("ctrl", str(index))
                time.sleep(0.2)
            pyautogui.hotkey("ctrl", "w")
            return "Closed the specified Chrome tab." if identifier else "Closed the current Chrome tab."

        elif action == "switch_tab":
            if not identifier or not identifier.isdigit():
                return "Please provide a valid tab index (1-based)."
            index = int(identifier)
            if index < 1 or index > 8:
                return "Chrome supports direct switching only for tabs 1 through 8 using Ctrl+Number."
            pyautogui.hotkey("ctrl", str(index))
            return f"Switched to Chrome tab {index}."

        elif action == "switch_by_title":
            if not identifier:
                return "Please provide part of the tab title to search for."

            # Cycle through tabs to find matching title
            for i in range(1, 9):
                pyautogui.hotkey("ctrl", str(i))
                time.sleep(0.4)
                active_window = gw.getActiveWindow()
                if active_window and identifier.lower() in active_window.title.lower():
                    return f"Switched to tab containing '{identifier}'."
            return f"No Chrome tab found containing '{identifier}'."

        else:
            return "Unsupported action. Use: new_tab, close_tab, switch_tab, or switch_by_title."

    except Exception as e:
        return f"Error controlling Chrome tabs: {str(e)}"