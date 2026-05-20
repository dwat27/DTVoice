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