#!/usr/bin/env python3
"""
Quick serial reader for BME688 test — filters boot noise, shows clean output.
Usage: python3 temp/serial_reader.py
Press Ctrl+C to stop.
"""
import serial
import sys
import time

PORT = "/dev/cu.usbserial-0001"
BAUD = 115200

def main():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
    except serial.SerialException as e:
        print(f"Cannot open {PORT}: {e}")
        sys.exit(1)

    print(f"Connected to {PORT} @ {BAUD} baud")
    print("Waiting for BME688 data (ignoring boot noise)...\n")

    # Skip boot garbage for 2 seconds
    time.sleep(2)
    ser.reset_input_buffer()

    try:
        while True:
            line = ser.readline()
            if line:
                try:
                    text = line.decode("utf-8", errors="ignore").rstrip()
                    if text:
                        print(text)
                except Exception:
                    pass
    except KeyboardInterrupt:
        print("\n\nStopped.")
    finally:
        ser.close()

if __name__ == "__main__":
    main()
