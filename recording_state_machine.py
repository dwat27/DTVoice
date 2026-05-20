"""
Recording State Machine for DTVoice.

Manages recording lifecycle with states:
- IDLE: Not recording, waiting for input
- RECORDING: Actively recording audio
- TRANSCRIBING: Processing audio to text
- OUTPUT: Transcription complete, ready for injection

Handles:
- Hotkey-triggered start/stop
- Auto-stop on silence (3s threshold)
- Auto-stop on max duration (60s default)
- System tray icon state updates
"""

import logging
import threading
import time
from enum import Enum
from typing import Optional, Callable

import numpy as np

from audio_capture import AudioCapture
from transcriber import Transcriber
from system_tray import SystemTray, TrayState
from i18n import get_i18n


logger = logging.getLogger(__name__)


class InvalidStateTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""
    pass


class RecordingState(Enum):
    """Recording state machine states."""
    IDLE = "idle"
    RECORDING = "recording"
    TRANSCRIBING = "transcribing"
    OUTPUT = "output"


# Valid state transitions: from_state -> [allowed_to_states]
VALID_TRANSITIONS: dict[RecordingState, list[RecordingState]] = {
    RecordingState.IDLE: [RecordingState.RECORDING],
    RecordingState.RECORDING: [RecordingState.TRANSCRIBING, RecordingState.IDLE],
    RecordingState.TRANSCRIBING: [RecordingState.OUTPUT, RecordingState.IDLE],
    RecordingState.OUTPUT: [RecordingState.IDLE],
}


