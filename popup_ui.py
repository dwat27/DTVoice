"""
Popup notification UI for DTVoice.
Uses plyer for cross-platform toast notifications.
"""

from plyer import notification


class PopupUI:
    """Handles popup notification display for transcription results."""

    MAX_TEXT_LENGTH = 500
    DISMISS_TIMEOUT = 5  # seconds

    def show_error(self, error_type: str, message: str) -> None:
        """
        Show a Windows toast notification for errors.

        Args:
            error_type: Type of error for logging purposes.
            message: User-friendly error message to display.
        """
        if not message or not message.strip():
            return

        notification = notification.Notification()
        notification.title = f"DTVoice - {error_type}"
        notification.message = message
        notification.timeout = self.DISMISS_TIMEOUT
        notification.send()

    def show_transcription(self, text: str) -> None:
        """
        Show a Windows toast notification with transcription text.

        Args:
            text: The transcription text to display.
        """
        if not text or not text.strip():
            return

        # Truncate text if too long
        display_text = text.strip()
        if len(display_text) > self.MAX_TEXT_LENGTH:
            display_text = display_text[:self.MAX_TEXT_LENGTH - 3] + "..."

        notification = notification.Notification()
        notification.title = "DTVoice Transcription"
        notification.message = display_text
        notification.timeout = self.DISMISS_TIMEOUT

        # Note: plyer doesn't natively support actions on Windows toast notifications.
        # The copy functionality would require platform-specific implementation
        # (e.g., win32gui, toaster, or windows-api). For cross-platform simplicity,
        # we rely on the system notification center which may allow copying text.
        notification.send()
