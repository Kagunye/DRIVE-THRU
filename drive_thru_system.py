"""
KFC Drive-Through Ordering System for Raspberry Pi
Detects car approach via loop detector, announces KFC menu, captures customer selection,
and hands off to human operator for ordering.
"""

import time
import threading
import queue
from datetime import datetime
from typing import List, Dict, Optional
import json
import os
import subprocess
import platform
import shutil

# Detect platform
IS_WINDOWS = platform.system() == "Windows"
IS_LINUX = platform.system() == "Linux"

# Raspberry Pi GPIO support
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("Warning: RPi.GPIO not available. Using simulation mode.")

try:
    import speech_recognition as sr
except ImportError:
    print("Installing required packages...")
    subprocess.check_call(["pip", "install", "speechrecognition", "pyaudio"])
    import speech_recognition as sr

# Ollama and Whisper support
OLLAMA_AVAILABLE = False
WHISPER_AVAILABLE = False

try:
    import ollama
    OLLAMA_AVAILABLE = True
    print("✓ Ollama available")
except ImportError:
    print("⚠ Ollama not available. Install with: pip install ollama")

try:
    import whisper
    WHISPER_AVAILABLE = True
    print("✓ Whisper available")
except ImportError:
    print("⚠ Whisper not available. Install with: pip install openai-whisper")

# Determine TTS engine based on platform
TTS_ENGINE = None
if IS_WINDOWS:
    # Windows: Prefer win32com SAPI (most reliable), fallback to pyttsx3
    try:
        import win32com.client
        TTS_ENGINE = "win32com_sapi"
        print("Using Windows SAPI via win32com (most reliable)")
    except ImportError:
        try:
            import pyttsx3
            TTS_ENGINE = "pyttsx3"
            print("Using pyttsx3 (Windows SAPI wrapper)")
        except ImportError:
            print("Warning: Neither win32com nor pyttsx3 available. TTS will be disabled.")
            TTS_ENGINE = None
elif IS_LINUX:
    # Linux/Raspberry Pi: Prefer espeak, fallback to pyttsx3
    if shutil.which("espeak"):
        TTS_ENGINE = "espeak"
        print("Using espeak for text-to-speech (Raspberry Pi compatible)")
    else:
        try:
            import pyttsx3
            TTS_ENGINE = "pyttsx3"
            print("Using pyttsx3 for text-to-speech")
        except ImportError:
            print("Warning: Neither espeak nor pyttsx3 available. TTS will be disabled.")
            TTS_ENGINE = None
else:
    # macOS or other: Try pyttsx3
    try:
        import pyttsx3
        TTS_ENGINE = "pyttsx3"
    except ImportError:
        print("Warning: pyttsx3 not available. TTS will be disabled.")
        TTS_ENGINE = None


