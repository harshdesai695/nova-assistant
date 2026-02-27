from core.registry import skill
from typing import Optional
import screen_brightness_control as sbc

@skill
def control_brightness(action: str, value: Optional[int] = None) -> str:
    """
    Control the Windows laptop screen brightness.

    Parameters:
    - action (str): One of 'set', 'increase', or 'decrease'.
    - value (Optional[int]): Brightness percentage (0-100). Required for 'set'.

    Examples:
    - 'set brightness to 50%' → action='set', value=50
    - 'increase brightness' → action='increase'
    - 'decrease brightness' → action='decrease'

    Returns:
    - A human-readable confirmation message.
    - Returns a string starting with 'BRIGHTNESS_CONTROL_UI' on success to trigger the UI.
    """
    try:
        current_brightness = sbc.get_brightness(display=0)[0]

        if action.lower() == "set":
            if value is None:
                return "Error: Please provide a brightness percentage between 0 and 100."
            if not 0 <= value <= 100:
                return "Error: Brightness value must be between 0 and 100."
            sbc.set_brightness(value, display=0)
            return f"BRIGHTNESS_CONTROL_UI: Brightness set to {value}%."

        elif action.lower() == "increase":
            new_value = min(100, current_brightness + 10)
            sbc.set_brightness(new_value, display=0)
            return f"BRIGHTNESS_CONTROL_UI: Brightness increased to {new_value}%."

        elif action.lower() == "decrease":
            new_value = max(0, current_brightness - 10)
            sbc.set_brightness(new_value, display=0)
            return f"BRIGHTNESS_CONTROL_UI: Brightness decreased to {new_value}%."

        else:
            return "Error: Invalid action. Use 'set', 'increase', or 'decrease'."

    except Exception as e:
        return f"Error controlling brightness: {str(e)}"
