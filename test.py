"""
Final test - VOICE ONLY
No keyboard input. All prompts are spoken and all answers are by voice.
"""

from drive_thru_system import DriveThruSystem
import time

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_system():
    """Voice-only system test - no input() calls"""
    print_section("KFC DRIVE-THROUGH - VOICE ONLY TEST")
    
    print("\n[1] Initializing system...")
    try:
        system = DriveThruSystem()
        print("✓ System initialized")
    except Exception as e:
        print(f"❌ Init failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Tell user they respond using voice
    system.speak("This is a voice only test. Do not type anything. I will speak and you respond using your voice. Speak into your microphone when I ask.")
    time.sleep(2)
    
    # Test 1: Menu loaded
    print_section("TEST 1: Menu Loading")
    menu_count = len(system.special_offers)
    if menu_count == 0:
        system.speak("Error. No menu items loaded.")
        return False
    print(f"Menu items: {menu_count}")
    system.speak(f"Menu loaded. {menu_count} items.")
    time.sleep(1)
    
    # Test 2: TTS
    print_section("TEST 2: Text to Speech")
    if system.tts_method is None:
        system.speak("Error. Text to speech not available.")
        return False
    system.speak("Hello. This is a voice test. Can you hear me?")
    time.sleep(2)
    
    # Test 3: Voice recognition - listen for confirmation
    print_section("TEST 3: Voice Recognition")
    print(">>> Respond using your voice (speak into microphone).\n")
    system.speak("You can respond using your voice. Say yes if you heard me, or no if you did not. I am listening now.")
    result = system.listen(timeout=10.0)
    if result:
        print(f"You said: {result}")
        if "yes" in (result or "").lower():
            system.speak("Voice recognition is working.")
        else:
            system.speak("Please check your speakers.")
    else:
        system.speak("I did not hear a response. Check your microphone.")
    time.sleep(2)
    
    # Test 4: Menu announcement
    print_section("TEST 4: Menu Announcement")
    system.speak("I will now read the menu. Listen carefully.")
    time.sleep(2)
    system.announce_offers()
    time.sleep(1)
    
    # Test 5: Full flow (voice only)
    print_section("TEST 5: Full Voice Flow")
    print(">>> When the menu is read, respond using your voice: say a number (e.g. one, two) or 'repeat'.\n")
    system.speak("Starting full order flow. When I read the menu, respond using your voice. Say a number like one or two, or say repeat to hear the menu again. I will listen for your voice.")
    time.sleep(2)
    
    try:
        handoff_info = system.process_customer()
        print(f"\nCustomer ID: {handoff_info['customer_id']}")
        if handoff_info.get('full_order_text'):
            print(f"Order: {handoff_info['full_order_text']}")
        system.speak("Test complete. System is ready for voice only use.")
    except Exception as e:
        print(f"Error: {e}")
        system.speak("An error occurred. Check the console.")
        return False
    
    print_section("TEST SUMMARY")
    print("✓ Voice-only test completed. You responded using your voice.")
    print("\nTo run full simulation: python simulate_loop.py")
    print("  Say 'hello' or 'start' to begin, then respond by voice (e.g. number one, or repeat).")
    print("  Say 'goodbye' or 'exit' to quit.")
    
    return True

if __name__ == "__main__":
    try:
        success = test_system()
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nStopped.")
        exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
