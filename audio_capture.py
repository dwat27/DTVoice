"""
Audio capture module for DTVoice.
Provides audio capture with 16kHz, mono, 16-bit configuration for Whisper compatibility.
"""

import sounddevice as sd
import numpy as np
from collections import deque
from typing import Optional


class MicrophoneUnavailableError(Exception):
    """Raised when no microphone is detected."""
    pass


class MicrophoneInUseError(Exception):
    """Raised when microphone is in use by another application."""
    pass


class CircularBuffer:
    """Thread-safe circular buffer for audio chunks."""

    def __init__(self, max_size: int = 100):
        self._buffer = deque(maxlen=max_size)

    def append(self, chunk: np.ndarray) -> None:
        self._buffer.append(chunk)

    def get_all(self) -> np.ndarray:
        """Get all audio data as contiguous array."""
        if not self._buffer:
            return np.array([], dtype=np.int16)
        return np.concatenate(list(self._buffer))

    def clear(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)


class AudioCapture:
    """
    Audio capture class for recording from default microphone.

    Configuration: 16kHz sample rate, mono channel, 16-bit depth
    (required for Whisper compatibility)
    """

    SAMPLE_RATE = 16000
    CHANNELS = 1
    DTYPE = np.int16
    CHUNK_SIZE = 1024  # samples per callback

    def __init__(self):
        """Initialize audio capture and detect microphone availability."""
        self._stream: Optional[sd.InputStream] = None
        self._buffer = CircularBuffer()
        self._recording = False

        # Detect microphone availability
        if not self._check_microphone_available():
            raise MicrophoneUnavailableError("No microphone detected or microphone unavailable")

    def _check_microphone_available(self) -> bool:
        """Check if a microphone is available and not in use."""
        try:
            # Try to query devices
            devices = sd.query_devices()
            default_input = sd.query_devices(kind='input')

            # Attempt to open a test stream to verify microphone is usable
            test_stream = sd.InputStream(
                device=default_input.get('index'),
                channels=self.CHANNELS,
                samplerate=self.SAMPLE_RATE,
                dtype=self.DTYPE,
                blocksize=self.CHUNK_SIZE
            )
            test_stream.close()
            return True
        except sd.PortAudioError as e:
            if "Device unavailable" in str(e) or "in use" in str(e).lower():
                raise MicrophoneInUseError(f"Microphone in use by another application: {e}")
            return False
        except Exception:
            return False

    def start(self) -> None:
        """Begin recording audio to circular buffer."""
        if self._recording:
            return

        try:
            self._buffer.clear()
            self._stream = sd.InputStream(
                device=None,  # Use default device
                channels=self.CHANNELS,
                samplerate=self.SAMPLE_RATE,
                dtype=self.DTYPE,
                blocksize=self.CHUNK_SIZE,
                callback=self._audio_callback
            )
            self._stream.start()
            self._recording = True
        except sd.PortAudioError as e:
            if "in use" in str(e).lower():
                raise MicrophoneInUseError(f"Microphone in use by another application: {e}")
            raise MicrophoneUnavailableError(f"Failed to start recording: {e}")

    def _audio_callback(self, indata: np.ndarray, frames: int, time, status: sd.CallbackFlags) -> None:
        """Callback for audio stream - appends chunks to buffer."""
        if status:
            # Log or handle callback status if needed
            pass
        # indata is already shaped correctly (frames, channels)
        self._buffer.append(indata.copy())

    def stop(self) -> bytes:
        """
        Stop recording and return recorded audio as bytes.

        Returns:
            bytes: Recorded audio data as PCM16 bytes
        """
        if not self._recording:
            return b''

        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        # Get all audio from buffer and convert to bytes
        audio_data = self._buffer.get_all()
        return audio_data.tobytes()

    def is_recording(self) -> bool:
        """Return True if currently recording."""
        return self._recording

    @property
    def sample_rate(self) -> int:
        """Return configured sample rate."""
        return self.SAMPLE_RATE

    @property
    def channels(self) -> int:
        """Return configured number of channels."""
        return self.CHANNELS

    @property
    def dtype(self) -> type:
        """Return configured audio data type."""
        return self.DTYPE