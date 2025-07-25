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

def read_param(start_addr, count, scale):
    try:
        rr = client.read_holding_registers(start_addr, count, unit=1)
        if rr.isError():
            return None
        raw = (rr.registers[0] << 16) + rr.registers[1]
        return raw / scale
    except Exception as e:
        print(f"Error reading 0x{start_addr:04X}: {e}")
        return None

while True:
    voltage = read_param(0x0100, 2, 10000)       # Voltage in V
    current = read_param(0x0102, 2, 10000)       # Current in A
    power   = read_param(0x0104, 2, 10000)       # Power in W
    pf      = read_param(0x010A, 2, 1000)        # Power Factor

    if voltage is not None and current is not None and power is not None and pf is not None:
        print(f"Voltage: {voltage:.2f} V | Current: {current:.2f} A | Power: {power:.2f} W | PF: {pf:.3f}")
    else:
        print("⚠️ Read failed for one or more parameters.")

    time.sleep(1)
