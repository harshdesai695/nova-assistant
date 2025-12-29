from core.registry import skill

@skill
def enable_visual_system():
    """
    Activates the camera and visual input systems. 
    Use this when the user says 'open camera', 'I want to see something', or 'turn on visual mode'.
    """
    # We return a specific confirmation code that the GUI listens for
    return "ACTIVATE_VISUAL_PROTOCOL_01"