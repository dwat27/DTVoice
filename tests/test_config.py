"""Tests for config module."""
import pytest
import config


class TestConfig:
    """Test config module."""

    def test_whisper_models_not_empty(self):
        """WHISPER_MODELS should not be empty."""
        assert len(config.WHISPER_MODELS) > 0

    def test_default_model_exists(self):
        """DEFAULT_MODEL should exist in WHISPER_MODELS."""
        assert config.DEFAULT_MODEL in config.WHISPER_MODELS
        assert config.get_model_config(config.DEFAULT_MODEL) is not None

    def test_get_model_config_returns_dict(self):
        """get_model_config should return a dict with expected keys."""
        model_config = config.get_model_config()
        assert isinstance(model_config, dict)
        assert "display_name" in model_config
        assert "size_mb" in model_config
        assert "description" in model_config
        assert "language" in model_config

    def test_get_model_config_with_specific_model(self):
        """get_model_config with specific model ID should return that model's config."""
        model_id = "Systran/faster-whisper-base"
        model_config = config.get_model_config(model_id)
        assert model_config["display_name"] == "Faster Whisper Base"

    def test_get_model_config_invalid_returns_default(self):
        """get_model_config with invalid ID should return default."""
        invalid_config = config.get_model_config("invalid/model")
        default_config = config.get_model_config()
        assert invalid_config == default_config

    def test_get_all_models_returns_dict(self):
        """get_all_models should return a dict copy."""
        all_models = config.get_all_models()
        assert isinstance(all_models, dict)
        assert len(all_models) == len(config.WHISPER_MODELS)

    def test_model_has_required_fields(self):
        """All models should have required fields."""
        required = {"display_name", "size_mb", "description", "language", "wer"}
        for model_id, model_info in config.WHISPER_MODELS.items():
            assert required.issubset(model_info.keys()), f"Model {model_id} missing fields"

    def test_paths_are_strings(self):
        """Path constants should be strings."""
        assert isinstance(config.APP_NAME, str)
        assert isinstance(config.APP_DATA_DIR, str)
        assert isinstance(config.MODEL_DIR, str)
        assert isinstance(config.LOG_DIR, str)