from pymodbus.client import ModbusSerialClient as ModbusClient
import serial, time

# === MODBUS SETUP ===
client = ModbusClient(
    method="rtu",
    port="/dev/ttyUSB0",        # Update with your COM port
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=2
)

if not client.connect():
    print("❌ Could not connect.")
    exit()

def read_input_register(addr, scale=1):
    try:
        rr = client.read_input_registers(addr, 1, slave=1)  # Function code 04
        if rr.isError():
            print(f"⚠️ Read error at 0x{addr:04X}")
            return None
        value = rr.registers[0]
        return value / scale
    except Exception as e:
        print(f"Error reading 0x{addr:04X}: {e}")
        return None

def toggle_breaker(address, state):
    try:
        # Write command to control the breaker (True = on, False = off)
        rr = client.write_coil(address, state, slave=1)  # state: True for on, False for off
        if rr.isError():
            print(f"⚠️ Failed to toggle breaker at 0x{address:04X}")
        else:
            print(f"✅ Breaker {'on' if state else 'off'} at 0x{address:04X}")
    except Exception as e:
        print(f"Error writing to 0x{address:04X}: {e}")

# Example: Continuously toggle the breaker on and off
while True:
    voltage = read_input_register(0x0008, 1)     # Voltage Phase A (scale: 0.1 V)
    current = read_input_register(0x0009, 100)    # Current Phase A (scale: 0.01 A)
    power   = read_input_register(0x000B, 10)     # Active Power Phase A (scale: 0.1 W)
    pf      = read_input_register(0x000A, 1000)   # Power Factor (scale: 0.001)

    if None not in (voltage, current, power, pf):
        print(f"Voltage: {voltage:.1f} V | Current: {current:.2f} A | Power: {power:.1f} W | PF: {pf:.3f}")
    else:
        print("⚠️ Failed to read one or more values.")
    
    # Toggle the breaker between on and off
    toggle_breaker(0x0001, True)   # Turn on the breaker (change address if needed)
    time.sleep(2)                  # Wait for 2 seconds
    toggle_breaker(0x0001, False)  # Turn off the breaker
    time.sleep(2)                  # Wait for 2 seconds before toggling again
