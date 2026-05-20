# Problems and Issues

## 2026-05-19: Integration Gap in main.py

### Issue: Components Not Wired Together
The DTVoice application builds successfully but the main.py does NOT integrate the core components:

1. `system_tray.py` is never started (no `tray.start()` call)
2. `hotkey.py` global hotkey is never started
3. `RecordingStateMachine` is never created
4. `OutputDispatcher.output()` is never called

### Evidence
- Build: SUCCESS (30.6 MB exe at dist/DTVoice.exe)
- Runtime: App starts, logs "DTVoice starting", but no tray icon appears
- Logs show repeated "DTVoice starting" entries from multiple attempts

### Root Cause
main.py only handles:
- Command line argument parsing
- Single-instance mutex check
- Logging setup
- First-run permission check

But does NOT create or start:
- SystemTray instance
- GlobalHotkey listener
- RecordingStateMachine
- AudioCapture/Transcriber pipeline
- OutputDispatcher

### Impact
The app launches but provides no functionality - no hotkey listening, no tray icon, no recording capability.

### Suggested Fix
main.py needs to:
1. Create AudioCapture, Transcriber, ModelLoader instances
2. Create SystemTray with proper callbacks
3. Create RecordingStateMachine with all dependencies
4. Register hotkey callback that triggers state machine
5. Start system tray (blocking call)

## 2026-05-19: Build Fixes Applied

### setuptools incompatibility
- Error: `ModuleNotFoundError: No module named 'pkg_resources'`
- Fix: Downgraded setuptools from 82.0.0 to 70.3.0

### version file missing
- Error: `FileNotFoundError: [Errno 2] No such file or directory: '0.1.0'`
- Fix: Removed `version='0.1.0'` from dtvoice.spec

### win32reg hidden import
- Warning: `Hidden import 'win32reg' not found`
- Non-fatal, build succeeded anyway