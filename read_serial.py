import serial
import time

try:
    ser = serial.Serial('/dev/cu.usbserial-0001', 115200, timeout=1)
    print("Reading serial for 10 seconds...")
    start = time.time()
    while time.time() - start < 10:
        data = ser.readline()
        if data:
            print(data.decode('utf-8', errors='replace').rstrip())
    ser.close()
except Exception as e:
    print(f"Error: {e}")
