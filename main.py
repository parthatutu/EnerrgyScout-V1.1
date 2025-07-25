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
    print("? Could not connect to JSY-MK-231.")
    exit()

CURRENT_SCALE = 0.1  # Adjusted scaling factor

def read_scaled(addr):
    """Read 2 registers (32-bit) and scale /10000."""
    result = client.read_holding_registers(addr, 2, slave=1)
    if result.isError():
        return None
    raw = (result.registers[0] << 16) | result.registers[1]
    return raw / 10000.0

# === MAIN LOOP ===
while True:
    voltage = read_scaled(0x0100)  # Voltage
    time.sleep(0.15)  # <-- Small gap to let device settle
    current_raw = read_scaled(0x0102)  # Current
    
    if voltage is not None and current_raw is not None:
        current = current_raw * CURRENT_SCALE
        print(f"Voltage: {voltage:.3f} V | Current: {current:.4f} A")
    else:
        print("?? Read failed.")
    
    time.sleep(2)  # Main loop delay

