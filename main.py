from pymodbus.client import ModbusSerialClient as ModbusClient
import serial, time

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

def read_scaled(addr):
    result = client.read_holding_registers(addr, 2, slave=1)
    if result.isError():
        print(f"⚠️ Error reading {hex(addr)}")
        return None
    raw = (result.registers[0] << 16) | result.registers[1]
    return raw / 10000.0  # scaling per manual

while True:
    voltage = read_scaled(0x0100)  # Voltage
    current = read_scaled(0x0102)  # Current
    if voltage is not None and current is not None:
        print(f"Voltage: {voltage:.2f} V | Current: {current:.2f} A")
    time.sleep(2)
