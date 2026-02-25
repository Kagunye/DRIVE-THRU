# Quick Start Guide - KFC Drive-Through System for Raspberry Pi

## Installation on Raspberry Pi

1. **Update system:**
```bash
sudo apt-get update
```

2. **Run installation script:**
```bash
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh
```

Or install manually:
```bash
# Install espeak (text-to-speech)
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Install Python dependencies
pip3 install speechrecognition pyaudio RPi.GPIO

# Install PyAudio dependencies
sudo apt-get install -y portaudio19-dev python3-pyaudio
```

## Hardware Setup

1. **Connect Loop Detector:**
   - Connect to GPIO pin 18 (default, configurable)
   - Connect ground (GND)
   - Connect power (3.3V or 5V depending on detector)

2. **Connect Microphone:**
   - USB microphone or 3.5mm microphone input
   - Test with: `arecord -d 5 test.wav && aplay test.wav`

3. **Connect Speaker:**
   - USB speaker or 3.5mm audio output
   - Test with: `espeak "Hello, this is a test"`

## Running the System

### Production Mode (with hardware)

```bash
python3 drive_thru_system.py
```

The system will:
- Initialize GPIO and loop detector
- Calibrate microphone
- Start monitoring for car approach
- When car detected: announce KFC menu → listen for selection → handoff to operator

### Testing Without Hardware

Use the simulation script:
```bash
python3 simulate_loop.py
```

Then press ENTER to simulate car approach, or type 'test' for automated test.

## Testing

Run the test script to verify installation:
```bash
python3 test_system.py
```

## Configuration

Edit `config.json` to customize:
- KFC special menu items (6 items pre-configured)
- GPIO pin number for loop detector (default: 18)
- Voice timeout settings
- Detection intervals

## System Flow

1. **Loop Detection** → GPIO pin detects car in drive-through loop
2. **Menu Announcement** → System speaks KFC welcome and special menu items
3. **Voice Capture** → System listens for customer selection (1-6 or "none")
4. **Operator Handoff** → System notifies operator and adds to queue
5. **Human Ordering** → Operator takes over for full order processing

## Voice Commands

When prompted, customers can say:
- **"One"** or **"1"** → Select menu item 1
- **"Two"** or **"2"** → Select menu item 2
- **"Three"** or **"3"** → Select menu item 3
- **"Four"** or **"4"** → Select menu item 4
- **"Five"** or **"5"** → Select menu item 5
- **"Six"** or **"6"** → Select menu item 6
- **"None"** or **"No"** → Skip specials, go to regular menu

## Troubleshooting

### Microphone Not Working
- Check permissions: `sudo usermod -a -G audio $USER` (then logout/login)
- Test microphone: `arecord -d 5 test.wav && aplay test.wav`
- Check levels: `alsamixer`
- Ensure microphone is set as default input device

### Speech Recognition Errors
- Requires internet connection (uses Google Speech API)
- Speak clearly and reduce background noise
- Increase `voice_timeout` in config.json if needed
- Check microphone is working first

### TTS Not Speaking
- Ensure espeak is installed: `sudo apt-get install espeak`
- Test espeak: `espeak "Hello, this is a test"`
- Check audio output: `aplay /usr/share/sounds/alsa/Front_Left.wav`

### GPIO Not Working
- Ensure RPi.GPIO is installed: `pip3 install RPi.GPIO`
- Check GPIO pin number in config.json matches your wiring
- Verify loop detector is working
- Check wiring connections

## KFC Menu Items

The system comes with 6 pre-configured KFC special menu items:
1. Original Recipe Chicken Combo
2. Famous Bowl Combo
3. 8 Piece Family Meal
4. Chicken Sandwich Combo
5. Popcorn Nuggets Combo
6. Zinger Burger Combo

Customize these in `config.json`.

## Next Steps

1. Wire up your loop detector to GPIO pin 18
2. Test microphone and speaker
3. Customize KFC menu items in `config.json`
4. Run system and test with real customers
5. Connect to POS system (optional)
