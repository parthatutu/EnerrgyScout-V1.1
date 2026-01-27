import minimalmodbus
import serial
import serial.rs485
import time

# --- SHARED CONFIGURATION ---
PORT = '/dev/ttyAMA0'
BAUDRATE = 9600
BEST_DELAY = 0.01  # Update this based on your tuner results

def setup_instrument(slave_id):
    """Initializes the meter with specific hardware RTS settings."""
    try:
        ins = minimalmodbus.Instrument(PORT, slave_id)
        ins.serial.baudrate = BAUDRATE
        ins.serial.timeout = 0.5
        ins.mode = minimalmodbus.MODE_RTU
        ins.clear_buffers_before_each_transaction = True
        
        # Configure the hardware RTS switching (GPIO 17)
        ins.serial.rs485_mode = serial.rs485.RS485Settings(
            rts_level_for_tx=True,
            rts_level_for_rx=False,
            delay_before_tx=0.01,
            delay_before_rx=BEST_DELAY
        )
        return ins
    except Exception as e:
        print(f"Initialization Error for ID {slave_id}: {e}")
        return None

# Initialize meters
meters_list = [
    {"id": 4, "name": "AC Meter (ID 4)", "type": "ac"},
    {"id": 2, "name": "DC Meter (ID 2)", "type": "dc"},
    {"id": 3, "name": "DC Meter (ID 3)", "type": "dc"}
]

# Create instrument objects
for m in meters_list:
    m["obj"] = setup_instrument(m["id"])

print(f"Starting Sequential Polling (5s per device)...")
print(f"Timing: {BEST_DELAY}s | Baud: {BAUDRATE}")
print("-" * 60)

try:
    while True:
        for meter in meters_list:
            if meter["obj"] is None: continue
            
            print(f"\n>>> Polling {meter['name']} for 5 seconds...")
            start_time = time.time()
            successes = 0
            attempts = 0
            
            while (time.time() - start_time) < 5:
                attempts += 1
                try:
                    if meter["type"] == "ac":
                        # Read SDM630 Phase 3 Voltage (Reg 4, FC 04)
                        val = meter["obj"].read_float(4, functioncode=4)
                    else:
                        # Read JSY DC Voltage (Reg 0, FC 03)
                        val = meter["obj"].read_register(0, functioncode=3) / 100.0
                    
                    print(f"[{meter['name']}] Voltage: {val:.2f} V")
                    successes += 1
                except Exception:
                    # Generic catch to keep the loop running
                    print(f"[{meter['name']}] Read Failed")
                
                time.sleep(0.5) # Poll roughly twice per second
            
            # Summary for the 5-second window
            rate = (successes / attempts * 100) if attempts > 0 else 0
            print(f"--- {meter['name']} Result: {successes}/{attempts} ({rate:.1f}%) ---")

except KeyboardInterrupt:
    print("\nStopping script...")
