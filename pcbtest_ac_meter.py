import minimalmodbus
import serial
import time

# --- CONFIGURATION ---
PORT = '/dev/ttyAMA0'
SLAVE_ID = 1  
BAUDRATE = 9600 # Use 4800 if you switched the whole system speed

instrument = minimalmodbus.Instrument(PORT, SLAVE_ID)
instrument.serial.baudrate = BAUDRATE
instrument.serial.timeout = 1.0

# --- RS485 TIMING (Required for your GPIO 17 setup) ---
instrument.serial.rs485_mode = serial.rs485.RS485Settings(
    rts_level_for_tx=True, 
    rts_level_for_rx=False,
    loopback=False,
    delay_before_tx=0.01,
    delay_before_rx=0.01
)

def read_line3_voltage():
    try:
        # Register 4 = Phase 3 (Line 3) Voltage
        # functioncode 4 is critical for SDM630
        v3 = instrument.read_float(4, functioncode=4, number_of_registers=2)
        
        print(f"L3 Voltage: {v3:.2f} V")
        return v3

    except Exception as e:
        print(f"Error reading L3: {e}")
        return None

if _name_ == "_main_":
    read_line3_voltage()
