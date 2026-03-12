"""Clipboard utilities."""


def copy_to_clipboard(text: str) -> bool:
    """Copy text to system clipboard.

    Args:
        text: Text to copy.

    Returns:
        True if successful, False otherwise.
    """
    try:
        import pyperclip

        pyperclip.copy(text)
        return True
    except Exception:
        # Clipboard may not be available in some environments
        return False
