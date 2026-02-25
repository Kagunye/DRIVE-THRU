# Voice-Only Drive-Through System

## ✅ System Overview

This is a **100% VOICE-BASED** drive-through ordering system. Everything is done through voice - no keyboard, mouse, or screen interaction required for customers.

## 🎤 Voice Features

### 1. **Voice Output (TTS)**
- ✅ All menu items are **SPOKEN** aloud
- ✅ All prompts and confirmations are **SPOKEN**
- ✅ Uses Windows SAPI (Windows) or espeak (Linux/Raspberry Pi)
- ✅ Female voice (Kenyan preference if available)
- ✅ Clear, natural speech

### 2. **Voice Input (Speech Recognition)**
- ✅ Listens continuously for customer speech
- ✅ Captures **ANY words** the customer says
- ✅ Uses Whisper (better accuracy) or Google Speech Recognition
- ✅ No keyboard input required
- ✅ Natural language understanding

### 3. **Complete Voice Flow**

```
1. Car Detected (Loop Trigger)
   ↓
2. SYSTEM SPEAKS: "Welcome to KFC drive-through..."
   ↓
3. SYSTEM SPEAKS: Menu items (all 6 items)
   ↓
4. SYSTEM SPEAKS: "Please tell me what you'd like to order..."
   ↓
5. SYSTEM LISTENS: Customer speaks their order
   ↓
6. SYSTEM SPEAKS: Confirmation or clarification
   ↓
7. SYSTEM LISTENS: Customer responds
   ↓
8. SYSTEM SPEAKS: "Thank you! Team member will take your order..."
   ↓
9. Handoff to Human Operator
```

## 🎯 Key Features

### Voice-Only Interaction
- ✅ **No typing required** - everything is spoken
- ✅ **No buttons to press** - voice commands only
- ✅ **Natural conversation** - speak normally
- ✅ **Continuous listening** - system always ready to hear

### Smart Listening
- ✅ **Immediate response** - starts listening as soon as prompted
- ✅ **Sensitive microphone** - picks up speech quickly
- ✅ **Long timeouts** - gives customers time to think
- ✅ **Multiple attempts** - retries if speech not understood

### Accurate Recognition
- ✅ **Whisper integration** - better accuracy than Google
- ✅ **Any language/accent** - understands natural speech
- ✅ **Full sentences** - captures complete orders
- ✅ **Error handling** - graceful fallbacks

## 📋 System Capabilities

### What Customers Can Say:
- ✅ "I'll take a number 2 combo"
- ✅ "Give me two chicken sandwiches and fries"
- ✅ "I want the family meal"
- ✅ "Number 3 please"
- ✅ "That's all" or "Done" to finish
- ✅ **ANY natural language** - system understands it all

### What System Does:
- ✅ **Speaks** menu items clearly
- ✅ **Listens** for complete orders
- ✅ **Confirms** what it heard
- ✅ **Captures** everything customer says
- ✅ **Hands off** to operator with full transcript

## 🔧 Configuration

All voice settings in `config.json`:

```json
{
  "voice_timeout": 15.0,              // How long to listen
  "use_continuous_listening": true,    // Continuous mode
  "use_ollama_whisper": true,         // Better accuracy
  "whisper_model": "base",            // Model size
  "tts_rate": 150,                    // Speech speed
  "tts_volume": 0.9                    // Volume level
}
```

## 🚀 Usage

### No Keyboard – Voice Only
- **Simulation mode**: Run `python simulate_loop.py`
  - Say **"hello"** or **"start"** to begin (like a car at the loop)
  - Say **"goodbye"** or **"exit"** to quit
  - Do not type or press ENTER; everything is voice.
- **Test**: Run `python test.py` – all prompts are spoken, you answer by voice only.

### For Customers (at drive-through):
1. **Drive up** - Loop detector triggers system (or say "hello" in simulation)
2. **Listen** - System speaks menu
3. **Speak** - Tell system your order
4. **Confirm** - Answer system's questions by voice
5. **Done** - System hands off to operator

### For Operators:
- View order transcript in console
- See full customer conversation
- Take over for detailed ordering

## ✨ Benefits

- 🎤 **100% Voice** - No typing or buttons
- 🎯 **Accurate** - Whisper for better recognition
- 🌍 **Natural** - Understands any way of speaking
- ⚡ **Fast** - Immediate listening response
- 🔄 **Reliable** - Multiple fallbacks

## 🎉 Perfect For:

- Drive-through restaurants
- Hands-free ordering
- Multi-language support
- Natural conversation flow
- Customer convenience

---

**The system is COMPLETELY VOICE-BASED - customers never need to touch anything!**