class DriveThruSystem:
    """Main drive-through ordering system"""
    
    def __init__(self, config_file: str = "config.json"):
        """Initialize the drive-through system"""
        self.config = self._load_config(config_file)
        self.running = False
        self.current_customer = None
        self.order_queue = queue.Queue()
        self._car_number = 0  # for "Car number one", etc.
        self.use_raspberry_pi = self.config.get("use_raspberry_pi", False)
        
        # Initialize Raspberry Pi GPIO if available
        if self.use_raspberry_pi and GPIO_AVAILABLE:
            self.loop_pin = self.config.get("loop_detector_pin", 18)
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.loop_pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
            print(f"Raspberry Pi GPIO initialized. Loop detector on pin {self.loop_pin}")
        else:
            print("Running in simulation mode (no GPIO)")
        
        # Initialize voice components
        self.recognizer = sr.Recognizer()
        try:
            self.microphone = sr.Microphone()
        except OSError as e:
            print(f"⚠ No microphone found: {e}")
            print("   Voice input disabled. Connect a mic or set default in Windows Sound settings.")
            self.microphone = None
        
        # Initialize Whisper model if enabled
        self.use_whisper = self.config.get("use_ollama_whisper", False) and WHISPER_AVAILABLE
        self.whisper_model = None
        if self.use_whisper:
            self._setup_whisper()
        
        # Initialize Ollama client if enabled
        self.use_ollama = self.config.get("use_ollama_for_processing", False) and OLLAMA_AVAILABLE
        self.ollama_client = None
        if self.use_ollama:
            self._setup_ollama()
        
        # Initialize TTS based on available engine
        self._setup_tts()
        
        # Calibrate microphone if available
        if self.microphone is not None:
            print("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.recognizer.energy_threshold = 300  # Lower = more sensitive
            print("✓ Microphone calibrated!")
            print(f"  Energy threshold: {self.recognizer.energy_threshold} (lower = more sensitive)")
            if self.use_whisper:
                print(f"  Using Whisper for speech recognition (model: {self.config.get('whisper_model', 'base')})")
            else:
                print("  Using Google Speech Recognition")
        else:
            print("  Voice input: disabled (no microphone)")
        
        # KFC special offers
        self.special_offers = self.config.get("special_offers", [])
        
        # Debug: Print loaded menu items
        if len(self.special_offers) > 0:
            print(f"\n✓ Loaded {len(self.special_offers)} menu items:")
            for i, offer in enumerate(self.special_offers, 1):
                print(f"  {i}. {offer[:70]}...")
        else:
            print("\n⚠ WARNING: No menu items loaded from config.json!")
            print("Please check that config.json contains 'special_offers' array.")
        
    def _setup_whisper(self):
        """Initialize Whisper model for better speech recognition"""
        try:
            import whisper
            model_name = self.config.get("whisper_model", "base")
            print(f"Loading Whisper model: {model_name}...")
            print("  (This may take a moment on first run)")
            self.whisper_model = whisper.load_model(model_name)
            print(f"✓ Whisper model '{model_name}' loaded successfully")
        except Exception as e:
            print(f"⚠ Failed to load Whisper model: {e}")
            print("  Falling back to Google Speech Recognition")
            self.use_whisper = False
            self.whisper_model = None
    
    def _setup_ollama(self):
        """Initialize Ollama client for order processing"""
        try:
            import ollama
            base_url = self.config.get("ollama_base_url", "http://localhost:11434")
            model_name = self.config.get("ollama_model", "llama2")
            
            # Test connection
            try:
                # Extract host from URL
                host = base_url.replace("http://", "").replace("https://", "").split(":")[0]
                port = base_url.split(":")[-1] if ":" in base_url else "11434"
                
                # Create client
                self.ollama_client = ollama.Client(host=f"{host}:{port}")
                
                # Test by listing models
                models = self.ollama_client.list()
                print(f"✓ Ollama connected at {base_url}")
                print(f"  Model: {model_name}")
                if models and 'models' in models:
                    available = [m.get('name', 'unknown') for m in models['models']]
                    print(f"  Available models: {', '.join(available)}")
            except Exception as e:
                print(f"⚠ Ollama connection failed: {e}")
                print("  Make sure Ollama is running: ollama serve")
                print("  Or install Ollama: https://ollama.ai")
                self.use_ollama = False
                self.ollama_client = None
        except ImportError:
            print("⚠ Ollama not installed. Install with: pip install ollama")
            self.use_ollama = False
            self.ollama_client = None
        except Exception as e:
            print(f"⚠ Failed to initialize Ollama: {e}")
            self.use_ollama = False
            self.ollama_client = None
    
    def _load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        default_config = {
            "special_offers": [],
            "loop_detector_pin": 18,
            "detection_interval": 3.0,
            "voice_timeout": 8.0,
            "operator_notification": True,
            "use_raspberry_pi": True,
            "use_ollama_whisper": False,
            "whisper_model": "base",
            "use_ollama_for_processing": False,
            "ollama_base_url": "http://localhost:11434",
            "ollama_model": "llama2"
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    default_config.update(config)
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
        
        return default_config
    
    def _setup_tts(self):
        """Configure text-to-speech engine"""
        global TTS_ENGINE
        
        if TTS_ENGINE == "win32com_sapi":
            # Windows SAPI via win32com - most reliable on Windows
            try:
                import win32com.client
                self.sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
                # Set volume to max (0-100) so voice is audible
                try:
                    self.sapi_speaker.Volume = 100
                except Exception:
                    pass
                
                # Set voice to female/Kenyan if available
                voices = self.sapi_speaker.GetVoices()
                voice_set = False
                
                # Get voice preferences from config
                voice_pref = self.config.get("voice_preference", "female").lower()
                lang_pref = self.config.get("voice_language_preference", "ke").lower()
                specific_voice_name = self.config.get("voice_name")
                
                # If specific voice name is provided, use it
                if specific_voice_name:
                    for i in range(voices.Count):
                        voice = voices.Item(i)
                        voice_name = voice.GetDescription()
                        if specific_voice_name.lower() in voice_name.lower():
                            self.sapi_speaker.Voice = voice
                            print(f"  Selected configured voice: {voice_name}")
                            voice_set = True
                            break
                
                # Otherwise, try to find female voice (preferably Kenyan/African)
                if not voice_set:
                    best_voice = None
                    best_score = 0
                    
                    for i in range(voices.Count):
                        voice = voices.Item(i)
                        voice_name = voice.GetDescription()
                        voice_id = voice.Id
                        gender = voice.GetAttribute("Gender")
                        language = voice.GetAttribute("Language")
                        
                        score = 0
                        
                        # Prefer female voices
                        if "female" in voice_name.lower() or "woman" in voice_name.lower() or gender == "Female":
                            score += 10
                        
                        # Prefer Kenyan/African language codes
                        if lang_pref in language.lower():
                            score += 20
                        elif "ke" in language.lower() or "kenya" in language.lower():
                            score += 15
                        elif "africa" in voice_name.lower() or "african" in language.lower():
                            score += 10
                        
                        # Prefer voices with "Zira" or common female names
                        if "zira" in voice_name.lower():
                            score += 5
                        
                        if score > best_score:
                            best_score = score
                            best_voice = voice
                    
                    if best_voice:
                        self.sapi_speaker.Voice = best_voice
                        voice_name = best_voice.GetDescription()
                        language = best_voice.GetAttribute("Language")
                        print(f"  Selected voice: {voice_name}")
                        print(f"  Language: {language}")
                        voice_set = True
                
                # If still no voice set, use default
                if not voice_set:
                    print("  Using default voice")
                
                # Second voice for order read-back (different from menu voice)
                self.sapi_speaker_order = None
                order_voice_name = self.config.get("order_voice_name")
                if order_voice_name and voices.Count > 1:
                    for i in range(voices.Count):
                        voice = voices.Item(i)
                        vname = voice.GetDescription()
                        # Prefer male/different voice for order (David, Mark, etc.)
                        if order_voice_name.lower() in vname.lower():
                            self.sapi_speaker_order = win32com.client.Dispatch("SAPI.SpVoice")
                            self.sapi_speaker_order.Voice = voice
                            try:
                                self.sapi_speaker_order.Volume = 100
                            except Exception:
                                pass
                            print(f"  Order voice: {vname}")
                            break
                    if self.sapi_speaker_order is None:
                        # Use first male voice if order_voice not found
                        for i in range(voices.Count):
                            voice = voices.Item(i)
                            if "male" in voice.GetDescription().lower() or "david" in voice.GetDescription().lower():
                                self.sapi_speaker_order = win32com.client.Dispatch("SAPI.SpVoice")
                                self.sapi_speaker_order.Voice = voice
                                try:
                                    self.sapi_speaker_order.Volume = 100
                                except Exception:
                                    pass
                                print(f"  Order voice: {voice.GetDescription()}")
                                break
                
                self.tts_method = "win32com_sapi"
                print("TTS initialized: Windows SAPI (win32com)")
                
                # Test TTS
                try:
                    self.sapi_speaker.Speak("TTS test", 0)
                    print("  ✓ TTS test successful")
                except Exception as test_e:
                    print(f"  ⚠ SAPI test failed: {test_e}")
                    self.sapi_speaker = None
                    self.sapi_speaker_order = None
                    print("  Trying pyttsx3...")
                    try:
                        import pyttsx3
                        self.tts_engine = pyttsx3.init()
                        self.tts_method = "pyttsx3"
                        voices = self.tts_engine.getProperty('voices')
                        if voices:
                            for v in voices:
                                if 'zira' in v.name.lower() or 'female' in v.name.lower():
                                    self.tts_engine.setProperty('voice', v.id)
                                    break
                            else:
                                self.tts_engine.setProperty('voice', voices[0].id)
                        print("  ✓ Using pyttsx3 (SAPI unavailable)")
                    except Exception as fallback_e:
                        print(f"  pyttsx3 init failed: {fallback_e}")
                        self.tts_method = "win32com_sapi"  # keep so speak() will try SAPI then runtime pyttsx3 fallback
            except Exception as e:
                print(f"Warning: Failed to initialize Windows SAPI: {e}")
                import traceback
                traceback.print_exc()
                self.tts_method = None
                self.sapi_speaker = None
        elif TTS_ENGINE == "pyttsx3":
            try:
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                
                # Stop any existing speech
                try:
                    self.tts_engine.stop()
                except:
                    pass
                
                # Set voice properties - prefer female voice
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    # Try to find female voice (preferably Kenyan/African if available)
                    voice_set = False
                    voice_pref = self.config.get("voice_preference", "female").lower()
                    
                    # First, try to find Kenyan/African female voice
                    for voice in voices:
                        voice_name_lower = voice.name.lower()
                        if voice_pref in voice_name_lower:
                            if "kenya" in voice_name_lower or "africa" in voice_name_lower or "ke" in voice_name_lower:
                                self.tts_engine.setProperty('voice', voice.id)
                                print(f"  Using voice: {voice.name}")
                                voice_set = True
                                break
                    
                    # If no Kenyan voice, use any female voice
                    if not voice_set:
                        for voice in voices:
                            voice_name_lower = voice.name.lower()
                            if 'female' in voice_name_lower or 'zira' in voice_name_lower or 'woman' in voice_name_lower:
                                self.tts_engine.setProperty('voice', voice.id)
                                print(f"  Using voice: {voice.name}")
                                voice_set = True
                                break
                    
                    # If still no voice set, use first available
                    if not voice_set and voices:
                        self.tts_engine.setProperty('voice', voices[0].id)
                        print(f"  Using default voice: {voices[0].name}")
                    if not voice_set and voices:
                        # Use first available voice
                        self.tts_engine.setProperty('voice', voices[0].id)
                        print(f"  Using voice: {voices[0].name}")
                
                # Set speech rate and volume - CRITICAL: Set volume to maximum
                self.tts_engine.setProperty('rate', self.config.get("tts_rate", 150))
                # Force volume to 1.0 (maximum) to ensure audio output
                self.tts_engine.setProperty('volume', 1.0)
                self.tts_method = "pyttsx3"
                print("TTS initialized: pyttsx3")
                
                # Test TTS with a short phrase - VERIFY AUDIO OUTPUT
                print("  Testing TTS audio output...")
                try:
                    self.tts_engine.say("TTS test")
                    self.tts_engine.runAndWait()
                    print("  ✓ TTS test completed - did you hear 'TTS test'?")
                except Exception as test_e:
                    print(f"  ⚠ TTS test failed: {test_e}")
                    
            except Exception as e:
                print(f"Warning: Failed to initialize pyttsx3: {e}")
                import traceback
                traceback.print_exc()
                self.tts_method = None
                self.tts_engine = None
        elif TTS_ENGINE == "espeak":
            # Check if espeak is available
            if shutil.which("espeak"):
                self.tts_method = "espeak"
                print("TTS initialized: espeak")
            else:
                print("Warning: espeak not found. TTS will be disabled.")
                self.tts_method = None
        else:
            print("Warning: No TTS engine available. Voice output will be disabled.")
            self.tts_method = None
        if self.tts_method:
            print("  If you can't hear voice: check Windows volume, default speaker, and that no app is muting audio.")
    
    def _clean_text_for_speech(self, text: str) -> str:
        """Clean text for better TTS pronunciation"""
        # Replace dollar signs with "dollars"
        text = text.replace("$", " dollars ")
        # Replace dashes with pauses
        text = text.replace(" - ", ". ")
        # Replace colons with pauses  
        text = text.replace(": ", ". ")
        # Clean up multiple spaces
        text = " ".join(text.split())
        return text
    
    def _sapi_speak_with_retry(self, text: str, speaker_attr: str = "sapi_speaker"):
        """Call SAPI Speak with one retry on failure (avoids intermittent 0x8004503A)."""
        speaker = getattr(self, speaker_attr, None)
        if not speaker:
            return
        try:
            speaker.Speak(text, 0)
        except Exception as e:
            print(f"  SAPI first attempt failed: {e}, retrying after delay...")
            time.sleep(0.6)
            try:
                speaker.Speak(text, 0)
            except Exception as e2:
                raise e2
    
    def _speak_with_pyttsx3_fallback(self, text: str) -> bool:
        """Speak using pyttsx3 (lazy init if needed). Returns True if successful."""
        try:
            if not getattr(self, 'tts_engine', None):
                import pyttsx3
                self.tts_engine = pyttsx3.init()
                for v in self.tts_engine.getProperty('voices') or []:
                    if 'zira' in v.name.lower() or 'female' in v.name.lower():
                        self.tts_engine.setProperty('voice', v.id)
                        break
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
            return True
        except Exception as e:
            print(f"  pyttsx3 fallback error: {e}")
            return False
    
    def _speak_sapi_in_chunks(self, text: str, max_length: int):
        """Speak long text in short chunks via SAPI to avoid driver errors."""
        parts = text.split(". ")
        chunk = ""
        for i, part in enumerate(parts):
            if len(chunk) + len(part) + 2 <= max_length:
                chunk += part + ". "
            else:
                if chunk.strip():
                    time.sleep(0.2)
                    self._sapi_speak_with_retry(chunk.strip())
                chunk = part + ". "
        if chunk.strip():
            time.sleep(0.2)
            self._sapi_speak_with_retry(chunk.strip())
    
    def _speak_in_chunks(self, text: str, max_length: int = 100):
        """Speak long text in smaller chunks to avoid TTS issues"""
        # If text is short enough, speak normally
        if len(text) <= max_length:
            self.speak(text)
            return
        
        # Break into sentences or phrases
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    self.speak(current_chunk.strip())
                    time.sleep(0.5)
                current_chunk = sentence + ". "
        
        # Speak remaining chunk
        if current_chunk:
            self.speak(current_chunk.strip())
    
    def speak_order(self, text: str):
        """Speak with ORDER voice (different from menu voice)"""
        cleaned_text = self._clean_text_for_speech(text)
        print(f"\n[ORDER VOICE]: {text}")
        
        if self.tts_method == "win32com_sapi" and getattr(self, 'sapi_speaker_order', None):
            try:
                time.sleep(0.25)
                if len(cleaned_text) > 80:
                    parts = cleaned_text.split(". ")
                    chunk, rest = "", parts
                    for part in rest:
                        if len(chunk) + len(part) + 2 <= 80:
                            chunk += part + ". "
                        else:
                            if chunk.strip():
                                self._sapi_speak_with_retry(chunk.strip(), "sapi_speaker_order")
                                time.sleep(0.2)
                            chunk = part + ". "
                    if chunk.strip():
                        self._sapi_speak_with_retry(chunk.strip(), "sapi_speaker_order")
                else:
                    self._sapi_speak_with_retry(cleaned_text, "sapi_speaker_order")
                print("[TTS] ✓ Order read-back completed")
            except Exception as e:
                print(f"Order voice failed: {e}, using main voice")
                self.speak(text)
        else:
            self.speak(text)
    
    def speak(self, text: str):
        """Convert text to speech and play (menu voice)"""
        # Clean text for better TTS
        cleaned_text = self._clean_text_for_speech(text)
        
        print(f"\n[SYSTEM SPEAKING]: {text}")
        print(f"[CLEANED TEXT]: {cleaned_text}")
        print(f"[TTS METHOD]: {self.tts_method}")
        
        if self.tts_method == "win32com_sapi":
            # Windows SAPI - use chunks + retry to avoid 0x8004503A / -2147200966
            try:
                if not hasattr(self, 'sapi_speaker') or self.sapi_speaker is None:
                    print("❌ ERROR: SAPI speaker not initialized!")
                    print("   Attempting to reinitialize...")
                    try:
                        import win32com.client
                        self.sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
                        print("   ✓ SAPI speaker reinitialized")
                    except Exception as e2:
                        print(f"   ❌ Failed to reinitialize: {e2}")
                        return
                
                # Long text: speak in chunks to avoid SAPI failures
                SAPI_MAX_CHARS = 80
                if len(cleaned_text) > SAPI_MAX_CHARS:
                    self._speak_sapi_in_chunks(cleaned_text, SAPI_MAX_CHARS)
                    return
                
                print("[TTS] Speaking via Windows SAPI...")
                time.sleep(0.25)  # let previous speech release
                self._sapi_speak_with_retry(cleaned_text)
                print("[TTS] ✓ Speech completed")
            except Exception as e:
                print(f"⚠ SAPI failed, trying pyttsx3: {e}")
                if self._speak_with_pyttsx3_fallback(cleaned_text):
                    self.tts_method = "pyttsx3"  # use pyttsx3 from now on, skip SAPI
                    print("[TTS] ✓ Speech completed (switched to pyttsx3)")
                else:
                    print(f"❌ TTS failed (SAPI and pyttsx3)")
        elif self.tts_method == "pyttsx3":
            try:
                if not hasattr(self, 'tts_engine') or self.tts_engine is None:
                    print("❌ ERROR: TTS engine not initialized!")
                    print("   Attempting to reinitialize...")
                    try:
                        import pyttsx3
                        self.tts_engine = pyttsx3.init()
                        print("   ✓ TTS engine reinitialized")
                    except Exception as e2:
                        print(f"   ❌ Failed to reinitialize: {e2}")
                        return
                
                # Stop any current speech first
                try:
                    self.tts_engine.stop()
                except:
                    pass
                
                print("[TTS] Sending text to pyttsx3...")
                print(f"[TTS] Text length: {len(cleaned_text)} characters")
                
                # CRITICAL: Stop any previous speech first
                try:
                    self.tts_engine.stop()
                except:
                    pass
                
                # Use cleaned text for better pronunciation
                self.tts_engine.say(cleaned_text)
                print("[TTS] Running TTS engine (this may take a moment)...")
                print("[TTS] ⚠ LISTEN NOW - Audio should be playing!")
                
                # Run and wait - this blocks until speech completes
                self.tts_engine.runAndWait()
                
                # Small delay to ensure speech completes
                time.sleep(0.5)
                
                print("[TTS] ✓ Speech completed - did you hear it?")
            except Exception as e:
                print(f"❌ ERROR: TTS error: {e}")
                import traceback
                traceback.print_exc()
                # Try to reinitialize for next time
                try:
                    import pyttsx3
                    self.tts_engine = pyttsx3.init()
                    print("   ✓ TTS engine reinitialized after error")
                except:
                    pass
        elif self.tts_method == "espeak":
            try:
                rate = self.config.get("tts_rate", 150)
                print(f"[TTS] Calling espeak with rate {rate}...")
                # Use cleaned text
                result = subprocess.call(['espeak', '-s', str(rate), '-a', '200', cleaned_text], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if result == 0:
                    print("[TTS] ✓ Speech completed successfully")
                else:
                    print(f"❌ [TTS] Warning: espeak returned error code {result}")
            except FileNotFoundError:
                print("❌ ERROR: espeak not found. Please install: sudo apt-get install espeak")
            except Exception as e:
                print(f"❌ ERROR: TTS error: {e}")
                import traceback
                traceback.print_exc()
        else:
            # No TTS available - just print the text
            print("❌ WARNING: TTS not available - text only (no audio)")
            print("  Current tts_method:", self.tts_method)
            print("  On Windows: pip install pyttsx3")
            print("  On Linux: sudo apt-get install espeak")
    
    def listen(self, timeout: float = 15.0, phrase_time_limit: int = 30) -> Optional[str]:
        """Listen for voice input and return transcribed text (captures any words)"""
        if self.microphone is None:
            print("\n⚠ No microphone available. Connect a mic or set default in Windows Sound settings.\n")
            return None
        try:
            with self.microphone as source:
                print(f"\n🎤 [LISTENING NOW] Speak when ready...")
                if self.use_whisper:
                    print(f"   Using Whisper for better accuracy")
                print(f"   (Timeout: {timeout}s, Max phrase: {phrase_time_limit}s)")
                print("   ⚠ SPEAK NOW - I'm listening!\n")
                
                # Listen with longer timeout and phrase limit for natural speech
                # Set energy_threshold lower to be more sensitive
                self.recognizer.energy_threshold = 300  # Lower threshold = more sensitive
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            
            print("\n[PROCESSING] Transcribing your speech...")
            
            # Use Whisper if available (better accuracy), otherwise Google Speech Recognition
            if self.use_whisper and self.whisper_model:
                try:
                    # Save audio to temporary file for Whisper
                    import tempfile
                    import wave
                    import io
                    
                    # Convert audio data to WAV format
                    wav_data = io.BytesIO()
                    with wave.open(wav_data, 'wb') as wav_file:
                        wav_file.setnchannels(1)  # Mono
                        wav_file.setsampwidth(audio.sample_width)
                        wav_file.setframerate(audio.sample_rate)
                        wav_file.writeframes(audio.frame_data)
                    
                    wav_data.seek(0)
                    
                    # Transcribe with Whisper
                    result = self.whisper_model.transcribe(wav_data, language="en", fp16=False)
                    text = result["text"].strip()
                    
                    print(f"\n✓ [CUSTOMER SAID - Whisper]: {text}\n")
                    return text
                except Exception as e:
                    print(f"⚠ Whisper transcription failed: {e}")
                    print("  Falling back to Google Speech Recognition...")
                    # Fall through to Google recognition
            
            # Fallback to Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language='en-US')
            print(f"\n✓ [CUSTOMER SAID]: {text}\n")
            return text  # Return original case for better readability
            
        except sr.WaitTimeoutError:
            print("\n⏱ [TIMEOUT] No speech detected within timeout period")
            print("   Try speaking again or check microphone connection\n")
            return None
        except sr.UnknownValueError:
            print("\n❌ [ERROR] Could not understand audio")
            print("   Please speak more clearly or check microphone\n")
            return None
        except sr.RequestError as e:
            print(f"\n❌ [ERROR] Speech recognition service error: {e}")
            print("   Check internet connection\n")
            return None
    
    def listen_continuous(self, max_duration: int = 60) -> List[str]:
        """Listen continuously and capture multiple phrases until customer finishes"""
        if self.microphone is None:
            print("\n⚠ No microphone available. Connect a mic or set default in Windows Sound settings.\n")
            return []
        phrases = []
        print(f"\n🎤 [CONTINUOUS LISTENING MODE]")
        if self.use_whisper:
            print(f"   Using Whisper for better accuracy")
        print(f"   Listening for up to {max_duration} seconds...")
        print("   Say 'done', 'that's all', or 'finished' when you're done ordering")
        print("   ⚠ START SPEAKING NOW - I'm listening!\n")
        
        # Lower energy threshold for better sensitivity
        self.recognizer.energy_threshold = 300
        
        start_time = time.time()
        silence_count = 0
        max_silence = 4  # Stop after 4 seconds of silence
        
        while (time.time() - start_time) < max_duration:
            try:
                with self.microphone as source:
                    print("   🎤 Listening... (speak now)")
                    audio = self.recognizer.listen(source, timeout=3.0, phrase_time_limit=20)
                
                print("   [Processing...]")
                
                # Use Whisper if available, otherwise Google
                if self.use_whisper and self.whisper_model:
                    try:
                        import tempfile
                        import wave
                        import io
                        
                        wav_data = io.BytesIO()
                        with wave.open(wav_data, 'wb') as wav_file:
                            wav_file.setnchannels(1)
                            wav_file.setsampwidth(audio.sample_width)
                            wav_file.setframerate(audio.sample_rate)
                            wav_file.writeframes(audio.frame_data)
                        
                        wav_data.seek(0)
                        result = self.whisper_model.transcribe(wav_data, language="en", fp16=False)
                        text = result["text"].strip()
                    except Exception as e:
                        print(f"   ⚠ Whisper failed: {e}, using Google...")
                        text = self.recognizer.recognize_google(audio, language='en-US')
                else:
                    text = self.recognizer.recognize_google(audio, language='en-US')
                
                print(f"\n   ✓ [CAPTURED]: {text}\n")
                
                # Check for completion phrases
                text_lower = text.lower()
                if any(phrase in text_lower for phrase in ["done", "that's all", "that's it", "finished", "that will be all", "complete"]):
                    print("   ✓ [ORDER COMPLETE] Customer finished ordering\n")
                    phrases.append(text)
                    break
                
                phrases.append(text)
                silence_count = 0
                print("   Continue speaking or say 'done' when finished...\n")
                
            except sr.WaitTimeoutError:
                silence_count += 1
                if silence_count >= max_silence:
                    print(f"\n   ⏱ [SILENCE DETECTED] No speech for {max_silence} seconds")
                    print("   Assuming customer finished ordering.\n")
                    break
                print(f"   ... waiting ({silence_count}/{max_silence}) ...")
                continue
            except sr.UnknownValueError:
                print("   ⚠ [PARTIAL] Could not understand some audio, continuing...")
                print("   Please repeat or continue speaking...\n")
                continue
            except sr.RequestError as e:
                print(f"   ❌ [ERROR] Speech recognition service error: {e}")
                print("   Check internet connection\n")
                break
        
        return phrases
    
    def detect_car_approach(self) -> bool:
        """
        Detect if a car has approached the drive-through loop.
        Uses Raspberry Pi GPIO to read inductive loop detector.
        """
        if self.use_raspberry_pi and GPIO_AVAILABLE:
            # Read GPIO pin - HIGH means car detected
            return GPIO.input(self.loop_pin) == GPIO.HIGH
        else:
            # Simulation mode for testing without hardware
            return False  # Will be triggered manually in test mode
    
    def announce_offers(self):
        """Announce KFC menu to the customer"""
        print("\n" + "="*70)
        print("🎤 MENU ANNOUNCEMENT STARTING")
        print("="*70)
        print(f"TTS Method: {self.tts_method}")
        print(f"Menu Items: {len(self.special_offers)}")
        print("="*70 + "\n")
        
        greeting = "Welcome to KFC drive thru. These are the specials of the day."
        print("[1/{}] Speaking greeting...".format(len(self.special_offers) + 2))
        self.speak(greeting)
        time.sleep(1.5)
        
        # Menu: 4 choices (1-4). 0 = repeat, 6 = cancel.
        menu_choices = 4
        offers_to_announce = self.special_offers[:menu_choices] if self.special_offers else []
        if len(offers_to_announce) == 0:
            print("\n❌ ⚠ WARNING: No menu items to announce!")
            error_msg = "I'm sorry, but our menu system is not configured. Please tell our staff member what you'd like to order."
            self.speak(error_msg)
            return
        
        print(f"\n📢 Now announcing {len(offers_to_announce)} menu items (say 1-4 to order, 0 repeat, 6 cancel)...\n")
        
        # Announce each menu item (first 5 only)
        for i, offer in enumerate(offers_to_announce, 1):
            print(f"\n[{i+1}/{len(offers_to_announce) + 2}] MENU ITEM {i}:")
            print(f"   Text: {offer[:70]}...")
            print(f"   Speaking now...")
            
            try:
                # Stop any previous speech first (important for pyttsx3)
                if self.tts_method == "pyttsx3" and hasattr(self, 'tts_engine') and self.tts_engine:
                    try:
                        self.tts_engine.stop()
                        time.sleep(0.2)  # Brief pause after stop
                    except:
                        pass
                
                # Speak the menu item without "Number N: " prefix (no number repetition)
                to_speak = offer.strip()
                if to_speak.lower().startswith("number ") and ": " in to_speak:
                    to_speak = to_speak.split(": ", 1)[1]
                self.speak(to_speak)
                
                # Verify TTS is still working
                if self.tts_method == "pyttsx3":
                    if not hasattr(self, 'tts_engine') or self.tts_engine is None:
                        print(f"   ⚠ WARNING: TTS engine lost after menu item {i}")
                        # Try to reinitialize
                        try:
                            import pyttsx3
                            self.tts_engine = pyttsx3.init()
                            # Reconfigure
                            self.tts_engine.setProperty('rate', self.config.get("tts_rate", 150))
                            self.tts_engine.setProperty('volume', self.config.get("tts_volume", 0.9))
                            print("   ✓ TTS engine reinitialized")
                        except Exception as e:
                            print(f"   ❌ Failed to reinitialize: {e}")
                            break
                
                print(f"   ✓ Menu item {i} spoken successfully")
                
            except Exception as e:
                print(f"   ❌ ERROR speaking menu item {i}: {e}")
                import traceback
                traceback.print_exc()
                # Try to continue with next item
                try:
                    if self.tts_method == "pyttsx3":
                        import pyttsx3
                        self.tts_engine = pyttsx3.init()
                except:
                    pass
                continue
            
            # Pause between items - ensure TTS finishes completely
            time.sleep(2.5)  # Increased pause to ensure speech completes
        
        # Menu choices: 1-4 = select item, 0 = repeat menu, 6 = cancel order
        prompt = "Say 1, 2, 3, or 4 for your choice. Say 0 to hear the menu again. Say 6 to cancel your order. I am listening now."
        print(f"\n[{len(offers_to_announce) + 2}/{len(offers_to_announce) + 2}] Speaking prompt...")
        self.speak(prompt)
        
        print("\n" + "="*70)
        print("✓ MENU ANNOUNCEMENT COMPLETE")
        print("="*70)
        print("Waiting for customer voice (say 1-4 to order, 0 to repeat, 6 to cancel)...\n")
    
    def get_customer_order(self) -> Dict[str, any]:
        """Capture customer's full order - recognizes any words/phrases"""
        max_attempts = 3
        order_text = None
        selected_offer = None
        
        for attempt in range(max_attempts):
            # Listen for full order with longer timeout
            response = self.listen(timeout=self.config.get("voice_timeout", 15.0), phrase_time_limit=30)
            
            if response is None:
                if attempt < max_attempts - 1:
                    self.speak("I didn't catch that. Could you please tell me your order again?")
                continue
            
            # Store the full order text
            order_text = response
            
            # Try to extract menu number if mentioned (for tracking)
            response_lower = response.lower()
            for i in range(1, len(self.special_offers) + 1):
                if str(i) in response_lower or self._number_to_word(i) in response_lower:
                    selected_offer = i
                    break
            
            # Confirm what we heard
            if attempt < max_attempts - 1:
                self.speak(f"I heard: {response}. Is that correct? Say yes to confirm, or tell me if you want to add anything else.")
                
                # Listen for confirmation or additions
                confirmation = self.listen(timeout=5.0, phrase_time_limit=15)
                if confirmation:
                    conf_lower = confirmation.lower()
                    if any(word in conf_lower for word in ["yes", "correct", "right", "that's it", "that's all"]):
                        # Customer confirmed, check if they want to add more
                        self.speak("Great! Is there anything else you'd like to add to your order?")
                        additional = self.listen(timeout=5.0, phrase_time_limit=15)
                        if additional:
                            add_lower = additional.lower()
                            if any(word in add_lower for word in ["no", "that's all", "nothing", "no thanks", "that's it"]):
                                break
                            else:
                                # Add to order
                                order_text += ". " + additional
                                break
                        break
                    elif any(word in conf_lower for word in ["no", "wrong", "change"]):
                        self.speak("No problem. Please tell me your order again.")
                        continue
                    else:
                        # They added something
                        order_text += ". " + confirmation
                        break
            else:
                break
        
        return {
            "full_order_text": order_text,
            "selected_offer": selected_offer,
            "order_phrases": order_text.split(". ") if order_text else []
        }
    
    def get_customer_order_simple(self) -> Dict[str, any]:
        """Simple flow: 1-5 = select item, 0 = repeat menu, 6 = cancel order. Timer starts when car on sensor (caller)."""
        menu_choices = 4
        max_repeats = 3
        for _ in range(max_repeats + 1):
            # Prompt already spoken by announce_offers; listen for choice
            response = self.listen(timeout=self.config.get("voice_timeout", 15.0), phrase_time_limit=30)
            order_text = response.strip() if response else None
            if not order_text:
                self.speak("Say 1, 2, 3, 4, or 5 to order. Say 0 to repeat the menu. Say 6 to cancel. I am listening now.")
                continue
            response_lower = order_text.lower().strip()
            # 0 = repeat menu
            if str(0) in response_lower or "zero" in response_lower or ("repeat" in response_lower and len(response_lower) < 15):
                self.speak("Repeating the menu.")
                self.announce_offers()
                continue
            # 6 = cancel order
            if str(6) in response_lower or "six" in response_lower:
                self.speak("Order cancelled.")
                return {
                    "full_order_text": None,
                    "selected_offer": None,
                    "order_phrases": [],
                    "car_number": None,
                    "order_id": None,
                    "cancelled": True,
                }
            # 1-5 = select menu item
            selected_offer = None
            for i in range(1, menu_choices + 1):
                if str(i) in response_lower or self._number_to_word(i) in response_lower:
                    selected_offer = i
                    break
            if selected_offer is None:
                self.speak("Say 1, 2, 3, 4, or 5 for your choice. Say 0 to hear the menu again. Say 6 to cancel. I am listening now.")
                continue
            self._car_number += 1
            car_num = self._number_to_word(self._car_number)
            self.speak(f"Order confirmed. Car number {car_num}.")
            offers = self.special_offers[:menu_choices] if self.special_offers else []
            order_display = offers[selected_offer - 1] if selected_offer and offers else order_text
            return {
                "full_order_text": order_display,
                "selected_offer": selected_offer,
                "order_phrases": [order_display],
                "car_number": self._car_number,
                "order_id": f"Car {self._car_number}",
                "cancelled": False,
            }
        return {
            "full_order_text": None,
            "selected_offer": None,
            "order_phrases": [],
            "car_number": None,
            "order_id": None,
            "cancelled": False,
        }
    
    def get_customer_order_continuous(self) -> Dict[str, any]:
        """Capture customer order using continuous listening - captures everything they say"""
        self.speak("Please tell me your complete order. You can take your time. Say 'done' or 'that's all' when you're finished.")
        
        # Listen continuously for full order
        phrases = self.listen_continuous(max_duration=60)
        
        if not phrases:
            self.speak("I didn't catch your order. Let me connect you with our team member.")
            return {
                "full_order_text": None,
                "selected_offer": None,
                "order_phrases": []
            }
        
        # Combine all phrases into full order
        full_order = ". ".join(phrases)
        
        # Try to extract menu number if mentioned
        selected_offer = None
        full_order_lower = full_order.lower()
        for i in range(1, len(self.special_offers) + 1):
            if str(i) in full_order_lower or self._number_to_word(i) in full_order_lower:
                selected_offer = i
                break
        
        # Confirm order
        self.speak(f"I captured your order. Let me repeat it back: {full_order}. Is that correct?")
        confirmation = self.listen(timeout=5.0)
        
        if confirmation:
            conf_lower = confirmation.lower()
            if any(word in conf_lower for word in ["no", "wrong", "change", "not quite"]):
                self.speak("No problem. Let me connect you with our team member who can help clarify your order.")
            else:
                self.speak("Perfect! I've captured your order.")
        
        # Optionally process order with Ollama for better understanding
        if self.use_ollama and self.ollama_client and full_order:
            try:
                processed_order = self._process_order_with_ollama(full_order)
                if processed_order:
                    full_order = processed_order
            except Exception as e:
                print(f"⚠ Ollama processing failed: {e}, using original order")
        
        return {
            "full_order_text": full_order,
            "selected_offer": selected_offer,
            "order_phrases": phrases
        }
    
    def _process_order_with_ollama(self, order_text: str) -> Optional[str]:
        """Process order text with Ollama for better understanding and formatting"""
        try:
            model_name = self.config.get("ollama_model", "llama2")
            
            prompt = f"""You are a drive-through order processing assistant. 
Extract and format the customer's order clearly. 
Customer said: "{order_text}"
Return only the formatted order, nothing else."""
            
            # Use Ollama client
            if self.ollama_client:
                response = self.ollama_client.generate(
                    model=model_name,
                    prompt=prompt
                )
                
                # Extract response text
                if isinstance(response, dict):
                    processed = response.get('response', '').strip()
                else:
                    processed = str(response).strip()
                
                if processed and processed.lower() != order_text.lower():
                    print(f"  [Ollama processed]: {processed}")
                    return processed
            return order_text
        except Exception as e:
            print(f"  ⚠ Ollama processing error: {e}")
            return order_text
    
    def _number_to_word(self, num: int) -> str:
        """Convert number to word for better recognition (0=repeat, 1-5=menu, 6=cancel)."""
        words = {
            0: "zero",
            1: "one", 2: "two", 3: "three", 4: "four",
            5: "five", 6: "six", 7: "seven", 8: "eight",
            9: "nine", 10: "ten"
        }
        return words.get(num, str(num))
    
    def handoff_to_operator(self, customer_id: str, order_data: Dict[str, any]):
        """Hand off to human operator with full order transcript; order displayed on screen, human prepares, car goes to pick-up."""
        if order_data.get("cancelled"):
            handoff_info = {"customer_id": customer_id, "cancelled": True, "full_order_text": None, "order_phrases": []}
            return handoff_info
        selected_offer = order_data.get("selected_offer")
        full_order_text = order_data.get("full_order_text", "")
        order_id = order_data.get("order_id") or customer_id
        car_number = order_data.get("car_number")
        
        handoff_info = {
            "customer_id": customer_id,
            "order_id": order_id,
            "car_number": car_number,
            "timestamp": datetime.now().isoformat(),
            "full_order_text": full_order_text,
            "order_phrases": order_data.get("order_phrases", []),
            "selected_offer": selected_offer,
            "offer_details": self.special_offers[selected_offer - 1] if selected_offer else None,
            "status": "ready_for_operator"
        }
        
        # Add to order queue
        self.order_queue.put(handoff_info)
        
        # Notify operator
        if self.config.get("operator_notification", True):
            self._notify_operator(handoff_info)
        
        # Inform customer: order on screen, human prepares, drive to pick-up to collect and pay
        if full_order_text:
            self.speak(f"Thank you! Your order is on the screen. Our team is preparing it. Please drive to the pick-up window to collect your order and pay.")
        else:
            self.speak("Please drive to the pick-up window. Our team will help you there.")
        
        print(f"\n{'='*60}")
        print(f"OPERATOR HANDOFF - Customer ID: {customer_id}")
        print(f"FULL ORDER TEXT: {full_order_text}")
        if selected_offer:
            print(f"Selected Offer Number: {selected_offer}")
        print(f"Order Phrases: {order_data.get('order_phrases', [])}")
        print(f"Timestamp: {handoff_info['timestamp']}")
        print(f"{'='*60}\n")
        
        return handoff_info
    
    def handoff_to_operator_simple(self, customer_id: str, order_data: Dict[str, any]):
        """Simple flow: if not cancelled, read back order in ORDER voice (different from menu), then hand off."""
        if order_data.get("cancelled"):
            return {"customer_id": customer_id, "cancelled": True, "full_order_text": None, "order_phrases": []}
        full_order_text = order_data.get("full_order_text") or "No order captured"
        self.speak_order("Your order is. " + full_order_text)
        return self.handoff_to_operator(customer_id, order_data)
    
    def _notify_operator(self, handoff_info: Dict):
        """Notify human operator with full order transcript"""
        # This could trigger:
        # - Visual alert on operator screen
        # - Sound notification
        # - Send to POS system
        # - Log to database
        
        print(f"\n🔔 OPERATOR NOTIFICATION 🔔")
        print(f"Order confirmed — {handoff_info.get('order_id', handoff_info['customer_id'])}")
        print(f"\n📝 ORDER (display on screen):")
        print(f"   {handoff_info.get('full_order_text', 'No order captured')}")
        if handoff_info.get('selected_offer'):
            print(f"\nSelected Special Offer: {handoff_info['offer_details']}")
        if handoff_info.get('order_phrases'):
            print(f"\nOrder Breakdown:")
            for i, phrase in enumerate(handoff_info['order_phrases'], 1):
                print(f"   {i}. {phrase}")
        print()
    
    def process_customer(self):
        """Process a single customer: trigger → read menu → listen → register order → read back order (different voice)."""
        customer_id = f"CUST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_customer = customer_id
        
        print(f"\n{'='*60}")
        print(f"NEW CUSTOMER: {customer_id}")
        print(f"{'='*60}\n")
        
        simple_flow = self.config.get("simple_flow", True)
        
        if simple_flow:
            # SIMPLE: 1. Read menu  2. Listen once  3. Register order  4. Read back order (different voice)
            self.announce_offers()
            order_data = self.get_customer_order_simple()
            handoff_info = self.handoff_to_operator_simple(customer_id, order_data)
        else:
            # Full flow (continuous listen, confirmations)
            self.announce_offers()
            use_continuous = self.config.get("use_continuous_listening", True)
            if use_continuous:
                order_data = self.get_customer_order_continuous()
            else:
                order_data = self.get_customer_order()
            handoff_info = self.handoff_to_operator(customer_id, order_data)
        
        self.current_customer = None
        return handoff_info
    
    def run(self):
        """Main loop - continuously monitors for car approach via loop detector"""
        self.running = True
        print("\n" + "="*60)
        print("KFC DRIVE-THROUGH SYSTEM STARTED")
        print("Monitoring loop detector for car approach...")
        if self.use_raspberry_pi and GPIO_AVAILABLE:
            print(f"Loop detector connected to GPIO pin {self.loop_pin}")
        else:
            print("Running in simulation mode")
        print("Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        car_detected = False
        
        try:
            while self.running:
                # Check for car approach
                if self.detect_car_approach():
                    if not car_detected:
                        # Car just arrived
                        car_detected = True
                        # Process customer
                        self.process_customer()
                        print("\nWaiting for car to leave detection zone...\n")
                else:
                    # Car has left or no car present
                    if car_detected:
                        car_detected = False
                        print("Car left detection zone. Ready for next customer.\n")
                    # No car detected, check again soon
                    time.sleep(0.2)
        
        except KeyboardInterrupt:
            print("\n\nShutting down KFC drive-through system...")
            self.running = False
        finally:
            if GPIO_AVAILABLE:
                GPIO.cleanup()
    
    def stop(self):
        """Stop the drive-through system"""
        self.running = False


def main():
    """Main entry point"""
    print("Initializing KFC Drive-Through System for Raspberry Pi...")
    
    # Create system instance
    system = DriveThruSystem()
    
    # Verify menu items are loaded
    if len(system.special_offers) == 0:
        print("\n⚠ WARNING: No menu items loaded from config.json!")
        print("The system will still work, but menu announcements will be skipped.")
        print("Please check that config.json contains 'special_offers' array.\n")
    
    # Start system
    system.run()


if __name__ == "__main__":
    main()
