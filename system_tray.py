"""
DTVoice System Tray Module

Provides system tray icon with 3 states:
- IDLE (gray): Default state, not recording
- RECORDING (red): Actively recording audio
- TRANSCRIBING (blue): Processing/transcribing audio

Author: DTVoice
"""

from __future__ import annotations

import os
import sys
import logging
from enum import Enum
from typing import Optional, Callable

from PIL import Image, ImageDraw

try:
    import pystray
    from pystray import Menu, MenuItem
except ImportError:
    pystray = None
    Menu = None
    MenuItem = None


logger = logging.getLogger(__name__)


class TrayState(Enum):
    """System tray icon states."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"


class SystemTray:
    """
    System tray manager for DTVoice application.
    
    Handles tray icon, menu, and state transitions.
    Application runs in tray-only mode (no main window).
    """
    
    # Icon colors (RGB)
    ICON_COLORS: dict[TrayState, tuple[int, int, int]] = {
        TrayState.IDLE: (128, 128, 128),        # Gray
        TrayState.RECORDING: (220, 50, 50),     # Red
        TrayState.TRANSCRIBING: (50, 120, 220), # Blue
    }
    
    # Icon size
    ICON_SIZE = (64, 64)
    
    def __init__(
        self,
        on_start_recording: Optional[Callable] = None,
        on_stop_recording: Optional[Callable] = None,
        on_open_settings: Optional[Callable] = None,
        on_exit: Optional[Callable] = None
    ):
        """
        Initialize system tray.
        
        Args:
            on_start_recording: Callback when "Start Recording" menu item clicked
            on_stop_recording: Callback when "Stop Recording" menu item clicked
            on_open_settings: Callback when "Settings" menu item clicked
            on_exit: Callback when "Exit" menu item clicked
        """
        self._state = TrayState.IDLE
        self._is_recording = False
        
        self._callbacks = {
            "start_recording": on_start_recording or (lambda: None),
            "stop_recording": on_stop_recording or (lambda: None),
            "open_settings": on_open_settings or (lambda: None),
            "exit": on_exit or (lambda: self._default_exit),
        }
        
        self._icon = None  # type: ignore[assignment]
        self._icon_image: Optional[Image.Image] = None
        
        if pystray is None:
            logger.error("pystray not installed. System tray will not be available.")
            return
    
    def _generate_icon_image(self, state: TrayState) -> Image.Image:
        """
        Generate tray icon image programmatically with Pillow.
        
        Args:
            state: Current tray state determining icon color
            
        Returns:
            PIL Image of the icon
        """
        size = self.ICON_SIZE
        color = self.ICON_COLORS[state]
        
        # Create image with transparent background
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Calculate circle parameters
        margin = 4
        center = (size[0] // 2, size[1] // 2)
        radius = (size[0] // 2) - margin
        
        # Draw main circle
        draw.ellipse(
            [margin, margin, size[0] - margin, size[1] - margin],
            fill=color + (255,)  # Add alpha
        )
        
        # Draw inner highlight for 3D effect
        highlight_radius = radius // 3
        highlight_center = (center[0] - radius // 4, center[1] - radius // 4)
        draw.ellipse(
            [
                highlight_center[0] - highlight_radius,
                highlight_center[1] - highlight_radius,
                highlight_center[0] + highlight_radius,
                highlight_center[1] + highlight_radius,
            ],
            fill=(255, 255, 255, 80)  # Semi-transparent white
        )
        
        # Draw state-specific symbol
        if state == TrayState.RECORDING:
            # Draw a small square (recording indicator)
            square_size = radius // 2
            draw.rectangle(
                [
                    center[0] - square_size // 2,
                    center[1] - square_size // 2,
                    center[0] + square_size // 2,
                    center[1] + square_size // 2,
                ],
                fill=(255, 255, 255, 200)
            )
        elif state == TrayState.TRANSCRIBING:
            # Draw sound wave bars
            bar_width = 4
            bar_spacing = 6
            bar_heights = [12, 20, 16, 24, 14]
            start_x = center[0] - (len(bar_heights) * bar_spacing) // 2
            
            for i, height in enumerate(bar_heights):
                x = start_x + i * bar_spacing
                draw.rectangle(
                    [
                        x,
                        center[1] - height // 2,
                        x + bar_width,
                        center[1] + height // 2,
                    ],
                    fill=(255, 255, 255, 200)
                )
        elif state == TrayState.IDLE:
            # Draw a microphone-like shape (circle with dot)
            mic_body_radius = radius // 3
            draw.ellipse(
                [
                    center[0] - mic_body_radius,
                    center[1] - mic_body_radius // 2,
                    center[0] + mic_body_radius,
                    center[1] + mic_body_radius * 1.5,
                ],
                fill=(255, 255, 255, 200)
            )
            # Draw stand
            stand_width = 4
            stand_height = radius // 2
            draw.rectangle(
                [
                    center[0] - stand_width // 2,
                    center[1] + mic_body_radius,
                    center[0] + stand_width // 2,
                    center[1] + mic_body_radius + stand_height,
                ],
                fill=(255, 255, 255, 200)
            )
        
        return image
    
    def _build_menu(self) -> "pystray.Menu":  # type: ignore[name-defined]
        """Build the system tray context menu."""
        
        if pystray is None or Menu is None or MenuItem is None:
            raise RuntimeError("pystray is not available")
        
        def get_recording_label():
            return "Stop Recording" if self._is_recording else "Start Recording"
        
        def toggle_recording(item):
            if self._is_recording:
                self._callbacks["stop_recording"]()
            else:
                self._callbacks["start_recording"]()
        
        # Settings submenu (locked for v1 - read-only display)
        settings_menu = Menu(
            MenuItem("Hotkey: Left Ctrl + Left Win", None, enabled=False),
            MenuItem("Output mode: Injection First", None, enabled=False),
            MenuItem("Auto-stop: 60s", None, enabled=False),
            MenuItem("Notifications: On", None, enabled=False),
        )
        
        menu = Menu(
            MenuItem(
                get_recording_label,
                toggle_recording,
            ),
            Menu.SEPARATOR,  # type: ignore[union-attr]
            MenuItem(
                "Settings",
                settings_menu,
            ),
            Menu.SEPARATOR,  # type: ignore[union-attr]
            MenuItem(
                "Exit",
                lambda item: self._callbacks["exit"](),
            ),
        )
        
        return menu
    
    def _update_icon(self):
        """Update the tray icon image."""
        if self._icon is None:
            return
        
        self._icon_image = self._generate_icon_image(self._state)
        self._icon.icon = self._icon_image
    
    def _update_menu(self):
        """Update the tray menu."""
        if self._icon is None:
            return
        
        self._icon.menu = self._build_menu()
    
    def start(self):
        """Start the system tray icon."""
        if pystray is None:
            logger.error("Cannot start system tray: pystray not available")
            return
        
        logger.info("Starting system tray...")
        
        # Generate initial icon
        self._icon_image = self._generate_icon_image(self._state)
        
        # Create tray icon
        self._icon = pystray.Icon(
            "DTVoice",
            self._icon_image,
            "DTVoice",
            menu=self._build_menu(),
        )
        
        # Run icon (blocking)
        self._icon.run()  # type: ignore[union-attr]
    
    def set_idle(self):
        """
        Set tray to IDLE state (gray icon).
        
        Called when recording stops and transcription completes.
        """
        logger.debug("Setting tray state to IDLE")
        self._state = TrayState.IDLE
        self._is_recording = False
        self._update_icon()
        self._update_menu()
    
    def set_recording(self):
        """
        Set tray to RECORDING state (red icon).
        
        Called when recording starts.
        """
        logger.debug("Setting tray state to RECORDING")
        self._state = TrayState.RECORDING
        self._is_recording = True
        self._update_icon()
        self._update_menu()
    
    def set_transcribing(self):
        """
        Set tray to TRANSCRIBING state (blue icon).
        
        Called when recording stops and transcription begins.
        """
        logger.debug("Setting tray state to TRANSCRIBING")
        self._state = TrayState.TRANSCRIBING
        self._is_recording = False
        self._update_icon()
        self._update_menu()
    
    def stop(self):
        """Stop the system tray icon."""
        if self._icon is not None:
            logger.info("Stopping system tray...")
            self._icon.stop()
            self._icon = None
    
    def _default_exit(self):
        """Default exit handler - stops tray and exits application."""
        logger.info("Exit requested from system tray")
        self.stop()
        sys.exit(0)
    
    @property
    def state(self) -> TrayState:
        """Get current tray state."""
        return self._state
    
    @property
    def is_recording(self) -> bool:
        """Check if currently recording."""
        return self._is_recording


def create_tray(
    on_start_recording: Optional[Callable] = None,
    on_stop_recording: Optional[Callable] = None,
    on_open_settings: Optional[Callable] = None,
    on_exit: Optional[Callable] = None,
) -> SystemTray:
    """
    Factory function to create and configure system tray.
    
    Args:
        on_start_recording: Callback for start recording action
        on_stop_recording: Callback for stop recording action
        on_open_settings: Callback for settings action
        on_exit: Callback for exit action
        
    Returns:
        Configured SystemTray instance
    """
    return SystemTray(
        on_start_recording=on_start_recording,
        on_stop_recording=on_stop_recording,
        on_open_settings=on_open_settings,
        on_exit=on_exit,
    )


if __name__ == "__main__":
    # Test/development mode - show tray and allow state testing
    import time
    
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    def test_callback(name: str):
        def cb():
            print(f"[TEST] {name} callback called")
        return cb
    
    print("Testing SystemTray...")
    print("Starting tray icon. Interact with it to test.")
    print("Press Ctrl+C to exit test.")
    
    tray = create_tray(
        on_start_recording=test_callback("start_recording"),
        on_stop_recording=test_callback("stop_recording"),
        on_open_settings=test_callback("open_settings"),
        on_exit=test_callback("exit"),
    )
    
    try:
        tray.start()
    except KeyboardInterrupt:
        print("\nTest ended.")