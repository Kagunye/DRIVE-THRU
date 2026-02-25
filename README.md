# KFC Drive-Through System

An automated drive-through ordering system for KFC that detects car approach via inductive loop detector, announces special menu items via voice, captures customer selections, and hands off to human operators.

## Try the car simulation in your browser

**→ [Open the Car Simulation](https://kagunye.github.io/DRIVE-THRU/)**

When you open the link above you’ll see the **car simulation**: the drive-thru lane, loop sensor, speaker, base station, and order flow. Click **START — Full run** to watch the car move from the sensor through ordering to pick-up.

**If you get a 404:** GitHub Pages might not be enabled yet. Go to the repo **Settings → Pages**, set **Source** to **Deploy from a branch**, choose branch **main** and folder **/ (root)**, then Save. Wait 1–2 minutes and try the link again. See **[GITHUB_PAGES_SETUP.md](GITHUB_PAGES_SETUP.md)** for step-by-step instructions.

---

## Features

- **Raspberry Pi GPIO Integration**: Reads inductive loop detector for car detection
- **Voice Announcements**: Announces KFC special menu items using espeak (Raspberry Pi compatible)
- **Voice Recognition**: Captures customer voice selections
- **Operator Handoff**: Seamlessly transfers to human operator after selection
- **Order Queue**: Tracks pending orders for operators

## Hardware Requirements

- Raspberry Pi (3B+ or newer recommended)
- Inductive loop detector connected to GPIO pin 18 (configurable)
- USB microphone or 3.5mm microphone input
- Speaker or audio output device

## Installation

### On Windows

```bash
# Install dependencies
pip install -r requirements.txt

# Windows SAPI support (recommended for Windows)
pip install pywin32
```

The system will automatically use Windows SAPI (via win32com) if available, which is more reliable than pyttsx3 on Windows.

### On Raspberry Pi

1. **Clone or download this repository**

2. **Run the installation script:**
```bash
chmod +x install_raspberry_pi.sh
./install_raspberry_pi.sh
```

Or install manually:
```bash
# Update system
sudo apt-get update

# Install espeak (text-to-speech)
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Install Python dependencies
pip3 install speechrecognition pyaudio RPi.GPIO

# Install PyAudio dependencies
sudo apt-get install -y portaudio19-dev python3-pyaudio
```

## Configuration

Edit `config.json` to customize:
- KFC special menu items
- GPIO pin number for loop detector (default: 18)
- Voice timeout settings
- Detection intervals

## Usage

### Testing

Run the comprehensive test to verify installation:

```bash
python test.py
```

This will test:
- System initialization
- Menu loading
- TTS initialization and audio output
- Menu announcement
- Voice recognition (optional)
- Full system simulation (optional)

### Running the System

```bash
python3 drive_thru_system.py
```

The system will:
1. Initialize GPIO and loop detector
2. Calibrate microphone
3. Start monitoring for car approach
4. When car detected: announce menu → listen for selection → handoff to operator

### Testing Without Hardware

Use the simulation script:

```bash
python3 simulate_loop.py
```

Then press ENTER to simulate a car approach and trigger the menu announcement.

Or run the **full car simulation** (visual drive-thru with lane, sensor, and order flow):

```bash
python3 car_simulation.py
```

Click **START — Full run** to see the car move through the drive-thru.

### System Flow

1. **Loop Detection**: System continuously monitors GPIO pin for car detection
2. **Menu Announcement**: When car approaches, system greets customer and announces KFC special menu
3. **Voice Capture**: System listens for customer selection (numbers 1-6 or "none")
4. **Operator Handoff**: System notifies operator and adds order to queue
5. **Human Ordering**: Operator takes over for full order processing

## GPIO Setup

### Wiring the Loop Detector

Connect your inductive loop detector to:
- **GPIO Pin 18** (default, configurable in config.json)
- **Ground (GND)**
- **3.3V or 5V** (depending on your detector)

The system reads the GPIO pin - HIGH signal means car detected.

### Testing Without Hardware

If you don't have hardware yet, the system will run in simulation mode. You can manually trigger by modifying the code temporarily or wait for GPIO integration.

## Voice Recognition

The system recognizes **ANY words or phrases** the customer says. Customers can:

- **Speak naturally**: "I'd like a number 2 combo and a large drink"
- **Place full orders**: "Give me two chicken sandwiches, fries, and a Pepsi"
- **Add modifications**: "I want the zinger burger but make it spicy"
- **Order multiple items**: "I'll take the family meal and add an extra side of coleslaw"
- **Use any words**: The system captures everything the customer says

The system uses Google Speech Recognition which recognizes natural language and any words/phrases. The full order transcript is passed to the operator.

## Troubleshooting

### Microphone Not Working
- Check microphone permissions: `sudo usermod -a -G audio $USER`
- Test microphone: `arecord -d 5 test.wav && aplay test.wav`
- Ensure microphone is set as default input device

### Speech Recognition Errors
- Requires internet connection (uses Google Speech API)
- Speak clearly and reduce background noise
- Increase `voice_timeout` in config.json if needed
- Check microphone levels: `alsamixer`

### GPIO Not Working
- Ensure RPi.GPIO is installed: `pip3 install RPi.GPIO`
- Check GPIO pin number in config.json matches your wiring
- Verify loop detector is working: `gpio readall` (if installed)

### TTS Not Speaking
- Ensure espeak is installed: `sudo apt-get install espeak`
- Test espeak: `espeak "Hello, this is a test"`
- Check audio output: `aplay /usr/share/sounds/alsa/Front_Left.wav`

## KFC Menu Items

The system is configured with 4 KFC specials (edit `config.json` to change):

1. Streetwise 2 plus coleslaw — 350 KES  
2. Mango crusher — 450 KES  
3. Zinger burger with 350ml coke — 500 KES  
4. Speak to Cashier  

Customize these in `config.json`.

## Order Queue

Orders are stored in an internal queue and displayed in the console when customers are processed. Each order includes:
- Customer ID (timestamp-based)
- Selected menu item
- Timestamp
- Status

## License

MIT License - Feel free to modify and use for your KFC drive-through system.
