"""Internationalization (i18n) module for DTVoice."""
import json
import os
import locale
from typing import Optional

import config


# Supported locales
SUPPORTED_LOCALES = ["pt_BR", "en_US"]
DEFAULT_LOCALE = "pt_BR"


def get_system_locale() -> str:
    """Detect system locale for initial language selection."""
    try:
        # Try to get Windows language
        import ctypes
        windll = ctypes.windll.kernel32
        # GetUserDefaultUILanguage returns a LANGID
        lang_id = windll.GetUserDefaultUILanguage()
        # Extract primary language (lower 10 bits)
        primary_lang = lang_id & 0x3FF

        # Portuguese (Brazil) = 0x0416 (1046)
        if primary_lang == 0x016:
            return "pt_BR"

        # English = 0x009
        if primary_lang == 0x009:
            return "en_US"

        # Default to Portuguese for Brazilian users
        return DEFAULT_LOCALE
    except Exception:
        # Fallback to locale module
        try:
            system_locale = locale.getdefaultlocale()[0]
            if system_locale and system_locale.startswith("pt"):
                return "pt_BR"
            return "en_US"
        except Exception:
            return DEFAULT_LOCALE


def load_locale(locale_name: str) -> dict:
    """Load a locale file from the locales directory."""
    locale_path = os.path.join(
        os.path.dirname(__file__),
        "locales",
        f"{locale_name}.json"
    )

    try:
        with open(locale_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback to embedded defaults
        return get_embedded_locale(locale_name)
    except json.JSONDecodeError:
        return get_embedded_locale(locale_name)


def get_embedded_locale(locale_name: str) -> dict:
    """Get embedded locale data as fallback."""
    if locale_name == "en_US":
        return {
            "app_name": "DTVoice",
            "start_recording": "Start Recording",
            "stop_recording": "Stop Recording",
            "settings": "Settings",
            "hotkey": "Hotkey",
            "output_mode": "Output mode",
            "auto_stop": "Auto-stop",
            "notifications": "Notifications",
            "language": "Language",
            "exit": "Exit",
            "recording": "Recording...",
            "transcribing": "Transcribing...",
            "idle": "Ready",
            "text_copied": "Text copied to clipboard",
            "text_injected": "Text injected",
            "error_no_mic": "No microphone detected",
            "error_mic_in_use": "Microphone in use by another app",
            "error_transcription": "Transcription failed",
            "error_injection": "Text injection failed, copied to clipboard",
            "model_downloading": "Downloading model...",
            "help_title": "DTVoice Help",
            "help_usage": "Usage: dtvoice [options]",
            "help_option_help": "Show this help message",
            "help_option_version": "Show version information",
            "help_option_startup": "Add DTVoice to Windows startup",
            "help_option_no_startup": "Remove DTVoice from Windows startup",
            "help_option_minimize": "Start minimized to system tray",
            "version": "Version",
            "already_running": "DTVoice is already running",
            "initializing": "DTVoice initializing...",
            "started_minimized": "Started minimized to system tray",
            "hotkey_active": "Hotkey active: Left Ctrl + Left Win",
            "warning_hotkey_failed": "Warning: Failed to start hotkey listener",
            "seconds": "seconds",
            "on": "On",
            "off": "Off",
            "injection_first": "Injection first",
            "portuguese": "Portuguese",
            "english": "English"
        }
    elif locale_name == "pt_BR":
        return {
            "app_name": "DTVoice",
            "start_recording": "Iniciar Gravação",
            "stop_recording": "Parar Gravação",
            "settings": "Configurações",
            "hotkey": "Atalho",
            "output_mode": "Modo de saída",
            "auto_stop": "Auto-parar",
            "notifications": "Notificações",
            "language": "Idioma",
            "exit": "Sair",
            "recording": "Gravando...",
            "transcribing": "Transcrevendo...",
            "idle": "Pronto",
            "text_copied": "Texto copiado para área de transferência",
            "text_injected": "Texto injetado",
            "error_no_mic": "Nenhum microfone detectado",
            "error_mic_in_use": "Microfone está sendo usado por outro aplicativo",
            "error_transcription": "Transcrição falhou",
            "error_injection": "Injeção de texto falhou, copiado para área de transferência",
            "model_downloading": "Baixando modelo...",
            "help_title": "Ajuda do DTVoice",
            "help_usage": "Uso: dtvoice [opções]",
            "help_option_help": "Mostrar esta mensagem de ajuda",
            "help_option_version": "Mostrar informações da versão",
            "help_option_startup": "Adicionar DTVoice ao iniciar do Windows",
            "help_option_no_startup": "Remover DTVoice do iniciar do Windows",
            "help_option_minimize": "Iniciar minimizado na bandeja do sistema",
            "version": "Versão",
            "already_running": "DTVoice já está em execução",
            "initializing": "DTVoice inicializando...",
            "started_minimized": "Iniciado minimizado na bandeja do sistema",
            "hotkey_active": "Atalho ativo: Ctrl Esquerdo + Win Esquerdo",
            "warning_hotkey_failed": "Aviso: Falha ao iniciar listener do atalho",
            "seconds": "segundos",
            "on": "Ativado",
            "off": "Desativado",
            "injection_first": "Injeção primeiro",
            "portuguese": "Português",
            "english": "Inglês"
        }
    else:
        return get_embedded_locale(DEFAULT_LOCALE)


class I18n:
    """Internationalization handler for DTVoice."""

    def __init__(self, locale_name: Optional[str] = None):
        """Initialize i18n with a locale name."""
        self._locale_name = locale_name or get_system_locale()
        self._translations: dict = {}
        self._load_translations()

    def _load_translations(self):
        """Load translations for current locale."""
        self._translations = load_locale(self._locale_name)

    @property
    def locale(self) -> str:
        """Get current locale name."""
        return self._locale_name

    def set_locale(self, locale_name: str) -> bool:
        """Set a new locale if supported."""
        if locale_name in SUPPORTED_LOCALES:
            self._locale_name = locale_name
            self._load_translations()
            self._save_preference()
            return True
        return False

    def _save_preference(self):
        """Save language preference to config."""
        try:
            config_dir = config.CONFIG_DIR
            os.makedirs(config_dir, exist_ok=True)
            pref_file = os.path.join(config_dir, ".locale")
            with open(pref_file, "w", encoding="utf-8") as f:
                f.write(self._locale_name)
        except Exception:
            pass

    @staticmethod
    def load_saved_locale() -> Optional[str]:
        """Load saved locale preference from config."""
        try:
            pref_file = os.path.join(config.CONFIG_DIR, ".locale")
            if os.path.exists(pref_file):
                with open(pref_file, "r", encoding="utf-8") as f:
                    saved = f.read().strip()
                    if saved in SUPPORTED_LOCALES:
                        return saved
        except Exception:
            pass
        return None

    def t(self, key: str, default: Optional[str] = None) -> str:
        """Translate a key to the current locale."""
        return self._translations.get(key, default or key)

    def get_translations(self) -> dict:
        """Get all translations for current locale."""
        return self._translations.copy()

    def __getitem__(self, key: str) -> str:
        """Allow dict-like access: i18n["key"]"""
        return self.t(key)


# Global i18n instance (initialized in main.py)
_i18n: Optional[I18n] = None


def init_i18n(locale_name: Optional[str] = None) -> I18n:
    """Initialize the global i18n instance."""
    global _i18n
    if _i18n is None:
        # Try saved locale first, then system locale, then parameter
        saved = I18n.load_saved_locale()
        target = saved or locale_name or get_system_locale()
        _i18n = I18n(target)
    return _i18n


def get_i18n() -> I18n:
    """Get the global i18n instance, initializing if needed."""
    global _i18n
    if _i18n is None:
        _i18n = init_i18n()
    return _i18n


def t(key: str, default: Optional[str] = None) -> str:
    """Convenience function for translation."""
    return get_i18n().t(key, default)