"""
Global hotkey registration for DTVoice.
Monitors Left Ctrl + Left Win combination for system-wide hotkey detection.
"""

import time
import logging
from typing import Callable, Optional
from pynput import keyboard

logger = logging.getLogger(__name__)


class GlobalHotkey:
    """
    Global hotkey listener using pynput.
    Monitors Left Ctrl + Left Win combination and triggers callbacks.
    Works when the app is in system tray (no focused window).
    """

    def __init__(self):
        self._callback: Optional[Callable[[bool], None]] = None
        self._last_press_time: float = 0
        self._debounce_ms: float = 500
        self._ctrl_pressed: bool = False
        self._win_pressed: bool = False
        self._listener: Optional[keyboard.Listener] = None

    def on_hotkey(self, callback: Callable[[bool], None]) -> None:
        """
        Register a callback to be called when hotkey is pressed/released.

        Args:
            callback: Callable that receives bool - True on press, False on release
        """
        self._callback = callback

    def _should_debounce(self) -> bool:
        """Check if the hotkey should be ignored due to debounce."""
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - self._last_press_time < self._debounce_ms:
            return True
        self._last_press_time = current_time
        return False

    def on_press(self, key) -> None:
        """Handle key press events."""
        try:
            if key == keyboard.Key.ctrl_l:
                self._ctrl_pressed = True
            elif key == keyboard.Key.cmd:
                self._win_pressed = True

            # Check if Left Ctrl + Left Win combination is pressed
            if self._ctrl_pressed and self._win_pressed:
                if self._should_debounce():
                    logger.debug("Hotkey press ignored due to debounce")
                    return

                logger.info("Hotkey pressed: Left Ctrl + Left Win")
                if self._callback:
                    self._callback(True)
        except Exception as e:
            logger.warning(f"Error handling key press: {e}")

    def on_release(self, key) -> None:
        """Handle key release events."""
        try:
            if key == keyboard.Key.ctrl_l:
                self._ctrl_pressed = False
            elif key == keyboard.Key.cmd:
                self._win_pressed = False

            # Check if the combination is released (both keys released)
            if not self._ctrl_pressed and not self._win_pressed:
                # Only trigger if we had pressed the combination before
                if self._callback and self._last_press_time > 0:
                    logger.info("Hotkey released: Left Ctrl + Left Win")
                    self._callback(False)
        except Exception as e:
            logger.warning(f"Error handling key release: {e}")

    def start(self) -> bool:
        """
        Start listening for global hotkey.
        Must be called to activate the hotkey detection.

        Returns:
            bool: True if listener started successfully, False otherwise
        """
        try:
            self._listener = keyboard.Listener(
                on_press=self.on_press,
                on_release=self.on_release,
                suppress=False  # Allow keys to be processed by other apps
            )
            self._listener.start()
            logger.info("Global hotkey listener started (Left Ctrl + Left Win)")
            return True
        except Exception as e:
            logger.warning(f"Failed to start hotkey listener: {e}")
            return False

    def stop(self) -> None:
        """Stop the hotkey listener."""
        if self._listener:
            self._listener.stop()
            self._listener = None
            logger.info("Global hotkey listener stopped")

    def __del__(self):
        """Cleanup when object is destroyed."""
        self.stop()


# Module-level singleton instance for easy access
_hotkey_instance: Optional[GlobalHotkey] = None


def get_global_hotkey() -> GlobalHotkey:
    """Get or create the global hotkey singleton instance."""
    global _hotkey_instance
    if _hotkey_instance is None:
        _hotkey_instance = GlobalHotkey()
    return _hotkey_instance


def start_global_hotkey(callback: Callable[[bool], None]) -> bool:
    """
    Convenience function to start the global hotkey with a callback.

    Args:
        callback: Callable that receives bool - True on press, False on release

    Returns:
        bool: True if hotkey started successfully
    """
    hotkey = get_global_hotkey()
    hotkey.on_hotkey(callback)
    return hotkey.start()


if __name__ == "__main__":
    # Simple test to verify import and functionality
    logging.basicConfig(level=logging.DEBUG)

    def test_callback(is_pressed: bool) -> None:
        state = "pressed" if is_pressed else "released"
        print(f"Hotkey {state}!")

    print("Starting global hotkey test...")
    print("Press Left Ctrl + Left Win to test")
    print("Press Ctrl+C to exit")

    started = start_global_hotkey(test_callback)
    if started:
        print("Hotkey listener is running...")
        # Keep the main thread alive
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping hotkey listener...")
            if _hotkey_instance is not None:
                _hotkey_instance.stop()
    else:
        print("Failed to start hotkey listener")