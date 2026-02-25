"""
Script to help select and configure a Kenya lady voice
"""

import platform
import json

if platform.system() != "Windows":
    print("This script is for Windows only")
    exit(1)

print("="*70)
print("KENYA LADY VOICE SELECTION")
print("="*70)

try:
    import win32com.client
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    
    # Get all voices
    voices = speaker.GetVoices()
    
    print(f"\nFound {voices.Count} available voices:\n")
    
    female_voices = []
    kenyan_voices = []
    
    for i in range(voices.Count):
        voice = voices.Item(i)
        voice_name = voice.GetDescription()
        voice_id = voice.Id
        gender = voice.GetAttribute("Gender")
        language = voice.GetAttribute("Language")
        
        is_female = "female" in voice_name.lower() or "woman" in voice_name.lower() or gender == "Female"
        is_kenyan = "ke" in language.lower() or "kenya" in voice_name.lower() or "africa" in voice_name.lower()
        
        if is_female:
            female_voices.append((i, voice_name, language, voice_id))
        if is_kenyan:
            kenyan_voices.append((i, voice_name, language, voice_id))
        
        status = ""
        if is_female and is_kenyan:
            status = " ⭐ FEMALE + KENYAN"
        elif is_female:
            status = " ♀ FEMALE"
        elif is_kenyan:
            status = " 🇰🇪 KENYAN"
        
        print(f"{i+1}. {voice_name}{status}")
        print(f"   Language: {language}")
        print()
    
    # Recommend best voice
    print("="*70)
    print("RECOMMENDATIONS:")
    print("="*70)
    
    if kenyan_voices:
        print("\n⭐ BEST OPTION: Kenyan female voice found!")
        for idx, name, lang, vid in kenyan_voices:
            if "female" in name.lower() or "woman" in name.lower():
                print(f"\nRecommended: {name}")
                print(f"Language: {lang}")
                print(f"\nTo use this voice, update config.json:")
                print(f'  "voice_name": "{name}"')
                break
    elif female_voices:
        print("\n✓ FEMALE VOICES AVAILABLE:")
        for idx, name, lang, vid in female_voices[:3]:  # Show first 3
            print(f"  - {name} ({lang})")
        
        print(f"\nRecommended: {female_voices[0][1]}")
        print(f"\nTo use this voice, update config.json:")
        print(f'  "voice_name": "{female_voices[0][1]}"')
    else:
        print("\n⚠ No female voices found. Using default voice.")
    
    # Test selected voice
    print("\n" + "="*70)
    print("TESTING VOICE")
    print("="*70)
    
    if female_voices:
        test_voice = female_voices[0]
        speaker.Voice = voices.Item(test_voice[0])
        print(f"\nTesting voice: {test_voice[1]}")
        print("Speaking: 'Hello, welcome to KFC drive-through'")
        speaker.Speak("Hello, welcome to KFC drive-through", 0)
        print("\nDid you like this voice?")
        
        # Update config.json
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
            
            config["voice_name"] = test_voice[1]
            config["voice_preference"] = "female"
            
            with open("config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            print(f"\n✓ Updated config.json to use: {test_voice[1]}")
        except Exception as e:
            print(f"\n⚠ Could not update config.json: {e}")
            print("Please manually update config.json with:")
            print(f'  "voice_name": "{test_voice[1]}"')
    
except ImportError:
    print("ERROR: win32com not available. Install with: pip install pywin32")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("NOTE: Windows may not have Kenyan-specific voices by default.")
print("You may need to install additional language packs or voices.")
print("="*70)
