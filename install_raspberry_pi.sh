#!/bin/bash
# Installation script for Raspberry Pi

echo "Installing KFC Drive-Through System on Raspberry Pi..."

# Update system
sudo apt-get update

# Install espeak for text-to-speech
sudo apt-get install -y espeak espeak-data libespeak1 libespeak-dev

# Install Python dependencies
pip3 install speechrecognition pyaudio RPi.GPIO

# Optional: Install pyttsx3 (may not work well on Pi, espeak is better)
pip3 install pyttsx3 || echo "pyttsx3 installation failed, using espeak instead"

# Install PyAudio dependencies
sudo apt-get install -y portaudio19-dev python3-pyaudio

echo ""
echo "Installation complete!"
echo ""
echo "To run the system:"
echo "  python3 drive_thru_system.py"
echo ""
echo "Make sure your loop detector is connected to GPIO pin 18 (or update config.json)"
