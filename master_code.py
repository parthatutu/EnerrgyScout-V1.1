import minimalmodbus
import serial
import serial.rs485 
import time

# --- SHARED CONFIGURATION ---
PORT = '/dev/ttyAMA0'
BAUDRATE = 9600
BEST_DELAY = 0.01  

def setup_instrument(slave_id):
    """Initializes meter with hardware RTS settings."""
    try:
        ins = minimalmodbus.Instrument(PORT, slave_id)
        ins.serial.baudrate = BAUDRATE
        ins.serial.timeout = 0.5
        ins.mode = minimalmodbus.MODE_RTU
        ins.clear_buffers_before_each_transaction = True
        
        # Configure hardware RTS switching (GPIO 17)
        ins.serial.rs485_mode = serial.rs485.RS485Settings(
            rts_level_for_tx=True,
            rts_level_for_rx=False,
            delay_before_tx=0.01,
            delay_before_rx=BEST_DELAY
        )
        return ins
    except Exception as e:
        print(f"Failed to initialize ID {slave_id}: {e}")
        return None

# --- DEFINE AND INITIALIZE METERS ---
# We build the list and initialize the 'obj' key immediately
meters_list = [
    {"id": 4, "name": "AC Meter (ID 4)", "type": "ac", "obj": setup_instrument(4)},
    {"id": 2, "name": "DC Meter (ID 2)", "type": "dc", "obj": setup_instrument(2)},
    {"id": 3, "name": "DC Meter (ID 3)", "type": "dc", "obj": setup_instrument(3)}
]

print(f"Starting Sequential Polling (5s per device)...")
print("-" * 70)

try:
    while True:
        for meter in meters_list:
            # Get the instrument object from the dictionary
            ins = meter["obj"]
            
            # Skip if the meter failed to initialize
            if ins is None:
                print(f"Skipping {meter['name']} (Not Initialized)")
                continue
            
            print(f"\n>>> Polling {meter['name']} for 5 seconds...")
            start_time = time.time()
            
            while (time.time() - start_time) < 5:
                try:
                    if meter["type"] == "ac":
                        # Eastron SDM630: L3 Voltage (Reg 4, FC 04)
                        v_ac = ins.read_float(4, functioncode=4, number_of_registers=2)
                        print(f"[{meter['name']}] L3 Voltage: {v_ac:.2f} V")
                    
                    else:
                        # JSY DC Meter: (FC 03)
                        # Voltage: 0x0100 (256), Current: 0x0102 (258), PF: 0x010A (266)
                        v_raw = ins.read_long(256, functioncode=3)
                        i_raw = ins.read_long(258, functioncode=3)
                        pf_raw = ins.read_long(266, functioncode=3)
                        
                        voltage = v_raw / 10000.0
                        current = i_raw / 100000.0
                        pf      = pf_raw / 1000.0
                        
                        print(f"[{meter['name']}] V: {voltage:.2f}V | I: {current:.3f}A | PF: {pf:.2f}")
                
                except Exception:
                    print(f"[{meter['name']}] Read Failed")
                
                time.sleep(0.5)

except KeyboardInterrupt:
    print("\nScript stopped by user.")
