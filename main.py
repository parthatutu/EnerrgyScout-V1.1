import serial
from pymodbus.client import ModbusSerialClient as ModbusClient

# === MODBUS SETUP ===
client = ModbusClient(
    method="rtu",
    port="/dev/ttyUSB0",   # Change if needed
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=2
)

if not client.connect():
    print("❌ Could not connect to JSY-MK-231. Check wiring/port.")
    exit(1)

def read_parameter(addr):
    """Read a 32-bit unsigned value (2 registers) and scale as per manual."""
    result = client.read_input_registers(addr, 2, slave=1)  # device default address =1
    if result.isError():
        print(f"⚠️ Error reading register {hex(addr)}")
        return None
    raw = (result.registers[0] << 16) | result.registers[1]
    return raw / 10000.0

# === TEST LOOP ===
while True:
    voltage = read_parameter(0x0100)  # DC Voltage
    current = read_parameter(0x0102)  # DC Current

    if voltage is not None and current is not None:
        print(f"DC Voltage: {voltage:.2f} V, DC Current: {current:.2f} A")
    else:
        print("⚠️ Failed to read parameters.")

    import time
    time.sleep(2)
