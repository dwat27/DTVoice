"""
DTVoice Output Dispatcher - Routes transcription output to appropriate handler.
"""

import logging

import text_injector
import clipboard_output
import popup_ui

from config import APP_NAME
from i18n import get_i18n

logger = logging.getLogger(__name__)


class OutputDispatcher:
    """
    Dispatches transcription output to the best available handler.

    Output strategy:
    1. Try text injection first (TextInjector) - direct input to focused control
    2. Fall back to clipboard (ClipboardOutput) if injection fails
    3. Always show popup notification (PopupUI) for user feedback
    """

    def __init__(self):
        """Initialize output handlers."""
        self._text_injector = text_injector
        self._clipboard = clipboard_output.ClipboardOutput()
        self._popup = popup_ui.PopupUI()
        self._last_mode = None

    @property
    def last_output_mode(self):
        """Return the output mode that succeeded in the last output() call."""
        return self._last_mode

    def output(self, text: str) -> bool:
        """
        Output text via the best available method.

        Args:
            text: The text to output.

        Returns:
            True if text was delivered successfully (injection or clipboard),
            False if all methods failed.
        """
        if not text or not text.strip():
            logger.warning(f"[{APP_NAME}] Empty text passed to output()")
            return False

        success = False
        self._last_mode = None

        # Step 1: Try text injection first
        logger.info(f"[{APP_NAME}] Attempting text injection...")
        if self._try_inject(text):
            self._last_mode = "injection"
            success = True
            logger.info(f"[{APP_NAME}] Text injection succeeded ({len(text)} chars)")
        else:
            # Step 2: Fall back to clipboard
            logger.info(f"[{APP_NAME}] Injection failed, attempting clipboard...")
            if self._clipboard.copy_text(text):
                self._last_mode = "clipboard"
                success = True
                logger.info(f"[{APP_NAME}] Clipboard copy succeeded ({len(text)} chars)")
            else:
                logger.error(f"[{APP_NAME}] All output methods failed for text ({len(text)} chars)")

        # Step 3: Always show popup notification (informational regardless of success)
        self._show_notification(text, success)

        return success

    def _try_inject(self, text: str) -> bool:
        """
        Try to inject text via text_injector module.

        Returns:
            True if injection succeeded, False otherwise.
        """
        try:
            # text_injector module has inject_text() function
            return text_injector.inject_text(text)
        except Exception as e:
            logger.error(f"[{APP_NAME}] Text injection exception: {e}")
            return False

    def _show_notification(self, text: str, success: bool) -> None:
        """
        Show popup notification regardless of output success.

        Args:
            text: The text that was (attempted to be) output.
            success: Whether the output succeeded.
        """
        try:
            self._popup.show_transcription(text)
            logger.debug(f"[{APP_NAME}] Popup notification shown")
        except Exception as e:
            logger.error(f"[{APP_NAME}] Failed to show popup notification: {e}")