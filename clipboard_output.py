"""Clipboard output module for DTVoice."""
import logging

import pyperclip

from config import APP_NAME

logger = logging.getLogger(__name__)


class ClipboardOutput:
    """Handles copying text to the system clipboard."""

    def copy_text(self, text: str) -> bool:
        """
        Copy text to the system clipboard.

        Args:
            text: The text to copy to clipboard.

        Returns:
            True if clipboard was set successfully, False otherwise.
        """
        try:
            pyperclip.copy(text)
            # Verify clipboard content
            clipboard_content = pyperclip.paste()
            if clipboard_content == text:
                logger.info(f"[{APP_NAME}] Copied {len(text)} characters to clipboard")
                return True
            else:
                logger.warning(
                    f"[{APP_NAME}] Clipboard verification failed: "
                    f"expected {len(text)} chars, got {len(clipboard_content)}"
                )
                return False
        except Exception as e:
            logger.error(f"[{APP_NAME}] Failed to copy to clipboard: {e}")
            return False