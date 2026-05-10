import pyautogui
import os

def take_screenshot(filename="screenshot.png"):
    """
    Take a screenshot and save it.

    Args:
        filename (str): Filename to save the screenshot.

    Returns:
        str: Path to the saved screenshot.
    """
    try:
        screenshot = pyautogui.screenshot()
        path = os.path.join(os.getcwd(), filename)
        screenshot.save(path)
        return f"Screenshot saved to {path}"
    except Exception as e:
        return f"Failed to take screenshot: {str(e)}"