"""Transcription module for DTVoice.
Uses sherpa-onnx OfflineRecognizer for Whisper-based transcription.
"""

import time
import threading
from typing import Optional

import numpy as np
import sherpa_onnx

from config import APP_DATA_DIR


class TranscriptionError(Exception):
    """Raised when transcription fails after all retries."""
    pass


class TranscriptionTimeout(Exception):
    """Raised when transcription exceeds timeout limit."""
    pass


class Transcriber:
    """
    Audio transcription using sherpa-onnx whisper pipeline.

    Handles audio in 16kHz mono 16-bit PCM format.
    """

    SAMPLE_RATE = 16000

    def __init__(
        self,
        encoder_path: Optional[str] = None,
        decoder_path: Optional[str] = None,
        tokens_path: Optional[str] = None,
        num_threads: int = 4,
        timeout_seconds: float = 30.0,
        max_audio_duration: float = 120.0,
        max_retries: int = 3,
        initial_retry_delay: float = 0.5,
    ):
        """
        Initialize the transcriber.

        Args:
            encoder_path: Path to whisper encoder ONNX model.
                         If None, uses default path in APP_DATA_DIR.
            decoder_path: Path to whisper decoder ONNX model.
                         If None, uses default path in APP_DATA_DIR.
            tokens_path: Path to tokens.txt file.
                        If None, uses default path in APP_DATA_DIR.
            num_threads: Number of threads for neural network computation.
            timeout_seconds: Maximum time to wait for transcription.
                           30s timeout for 60s audio is typical target.
            max_audio_duration: Maximum audio duration in seconds to accept.
                              Audio longer than this will be truncated.
            max_retries: Maximum number of retry attempts for transient failures.
            initial_retry_delay: Initial delay between retries (doubles each retry).
        """
        self._num_threads = num_threads
        self._timeout_seconds = timeout_seconds
        self._max_audio_duration = max_audio_duration
        self._max_retries = max_retries
        self._initial_retry_delay = initial_retry_delay

        # Resolve model paths
        if encoder_path is None:
            encoder_path = self._get_default_model_path("encoder.onnx")
        if decoder_path is None:
            decoder_path = self._get_default_model_path("decoder.onnx")
        if tokens_path is None:
            tokens_path = self._get_default_model_path("tokens.txt")

        self._encoder_path = encoder_path
        self._decoder_path = decoder_path
        self._tokens_path = tokens_path

        self._recognizer: Optional[sherpa_onnx.OfflineRecognizer] = None

    def _get_default_model_path(self, filename: str) -> str:
        """Get default model path in APP_DATA_DIR/models/."""
        import os
        return os.path.join(APP_DATA_DIR, "models", filename)

    def _ensure_initialized(self) -> None:
        """Lazy initialization of the recognizer."""
        if self._recognizer is None:
            self._recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                encoder=self._encoder_path,
                decoder=self._decoder_path,
                tokens=self._tokens_path,
                num_threads=self._num_threads,
                decoding_method="greedy_search",
                debug=False,
                language="",
                task="transcribe",
            )

    def _bytes_to_float32_array(self, audio_bytes: bytes) -> np.ndarray:
        """
        Convert audio bytes to float32 array normalized to [-1, 1].

        Args:
            audio_bytes: Raw PCM16 audio data.

        Returns:
            numpy array of float32 samples in range [-1, 1].
        """
        # Convert bytes to int16 array
        samples_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

        # Convert to float32 and normalize to [-1, 1]
        samples_float32 = samples_int16.astype(np.float32) / 32768.0

        return samples_float32

    def _is_empty_audio(self, audio_bytes: bytes) -> bool:
        """Check if audio contains only silence (zeros)."""
        if len(audio_bytes) == 0:
            return True

        # Check if all samples are zero (or very close to zero)
        # Minimum valid audio: 1 sample = 2 bytes
        if len(audio_bytes) < 2:
            return True

        # Convert to int16 and check if all zeros
        samples = np.frombuffer(audio_bytes, dtype=np.int16)
        return bool(np.all(samples == 0))

    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        """
        Synchronous transcription implementation.

        Args:
            audio_bytes: Raw PCM16 audio data.

        Returns:
            Transcription text.
        """
        # Ensure recognizer is initialized
        self._ensure_initialized()
        assert self._recognizer is not None

        # Handle empty audio (after initialization)
        if self._is_empty_audio(audio_bytes):
            return ""

        # Convert bytes to float32 array
        samples = self._bytes_to_float32_array(audio_bytes)

        # Validate audio duration
        duration = len(samples) / self.SAMPLE_RATE
        if duration > self._max_audio_duration:
            # Truncate to max duration
            max_samples = int(self._max_audio_duration * self.SAMPLE_RATE)
            samples = samples[:max_samples]

        # Create stream and accept waveform
        stream = self._recognizer.create_stream()
        stream.accept_waveform(self.SAMPLE_RATE, samples)

        # Decode
        self._recognizer.decode_streams([stream])

        # Get result
        result = stream.result
        if result is None:
            return ""

        return result.text if hasattr(result, 'text') else ""

    def transcribe(self, audio_bytes: bytes) -> str:
        """
        Transcribe audio bytes to text.

        Args:
            audio_bytes: Raw audio data in 16kHz mono 16-bit PCM format.

        Returns:
            Transcription text (may be empty string for silence/empty audio).

        Raises:
            TranscriptionTimeout: If transcription exceeds timeout limit.
            TranscriptionError: If transcription fails after all retries.
        """
        # Fast path for empty audio
        if self._is_empty_audio(audio_bytes):
            return ""

        # Retry loop with exponential backoff
        last_exception: Optional[Exception] = None
        delay = self._initial_retry_delay

        for attempt in range(self._max_retries):
            try:
                # Use thread with timeout for transcription
                result_container: list[str] = []
                exception_container: list[Optional[Exception]] = []

                def transcription_task():
                    try:
                        result_container.append(self._transcribe_sync(audio_bytes))
                    except Exception as e:  # noqa: BLE001
                        exception_container.append(e)

                thread = threading.Thread(target=transcription_task, daemon=True)
                thread.start()
                thread.join(timeout=self._timeout_seconds)

                # Check for timeout
                if thread.is_alive():
                    raise TranscriptionTimeout(
                        f"Transcription timed out after {self._timeout_seconds}s"
                    )

                # Check for exception
                if exception_container:
                    exc = exception_container[0]
                    if exc is not None:
                        raise exc

                # Success
                return result_container[0] if result_container else ""

            except TranscriptionTimeout:
                # Timeout - don't retry, propagate immediately
                raise

            except Exception as e:  # noqa: BLE001
                last_exception = e
                if attempt < self._max_retries - 1:
                    # Wait before retry with exponential backoff
                    time.sleep(delay)
                    delay *= 2
                # Continue to next retry attempt

        # All retries exhausted
        final_error = last_exception if last_exception else TranscriptionError(
            f"Transcription failed after {self._max_retries} attempts (unknown error)"
        )
        raise TranscriptionError(
            f"Transcription failed after {self._max_retries} attempts: {final_error}"
        ) from final_error

    @property
    def sample_rate(self) -> int:
        """Return expected audio sample rate."""
        return self.SAMPLE_RATE

    @property
    def max_audio_duration(self) -> float:
        """Return maximum supported audio duration in seconds."""
        return self._max_audio_duration