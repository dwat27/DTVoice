"""DTVoice configuration settings."""
import os

# Application paths
APP_NAME = "DTVoice"
APP_DATA_DIR = os.path.join(os.environ["APPDATA"], APP_NAME)
CONFIG_DIR = APP_DATA_DIR
LOG_DIR = os.path.join(APP_DATA_DIR, "logs")
LOG_FILE = os.path.join(LOG_DIR, "dtvoice.log")

# Logging settings
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5MB
LOG_BACKUP_COUNT = 3

# Model settings
MODEL_DIR = os.path.join(APP_DATA_DIR, "models")


# Supported Whisper models
# Format: (repo_id, display_name, size_mb, description, language)
WHISPER_MODELS = {
    "remynd/whisper-small-pt": {
        "display_name": "Whisper Small PT",
        "size_mb": 466,
        "description": "Optimized for Brazilian Portuguese",
        "language": "Portuguese",
        "wer": "~10%",
    },
    "Systran/faster-whisper-small-pt": {
        "display_name": "Faster Whisper Small PT",
        "size_mb": 466,
        "description": "Optimized for Brazilian Portuguese (Faster variant)",
        "language": "Portuguese",
        "wer": "~8%",
    },
    "Systran/faster-whisper-base": {
        "display_name": "Faster Whisper Base",
        "size_mb": 140,
        "description": "Multi-language, smaller size",
        "language": "Multi",
        "wer": "~12%",
    },
    "Systran/faster-whisper-medium": {
        "display_name": "Faster Whisper Medium",
        "size_mb": 1500,
        "description": "Multi-language, higher accuracy",
        "language": "Multi",
        "wer": "~6%",
    },
    "Systran/faster-whisper-large-v3": {
        "display_name": "Faster Whisper Large v3",
        "size_mb": 3100,
        "description": "Multi-language, highest accuracy",
        "language": "Multi",
        "wer": "~4%",
    },
    "openai/whisper-base": {
        "display_name": "Whisper Base",
        "size_mb": 140,
        "description": "OpenAI base model, multi-language",
        "language": "Multi",
        "wer": "~15%",
    },
    "openai/whisper-small": {
        "display_name": "Whisper Small",
        "size_mb": 466,
        "description": "OpenAI small model, multi-language",
        "language": "Multi",
        "wer": "~11%",
    },
}

# Default model
DEFAULT_MODEL = "remynd/whisper-small-pt"


def get_model_config(model_id: str = None) -> dict:
    """Get configuration for a specific model or default."""
    if model_id is None:
        model_id = DEFAULT_MODEL
    return WHISPER_MODELS.get(model_id, WHISPER_MODELS[DEFAULT_MODEL])


def get_all_models() -> dict:
    """Get all available models."""
    return WHISPER_MODELS.copy()