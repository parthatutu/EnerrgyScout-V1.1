import minimalmodbus
import serial
import time
import serial.rs485

# --- Configuration ---
PORT_NAME = '/dev/ttyAMA0'  # Check dmesg for your port name (e.g., ttyUSB0 or ttyAMA0 for GPIO UART)
SLAVE_ADDRESS = 3           # The Modbus ID of your device (decimal)
BAUDRATE = 9600             # Check your device manual for the correct baud rate
TIMEOUT = 0.5               # Seconds

# Define the starting register address for Voltage
# The documentation uses 0x0100 (hexadecimal), which is 256 in decimal
VOLTAGE_REGISTER_START = 256 
SCALE_FACTOR = 10000.0

# --- Setup Instrument ---
instrument = minimalmodbus.Instrument(PORT_NAME, SLAVE_ADDRESS)
instrument.serial.baudrate = BAUDRATE
instrument.serial.bytesize = 8
instrument.serial.parity = serial.PARITY_NONE
instrument.serial.stopbits = 1
instrument.serial.timeout = TIMEOUT
instrument.mode = minimalmodbus.MODE_RTU # Assuming RTU mode

instrument.serial.rs485_mode = serial.rs485.RS485Settings(
    rts_level_for_tx=True,
    rts_level_for_rx=False,
    loopback=False,
    delay_before_tx=0.0015,
    delay_before_rx=0.00005)

# Optional: Good practice for RS-485
instrument.close_port_after_each_call = True 
instrument.clear_buffers_before_each_transaction = True

# --- Read Data ---
try:
    # Read the 32-bit unsigned integer using read_long()
    # functioncode=3 is the default for 'read holding registers'
    # signed=False because the table says "Unsigned number"
    raw_value = instrument.read_long(
        VOLTAGE_REGISTER_START, 
        functioncode=3, 
        signed=False,
        number_of_registers=2 # Read two 16-bit registers
    )
    
    # Apply the scaling factor to get the actual voltage in Volts
    voltage = raw_value / SCALE_FACTOR
    
    print(f"Raw Value (32-bit unsigned int): {raw_value}")
    print(f"Voltage: {voltage} V")

except IOError as e:
    print(f"Error communicating with instrument: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
