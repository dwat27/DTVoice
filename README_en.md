# DTVoice

**DTVoice** is a Windows speech-to-text application that uses a local Whisper model optimized for Brazilian Portuguese. Press a global hotkey and start dictating — text appears where your cursor is.

## ✨ Features

- 🎤 **Speech-to-text** — transcribes audio to text using local AI
- 🌍 **Optimized for Brazilian Portuguese** — model `remynd/whisper-small-pt` (~466MB)
- ⌨️ **Global hotkey** — Left Ctrl + Left Win to start/stop recording
- 📋 **3 output modes**:
  - **Direct injection**: text typed where your cursor is
  - **Clipboard**: text copied to paste
  - **Popup**: notification with copy option
- 🔒 **Privacy** — all processing is local, nothing goes to the cloud
- 💾 **Works offline** — after downloading the model, works without internet
- 🖥️ **System tray** — runs minimized, visual state indicator

## 📋 Requirements

- **Operating System**: Windows 10/11 (64-bit)
- **Python**: Not required (standalone executable included)
- **Microphone**: Required for recording

## 📥 Installation

### Option 1: Pre-compiled executable (Recommended)

1. Download `DTVoice.exe` from the `dist/` folder
2. Run `DTVoice.exe --startup` to add to Windows startup (optional)
3. Run `DTVoice.exe --minimize` to start minimized to tray

### Option 2: Run from source code

```powershell
# Clone the repository
git clone https://github.com/dwat27/DTVoice.git
cd dtvoice

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run
python main.py --minimize
```

## 🚀 How to Use

### Start Recording
Press **Left Ctrl + Left Win** simultaneously to start recording.

### Stop Recording
Press **Left Ctrl + Left Win** again to stop and transcribe.

### System Tray Menu
- **Start Recording** / **Stop Recording** — manual control
- **Settings** — shows current settings (read-only in v1)
- **Exit** — closes the application

### Command Line Options

```powershell
dtvoice.exe --help          # Show help
dtvoice.exe --version       # Show version
dtvoice.exe --startup        # Add to Windows startup
dtvoice.exe --no-startup     # Remove from Windows startup
dtvoice.exe --minimize       # Start minimized to tray
```

## ⚙️ Configuration

### File Locations
- **Logs**: `%APPDATA%/dtvoice/logs/`
- **Model**: `%APPDATA%/dtvoice/models/` (automatically downloaded on first transcription)

### Language Model
The app uses the `remynd/whisper-small-pt` model from Hugging Face (~466MB):
- **WER**: ~10% (word error rate)
- **Optimized**: Brazilian Portuguese
- **Performance**: CPU-friendly, works on modest machines

### Current Settings (v1)
| Setting | Value |
| ------- | ----- |
| Hotkey | Left Ctrl + Left Win |
| Output mode | Injection → Clipboard → Popup |
| Auto-stop | 60 seconds |
| Silence detection | 3 seconds |

> ⚠️ In version 1, settings are not user-customizable. This will be added in future versions.

## 🧠 Supported AI Models

DTVoice supports multiple Whisper models. The default model is optimized for Brazilian Portuguese, but you can choose other models.

### Available Models

| Model | Language | Size | WER | Description |
| ----- | -------- | ---- | --- | ------------ |
| `remynd/whisper-small-pt` | PT-BR | 466 MB | ~10% | Recommended for PT-BR |
| `Systran/faster-whisper-small-pt` | PT-BR | 466 MB | ~8% | Faster variant for PT-BR |
| `Systran/faster-whisper-base` | Multi | 140 MB | ~12% | Multi-language, smaller |
| `Systran/faster-whisper-medium` | Multi | 1500 MB | ~6% | Multi-language, higher accuracy |
| `Systran/faster-whisper-large-v3` | Multi | 3100 MB | ~4% | Multi-language, highest accuracy |
| `openai/whisper-base` | Multi | 140 MB | ~15% | OpenAI base, multi-language |
| `openai/whisper-small` | Multi | 466 MB | ~11% | OpenAI small, multi-language |

### Changing Models

In the current version, you can change the model via the tray menu:
1. Click on the DTVoice icon in the system tray
2. Go to **Settings** → **Change Model**
3. Select the desired model

> ⚠️ When changing models, the new model will be downloaded automatically the first time.

### How It Works
- Each model is downloaded to `%APPDATA%/dtvoice/models/{model_id}/`
- Downloaded models work offline
- You can have multiple models installed simultaneously

## 🔧 Technologies

| Component | Technology |
| --------- | ---------- |
| AI Model | [sherpa-onnx](https://github.com/k2-fsa/sherpa-onnx) + Whisper |
| Audio capture | sounddevice |
| Global hotkey | pynput |
| System tray | pystray + Pillow |
| Text injection | Win32 API (WM_SETTEXT) |
| Notifications | plyer |
| Clipboard | pyperclip |

## 📁 Project Structure

```
dtvoice/
├── main.py                  # Entry point + integration
├── system_tray.py           # Tray icon + menu
├── hotkey.py                # Global hotkey listener
├── audio_capture.py         # Audio recording (16kHz mono)
├── transcriber.py           # Whisper transcription pipeline
├── model_loader.py          # Lazy model loading
├── recording_state_machine.py  # Recording state machine
├── output_dispatcher.py     # Output modes dispatcher
├── text_injector.py         # Win32 text injection
├── clipboard_output.py      # Clipboard integration
├── popup_ui.py              # Popup notifications
├── config.py                # Application settings
├── requirements.txt         # Python dependencies
├── pyproject.toml          # Project configuration
├── dtvoice.spec            # PyInstaller spec
└── dist/DTVoice.exe        # Compiled executable
```

## 🐛 Known Issues

- **Microphone permission**: On first run, Windows may ask for microphone permission. Grant it via Settings > Privacy > Microphone.
- **Non-admin install**: The app doesn't require admin privileges. If you need help, run as administrator once to register the global hotkey.

## 🚧 Roadmap

- [x] Graphical settings interface
- [x] Language/model selection
- [x] Transcription history
- [x] Customizable hotkeys
- [x] Light/dark theme

## 📄 License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please open an issue first to discuss larger changes.

1. Fork the repository
2. Create a branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'feat: new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

Made with ❤️ for the Brazilian Windows user community.