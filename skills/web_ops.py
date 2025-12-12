import webbrowser
from core.registry import skill

@skill
def open_website(url: str):
    """
    Opens a specific website URL in the default browser.
    Args:
        url: The full URL to open (e.g., https://www.google.com)
    """
    if not url.startswith('http'):
        url = 'https://' + url
    webbrowser.open(url)
    return f"Opening {url} in your browser."