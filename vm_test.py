import minimalmodbus
import serial
import serial.rs485 
import time
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# --- INFLUXDB CLOUD CONFIGURATION ---
INFLUX_URL = "https://us-east-1-1.aws.cloud2.influxdata.com"
INFLUX_TOKEN = "qsGKuJsL9po_6rsu8VpoLmspiyWfcvQRK2oCpu2Vht6je5_aYJMk16YKAci0cQB2Jn0-3hpkScs6KtBLJUZEVw=="  # Replace with your actual token
INFLUX_ORG = "Atutu"
INFLUX_BUCKET = "power-monitoring"

# Initialize InfluxDB Client
influx_client = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx_client.write_api(write_options=SYNCHRONOUS)

# --- MODBUS CONFIGURATION ---
MODBUS_PORT  = '/dev/ttyAMA0'
GPS_PORT     = '/dev/ttyAMA2'
BAUD_MODBUS  = 9600
BAUD_GPS     = 9600
GPS_INTERVAL = 1800  # 30 minutes (1800 seconds)

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
    except: 
        return None

meters = [
    {"id": 4, "name": "AC Meter", "type": "ac", "obj": setup_modbus(4)},
    {"id": 2, "name": "DC Meter 1", "type": "dc", "obj": setup_modbus(2)},
    {"id": 3, "name": "DC Meter 2", "type": "dc", "obj": setup_modbus(3)}
]

def parse_nmea_to_decimal(value, direction):
    """Converts DDMM.MMMM to Decimal Degrees"""
    if not value or not direction: 
        return None
    float_val = float(value)
    degrees = int(float_val / 100)
    minutes = float_val - (degrees * 100)
    decimal = degrees + (minutes / 60)
    if direction in ['S', 'W']:
        decimal *= -1
    return round(decimal, 6)

def get_gps_location():
    """Returns GPS coordinates as a tuple (lat, lon) or (None, None)"""
    print(f"\n[GPS] Attempting to acquire location from {GPS_PORT}...")
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
                        print(f">>> GPS UPDATE: LAT: {lat}, LON: {lon}")
                        return lat, lon
                    elif len(parts) > 2 and parts[2] == 'V':
                        print(">>> GPS UPDATE: NO FIX (Satellite Search in Progress)")
                        return None, None
            print(">>> GPS UPDATE: TIMEOUT (No Data on Serial)")
            return None, None
    except Exception as e:
        print(f">>> GPS UPDATE: ERROR - {e} (continuing without GPS)")
        return None, None

def send_to_influxdb(meter_name, voltage, latitude=None, longitude=None):
    """Send meter reading to InfluxDB Cloud"""
    try:
        point = Point("power_meter") \
            .tag("meter", meter_name) \
            .field("voltage", voltage)
        
        # Add GPS coordinates if available
        if latitude is not None and longitude is not None:
            point.field("latitude", latitude)
            point.field("longitude", longitude)
        
        write_api.write(bucket=INFLUX_BUCKET, record=point)
        print(f"✓ Data sent to InfluxDB: {meter_name} = {voltage:.2f}V")
    except Exception as e:
        print(f"✗ InfluxDB Error: {e}")

# --- MAIN EXECUTION ---
last_gps_time = 0 
current_lat = None
current_lon = None

print("System Started. Entering Polling Loop...")
print(f"Sending data to InfluxDB Cloud at: {INFLUX_URL}")
print("NOTE: System will continue running even if GPS or individual meters fail")

try:
    while True:
        current_time = time.time()
        
        # 1. GPS UPDATE (Every 30 Minutes) - Non-blocking, continues on error
        if current_time - last_gps_time >= GPS_INTERVAL:
            try:
                current_lat, current_lon = get_gps_location()
            except Exception as e:
                print(f">>> GPS UPDATE: Unexpected error - {e} (continuing without GPS)")
                current_lat, current_lon = None, None
            last_gps_time = current_time
        
        # 2. METER POLLING (5 Seconds per meter) - Each meter independent
        for m in meters:
            if m["obj"] is None: 
                print(f"\n--- Skipping {m['name']} (Slave {m['id']}) - Not initialized ---")
                continue
            
            print(f"\n--- Reading {m['name']} (Slave {m['id']}) ---")
            meter_start = time.time()
            successful_reads = 0
            
            while time.time() - meter_start < 5:
                try:
                    if m["type"] == "ac":
                        # Read Voltage for AC (register 4)
                        val = m["obj"].read_float(4, functioncode=4)
                        print(f"{m['name']} Voltage: {val:.2f}V")
                        send_to_influxdb(m['name'], val, current_lat, current_lon)
                        successful_reads += 1
                    else:
                        # Read Voltage for DC (register 256)
                        raw_v = m["obj"].read_long(256, functioncode=3)
                        val = raw_v / 10000.0
                        print(f"{m['name']} Voltage: {val:.2f}V")
                        send_to_influxdb(m['name'], val, current_lat, current_lon)
                        successful_reads += 1
                except Exception as e:
                    print(f"{m['name']}: Read Error - {e} (continuing)")
                
                time.sleep(1)  # Frequency of reads within the 5s window
            
            if successful_reads == 0:
                print(f"{m['name']}: No successful reads in this cycle (will retry next cycle)")

except KeyboardInterrupt:
    print("\nShutting down master script gracefully...")
    influx_client.close()
    print("InfluxDB connection closed. Goodbye!")
except Exception as e:
    print(f"\nUnexpected error in main loop: {e}")
    print("Attempting to close InfluxDB connection...")
    try:
        influx_client.close()
    except:
        pass
    print("System stopped.")
