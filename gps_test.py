import serial
import time
import os

# --- CONFIGURATION ---
GPS_PORT = '/dev/ttyAMA2' 
BAUDRATE = 9600
FIX_PIN = 23

print("--- Initializing GPS Test (GPIO 12 Reset Mode) ---")

# Force reset the pin to Input using the system tool to bypass 'Busy' errors
os.system(f"sudo pinctrl set {FIX_PIN} ip pu")

# Use a lighter way to check the pin since RPi.GPIO is struggling
from gpiozero import InputDevice
try:
    fix_pin = InputDevice(FIX_PIN, pull_up=True)
    print(f"GPIO {FIX_PIN} claimed successfully.")
except Exception as e:
    print(f"Could not claim GPIO {FIX_PIN} via Python: {e}")
    print("Will attempt to read serial data anyway...")
    fix_pin = None

# Initialize Serial
try:
    ser = serial.Serial(GPS_PORT, BAUDRATE, timeout=1)
    ser.reset_input_buffer()
    print(f"Connected to {GPS_PORT}. Waiting for data...\n")
except Exception as e:
    print(f"Serial Error: {e}")
    exit()

# Main Loop
try:
    while True:
        # Check Fix Status
        status_label = "UNKNOWN"
        if fix_pin:
            # value 0 = Fix (LED slow/off), value 1 = No Fix (LED pulsing)
            status_label = "SEARCHING" if fix_pin.value == 1 else "FIX OK"

        if ser.in_waiting > 0:
            try:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if "$GP" in line:
                    print(f"[{status_label}] {line}")
            except Exception as e:
                print(f"Data Error: {e}")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping...")
finally:
    ser.close()
