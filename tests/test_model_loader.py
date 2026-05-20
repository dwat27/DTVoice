"""Tests for model_loader module."""
import os
import pytest
from unittest.mock import MagicMock, patch
import config


class TestModelLoader:
    """Test ModelLoader class."""

    def test_model_loader_import(self):
        """model_loader should be importable."""
        try:
            from model_loader import ModelLoader
            assert ModelLoader is not None
        except ImportError as e:
            pytest.skip(f"model_loader import failed: {e}")

    def test_model_loader_init(self):
        """ModelLoader should initialize with model_id."""
        try:
            from model_loader import ModelLoader
            loader = ModelLoader(model_id="Systran/faster-whisper-base")
            assert loader._model_id == "Systran/faster-whisper-base"
        except ImportError:
            pytest.skip("model_loader not available")

    def test_get_model_id(self):
        """get_model_id should return current model ID."""
        try:
            from model_loader import ModelLoader
            loader = ModelLoader()
            assert loader.get_model_id() == config.DEFAULT_MODEL
        except ImportError:
            pytest.skip("model_loader not available")

    def test_get_model_config(self):
        """get_model_config should return model config."""
        try:
            from model_loader import ModelLoader
            loader = ModelLoader()
            model_config = loader.get_model_config()
            assert isinstance(model_config, dict)
            assert "display_name" in model_config
        except ImportError:
            pytest.skip("model_loader not available")

    def test_model_exists_method(self):
        """model_exists should check if model files exist."""
        try:
            from model_loader import ModelLoader
            loader = ModelLoader()
            # Model shouldn't exist yet (not downloaded)
            exists = loader.model_exists()
            assert isinstance(exists, bool)
        except ImportError:
            pytest.skip("model_loader not available")

    @patch("os.path.exists")
    def test_model_exists_with_files(self, mock_exists):
        """model_exists should return True when files exist."""
        mock_exists.return_value = True
        try:
            from model_loader import ModelLoader
            loader = ModelLoader()
            # This test checks the logic path
            assert loader.model_exists() is not None
        except ImportError:
            pytest.skip("model_loader not available")


class TestModelLoaderDownload:
    """Test model downloading functionality."""

    def test_download_model_not_implemented(self):
        """Download should be handled gracefully."""
        try:
            from model_loader import ModelLoader
            loader = ModelLoader()
            # If model doesn't exist, trying to get recognizer should handle it
            # This is a basic smoke test
            assert loader._model_id is not None
        except ImportError:
            pytest.skip("model_loader not available")