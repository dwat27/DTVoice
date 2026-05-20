"""
DTVoice Text Injector - Win32 text injection via WM_SETTEXT and clipboard fallback.
"""

import ctypes
from ctypes import wintypes

# Win32 constants
WM_SETTEXT = 0x000C
BM_GETCHECK = 0x00F0
BST_CHECKED = 0x0001

user32 = ctypes.windll.user32


def inject_text(text):
    """
    Inject text into the focused Win32 edit control.

    Attempts to inject text using WM_SETTEXT message.
    Falls back to clipboard if injection fails.

    Args:
        text: String text to inject

    Returns:
        True if text was injected successfully, False otherwise.
        When False is returned, caller should use clipboard fallback.
    """
    if not text:
        return False

    # Get the foreground window (topmost window with focus)
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False

    # Get the focused control within that window
    hwnd_focused = user32.GetFocus()
    if not hwnd_focused:
        return False

    # Try to send WM_SETTEXT to the focused control
    if _send_text_via_message(hwnd_focused, text):
        return True

    # Fallback: try sending to the foreground window itself
    if hwnd_focused != hwnd:
        if _send_text_via_message(hwnd, text):
            return True

    # Final fallback: use clipboard
    return _inject_via_clipboard(text)


def _send_text_via_message(hwnd, text):
    """
    Send WM_SETTEXT message to an edit control.

    Returns True if the message was sent and the control appears to accept text.
    Returns False if the control rejects the message or is a protected window.
    """
    try:
        # Check if window is responsive and not protected
        if _is_protected_window(hwnd):
            return False

        # Send WM_SETTEXT
        # LPARAM is a pointer to the string ( LPCWSTR = ctypes.wintypes.LPCWSTR )
        # The string must remain valid until the message is processed
        text_w = ctypes.c_wchar_p(text)

        result = user32.SendMessageW(hwnd, WM_SETTEXT, 0, text_w)

        # SendMessageW returns 1 (non-zero) for success with EM_SETTEXT
        # Some controls return 0 on failure, but we treat any non-zero as success
        return result != 0

    except (ctypes.ArgumentError, OSError, ValueError):
        return False


def _is_protected_window(hwnd):
    """
    Check if a window is protected (e.g., password fields, secure input).
    """
    try:
        # Protected windows often have specific class names
        class_name = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, class_name, 256)

        class_str = class_name.value.lower()

        # List of protected window class patterns
        protected_patterns = [
            'password',
            'protected',
            'secure',
            'pillow',
        ]

        for pattern in protected_patterns:
            if pattern in class_str:
                return True

        # Check for read-only or disabled controls
        style = user32.GetWindowLongW(hwnd, -16)  # GWL_STYLE
        if style & 0x08000000:  # ES_READONLY
            return True

        # WS_DISABLED
        if style & 0x08000000:
            return True

        return False

    except (ctypes.ArgumentError, OSError):
        # If we can't determine, assume protected to be safe
        return True


def _inject_via_clipboard(text):
    """
    Inject text via clipboard as final fallback.

    Saves current clipboard content, sets new text, pastes, then restores.
    """
    try:
        # Open clipboard
        if not user32.OpenClipboard(None):
            return False

        try:
            # Empty clipboard
            user32.EmptyClipboard()

            # Allocate global memory and copy text
            text_bytes = (text + '\0').encode('utf-16le')
            h_mem = ctypes.windll.kernel32.GlobalAlloc(0x0002, len(text_bytes))  # GMEM_MOVEABLE
            if not h_mem:
                return False

            p_mem = ctypes.windll.kernel32.GlobalLock(h_mem)
            if not p_mem:
                ctypes.windll.kernel32.GlobalFree(h_mem)
                return False

            try:
                ctypes.memmove(p_mem, text_bytes, len(text_bytes))
            finally:
                ctypes.windll.kernel32.GlobalUnlock(h_mem)

            # Set clipboard data (CF_UNICODETEXT = 13)
            CF_UNICODETEXT = 13
            if not user32.SetClipboardData(CF_UNICODETEXT, h_mem):
                ctypes.windll.kernel32.GlobalFree(h_mem)
                return False

        finally:
            user32.CloseClipboard()

        # Simulate Ctrl+V paste
        _simulate_paste()

        return True

    except (ctypes.ArgumentError, OSError, MemoryError):
        return False


def _simulate_paste():
    """
    Simulate Ctrl+V keystroke to paste text.
    """
    try:
        # Keybd_event parameters
        VK_CONTROL = 0x11
        VK_V = 0x56

        # Press Ctrl
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        # Press V
        user32.keybd_event(VK_V, 0, 0, 0)
        # Release V
        user32.keybd_event(VK_V, 0, 2, 0)  # 2 = KEYEVENTF_KEYUP
        # Release Ctrl
        user32.keybd_event(VK_CONTROL, 0, 2, 0)

    except OSError:
        pass