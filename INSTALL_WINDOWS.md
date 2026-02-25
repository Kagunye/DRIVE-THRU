# Windows Installation Guide

## Quick Install

```bash
pip install -r requirements.txt
pip install pywin32
```

## TTS Engine Priority

The system uses the following priority on Windows:

1. **Windows SAPI (win32com)** - Most reliable, recommended
   - Uses native Windows Speech API
   - Better audio quality
   - More stable
   - Install: `pip install pywin32`

2. **pyttsx3** - Fallback option
   - Wrapper around Windows SAPI
   - May have audio issues on some systems
   - Install: `pip install pyttsx3`

## Verify Installation

Run this to test TTS:

```bash
python test_windows_sapi.py
```

Or test menu speaking:

```bash
python speak_menu_only.py
```

## Troubleshooting

### No Audio Output

1. **Check Windows Audio Settings:**
   - Right-click speaker icon → Open Sound settings
   - Verify output device is correct
   - Check volume is not muted

2. **Test Windows Narrator:**
   - Press `Win+Ctrl+Enter`
   - If Narrator speaks, TTS works but config may be wrong
   - If Narrator doesn't speak, it's a Windows audio issue

3. **Install pywin32:**
   ```bash
   pip install pywin32
   ```
   This provides direct Windows SAPI access (most reliable)

### TTS Errors

If you see errors about win32com:
- Install: `pip install pywin32`
- The system will automatically fall back to pyttsx3 if win32com is not available

## Running the System

```bash
# Test menu announcement
python speak_menu_only.py

# Run full system (simulation mode)
python simulate_loop.py

# Run full system (production)
python drive_thru_system.py
```
