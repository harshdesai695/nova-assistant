from core.registry import skill
import platform
import subprocess
import os

@skill
def control_system(setting: str, action: str, value: int | None = None) -> str:
    """
    Control essential laptop system settings.
    """
    try:
        system = platform.system().lower()
        setting = setting.lower()
        action = action.lower()

        # ---------------------- VOLUME CONTROL ----------------------
        if setting == "volume":
            if system == "windows":
                if action == "set" and value is not None:
                    value = max(0, min(100, int(value)))

                    # Reset volume to 0 (50 steps down)
                    subprocess.run([
                        "powershell",
                        "-Command",
                        "$wshell = New-Object -ComObject WScript.Shell; "
                        "1..50 | ForEach-Object { $wshell.SendKeys([char]174) }"
                    ], capture_output=True)

                    # Windows typically has ~50 volume steps
                    steps = int(value / 2)

                    # Increase to desired level
                    subprocess.run([
                        "powershell",
                        "-Command",
                        f"$wshell = New-Object -ComObject WScript.Shell; "
                        f"1..{steps} | ForEach-Object {{ $wshell.SendKeys([char]175) }}"
                    ], capture_output=True)

                    return f"System volume set to approximately {value}%."

                elif action == "mute":
                    subprocess.run([
                        "powershell",
                        "-Command",
                        "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
                    ], capture_output=True)
                    return "System volume muted."

                elif action == "unmute":
                    subprocess.run([
                        "powershell",
                        "-Command",
                        "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"
                    ], capture_output=True)
                    return "System volume unmuted."

                else:
                    return "Unsupported volume action."
            else:
                return "Volume control is currently only supported on Windows."

        # ---------------------- WIFI CONTROL ----------------------
        elif setting in ["wifi", "internet"]:
            if system == "windows":
                if action == "on":
                    subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "enabled"], capture_output=True)
                    return "Wi-Fi turned ON."
                elif action == "off":
                    subprocess.run(["netsh", "interface", "set", "interface", "Wi-Fi", "disabled"], capture_output=True)
                    return "Wi-Fi turned OFF."
                else:
                    return "Unsupported Wi-Fi action."
            else:
                return "Wi-Fi control is currently only supported on Windows."

        # ---------------------- BLUETOOTH CONTROL ----------------------
        elif setting == "bluetooth":
            if system == "windows":
                if action == "on":
                    subprocess.run([
                        "powershell",
                        "-Command",
                        "Start-Service bthserv"
                    ], capture_output=True)
                    return "Bluetooth service started (may require admin privileges)."
                elif action == "off":
                    subprocess.run([
                        "powershell",
                        "-Command",
                        "Stop-Service bthserv"
                    ], capture_output=True)
                    return "Bluetooth service stopped (may require admin privileges)."
                else:
                    return "Unsupported Bluetooth action."
            else:
                return "Bluetooth control is currently only supported on Windows."

        else:
            return "Unsupported system setting. Available options: volume, wifi, bluetooth, internet."

    except Exception as e:
        return f"Error controlling system setting: {str(e)}"