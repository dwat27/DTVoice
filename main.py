"""DTVoice main entry point."""
import sys
import os
import logging
import atexit
from logging.handlers import RotatingFileHandler
import win32api
import win32event
import win32con
import winreg
import platform

import config
from i18n import init_i18n, get_i18n

# Import components for integration
from system_tray import SystemTray
from recording_state_machine import RecordingStateMachine
from hotkey import start_global_hotkey, get_global_hotkey
from audio_capture import AudioCapture
from transcriber import Transcriber
from output_dispatcher import OutputDispatcher

__version__ = "0.1.0"
MUTEX_NAME = "DTVoice_SingleInstance_Mutex"
_global_mutex = None  # Module-level variable to keep mutex alive
_startup_flag = False  # Track if we registered startup

# Global references for cleanup (set during initialization)
_hotkey_instance = None  # GlobalHotkey instance for cleanup
_audio_capture_instance = None  # AudioCapture instance for cleanup


def setup_logging():
    """Configure logging with rotation to APPDATA/logs directory."""
    os.makedirs(config.LOG_DIR, exist_ok=True)

    logger = logging.getLogger(config.APP_NAME)
    logger.setLevel(logging.INFO)

    handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=config.LOG_MAX_BYTES,
        backupCount=config.LOG_BACKUP_COUNT
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def check_single_instance():
    """Check if another instance is already running using named mutex."""
    global _global_mutex
    ERROR_ALREADY_EXISTS = 183

    # Create mutex - if it already exists, Windows returns existing handle
    # and sets GetLastError to ERROR_ALREADY_EXISTS
    _global_mutex = win32event.CreateMutex(None, False, MUTEX_NAME)  # type: ignore[arg-type]
    last_error = win32api.GetLastError()

    if last_error == ERROR_ALREADY_EXISTS:
        # Mutex was created by another process first
        win32api.CloseHandle(_global_mutex)
        _global_mutex = None
        return False

    # We created the mutex - we're the first instance
    return True


def get_windows_version():
    """Detect Windows version for compatibility checks."""
    try:
        ver = platform.version()
        release = platform.release()
        # Windows 10/11 have major version 10
        major = int(platform.version().split('.')[0]) if '.' in ver else 10
        return {
            'version': ver,
            'release': release,
            'major': major,
            'is_modern': major >= 10
        }
    except Exception:
        return {'version': 'unknown', 'release': 'unknown', 'major': 0, 'is_modern': False}


def is_startup_enabled():
    """Check if DTVoice is set to run at Windows startup."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ
        )
        try:
            winreg.QueryValueEx(key, "DTVoice")
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            winreg.CloseKey(key)
            return False
    except Exception:
        return False


def set_startup_enabled(enable):
    """Add or remove DTVoice from Windows startup via registry."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE
        )
        if enable:
            exe_path = sys.executable
            script_path = os.path.abspath(__file__)
            # Use pythonw.exe to avoid console window, or python.exe if needed
            command = f'"{exe_path}" "{script_path}"'
            winreg.SetValueEx(key, "DTVoice", 0, winreg.REG_SZ, command)
        else:
            try:
                winreg.DeleteValue(key, "DTVoice")
            except FileNotFoundError:
                pass  # Already removed
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logging.error(f"Failed to update startup registry: {e}")
        return False


def request_microphone_permission():
    """Request microphone permission on first run."""
    try:
        import sounddevice as sd
        # Try to get device info to verify microphone access
        devices = sd.query_devices()
        # If we can query devices, we have microphone access
        logging.info("Microphone permission verified")
        return True
    except Exception as e:
        logging.warning(f"Microphone permission check failed: {e}")
        # On Windows 10/11, sounddevice will fail without permission
        # The user will need to grant permission via Windows settings
        return False


def check_first_run():
    """Check if this is first run and handle initial setup."""
    first_run_file = os.path.join(config.CONFIG_DIR, ".first_run_complete")
    if not os.path.exists(first_run_file):
        # First run - request microphone permission
        logging.info("First run detected - requesting microphone permission")
        request_microphone_permission()
        # Mark first run as complete
        os.makedirs(config.CONFIG_DIR, exist_ok=True)
        with open(first_run_file, 'w') as f:
            f.write("1")
        return True
    return False


def cleanup():
    """Clean up resources on exit."""
    global _global_mutex, _startup_flag, _hotkey_instance, _audio_capture_instance

    logging.info("DTVoice shutting down")

    # Clean up hotkey if registered
    try:
        if _hotkey_instance is not None:
            _hotkey_instance.stop()
            logging.info("Hotkey cleanup completed")
    except Exception as e:
        logging.warning(f"Hotkey cleanup error: {e}")

    # Close audio resources if open
    try:
        if _audio_capture_instance is not None:
            # Check if audio is recording and stop first
            if _audio_capture_instance.is_recording():
                _audio_capture_instance.stop()
            logging.info("Audio cleanup completed")
    except Exception as e:
        logging.warning(f"Audio cleanup error: {e}")

    # Close mutex handle
    if _global_mutex is not None:
        try:
            win32api.CloseHandle(_global_mutex)
            _global_mutex = None
            logging.info("Mutex cleanup completed")
        except Exception as e:
            logging.warning(f"Mutex cleanup error: {e}")

    logging.info("DTVoice cleanup complete")


