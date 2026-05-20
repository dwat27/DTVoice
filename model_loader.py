"""Whisper model loader for DTVoice.

Lazy loads the whisper-small-pt model from HuggingFace on first transcription.
Model is stored in %APPDATA%/dtvoice/models/.
"""
import os
import logging
import shutil
from pathlib import Path
from typing import Optional

import huggingface_hub
import sherpa_onnx

logger = logging.getLogger("DTVoice")


class ModelLoader:
    """Handles Whisper model downloading and loading with lazy initialization."""

    MODEL_NAME = "remynd/whisper-small-pt"
    MODEL_SUBDIR = "models"
    MIN_MODEL_SIZE_MB = 400

    def __init__(self, app_data_dir: str):
        """Initialize ModelLoader.

        Args:
            app_data_dir: Application data directory path (e.g., %APPDATA%/DTVoice)
        """
        self._app_data_dir = Path(app_data_dir)
        self._model_dir = self._app_data_dir / self.MODEL_SUBDIR
        self._model_path: Optional[Path] = None
        self._recognizer: Optional[sherpa_onnx.OfflineRecognizer] = None
        self._model_loaded = False

    @property
    def model_dir(self) -> Path:
        """Get the model storage directory."""
        return self._model_dir

    @property
    def model_path(self) -> Optional[Path]:
        """Get the downloaded model path, or None if not downloaded."""
        if self._model_path is None:
            self._model_path = self._find_model_file()
        return self._model_path

    @property
    def is_model_downloaded(self) -> bool:
        """Check if model is already downloaded and verified."""
        path = self.model_path
        if path is None:
            return False
        return self._verify_model_file(path)

    @property
    def is_model_loaded(self) -> bool:
        """Check if model is loaded into memory."""
        return self._model_loaded

    def _find_model_file(self) -> Optional[Path]:
        """Find the model file in the model directory.

        Returns:
            Path to model file if found, None otherwise.
        """
        if not self._model_dir.exists():
            return None

        # Look for .onnx files in the model directory
        for file in self._model_dir.iterdir():
            if file.suffix == ".onnx":
                return file

        return None

    def _verify_model_file(self, path: Path) -> bool:
        """Verify model file exists and meets size requirements.

        Args:
            path: Path to the model file.

        Returns:
            True if file exists and size > MIN_MODEL_SIZE_MB MB.
        """
        if not path.exists():
            logger.warning(f"Model file not found: {path}")
            return False

        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb < self.MIN_MODEL_SIZE_MB:
            logger.warning(
                f"Model file too small: {size_mb:.1f}MB < {self.MIN_MODEL_SIZE_MB}MB"
            )
            return False

        logger.info(f"Model verified: {path.name} ({size_mb:.1f}MB)")
        return True

    def download_model(self, force: bool = False) -> Path:
        """Download the Whisper model from HuggingFace.

        Args:
            force: If True, re-download even if model exists.

        Returns:
            Path to the downloaded model file.

        Raises:
            Exception: If download fails.
        """
        if not force and self.is_model_downloaded and self.model_path:
            logger.info("Model already downloaded and verified")
            return self.model_path

        logger.info(f"Downloading model {self.MODEL_NAME}...")
        print(f"Downloading Whisper model (~466MB)...")

        # Create model directory
        self._model_dir.mkdir(parents=True, exist_ok=True)

        # Remove existing files if force download
        if force:
            shutil.rmtree(self._model_dir, ignore_errors=True)
            self._model_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Download the model files from HuggingFace
            # The remynd/whisper-small-pt model contains multiple files
            model_info = huggingface_hub.model_info(self.MODEL_NAME)
            logger.info(f"Model repo: {model_info.id}")

            # Download all files in the model repo
            downloaded_files = []
            for sibling in (model_info.siblings or []):
                file_path = sibling.rfilename
                if file_path.endswith((".onnx", ".json", ".txt", ".pt", ".pth")):
                    target_path = self._model_dir / os.path.basename(file_path)
                    logger.info(f"  Downloading {file_path}...")
                    huggingface_hub.hf_hub_download(
                        repo_id=self.MODEL_NAME,
                        filename=file_path,
                        local_dir=self._model_dir,
                        local_dir_use_symlinks=False,
                    )
                    downloaded_files.append(file_path)

            # Find the main model file
            model_file = self.model_path
            if model_file is None or not self._verify_model_file(model_file):
                raise FileNotFoundError(
                    f"Model download failed: no valid model file found in {self._model_dir}"
                )

            logger.info(f"Model downloaded successfully to {model_file}")
            print(f"Model downloaded: {model_file.name}")

            return model_file

        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            # Clean up partial download
            if self._model_dir.exists():
                shutil.rmtree(self._model_dir, ignore_errors=True)
            raise

    def load_model(self) -> sherpa_onnx.OfflineRecognizer:
        """Load the model into memory using sherpa-onnx.

        Returns:
            Configured OfflineRecognizer instance.

        Raises:
            RuntimeError: If model is not downloaded or loading fails.
        """
        if self._model_loaded and self._recognizer is not None:
            return self._recognizer

        # Ensure model is downloaded first
        model_file = self.model_path
        if model_file is None or not self._verify_model_file(model_file):
            logger.info("Model not found, downloading...")
            model_file = self.download_model()

        logger.info("Loading Whisper model into memory...")
        print("Loading Whisper model (this may take a few seconds)...")

        try:
            # Find the model files - sherpa-onnx needs both .onnx model and tokens.json
            model_files = list(self._model_dir.glob("*.onnx"))
            tokens_files = list(self._model_dir.glob("*tokens*.json"))

            if not model_files:
                raise FileNotFoundError("No .onnx model file found")
            if not tokens_files:
                raise FileNotFoundError("No tokens.json found")

            model_path = str(model_files[0])
            tokens_path = str(tokens_files[0])

            logger.info(f"  Model: {model_path}")
            logger.info(f"  Tokens: {tokens_path}")

            # Configure and create recognizer
            # Using OfflineRecognizerConfig for offline transcription
            recognizer_config = sherpa_onnx.OfflineRecognizerConfig()

            # For whisper models from remynd, we need to use the right config
            # The model is a whisper encoder + decoder in ONNX format
            # with decoder_nemo_template is not needed for this model type

            # Create the recognizer with the model
            recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                model=str(model_path),
                tokens=str(tokens_path),
                num_threads=4,
                provider="cpu",  # Use CPU for compatibility
            )

            self._recognizer = recognizer
            self._model_loaded = True

            logger.info("Model loaded successfully")
            print("Whisper model ready")

            return recognizer

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self._model_loaded = False
            self._recognizer = None
            raise RuntimeError(f"Model loading failed: {e}") from e

    def get_recognizer(self) -> sherpa_onnx.OfflineRecognizer:
        """Get the recognizer instance, downloading and loading if needed.

        This is the main entry point for lazy loading.

        Returns:
            Loaded OfflineRecognizer instance.
        """
        if not self._model_loaded:
            return self.load_model()
        return self._recognizer

    def unload_model(self) -> None:
        """Unload the model from memory to free resources."""
        if self._recognizer is not None:
            logger.info("Unloading model from memory")
            self._recognizer = None
            self._model_loaded = False

    def get_model_size_mb(self) -> float:
        """Get the size of the downloaded model in MB.

        Returns:
            Model size in megabytes, or 0 if not downloaded.
        """
        path = self.model_path
        if path is None or not path.exists():
            return 0.0
        return path.stat().st_size / (1024 * 1024)


# Singleton instance for app-wide use
_loader_instance: Optional[ModelLoader] = None


def get_model_loader(app_data_dir: str) -> ModelLoader:
    """Get or create the global ModelLoader instance.

    Args:
        app_data_dir: Application data directory path.

    Returns:
        ModelLoader singleton instance.
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ModelLoader(app_data_dir)
    return _loader_instance
