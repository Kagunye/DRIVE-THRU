"""
Hardware Integration Examples
Replace the simulated detect_car_approach() with actual hardware interfaces
"""

# Example 1: Raspberry Pi GPIO Integration
"""
import RPi.GPIO as GPIO

class RaspberryPiLoopDetector:
    def __init__(self, pin_number=18):
        self.pin = pin_number
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    def detect_car(self):
        return GPIO.input(self.pin) == GPIO.HIGH
"""

# Example 2: Arduino Serial Communication
"""
import serial

class ArduinoLoopDetector:
    def __init__(self, port='COM3', baudrate=9600):
        self.serial = serial.Serial(port, baudrate)
    
    def detect_car(self):
        if self.serial.in_waiting > 0:
            data = self.serial.readline().decode().strip()
            return data == "CAR_DETECTED"
        return False
"""

# Example 3: Camera-based Detection (OpenCV)
"""
import cv2
import numpy as np

class CameraCarDetector:
    def __init__(self, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2()
    
    def detect_car(self):
        ret, frame = self.cap.read()
        if not ret:
            return False
        
        # Apply background subtraction
        fg_mask = self.background_subtractor.apply(frame)
        
        # Detect motion/objects
        contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # If large contour detected, car is present
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 5000:  # Threshold for car size
                return True
        
        return False
"""

# Example 4: Ultrasonic Sensor (Distance-based)
"""
import RPi.GPIO as GPIO
import time

class UltrasonicCarDetector:
    def __init__(self, trigger_pin=23, echo_pin=24):
        self.trigger = trigger_pin
        self.echo = echo_pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.trigger, GPIO.OUT)
        GPIO.setup(self.echo, GPIO.IN)
    
    def get_distance(self):
        GPIO.output(self.trigger, False)
        time.sleep(0.00001)
        GPIO.output(self.trigger, True)
        time.sleep(0.00001)
        GPIO.output(self.trigger, False)
        
        while GPIO.input(self.echo) == 0:
            pulse_start = time.time()
        
        while GPIO.input(self.echo) == 1:
            pulse_end = time.time()
        
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150  # Speed of sound
        return round(distance, 2)
    
    def detect_car(self, threshold_distance=50):
        distance = self.get_distance()
        return distance < threshold_distance  # Car within threshold
"""

# Example 5: Integration with drive_thru_system.py
"""
# In drive_thru_system.py, replace detect_car_approach() with:

from hardware_integration import RaspberryPiLoopDetector

class DriveThruSystem:
    def __init__(self, config_file: str = "config.json"):
        # ... existing code ...
        self.loop_detector = RaspberryPiLoopDetector(pin_number=18)
    
    def detect_car_approach(self) -> bool:
        return self.loop_detector.detect_car()
"""
