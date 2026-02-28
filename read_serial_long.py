import serial
import time

try:
    ser = serial.Serial('/dev/cu.usbserial-0001', 115200, timeout=1)
    print("Reading serial for 35 seconds (waiting for PMS warmup + WiFi)...")
    start = time.time()
    line_count = 0
    while time.time() - start < 35:
        data = ser.readline()
        if data:
            line = data.decode('utf-8', errors='replace').rstrip()
            print(line)
            line_count += 1
            # Check for WiFi-related messages
            if 'NET' in line or 'WiFi' in line or 'Portal' in line or 'AP:' in line:
                print(">>> " + line)
    ser.close()
    print(f"\nRead {line_count} lines total")
except Exception as e:
    print(f"Error: {e}")
