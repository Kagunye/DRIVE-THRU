"""
Simulation script - VOICE ONLY
No keyboard input. Say "hello" or "start" to begin, "goodbye" or "exit" to quit.
"""

from drive_thru_system import DriveThruSystem
import time

def simulate_car_approach():
    """Voice-only simulation - listen for wake words to trigger"""
    print("="*60)
    print("KFC DRIVE-THROUGH - VOICE ONLY MODE")
    print("="*60)
    print("\nNo keyboard needed. Use your voice only.\n")
    
    system = DriveThruSystem()
    
    car_present = False
    def simulated_detect():
        return car_present
    
    system.detect_car_approach = simulated_detect
    
    # Tell user they respond using voice
    system.speak("Voice only mode. Respond using your voice. Say hello or start when you are ready to order. When I read the menu, say a number or say repeat. Say goodbye or exit when you are done.")
    time.sleep(1)
    
    print("Respond using your voice. Say 'hello' or 'start' to begin, then say your order (e.g. number one). Say 'goodbye' or 'exit' to quit.\n")
    
    try:
        while True:
            # Listen for voice command - NO keyboard input
            print("[Listening for wake word...]")
            said = system.listen(timeout=20.0, phrase_time_limit=5)
            
            if said is None:
                print("(No speech detected, listening again...)\n")
                continue
            
            said_lower = said.lower().strip()
            print(f"You said: {said}\n")
            
            # Start/trigger: hello, start, ready, I'm here, order, etc.
            if any(w in said_lower for w in ["hello", "start", "ready", "here", "order", "hi", "yes"]):
                print("--- Car approach triggered by voice ---")
                car_present = True
                system.process_customer()
                car_present = False
                print("Ready for next customer. Say 'hello' or 'start' again, or 'goodbye' to exit.\n")
                time.sleep(1)
                system.speak("Say hello or start when you want to order again. Say goodbye to exit.")
                continue
            
            # Quit: goodbye, exit, quit, stop
            if any(w in said_lower for w in ["goodbye", "exit", "quit", "stop", "done", "bye"]):
                system.speak("Goodbye. Have a nice day.")
                print("\nExiting (voice command).\n")
                break
            
            # Unknown - ask to repeat
            system.speak("Say hello or start to order, or goodbye to exit.")
            print("(Say 'hello' to order or 'goodbye' to exit)\n")
    
    except KeyboardInterrupt:
        print("\nStopped.")
    
    print("Simulation ended.")

if __name__ == "__main__":
    simulate_car_approach()
