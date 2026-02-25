"""
List all available Windows SAPI voices
"""

import platform

if platform.system() != "Windows":
    print("This script is for Windows only")
    exit(1)

print("="*70)
print("AVAILABLE WINDOWS SAPI VOICES")
print("="*70)

try:
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    
    # Get all voices
    voices = speaker.GetVoices()
    
    print(f"\nFound {voices.Count} voices:\n")
    
    for i in range(voices.Count):
        voice = voices.Item(i)
        voice_id = voice.Id
        voice_name = voice.GetDescription()
        
        # Get voice attributes
        attributes = voice.GetAttribute("Gender")
        language = voice.GetAttribute("Language")
        
        print(f"{i+1}. {voice_name}")
        print(f"   ID: {voice_id}")
        print(f"   Gender: {attributes}")
        print(f"   Language: {language}")
        print()
    
    print("="*70)
    print("\nTo use a specific voice, note the voice name or ID above.")
    print("Female voices are typically marked with 'Female' in Gender.")
    
except ImportError:
    print("ERROR: win32com not available. Install with: pip install pywin32")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
