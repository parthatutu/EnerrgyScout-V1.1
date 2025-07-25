from pymodbus.client import ModbusSerialClient as ModbusClient
import serial, time

# === MODBUS SETUP ===
client = ModbusClient(
    method="rtu",
    port="/dev/ttyUSB0",
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

while True:
    voltage = read_input_register(0x0008, 1)     # Voltage Phase A (scale: 0.1 V)
    current = read_input_register(0x0009, 100)    # Current Phase A (scale: 0.01 A)
    power   = read_input_register(0x000B, 10)     # Active Power Phase A (scale: 0.1 W)
    pf      = read_input_register(0x000A, 1000)   # Power Factor (scale: 0.001)

    if None not in (voltage, current, power, pf):
        print(f"Voltage: {voltage:.1f} V | Current: {current:.2f} A | Power: {power:.1f} W | PF: {pf:.3f}")
    else:
        print("⚠️ Failed to read one or more values.")

    time.sleep(1)
