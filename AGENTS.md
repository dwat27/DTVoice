# PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-19
**Commit:** 572b3c7
**Branch:** main

## OVERVIEW
DTVoice is a Windows voice-to-text app using Whisper (sherpa-onnx). Flat structure, 15 core modules, system tray UI, global hotkey (Left Ctrl+Left Win).

## STRUCTURE
```
DTVoice/
├── main.py                    # Entry point + orchestration
├── audio_capture.py           # 16kHz mono PCM recording
├── transcriber.py             # Whisper via sherpa-onnx
├── model_loader.py            # HuggingFace lazy loading
├── recording_state_machine.py # IDLE→RECORDING→TRANSCRIBING→OUTPUT
├── system_tray.py             # pystray icon + menu
├── output_dispatcher.py       # injection→clipboard→popup chain
├── settings_ui.py             # Tkinter tabs (General/Hotkey/Theme/Model)
├── history.py                 # JSON-persisted transcription history
├── hotkey.py                  # pynput global listener
├── text_injector.py           # Win32 WM_SETTEXT
├── clipboard_output.py        # pyperclip wrapper
├── popup_ui.py                # plyer notifications
├── i18n.py                    # pt-BR/en-US with GetUserDefaultUILanguage
├── config.py                  # WHISPER_MODELS registry
├── locales/                   # i18n JSON files
│   ├── pt_BR.json
│   └── en_US.json
└── tests/                     # pytest suite
    ├── conftest.py            # fixtures: temp_workspace, clean_env
    ├── test_config.py
    ├── test_history.py
    └── test_model_loader.py
```

## WHERE TO LOOK
| Task | Location | Notes |
|------|----------|-------|
| Add output mode | `output_dispatcher.py` | Chain: injection→clipboard→popup |
| Change hotkey | `hotkey.py` | pynput listener, debounce |
| Model selection UI | `settings_ui.py` | Tkinter tabs |
| State transitions | `recording_state_machine.py` | VALID_TRANSITIONS dict |
| i18n strings | `i18n.py` | Embedded JSON, not locales/ |
| New Whisper model | `config.py` | Add to WHISPER_MODELS dict |

## CONVENTIONS
- **Singleton accessors**: `get_i18n()`, `get_history()`, `get_global_hotkey()`
- **Module-level loggers**: `logger = logging.getLogger(__name__)`
- **Type hints**: Consistent on params/returns, rare `# type: ignore`
- **Error handling**: Broad `except Exception:` with logging (some suppressed via `# noqa: BLE001`)
- **State machine**: Enum + VALID_TRANSITIONS dict, custom `InvalidStateTransitionError`

## ANTI-PATTERNS (THIS PROJECT)
- **pyproject.toml bug**: Entry point `dtvoice.main:main` references non-existent package
- **Bare `except Exception:`**: 114 occurrences, some with `# noqa: BLE001`
- **No TODO/FIXME markers**: Inline issues not documented
- **Direct Win32 API**: `win32api`, `win32event`, `win32con` in `main.py`

## COMMANDS
```bash
# Install
pip install -r requirements.txt

# Run
python main.py --minimize

# Test
pytest tests/ -v

# Build
pyinstaller dtvoice.spec
```

## NOTES
- **Windows only**: Heavy Win32 API, pynput, sounddevice
- **Single instance**: Mutex `DTVoice_SingleInstance_Mutex`
- **Logs**: `%APPDATA%/dtvoice/logs/dtvoice.log` (5MB rotation, 3 backups)
- **Models**: `%APPDATA%/dtvoice/models/{model_id}/` (downloaded on first use)
- **Silence detection**: -40dB threshold, 3s duration (in `recording_state_machine.py`)