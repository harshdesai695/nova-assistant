from core.registry import skill

@skill
def request_user_input(reason: str) -> str:
    """
    Requests additional input, text, or file uploads from the user via a GUI popup.
    Call this skill when you explicitly need the user to type something out,
    provide a file or image, or clarify a complex request that requires a dedicated UI input.
    
    Args:
        reason: A brief explanation to show the user why input is needed.
    """
    return f"ACTIVATE_USER_INPUT_PROTOCOL {reason}"