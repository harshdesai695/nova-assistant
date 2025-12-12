from core.registry import skill
from AppOpener import open as open_app
import logging

logger = logging.getLogger("NOVA")

@skill
def launch_application(app_name: str):
    """
    Opens any installed application on the Windows system by its name.
    Useful when the user says "Open WhatsApp", "Start Spotify", "Launch Visual Studio Code".
    
    Args:
        app_name: The name of the application to open (e.g., 'whatsapp', 'chrome', 'notepad').
    """
    logger.info(f"🚀 Launching App: {app_name}")
    
    try:
        # 'match_closest=True' allows it to find "WhatsApp" even if you type "whatsap"
        # 'output=False' silences the library's console logs
        open_app(app_name, match_closest=True, output=False)
        return f"Opening {app_name}..."
    except Exception as e:
        logger.error(f"App Launch Failed: {e}")
        return f"I couldn't find an app named '{app_name}' on this system."