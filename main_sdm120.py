import minimalmodbus
import serial
import serial.rs485 
import time

# --- CONFIGURATION ---
MODBUS_PORT  = '/dev/ttyAMA0'
GPS_PORT     = '/dev/ttyAMA2' 
BAUD_MODBUS  = 9600
BAUD_GPS     = 9600
GPS_INTERVAL = 1800  # 30 minutes

# --- INSTRUMENT SETUP ---
def setup_modbus(slave_id):
    try:
        ins = minimalmodbus.Instrument(MODBUS_PORT, slave_id)
        ins.serial.baudrate = BAUD_MODBUS
        ins.serial.timeout = 0.5
        ins.mode = minimalmodbus.MODE_RTU
        ins.serial.rs485_mode = serial.rs485.RS485Settings(
            rts_level_for_tx=True, rts_level_for_rx=False,
            delay_before_tx=0.01, delay_before_rx=0.01
        )
        return ins
    except: return None

meters = [
    {"id": 4, "name": "AC Meter (SDM120)", "type": "sdm120", "obj": setup_modbus(4)},
    {"id": 2, "name": "DC Meter 1", "type": "dc", "obj": setup_modbus(2)},
    {"id": 3, "name": "DC Meter 2", "type": "dc", "obj": setup_modbus(3)}
]

def parse_nmea_to_decimal(value, direction):
    if not value or not direction: return None
    float_val = float(value)
    degrees = int(float_val / 100)
    minutes = float_val - (degrees * 100)
    decimal = degrees + (minutes / 60)
    if direction in ['S', 'W']: decimal *= -1
    return round(decimal, 6)

def get_gps_location():
    print(f"\n[GPS] Attempting location from {GPS_PORT}...")
    try:
        with serial.Serial(GPS_PORT, BAUD_GPS, timeout=2) as ser:
            start_search = time.time()
            while time.time() - start_search < 5:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line.startswith("$GPRMC"):
                    parts = line.split(',')
                    if len(parts) > 6 and parts[2] == 'A':
                        lat = parse_nmea_to_decimal(parts[3], parts[4])
                        lon = parse_nmea_to_decimal(parts[5], parts[6])
                        return f"LAT: {lat}, LON: {lon}"
                    elif len(parts) > 2 and parts[2] == 'V':
                        return "NO FIX"
            return "TIMEOUT"
    except Exception as e: return f"SERIAL ERROR: {e}"

# --- MAIN EXECUTION ---
last_gps_time = 0 
print("System Started. Polling SDM120 and DC Meters...")

try:
    while True:
        current_time = time.time()

        # 1. GPS UPDATE
        if current_time - last_gps_time >= GPS_INTERVAL:
            location_result = get_gps_location()
            print(f">>> GPS: {location_result}")
            last_gps_time = current_time

        # 2. METER POLLING
        for m in meters:
            if m["obj"] is None: continue
            
            print(f"\n--- {m['name']} (Slave {m['id']}) ---")
            meter_start = time.time()
            
            while time.time() - meter_start < 5:
                try:
                    if m["type"] == "sdm120":
                        # Updated SDM120 Register Addresses (Function Code 04)
                        # Voltage: Hex 0000 (Dec 0) 
                        # Current: Hex 0006 (Dec 6) 
                        # Active Power: Hex 000C (Dec 12) 
                        v = m["obj"].read_float(0, functioncode=4)
                        a = m["obj"].read_float(6, functioncode=4)
                        p = m["obj"].read_float(12, functioncode=4)
                        print(f"AC -> {v:.1f}V | {a:.2f}A | {p:.1f}W")
                    
                    else:
                        # DC Meter Logic (Unchanged)
                        raw_v = m["obj"].read_long(256, functioncode=3)
                        print(f"DC -> {raw_v/10000.0:.2f}V")
                        
                except Exception as e:
                    print(f"{m['name']} Error: {e}")
                
                time.sleep(1)

except KeyboardInterrupt:
    print("\nShutting down.")