def register_cleanup():
    """Register cleanup function for exit."""
    atexit.register(cleanup)


def parse_args():
    """Parse command line arguments."""
    i18n = get_i18n()

    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"DTVoice - {i18n['app_name']}")
        print(i18n["help_usage"])
        print("Options:")
        print(f"  --help, -h     {i18n['help_option_help']}")
        print(f"  --version      {i18n['help_option_version']}")
        print(f"  --startup      {i18n['help_option_startup']}")
        print(f"  --no-startup   {i18n['help_option_no_startup']}")
        print(f"  --minimize     {i18n['help_option_minimize']}")
        sys.exit(0)

    if "--version" in sys.argv or "-v" in sys.argv:
        print(f"{i18n['app_name']} {i18n['version']} {__version__}")
        sys.exit(0)

    # Handle startup registration
    global _startup_flag
    if "--startup" in sys.argv:
        if set_startup_enabled(True):
            print("DTVoice added to Windows startup")
        else:
            print("Failed to add to Windows startup")
        sys.exit(0)

    if "--no-startup" in sys.argv:
        if set_startup_enabled(False):
            print("DTVoice removed from Windows startup")
        else:
            print("Failed to remove from Windows startup")
        sys.exit(0)

    # Check if minimize flag was passed
    start_minimized = "--minimize" in sys.argv or "--minimized" in sys.argv
    return start_minimized


def main():
    """Main application entry point."""
    logger = setup_logging()

    try:
        # Register cleanup handler immediately
        register_cleanup()

        # Detect Windows version
        win_info = get_windows_version()
        logger.info(f"Windows version: {win_info['version']} ({win_info['release']})")
        if not win_info['is_modern']:
            logger.warning("Windows version may not be fully supported")

        # Initialize i18n (loads saved locale or auto-detects) BEFORE parse_args
        i18n = init_i18n()
        logger.info(f"Language: {i18n.locale}")

        start_minimized = parse_args()

        if not check_single_instance():
            print(i18n["already_running"])
            logger.info("Second instance blocked by mutex")
            sys.exit(1)

        # Check first run and request permissions
        check_first_run()

        # Initialize i18n (loads saved locale or auto-detects)
        i18n = init_i18n()
        logger.info(f"Language: {i18n.locale}")

        logger.info("DTVoice starting")
        print(f"DTVoice v{__version__} initialized")

        if start_minimized:
            logger.info("Starting minimized")
            print(i18n["started_minimized"])

        # =====================================================
        # INTEGRATION: Wire all components together
        # =====================================================

        # Create output dispatcher
        output_dispatcher = OutputDispatcher()

        # Create audio capture
        audio_capture = AudioCapture()
        logger.info("Audio capture initialized")

        # Create transcriber (lazy loads model on first transcription)
        transcriber = Transcriber()
        logger.info("Transcriber initialized")

        # Create system tray with callbacks
        def on_start_recording():
            """Callback when tray menu requests start recording."""
            logger.info("Start recording requested from tray")

        def on_stop_recording():
            """Callback when tray menu requests stop recording."""
            logger.info("Stop recording requested from tray")

        def on_exit():
            """Callback when tray menu requests exit."""
            logger.info("Exit requested from system tray")
            # Cleanup is handled by atexit registered cleanup()
            sys.exit(0)

        def on_model_change(model_id: str):
            """Callback when user selects a different model."""
            logger.info(f"Model change requested: {model_id}")
            # Update config default
            import config
            config.DEFAULT_MODEL = model_id
            # Reset transcriber to use new model
            transcriber.reload_model(model_id)

        system_tray = SystemTray(
            on_start_recording=on_start_recording,
            on_stop_recording=on_stop_recording,
            on_exit=on_exit,
            on_model_change=on_model_change
        )
        logger.info("System tray initialized")

        # Create recording state machine
        state_machine = RecordingStateMachine(
            audio_capture=audio_capture,
            transcriber=transcriber,
            system_tray=system_tray
        )

        # Wire state machine transcription callback to output dispatcher
        def on_transcription_complete(text):
            """Handle transcription completion - dispatch to output modes."""
            logger.info(f"Transcription complete: {len(text)} chars")
            output_dispatcher.output(text)

        state_machine.set_on_transcription_complete(on_transcription_complete)

        # Wire hotkey to state machine
        def hotkey_callback(is_pressed):
            """Handle hotkey press/release."""
            if is_pressed:
                state_machine.on_hotkey_pressed()

        # Start global hotkey listener
        hotkey_started = start_global_hotkey(hotkey_callback)
        if hotkey_started:
            logger.info("Global hotkey started (Left Ctrl + Left Win)")
            print(i18n["hotkey_active"])
        else:
            logger.error("Failed to start global hotkey")
            print(i18n["warning_hotkey_failed"])

        # Store references for cleanup (used by cleanup() function)
        global _hotkey_instance, _audio_capture_instance
        _hotkey_instance = get_global_hotkey()  # Get the actual GlobalHotkey instance
        _audio_capture_instance = audio_capture

        # Start the state machine
        state_machine.start()
        logger.info("Recording state machine started")

        # Run system tray (blocking - keeps app alive)
        logger.info("Entering system tray loop")
        system_tray.start()
        # system_tray.start() blocks until exit is called
        # After tray exits, cleanup() will be called via atexit

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()