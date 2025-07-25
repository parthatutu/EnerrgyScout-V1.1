import serial
from pymodbus.client import ModbusSerialClient as ModbusClient
import struct
import time
from datetime import datetime

# === CONFIG ===
client = ModbusClient(
    method="rtu",
    port="/dev/ttyUSB0",
    baudrate=9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)
log_file = "/home/miyatakeuchi/battery_log.txt"

# === HELPERS ===
def log_data(data):
    with open(log_file, "a") as f:
        f.write(data + "\n")

def read_float_register(addr, retries=3):
    """Reads a 32-bit float (2 registers) with retry."""
    for _ in range(retries):
        try:
            rr = client.read_input_registers(addr, 2, slave=1)
            if not rr.isError():
                return struct.unpack('>f', struct.pack('>HH', *rr.registers))[0]
        except Exception as e:
            print(f"⚠️ Error reading 0x{addr:04X}: {e}")
        time.sleep(0.1)  # small delay before retry
    return None

# === MAIN LOOP ===
while True:
    # Ensure connection
    if not client.is_socket_open():
        if not client.connect():
            print("❌ Could not connect.")
            time.sleep(2)
            continue

    # Read parameters (addresses from your doc)
    voltage = read_float_register(0x0004)        # Voltage
    current = read_float_register(0x000A)        # Current
    power_factor = read_float_register(0x001E)   # Power factor
    total_pf = read_float_register(0x003E)       # Total PF
    total_thd = read_float_register(0x00FA)      # Total line THD

    if None not in (voltage, current, power_factor, total_pf, total_thd):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = (f"{timestamp}, Voltage: {voltage:.2f} V, Current: {current:.2f} A, "
                f"PF: {power_factor:.3f}, Total PF: {total_pf:.3f}, THD: {total_thd:.2f}%")
        print(data)
        log_data(data)
    else:
        print("⚠️ One or more parameters failed to read.")

    time.sleep(5)
