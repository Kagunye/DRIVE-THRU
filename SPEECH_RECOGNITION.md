# Speech Recognition Features

## Full Speech Recognition

The KFC Drive-Through System uses **Google Speech Recognition API** to capture and transcribe **ANY words or phrases** the customer says. The system does not limit customers to specific commands - it recognizes natural language.

## How It Works

### 1. **Natural Language Processing**
- Customers can speak naturally: "I'd like a chicken sandwich combo"
- No need for specific commands or keywords
- System captures complete sentences and phrases

### 2. **Continuous Listening Mode**
- System listens continuously for up to 60 seconds
- Captures multiple phrases until customer says "done" or "that's all"
- Handles pauses and interruptions naturally

### 3. **Order Capture**
- Full order transcript is saved
- All words and phrases are captured
- Order is broken down into phrases for operator review

## Example Customer Interactions

### Example 1: Simple Order
**Customer**: "I'll take a number 2 combo"
**System Captures**: "I'll take a number 2 combo"
**Operator Sees**: Full transcript with menu number identified

### Example 2: Complex Order
**Customer**: "I want two chicken sandwiches, one spicy and one regular, with large fries and two drinks, one Pepsi and one Sprite"
**System Captures**: Complete sentence with all details
**Operator Sees**: Full order breakdown

### Example 3: Multiple Phrases
**Customer**: 
- "Give me the family meal"
- "And add an extra side of coleslaw"
- "That's all"
**System Captures**: All phrases combined
**Operator Sees**: Complete order with all additions

## Configuration Options

In `config.json`:

```json
{
  "voice_timeout": 15.0,           // Timeout for single phrase listening
  "use_continuous_listening": true, // Enable continuous listening mode
  "max_order_duration": 60         // Maximum seconds for order capture
}
```

## Speech Recognition Settings

- **Language**: English (US) - `en-US`
- **Phrase Time Limit**: 30 seconds per phrase
- **Continuous Mode**: Up to 60 seconds total
- **Silence Detection**: Stops after 3 seconds of silence

## What Gets Captured

1. **Full Order Text**: Complete transcript of everything customer said
2. **Order Phrases**: Breakdown of order into individual phrases
3. **Menu Numbers**: Automatically identified if customer mentions numbers
4. **All Words**: Every word is captured and transcribed

## Operator Display

Operators see:
- Complete order transcript
- Individual phrases breakdown
- Identified menu numbers (if any)
- Timestamp and customer ID

## Troubleshooting

### If Speech Not Recognized
- Check internet connection (Google API requires internet)
- Ensure microphone is working: `arecord -d 5 test.wav`
- Speak clearly and reduce background noise
- Increase `voice_timeout` in config.json

### For Offline Recognition
Consider integrating:
- **Vosk** - Offline speech recognition
- **PocketSphinx** - Lightweight offline option
- **Azure Speech Services** - Cloud alternative
- **AWS Transcribe** - Enterprise solution

## Technical Details

- Uses `speech_recognition` library with Google API
- Supports natural language processing
- Handles accents and variations
- Works with any microphone input
- Real-time transcription display
