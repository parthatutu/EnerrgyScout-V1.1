import serial
import RPi.GPIO as GPIO
import time

# GPIO Pin for RS485 DE/RE control (change if needed)
RS485_CONTROL_PIN = 18 

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RS485_CONTROL_PIN, GPIO.OUT)
GPIO.output(RS485_CONTROL_PIN, GPIO.LOW) # Start in receive mode

# Configure Serial Port
ser = serial.Serial(
    port='/dev/serial0', 
    baudrate=9600, 
    bytesize=serial.EIGHTBITS, 
    parity=serial.PARITY_NONE, 
    stopbits=serial.STOPBITS_ONE, 
    timeout=1
)

def send_data(data_to_send):
    GPIO.output(RS485_CONTROL_PIN, GPIO.HIGH) # Enable transmit (DE=HIGH)
    time.sleep(0.01) # Short delay for transceiver to switch
    ser.write(data_to_send.encode())
    time.sleep(0.01) # Short delay after sending
    GPIO.output(RS485_CONTROL_PIN, GPIO.LOW)  # Disable transmit (DE=LOW)

def read_data():
    # Check if data is available to read
    if ser.in_waiting > 0:
        return ser.read(ser.in_waiting).decode()
    return None

# --- Example Usage ---
try:
    print("Starting RS-485 communication...")
    send_data("Hello RS-485!")
    time.sleep(2) # Wait for potential response
    
    received = read_data()
    if received:
        print(f"Received: {received}")
    else:
        print("No data received.")

except KeyboardInterrupt:
    print("Exiting program.")