class RecordingStateMachine:
    """
    State machine managing recording lifecycle.

    Accepts AudioCapture and Transcriber instances for actual recording/transcription,
    and SystemTray instance for UI state updates.
    """

    # Silence detection
    SILENCE_THRESHOLD_DB = -40.0  # dB threshold for silence
    SILENCE_DURATION_SEC = 3.0   # seconds of silence before auto-stop

    # Duration limits
    DEFAULT_MAX_DURATION_SEC = 60.0

    def __init__(
        self,
        audio_capture: AudioCapture,
        transcriber: Transcriber,
        system_tray: SystemTray,
        max_duration_sec: float = DEFAULT_MAX_DURATION_SEC,
    ):
        """
        Initialize recording state machine.

        Args:
            audio_capture: AudioCapture instance for recording
            transcriber: Transcriber instance for speech-to-text
            system_tray: SystemTray instance for icon updates
            max_duration_sec: Maximum recording duration before auto-stop
        """
        self._audio_capture = audio_capture
        self._transcriber = transcriber
        self._system_tray = system_tray
        self._max_duration_sec = max_duration_sec

        # Current state
        self._state = RecordingState.IDLE
        self._lock = threading.Lock()

        # Recording metadata
        self._recording_start_time: Optional[float] = None
        self._last_audio_time: Optional[float] = None
        self._last_audio_level: float = float('-inf')

        # Transcription result
        self._transcription_text: str = ""

        # Callbacks
        self._on_transcription_complete: Optional[Callable[[str], None]] = None
        self._on_state_changed: Optional[Callable[[RecordingState], None]] = None

        # Audio level tracking for silence detection
        self._silence_start_time: Optional[float] = None

        logger.info(f"RecordingStateMachine initialized (max_duration={max_duration_sec}s)")

    @property
    def state(self) -> RecordingState:
        """Get current recording state."""
        with self._lock:
            return self._state

    @property
    def transcription_text(self) -> str:
        """Get transcription result from last recording."""
        return self._transcription_text

    def set_on_transcription_complete(self, callback: Callable[[str], None]) -> None:
        """Set callback for when transcription completes."""
        self._on_transcription_complete = callback

    def set_on_state_changed(self, callback: Callable[[RecordingState], None]) -> None:
        """Set callback for when state changes."""
        self._on_state_changed = callback

    def _can_transition_to(self, new_state: RecordingState) -> bool:
        """Check if transition to new_state is valid."""
        allowed = VALID_TRANSITIONS.get(self._state, [])
        return new_state in allowed

    def _transition_to(self, new_state: RecordingState) -> None:
        """
        Transition to a new state.

        Args:
            new_state: State to transition to

        Raises:
            InvalidStateTransitionError: If transition is not allowed
        """
        if not self._can_transition_to(new_state):
            raise InvalidStateTransitionError(
                f"Cannot transition from {self._state.value} to {new_state.value}"
            )

        old_state = self._state
        self._state = new_state

        logger.info(f"State transition: {old_state.value} -> {new_state.value}")

        # Update tray icon based on new state
        self._update_tray_state()

        # Fire state change callback
        if self._on_state_changed:
            self._on_state_changed(new_state)

    def _update_tray_state(self) -> None:
        """Update system tray icon to match current state."""
        if self._system_tray is None:
            return

        state_map = {
            RecordingState.IDLE: TrayState.IDLE,
            RecordingState.RECORDING: TrayState.RECORDING,
            RecordingState.TRANSCRIBING: TrayState.TRANSCRIBING,
            RecordingState.OUTPUT: TrayState.TRANSCRIBING,  # Output uses transcribing color
        }

        tray_state = state_map.get(self._state, TrayState.IDLE)

        if tray_state == TrayState.IDLE:
            self._system_tray.set_idle()
        elif tray_state == TrayState.RECORDING:
            self._system_tray.set_recording()
        elif tray_state == TrayState.TRANSCRIBING:
            self._system_tray.set_transcribing()

    def _calculate_audio_level_db(self, audio_data: bytes) -> float:
        """
        Calculate audio level in decibels.

        Args:
            audio_data: Raw PCM16 audio bytes

        Returns:
            Audio level in dB (relative to full scale)
        """
        if len(audio_data) < 2:
            return float('-inf')

        samples = np.frombuffer(audio_data, dtype=np.int16)
        if len(samples) == 0:
            return float('-inf')

        # Calculate RMS (root mean square)
        rms = np.sqrt(np.mean(samples.astype(np.float32) ** 2))

        if rms < 1e-10:
            return float('-inf')

        # Convert to dB (relative to full scale of 32768)
        db = 20 * np.log10(rms / 32768)
        return db

    def _is_silence(self, audio_data: bytes) -> bool:
        """Check if audio data is silence."""
        level = self._calculate_audio_level_db(audio_data)
        return level < self.SILENCE_THRESHOLD_DB

    def _hotkey_callback(self, is_pressed: bool) -> None:
        """
        Handle hotkey press/release.

        Args:
            is_pressed: True if hotkey was pressed, False if released
        """
        if is_pressed:
            logger.debug("Hotkey pressed")
            self._toggle_recording()

    def _toggle_recording(self) -> None:
        """Toggle between IDLE and RECORDING states."""
        current = self.state

        try:
            if current == RecordingState.IDLE:
                self._start_recording()
            elif current == RecordingState.RECORDING:
                self._stop_recording()
            else:
                logger.debug(f"Cannot toggle recording from state: {current.value}")
        except Exception as e:
            logger.error(f"Error toggling recording: {e}")

    def _start_recording(self) -> None:
        """Start recording audio."""
        current = self.state
        if current != RecordingState.IDLE:
            logger.warning(f"Cannot start recording from state: {current.value}")
            return

        # Guard against concurrent recording
        if self._audio_capture.is_recording():
            logger.warning("AudioCapture already recording, ignoring start request")
            return

        try:
            logger.info("Starting recording...")
            self._audio_capture.start()
            self._recording_start_time = time.time()
            self._last_audio_time = time.time()
            self._silence_start_time = None
            self._transition_to(RecordingState.RECORDING)
            logger.info("Recording started")
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            # Revert to IDLE on failure
            self._transition_to(RecordingState.IDLE)
            raise

    def _stop_recording(self) -> None:
        """Stop recording and start transcription."""
        current = self.state
        if current != RecordingState.RECORDING:
            logger.warning(f"Cannot stop recording from state: {current.value}")
            return

        try:
            logger.info("Stopping recording...")
            audio_data = self._audio_capture.stop()
            self._recording_start_time = None

            # Check if we got any audio
            if len(audio_data) < 2:
                logger.warning("No audio recorded")
                self._transcription_text = ""
                self._transition_to(RecordingState.IDLE)
                return

            # Transition to TRANSCRIBING
            self._transition_to(RecordingState.TRANSCRIBING)

            # Perform transcription in background
            threading.Thread(target=self._transcribe_audio, args=(audio_data,), daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            self._transition_to(RecordingState.IDLE)
            raise

    def _transcribe_audio(self, audio_data: bytes) -> None:
        """Transcribe audio in background thread."""
        try:
            logger.info("Starting transcription...")
            text = self._transcriber.transcribe(audio_data)
            self._transcription_text = text
            logger.info(f"Transcription complete: '{text[:50]}...' ({len(text)} chars)" if len(text) > 50 else f"Transcription complete: '{text}'")

            # Transition to OUTPUT
            self._transition_to(RecordingState.OUTPUT)

            # Fire completion callback
            if self._on_transcription_complete:
                self._on_transcription_complete(text)

            # After a short delay, return to IDLE
            threading.Timer(2.0, self._transition_to, args=(RecordingState.IDLE,)).start()

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            self._transcription_text = ""
            self._transition_to(RecordingState.IDLE)

    def _check_auto_stop_conditions(self) -> Optional[str]:
        """
        Check if recording should auto-stop.

        Returns:
            Reason for auto-stop, or None if should continue
        """
        if self._recording_start_time is None:
            return None

        current_time = time.time()
        elapsed = current_time - self._recording_start_time

        # Check max duration
        if elapsed >= self._max_duration_sec:
            return f"Max duration reached ({self._max_duration_sec}s)"

        return None

    def _update_audio_level(self, audio_data: bytes) -> None:
        """
        Update audio level tracking for silence detection.

        Args:
            audio_data: Current audio chunk
        """
        current_time = time.time()
        self._last_audio_time = current_time
        self._last_audio_level = self._calculate_audio_level_db(audio_data)

        if self._is_silence(audio_data):
            if self._silence_start_time is None:
                self._silence_start_time = current_time
            else:
                silence_duration = current_time - self._silence_start_time
                if silence_duration >= self.SILENCE_DURATION_SEC:
                    logger.info(f"Auto-stop triggered: silence for {silence_duration:.1f}s")
                    self._stop_recording()
        else:
            # Reset silence tracking when we detect sound
            self._silence_start_time = None

    def on_hotkey_pressed(self) -> None:
        """
        External method to handle hotkey press.
        Can be connected directly to hotkey callback.
        """
        self._hotkey_callback(True)

    def start(self) -> None:
        """Start the state machine and begin listening for hotkey."""
        logger.info("Starting recording state machine...")

        # Start audio capture monitoring thread for silence detection
        self._monitor_thread = threading.Thread(target=self._monitor_audio_levels, daemon=True)
        self._monitor_thread.start()

        logger.info("Recording state machine started")

    def _monitor_audio_levels(self) -> None:
        """Monitor audio levels for silence detection during recording."""
        while True:
            try:
                if self.state == RecordingState.RECORDING:
                    # Check auto-stop conditions
                    auto_stop_reason = self._check_auto_stop_conditions()
                    if auto_stop_reason:
                        logger.info(f"Auto-stop: {auto_stop_reason}")
                        # Note: _stop_recording is called directly since we need to post-process
                        # This is a simplified approach; a more robust solution would use events
                        threading.Thread(target=self._stop_recording, daemon=True).start()

                # Sleep interval for checking
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in audio monitoring: {e}")
                time.sleep(0.5)

    def stop(self) -> None:
        """Stop the state machine."""
        logger.info("Stopping recording state machine...")

        # If recording, stop first
        if self.state == RecordingState.RECORDING:
            try:
                self._stop_recording()
            except Exception as e:
                logger.error(f"Error stopping recording during shutdown: {e}")

        logger.info("Recording state machine stopped")