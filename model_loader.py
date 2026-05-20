"""Whisper model loader for DTVoice.

Lazy loads whisper models from HuggingFace on first transcription.
Model is stored in %APPDATA%/dtvoice/models/.
Supports multiple model variants.
"""
import os
import logging
import shutil
from pathlib import Path
from typing import Optional

import huggingface_hub
import sherpa_onnx

import config

logger = logging.getLogger("DTVoice")


class ModelLoader:
    """Handles Whisper model downloading and loading with lazy initialization."""

    MIN_MODEL_SIZE_MB = 50  # Minimum size to consider a valid model

    def __init__(self, app_data_dir: str, model_id: Optional[str] = None):
        """Initialize ModelLoader.

        Args:
            app_data_dir: Application data directory path (e.g., %APPDATA%/DTVoice)
            model_id: Optional model ID to use. If None, uses config.DEFAULT_MODEL
        """
        self._app_data_dir = Path(app_data_dir)
        self._model_id = model_id or config.DEFAULT_MODEL
        self._model_dir = self._app_data_dir / "models"
        self._model_subdir = self._get_model_subdir()
        self._model_path: Optional[Path] = None
        self._recognizer: Optional[sherpa_onnx.OfflineRecognizer] = None
        self._model_loaded = False
        self._num_threads = 4

    @property
    def model_id(self) -> str:
        """Get current model ID."""
        return self._model_id

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

    def _get_model_subdir(self) -> Path:
        """Get the subdirectory for current model."""
        # Use model_id with / replaced by _ for folder names
        safe_name = self._model_id.replace("/", "_")
        return self._model_dir / safe_name

    def _find_model_file(self) -> Optional[Path]:
        """Find the model file in the model directory.

        Returns:
            Path to model file if found, None otherwise.
        """
        model_subdir = self._get_model_subdir()
        if not model_subdir.exists():
            return None

        # Look for .onnx files in the model directory
        for file in model_subdir.iterdir():
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

    def set_model(self, model_id: str) -> bool:
        """Set a new model ID and unload current model if different.

        Args:
            model_id: The model ID to use.

        Returns:
            True if model was changed, False if same model.
        """
        if model_id == self._model_id:
            return False

        # Unload current model
        self.unload_model()

        # Update model ID
        self._model_id = model_id
        self._model_subdir = self._get_model_subdir()
        self._model_path = None  # Reset path for new model

        logger.info(f"Model changed to: {model_id}")
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

        model_config = config.get_model_config(self._model_id)
        model_name = self._model_id

        logger.info(f"Downloading model {model_name}...")
        print(f"Downloading {model_config['display_name']} (~{model_config['size_mb']}MB)...")

        # Create model subdirectory
        model_subdir = self._get_model_subdir()
        model_subdir.mkdir(parents=True, exist_ok=True)

        # Remove existing files if force download
        if force:
            shutil.rmtree(model_subdir, ignore_errors=True)
            model_subdir.mkdir(parents=True, exist_ok=True)

        try:
            # Download the model files from HuggingFace
            model_info = huggingface_hub.model_info(model_name)
            logger.info(f"Model repo: {model_info.id}")

            # Download all files in the model repo
            downloaded_files = []
            siblings = model_info.siblings or []

            for sibling in siblings:
                file_path = sibling.rfilename
                if file_path.endswith((".onnx", ".json", ".txt", ".pt", ".pth")):
                    target_path = model_subdir / os.path.basename(file_path)
                    logger.info(f"  Downloading {file_path}...")
                    huggingface_hub.hf_hub_download(
                        repo_id=model_name,
                        filename=file_path,
                        local_dir=model_subdir,
                        local_dir_use_symlinks=False,
                    )
                    downloaded_files.append(file_path)

            # Find the main model file
            model_file = self.model_path
            if model_file is None or not self._verify_model_file(model_file):
                raise FileNotFoundError(
                    f"Model download failed: no valid model file found in {model_subdir}"
                )

            logger.info(f"Model downloaded successfully to {model_file}")
            print(f"Model downloaded: {model_file.name}")

            return model_file

        except Exception as e:
            logger.error(f"Failed to download model: {e}")
            # Clean up partial download
            if model_subdir.exists():
                shutil.rmtree(model_subdir, ignore_errors=True)
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
        model_config = config.get_model_config(self._model_id)
        print(f"Loading {model_config['display_name']}...")

        try:
            # Find the model files
            model_subdir = self._get_model_subdir()
            model_files = list(model_subdir.glob("*.onnx"))
            tokens_files = list(model_subdir.glob("*tokens*.json"))
            decoder_files = list(model_subdir.glob("*decoder*.onnx"))
            encoder_files = list(model_subdir.glob("*encoder*.onnx"))
            joiner_files = list(model_subdir.glob("*joiner*.onnx"))

            if not model_files:
                raise FileNotFoundError("No .onnx model file found")

            if not tokens_files:
                tokens_files = list(model_subdir.glob("*.json"))
                tokens_files = [f for f in tokens_files if "token" in f.name.lower()]

            if not tokens_files:
                raise FileNotFoundError("No tokens.json found")

            model_path = str(model_files[0])
            tokens_path = str(tokens_files[0])

            logger.info(f"  Model: {model_path}")
            logger.info(f"  Tokens: {tokens_path}")

            # Determine which loading method to use based on available files
            # Check for faster-whisper style files first
            if encoder_files and decoder_files:
                # Faster-whisper has encoder.onnx, decoder.onnx, joiner.onnx
                if joiner_files:
                    logger.info("  Loading with encoder+decoder+joiner (faster-whisper full)")
                    self._recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                        encoder=str(encoder_files[0]),
                        decoder=str(decoder_files[0]),
                        joiner=str(joiner_files[0]),
                        tokens=tokens_path,
                        num_threads=self._num_threads,
                        provider="cpu",
                    )
                else:
                    # Try using from_whisper which handles encoder+decoder
                    try:
                        logger.info("  Loading with encoder+decoder")
                        self._recognizer = sherpa_onnx.OfflineRecognizer.from_whisper(
                            encoder=str(encoder_files[0]),
                            decoder=str(decoder_files[0]),
                            tokens=tokens_path,
                        )  # type: ignore[call-arg]
                    except Exception:
                        # Fall back: for some models encoder IS the full model
                        logger.info("  Loading single model (encoder=decoder)")
                        self._recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                            encoder=str(model_path),
                            decoder=str(model_path),
                            tokens=tokens_path,
                            num_threads=self._num_threads,
                            provider="cpu",
                        )
            else:
                # Single model file (standard whisper)
                logger.info("  Loading single model file")
                self._recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                    encoder=str(model_path),
                    decoder=str(model_path),
                    tokens=tokens_path,
                    num_threads=self._num_threads,
                    provider="cpu",
                )

            self._model_loaded = True
            logger.info("Model loaded successfully")
            print(f"{model_config['display_name']} ready")

            return self._recognizer

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
        if not self._model_loaded or self._recognizer is None:
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

    def get_downloaded_models(self) -> list[str]:
        """Get list of model IDs that are already downloaded.

        Returns:
            List of downloaded model IDs.
        """
        if not self._model_dir.exists():
            return []

        downloaded = []
        for subdir in self._model_dir.iterdir():
            if subdir.is_dir():
                onnx_files = list(subdir.glob("*.onnx"))
                if onnx_files:
                    # Convert folder name back to model ID
                    model_id = subdir.name.replace("_", "/")
                    downloaded.append(model_id)

        return downloaded


# Singleton instance for app-wide use
_loader_instance: Optional[ModelLoader] = None


def get_model_loader(app_data_dir: str, model_id: Optional[str] = None) -> ModelLoader:
    """Get or create the global ModelLoader instance.

    Args:
        app_data_dir: Application data directory path.
        model_id: Optional model ID to use.

    Returns:
        ModelLoader singleton instance.
    """
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = ModelLoader(app_data_dir, model_id)
    return _loader_instance


def reset_model_loader() -> None:
    """Reset the global ModelLoader instance."""
    global _loader_instance
    if _loader_instance is not None:
        _loader_instance.unload_model()
        _loader_instance = None